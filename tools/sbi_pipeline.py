# 01-Analysis/sbi_pipeline.py
"""
SBI (SHawn Bio-Intelligence) Knowledge Pipeline
FAISS 기반 벡터 검색 및 OneDrive 문서 인덱싱
"""
import os
import glob
import pickle
import re
import numpy as np
from typing import List, Dict, Optional, Tuple
from loguru import logger

# 선택적 임포트 (의존성 없을 때 graceful degradation)
try:
    import faiss
    FAISS_AVAILABLE = True
except ImportError:
    FAISS_AVAILABLE = False
    logger.warning("FAISS not installed. Run: pip install faiss-cpu")

try:
    from langchain_community.document_loaders import PyPDFLoader, TextLoader
    from langchain_text_splitters import RecursiveCharacterTextSplitter
    LANGCHAIN_AVAILABLE = True
except ImportError:
    LANGCHAIN_AVAILABLE = False
    logger.warning("LangChain not installed. Run: pip install langchain langchain-community")

try:
    from sentence_transformers import SentenceTransformer
    SENTENCE_TRANSFORMERS_AVAILABLE = True
except ImportError:
    SENTENCE_TRANSFORMERS_AVAILABLE = False
    logger.warning("Sentence Transformers not installed. Run: pip install sentence-transformers")


def get_onedrive_path() -> str:
    """환경 변수 또는 기본 경로에서 OneDrive 경로 반환"""
    # 1순위: 환경 변수
    env_path = os.environ.get('ONEDRIVE_PATH')
    if env_path and os.path.exists(env_path):
        return env_path

    # 2순위: .env 파일 (프로젝트 루트)
    curr_dir = os.path.dirname(os.path.abspath(__file__))
    env_file = os.path.join(os.path.dirname(curr_dir), '.env')
    if os.path.exists(env_file):
        try:
            with open(env_file, 'r') as f:
                for line in f:
                    if line.startswith('ONEDRIVE_PATH='):
                        path = line.split('=', 1)[1].strip().strip('"\'')
                        if os.path.exists(path):
                            return path
        except Exception:
            pass

    # 3순위: 플랫폼별 기본 경로
    home = os.path.expanduser('~')
    default_paths = [
        os.path.join(home, 'OneDrive'),  # Windows/Linux
        os.path.join(home, 'Library/CloudStorage/OneDrive-개인'),  # macOS
        os.path.join(home, 'Library/CloudStorage/OneDrive-Personal'),  # macOS (English)
    ]
    for path in default_paths:
        if os.path.exists(path):
            return path

    # 기본값 (존재하지 않을 수 있음)
    return os.path.join(home, 'OneDrive')


def get_project_root() -> str:
    """현재 파일 기준 프로젝트 루트 경로 반환"""
    curr_dir = os.path.dirname(os.path.abspath(__file__))
    return os.path.dirname(curr_dir)


def resolve_knowledge_paths(db_path: Optional[str] = None) -> Tuple[str, str]:
    """
    지식 DB 경로를 결정.
    우선순위:
    1) 인자 db_path
    2) 환경 변수 SBI_DB_PATH
    3) 기본 경로 knowledge/
    """
    root_dir = get_project_root()
    legacy_path = os.path.join(root_dir, "knowledge_base")

    if db_path:
        return db_path, legacy_path

    env_db_path = os.environ.get("SBI_DB_PATH")
    if env_db_path:
        return env_db_path, legacy_path

    return os.path.join(root_dir, "knowledge"), legacy_path


class SBIPipeline:
    """SHawn Bio-Intelligence (SBI) Knowledge Pipeline (FAISS Edition)"""

    def __init__(self,
                 onedrive_path: Optional[str] = None,
                 db_path: Optional[str] = None):

        # OneDrive 경로 설정
        self.onedrive_path = onedrive_path or get_onedrive_path()

        # 프로젝트 루트 기준으로 지식 저장 경로 설정
        self.db_path, self.legacy_db_path = resolve_knowledge_paths(db_path)
        self.index_file = os.path.join(self.db_path, "faiss_index.bin")
        self.data_file = os.path.join(self.db_path, "knowledge_data.pkl")
        self.legacy_index_file = os.path.join(self.legacy_db_path, "faiss_index.bin")
        self.legacy_data_file = os.path.join(self.legacy_db_path, "knowledge_data.pkl")

        # 의존성 체크
        self._check_dependencies()

        # 임베딩 모델 로드
        if SENTENCE_TRANSFORMERS_AVAILABLE:
            self.model = SentenceTransformer('all-MiniLM-L6-v2')
        else:
            self.model = None

        if LANGCHAIN_AVAILABLE:
            self.text_splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=100)
        else:
            self.text_splitter = None

        # 인덱스 및 데이터 초기화
        self.index = None
        self.metadata = []  # List of {content, source}
        self.indexed_files = set()

        if FAISS_AVAILABLE:
            self.load_index()

        logger.info(f"SBI FAISS Pipeline initialized. Monitoring: {self.onedrive_path}")

    def _check_dependencies(self):
        """필수 의존성 체크"""
        missing = []
        if not FAISS_AVAILABLE:
            missing.append('faiss-cpu')
        if not LANGCHAIN_AVAILABLE:
            missing.append('langchain langchain-community')
        if not SENTENCE_TRANSFORMERS_AVAILABLE:
            missing.append('sentence-transformers')

        if missing:
            logger.warning(f"Missing dependencies: {', '.join(missing)}")
            logger.warning("Some features may be unavailable. Run: pip install " + ' '.join(missing))

    def load_index(self):
        """저장된 인덱스와 메타데이터 로드"""
        if not FAISS_AVAILABLE:
            return

        if os.path.exists(self.index_file) and os.path.exists(self.data_file):
            try:
                self._load_index_files(self.index_file, self.data_file)
                logger.info(f"Loaded existing index from {self.db_path} with {len(self.metadata)} chunks.")
                return
            except Exception as e:
                logger.error(f"Failed to load index from {self.db_path}: {e}")

        if os.path.exists(self.legacy_index_file) and os.path.exists(self.legacy_data_file):
            try:
                self._load_index_files(self.legacy_index_file, self.legacy_data_file)
                logger.warning(
                    "Loaded legacy index from knowledge_base/. "
                    "It will be migrated to knowledge/ on next save."
                )
                return
            except Exception as e:
                logger.error(f"Failed to load legacy index from {self.legacy_db_path}: {e}")

        self._create_new_index()

    def _load_index_files(self, index_file: str, data_file: str):
        """index/data 파일 쌍을 읽어 메모리로 로드"""
        self.index = faiss.read_index(index_file)
        with open(data_file, 'rb') as f:
            save_data = pickle.load(f)
            self.metadata = save_data.get('metadata', [])
            self.indexed_files = set(save_data.get('indexed_files', set()))

    def _create_new_index(self):
        """새 FAISS 인덱스 생성"""
        if not FAISS_AVAILABLE:
            return

        dimension = 384  # all-MiniLM-L6-v2 output dimension
        self.index = faiss.IndexFlatL2(dimension)
        self.metadata = []
        self.indexed_files = set()
        logger.info("Created fresh FAISS index.")

    def save_index(self):
        """인덱스와 메타데이터 파일로 저장"""
        if not FAISS_AVAILABLE or self.index is None:
            return

        os.makedirs(self.db_path, exist_ok=True)
        faiss.write_index(self.index, self.index_file)
        with open(self.data_file, 'wb') as f:
            pickle.dump({
                'metadata': self.metadata,
                'indexed_files': self.indexed_files
            }, f)
        logger.success("FAISS index and metadata saved.")

    def get_status(self) -> Dict[str, object]:
        """파이프라인 상태 요약"""
        return {
            "onedrive_path": self.onedrive_path,
            "db_path": self.db_path,
            "legacy_db_path": self.legacy_db_path,
            "index_exists": os.path.exists(self.index_file),
            "data_exists": os.path.exists(self.data_file),
            "indexed_files": len(self.indexed_files),
            "chunks": len(self.metadata),
            "faiss_available": FAISS_AVAILABLE,
            "langchain_available": LANGCHAIN_AVAILABLE,
            "sentence_transformers_available": SENTENCE_TRANSFORMERS_AVAILABLE,
        }

    def load_and_index(self, force: bool = False):
        """원드라이브 폴더 스캔 및 신규 파일 인덱싱 (부하 방지 배치 처리 적용)"""
        if not all([FAISS_AVAILABLE, LANGCHAIN_AVAILABLE, SENTENCE_TRANSFORMERS_AVAILABLE]):
            logger.error("Cannot index: missing required dependencies")
            return

        if not os.path.exists(self.onedrive_path):
            logger.warning(f"OneDrive path not found: {self.onedrive_path}")
            logger.info("Set ONEDRIVE_PATH environment variable or create .env file")
            return

        import time
        files = glob.glob(os.path.join(self.onedrive_path, "**/*.pdf"), recursive=True) + \
                glob.glob(os.path.join(self.onedrive_path, "**/*.txt"), recursive=True)

        new_files = [f for f in files if f not in self.indexed_files or force]
        if not new_files:
            logger.info("No new files found in OneDrive.")
            return

        logger.info(f"Found {len(new_files)} new files to index. Starting throttled indexing...")

        batch_size = 10
        for i in range(0, len(new_files), batch_size):
            batch = new_files[i:i + batch_size]
            logger.info(f"Processing Batch {i//batch_size + 1}/{(len(new_files)-1)//batch_size + 1} ({len(batch)} files)...")

            for file_path in batch:
                try:
                    self._index_file(file_path)
                    self.indexed_files.add(file_path)
                    # 파일 간 짧은 지연 (CPU 쿨링)
                    time.sleep(1)
                except Exception as e:
                    logger.error(f"Failed to index {file_path}: {e}")

            # 배치 간 중간 지연 (메모리 정리 유도)
            self.save_index()
            if i + batch_size < len(new_files):
                logger.info("Batch completed. Cooling down for 3 seconds...")
                time.sleep(3)

    def _index_file(self, file_path: str):
        """단일 파일 파싱 및 벡터화"""
        if not LANGCHAIN_AVAILABLE or not self.model:
            return

        file_name = os.path.basename(file_path)
        logger.info(f"Processing {file_name}...")

        if file_path.endswith('.pdf'):
            loader = PyPDFLoader(file_path)
        else:
            loader = TextLoader(file_path)

        documents = loader.load()
        chunks = self.text_splitter.split_documents(documents)

        contents = [chunk.page_content for chunk in chunks]
        embeddings = self.model.encode(contents).astype('float32')

        self.index.add(embeddings)
        for content in contents:
            self.metadata.append({"content": content, "source": file_name})

        logger.success(f"Added {len(chunks)} chunks from {file_name}")

    @staticmethod
    def _normalize_text(text: str) -> str:
        """비교용 텍스트 정규화"""
        lowered = text.lower()
        return re.sub(r"[^0-9a-z가-힣\s]", " ", lowered)

    def _build_query_variants(self, query: str) -> List[str]:
        """
        Query Builder:
        - 원문
        - 정규화 원문
        - 의미 있는 토큰 조합(바이그램)
        """
        normalized = self._normalize_text(query)
        tokens = [t for t in normalized.split() if len(t) >= 2]

        variants: List[str] = [query.strip(), normalized.strip()]
        variants.extend(tokens)

        # 인접 토큰 바이그램 추가
        for i in range(len(tokens) - 1):
            variants.append(f"{tokens[i]} {tokens[i + 1]}")

        # 중복 제거 + 빈 문자열 제거
        deduped = []
        seen = set()
        for v in variants:
            v = v.strip()
            if not v or v in seen:
                continue
            deduped.append(v)
            seen.add(v)
        return deduped

    def _search_single(self, query: str, probe_k: int) -> Tuple[np.ndarray, np.ndarray]:
        """단일 쿼리 벡터 검색"""
        query_vector = self.model.encode([query]).astype('float32')
        return self.index.search(query_vector, probe_k)

    def _keyword_stats(self, query: str, content: str, source: str) -> Dict[str, float]:
        """쿼리-문서 키워드 매칭 점수 산출"""
        normalized_query = self._normalize_text(query)
        q_tokens = [t for t in normalized_query.split() if len(t) >= 2]

        text = f"{source} {content}"
        normalized_text = self._normalize_text(text)

        token_hits = sum(1 for t in q_tokens if t in normalized_text)
        token_coverage = (token_hits / len(q_tokens)) if q_tokens else 0.0
        phrase_hit = 1.0 if normalized_query and normalized_query in normalized_text else 0.0
        return {
            "token_hits": float(token_hits),
            "token_coverage": float(token_coverage),
            "phrase_hit": float(phrase_hit),
        }

    @staticmethod
    def _source_quality_score(source: str) -> float:
        """
        소스 품질 가중치:
        - 논문 파일(pdf) 가중
        - 노이즈 가능성 높은 파일(fasta 등) 감점
        """
        s = source.lower()
        bonus = 0.0
        if s.endswith(".pdf"):
            bonus += 0.08
        elif s.endswith(".txt"):
            bonus -= 0.03

        if "fasta" in s or s.endswith(".fa") or s.endswith(".fasta"):
            bonus -= 0.08
        return bonus

    def search(self, query: str, n_results: int = 3, collapse_by_source: bool = True) -> List[Dict]:
        """
        지식 검색 (Recall 확장 + Re-ranking)
        - Query Builder로 변형 쿼리 생성
        - 각 변형 쿼리 결과를 합집합으로 모음
        - semantic distance + keyword match + variant hit 수로 재정렬
        """
        if not FAISS_AVAILABLE or self.index is None or len(self.metadata) == 0:
            return []

        if not self.model:
            logger.warning("Embedding model not available for search")
            return []

        query_variants = self._build_query_variants(query)
        if not query_variants:
            return []

        probe_k = min(max(n_results * 12, 60), len(self.metadata))

        # 후보 수집: idx 기준으로 병합
        candidates: Dict[int, Dict[str, object]] = {}
        for variant in query_variants:
            try:
                distances, indices = self._search_single(variant, probe_k=probe_k)
            except Exception as e:
                logger.warning(f"Search failed for variant '{variant}': {e}")
                continue

            for rank_i, idx in enumerate(indices[0]):
                if idx == -1 or idx >= len(self.metadata):
                    continue
                distance = float(distances[0][rank_i])
                if idx not in candidates:
                    candidates[idx] = {
                        "min_distance": distance,
                        "variant_hits": set([variant]),
                    }
                else:
                    prev = candidates[idx]
                    prev["min_distance"] = min(float(prev["min_distance"]), distance)
                    prev["variant_hits"].add(variant)

        if not candidates:
            return []

        total_variants = max(len(query_variants), 1)
        scored_hits: List[Dict] = []
        for idx, info in candidates.items():
            meta = self.metadata[idx]
            content = meta.get("content", "")
            source = meta.get("source", "")
            min_distance = float(info["min_distance"])
            variant_hit_count = len(info["variant_hits"])

            kw = self._keyword_stats(query, content, source)

            # distance가 작을수록 좋은 score를 위해 역변환
            semantic_score = 1.0 / (1.0 + max(min_distance, 0.0))
            variant_score = variant_hit_count / total_variants
            source_quality = self._source_quality_score(source)

            # 정확도(semantic) + 키워드 매칭 + query builder 매칭 반영
            final_score = (
                semantic_score * 0.45
                + kw["token_coverage"] * 0.35
                + variant_score * 0.15
                + kw["phrase_hit"] * 0.15
                + source_quality
            )
            if query.strip() and kw["token_hits"] <= 0:
                # 키워드 매칭이 0이면 상위 노출 억제 (완전 배제는 하지 않음)
                final_score *= 0.35

            scored_hits.append({
                "content": content,
                "source": source,
                "distance": min_distance,
                "score": float(final_score),
                "token_hits": int(kw["token_hits"]),
                "token_coverage": float(kw["token_coverage"]),
                "variant_hit_count": int(variant_hit_count),
                "source_quality": float(source_quality),
            })

        if collapse_by_source:
            grouped: Dict[str, Dict] = {}
            for hit in scored_hits:
                src = hit["source"]
                prev = grouped.get(src)
                if prev is None or hit["score"] > prev["score"]:
                    grouped[src] = hit
            scored_hits = list(grouped.values())

        # score 우선, 동점 시 distance 작은 순
        scored_hits.sort(key=lambda x: (-x["score"], x["distance"]))
        # 단일 source가 상위 결과를 과점하지 않도록 제한
        per_source_cap = 2
        selected = []
        source_count: Dict[str, int] = {}
        for hit in scored_hits:
            src = hit["source"]
            cnt = source_count.get(src, 0)
            if cnt >= per_source_cap:
                continue
            source_count[src] = cnt + 1
            selected.append(hit)
            if len(selected) >= max(n_results, 1):
                break

        # cap으로 부족하면 남은 후보를 순서대로 채움
        if len(selected) < max(n_results, 1):
            selected_ids = {(h["source"], h["content"]) for h in selected}
            for hit in scored_hits:
                key = (hit["source"], hit["content"])
                if key in selected_ids:
                    continue
                selected.append(hit)
                if len(selected) >= max(n_results, 1):
                    break

        return selected


if __name__ == "__main__":
    pipeline = SBIPipeline()
    pipeline.load_and_index()

    test_query = "오가노이드"
    results = pipeline.search(test_query)
    print(f"\nSearch Results for '{test_query}':")
    for hit in results:
        print(f"- [{hit['source']}] {hit['content'][:150]}...")
