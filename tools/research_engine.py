"""
ResearchEngine - SHawn-BIO 고도화 엔진 (v3.6)
여러 문서의 컨텍스트를 병합하여 새로운 가설이나 요약 생성
"""
import os
import sys
import asyncio
import re
from typing import List, Optional, Tuple
from loguru import logger

# 프로젝트 루트 및 시스템 폴더 경로 추가
curr_dir = os.path.dirname(os.path.abspath(__file__))
root_dir = os.path.dirname(curr_dir)
sys.path.append(os.path.join(root_dir, "99-System"))

def _inject_brain_paths():
    """SHawn-BOT/Brain 후보 경로를 sys.path에 주입"""
    workspace_parent = os.path.dirname(root_dir)
    env_brain_path = os.environ.get("SHAWN_BOT_PATH")
    candidates = [
        env_brain_path,
        os.path.join(root_dir, "99-System"),
        os.path.join(workspace_parent, "SHawn-LAB", "SHawn-BOT"),
        os.path.join(workspace_parent, "SHawn-Brain"),
        os.path.join(workspace_parent, "SHawn-Lab-Vault", "99-System"),
        os.path.join(workspace_parent, "SHawn-Lab-Vault", "99-System", "shawn_bot"),
    ]
    for base in candidates:
        if not base:
            continue
        for path in [base, os.path.join(base, "99-System"), os.path.join(base, "shawn_bot")]:
            if os.path.isdir(path) and path not in sys.path:
                sys.path.insert(0, path)


_inject_brain_paths()

# SHawnBrain 의존성 - 다중 버전 유연 임포트
BRAIN_AVAILABLE = False
brain_class = None
brain_name = None
brain_load_errors = []

for module_name, class_name in [
    ("shawn_brain_v4", "SHawnBrainV4"),
    ("shawn_brain", "SHawnBrain"),
    ("shawn_brain_v2", "SHawnBrainV2"),
    ("shawn_bot.shawn_brain_v2", "SHawnBrainV2"),
]:
    try:
        module = __import__(module_name, fromlist=[class_name])
        brain_class = getattr(module, class_name)
        brain_name = class_name
        BRAIN_AVAILABLE = True
        logger.info(f"✅ {brain_name} loaded successfully ({module_name})")
        break
    except Exception as e:
        brain_load_errors.append(f"{module_name}.{class_name}: {e}")
        continue

if not BRAIN_AVAILABLE:
    logger.warning("⚠️ SHawnBrain not available. Install SHawn-BOT/SHawn-Brain or set SHAWN_BOT_PATH.")
    for err in brain_load_errors:
        logger.warning(f"  - load failed: {err}")

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
                if brain_name == 'SHawnBrainV4':
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
        self.bio_root = root_dir  # 프로젝트 루트 (01~04 폴더 포함)
        logger.info(f"🧬 ResearchEngine initialized. Bio-Root: {self.bio_root}")

    async def meta_analyze(self, topic: str, is_debate: bool = False) -> str:
        """관련된 모든 문서(OneDrive RAG + Local md)를 찾아 통합 분석 수행"""
        logger.info(f"Starting {'Debate' if is_debate else 'Meta-Analysis'} for: {topic}")
        
        matched_content = []
        topic_tokens = [t for t in re.sub(r"[^0-9a-z가-힣\s]", " ", topic.lower()).split() if len(t) >= 2]

        # 1. 문서 검색 (Vector DB - OneDrive)
        if self.pipeline:
            try:
                rag_hits = self.pipeline.search(topic, n_results=12)
                for hit in rag_hits:
                    matched_content.append(
                        f"Source (OneDrive): {hit['source']}\n"
                        f"Score: {hit.get('score', 0):.4f}, Distance: {hit.get('distance', 0):.4f}\n"
                        f"Content:\n{hit['content'][:1000]}"
                    )
            except Exception as e:
                logger.error(f"RAG Search failed: {e}")

        # 2. 문서 검색 (Local md - 전문 구조 탐색)
        search_dirs = ["01-Analysis", "02-Literature", "03-Vault", "papers", "concepts", "analysis"]
        for sub in search_dirs:
            target_path = os.path.join(self.bio_root, sub)
            if not os.path.exists(target_path): continue
            
            for root, dirs, files in os.walk(target_path):
                for file in files:
                    if file.endswith(".md"):
                        path = os.path.join(root, file)
                        try:
                            with open(path, 'r', encoding='utf-8') as f:
                                content = f.read()
                                lowered = content.lower()
                                direct_match = topic.lower() in lowered
                                token_match_count = sum(1 for t in topic_tokens if t in lowered)
                                partial_match = token_match_count >= 1 if topic_tokens else False

                                if direct_match or partial_match:
                                    matched_content.append(f"Source ({sub}/{file}): {content[:1000]}...")
                                    if len(matched_content) >= 10: break
                        except Exception as e:
                            logger.error(f"Error reading {file}: {e}")
                if len(matched_content) >= 10: break

        if not matched_content:
            return "🔍 관련 문서를 찾을 수 없습니다. 주제를 더 광범위하게 입력해 보세요."

        combined_context = "\n\n".join(matched_content[:8])
        
        # 3. 분석/토론 프롬프트 구성
        task_type = "gemini"
        if is_debate:
            prompt = f"""
당신은 SHawn Lab의 지능형 연구 협의체(Brain Council)입니다. 
주제: '{topic}'

[연구 자료 기초]
{combined_context}

[과업]
위 자료들의 상충하는 부분이나 논리적 공백을 찾아 에이전트들끼리 치열하게 토론하세요.
마지막에는 하나로 합치지 말고, '대립하는 가설 A'와 '대립하는 가설 B'를 각각 정교하게 제시하고 Dr. SHawn이 선택할 수 있도록 권고안을 작성하세요.
"""
            task_type = "debate"
        else:
            prompt = f"""
당신은 SHawn Lab의 수석 바이오 연구원입니다. 
주제: '{topic}'

[연구 자료 기초]
{combined_context}

[과업]
1. 기존 연구들의 핵심 연결 고리 (Cross-link) 발견
2. 새로운 통합 연구 가설 (Unified Hypothesis) 제안
3. 추가 실험 설계 (Detailed Design) 제안
"""
            task_type = "gemini" # v4.5에서 지원하는 일반 지능 타입

        # 4. Brain 호출
        if not self.brain:
            logger.warning("SHawnBrain not initialized. Returning raw context only.")
            return f"⚠️ SHawnBrain 모듈 미연결. 수집된 문서:\n\n{combined_context}"

        try:
            # V4는 think() 메서드 사용, 기본은 process() 사용
            if hasattr(self.brain, 'think'):
                # V4 think() supports task_type
                response, info = await self.brain.think(prompt, task_type=task_type)
            elif hasattr(self.brain, 'process'):
                # Legacy compatibility
                response, used_model, _ = await self.brain.process(prompt, domain="bio")
            else:
                response = "⚠️ Brain 인터페이스를 확인할 수 없습니다."
        except Exception as e:
            logger.error(f"Brain processing failed: {e}")
            response = f"⚠️ 분석 중 오류 발생: {e}"

        return response

    def get_stats(self):
        """SBI 시스템 통계 반환"""
        if self.pipeline:
            return self.pipeline.get_status()
        return "Pipeline not active"

if __name__ == "__main__":
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    engine = ResearchEngine()
    print("ResearchEngine v3.6 Ready.")
