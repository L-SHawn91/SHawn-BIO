"""
ResearchEngine - SHawn-BIO 고도화 엔진 (v3.5)
여러 문서의 컨텍스트를 병합하여 새로운 가설이나 요약 생성
"""
import os
import asyncio
from typing import List, Optional, Tuple
from loguru import logger

# SHawnBrain 의존성 - 유연한 임포트 지원
BRAIN_AVAILABLE = False
brain_class = None

# 환경에 따라 적절한 Brain 모듈 로드
try:
    # 1순위: SHawn-BOT의 최신 v4 아키텍처
    from shawn_brain_v4 import SHawnBrainV4
    brain_class = SHawnBrainV4
    BRAIN_AVAILABLE = True
    logger.info("✅ SHawnBrainV4 loaded successfully")
except ImportError:
    try:
        # 2순위: 기본 SHawnBrain
        from shawn_brain import SHawnBrain
        brain_class = SHawnBrain
        BRAIN_AVAILABLE = True
        logger.info("✅ SHawnBrain loaded successfully")
    except ImportError:
        logger.warning("⚠️ SHawnBrain not available. Install SHawn-BOT or set PYTHONPATH.")

# 로컬 SBI Pipeline 임포트
try:
    from sbi_pipeline import SBIPipeline
    PIPELINE_AVAILABLE = True
except ImportError:
    PIPELINE_AVAILABLE = False
    logger.warning("⚠️ SBIPipeline not available. RAG search disabled.")


class ResearchEngine:
    """SHawn-BIO 메타 분석 엔진"""

    def __init__(self):
        # Brain 초기화 (가용 버전에 따라)
        if BRAIN_AVAILABLE and brain_class:
            try:
                # V4는 use_ensemble 파라미터 지원
                if brain_class.__name__ == 'SHawnBrainV4':
                    self.brain = brain_class(use_ensemble=False)
                else:
                    self.brain = brain_class()
            except Exception as e:
                logger.error(f"Failed to initialize brain: {e}")
                self.brain = None
        else:
            self.brain = None

        # Pipeline 초기화
        if PIPELINE_AVAILABLE:
            try:
                self.pipeline = SBIPipeline()
            except Exception as e:
                logger.error(f"Failed to initialize pipeline: {e}")
                self.pipeline = None
        else:
            self.pipeline = None

        # 연구 문서 경로 설정
        curr_dir = os.path.dirname(os.path.abspath(__file__))
        self.bio_root = os.path.dirname(curr_dir)  # 프로젝트 루트

        logger.info(f"🧬 ResearchEngine initialized. Bio-Root: {self.bio_root}")

    async def meta_analyze(self, topic: str) -> str:
        """관련된 모든 문서(Local md + OneDrive RAG)를 찾아 통합 토론 분석 수행"""
        logger.info(f"Starting Meta-Analysis for: {topic}")

        matched_content = []

        # 1. RAG 검색 (OneDrive - Pipeline 사용 가능 시)
        if self.pipeline:
            try:
                rag_hits = self.pipeline.search(topic, n_results=5)
                for hit in rag_hits:
                    matched_content.append(
                        f"Source (OneDrive): {hit['source']}\nContent:\n{hit['content'][:1000]}"
                    )
            except Exception as e:
                logger.warning(f"RAG search failed: {e}")

        # 2. 로컬 문서 검색 (Local md files)
        search_dirs = ['papers', 'concepts', 'analysis', '01-Analysis']
        for search_dir in search_dirs:
            dir_path = os.path.join(self.bio_root, search_dir)
            if not os.path.exists(dir_path):
                continue
            for root, dirs, files in os.walk(dir_path):
                for file in files:
                    if file.endswith(".md"):
                        path = os.path.join(root, file)
                        try:
                            with open(path, 'r', encoding='utf-8') as f:
                                content = f.read()
                                if topic.lower() in content.lower():
                                    matched_content.append(
                                        f"Source: {file}\nContent:\n{content[:1000]}..."
                                    )
                        except Exception as e:
                            logger.error(f"Error reading {file}: {e}")

        if not matched_content:
            return "🔍 관련 문서를 찾을 수 없습니다. 주제를 더 광범위하게 입력해 보세요."

        combined_context = "\n\n".join(matched_content[:5])  # 최대 5개 문서 합성

        # 3. 통합 추론 프롬프트
        prompt = f"""
당신은 SHawn Lab의 수석 바이오 연구원입니다.
다음은 '{topic}'과 관련된 기존 연구 문서들입니다:

{combined_context}

위 정보들을 바탕으로 다음 연구 과업을 수행하세요:
1. 기존 연구들의 핵심 연결 고리 (Cross-link) 발견
2. 새로운 연구 가설 (Hypothesis) 제안
3. 추가 실험 설계 (Experimental Design) 제안

모든 결과는 한국어로 작성하며, 전문적이고 통찰력 있는 형식을 유지하세요.
"""

        # 4. Brain 호출
        if not self.brain:
            logger.warning("SHawnBrain not initialized. Returning raw context only.")
            return f"⚠️ SHawnBrain 모듈 미연결. 수집된 문서:\n\n{combined_context}"

        try:
            # V4는 think() 메서드 사용, 기본은 process() 사용
            if hasattr(self.brain, 'think'):
                response, info = await self.brain.think(prompt, task_type="debate")
            elif hasattr(self.brain, 'process'):
                response, used_model, _ = await self.brain.process(prompt, domain="bio")
            else:
                response = "⚠️ Brain 인터페이스를 확인할 수 없습니다."
        except Exception as e:
            logger.error(f"Brain processing failed: {e}")
            response = f"⚠️ 분석 중 오류 발생: {e}"

        return response


if __name__ == "__main__":
    # 간단한 테스트 실행
    engine = ResearchEngine()
    # 예시: asyncio.run(engine.meta_analyze("Single-cell RNA-seq"))
    pass
