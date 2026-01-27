"""
ResearchEngine - SHawn-BIO 고도화 엔진
여러 문서의 컨텍스트를 병합하여 새로운 가설이나 요약 생성
"""
import os
import asyncio
from typing import List, Optional, Tuple
from loguru import logger

# SHawnBrain 의존성 - 외부 모듈 (SHawn-BOT)
try:
    from shawn_brain import SHawnBrain
    BRAIN_AVAILABLE = True
except ImportError:
    BRAIN_AVAILABLE = False
    logger.warning("SHawnBrain not available. Install SHawn-BOT or set PYTHONPATH.")

class ResearchEngine:
    def __init__(self):
        self.brain = SHawnBrain() if BRAIN_AVAILABLE else None
        curr_dir = os.path.dirname(os.path.abspath(__file__))
        # 연구 문서 저장 경로 (papers, concepts, analysis 폴더 참조)
        self.bio_root = curr_dir

    async def meta_analyze(self, topic: str) -> str:
        """관련된 모든 문서를 찾아 통합 분석 수행"""
        logger.info(f"Starting Meta-Analysis for: {topic}")
        
        # 1. 문서 검색
        matched_content = []
        for root, dirs, files in os.walk(self.bio_root):
            for file in files:
                if file.endswith(".md"):
                    path = os.path.join(root, file)
                    try:
                        with open(path, 'r', encoding='utf-8') as f:
                            content = f.read()
                            if topic.lower() in content.lower():
                                matched_content.append(f"Source: {file}\nContent:\n{content[:1000]}...")
                    except Exception as e:
                        logger.error(f"Error reading {file}: {e}")

        if not matched_content:
            return "🔍 관련 문서를 찾을 수 없습니다. 주제를 더 광범위하게 입력해 보세요."

        combined_context = "\n\n".join(matched_content[:5]) # 최대 5개 문서 합성
        
        # 2. 통합 추론 프롬프트
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
        
        # SHawnBrain.process 호출
        if not self.brain:
            logger.error("SHawnBrain not initialized. Cannot perform meta-analysis.")
            return "⚠️ SHawnBrain 모듈이 설치되지 않았습니다. SHawn-BOT 프로젝트를 연결하세요."

        response, used_model, _ = await self.brain.process(prompt, domain="bio")
        return response

if __name__ == "__main__":
    # 간단한 테스트 실행
    engine = ResearchEngine()
    # 예시: asyncio.run(engine.meta_analyze("Single-cell RNA-seq"))
    pass
