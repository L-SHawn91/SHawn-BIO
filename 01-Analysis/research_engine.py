"""
ResearchEngine - SHawn-BIO 고도화 엔진
여러 문서의 컨텍스트를 병합하여 새로운 가설이나 요약 생성
"""
import os
import sys
from typing import List, Optional
from loguru import logger

# 프로젝트 루트 및 시스템 폴더 경로 추가
curr_dir = os.path.dirname(os.path.abspath(__file__))
root_dir = os.path.dirname(curr_dir)
sys.path.append(os.path.join(root_dir, "99-System"))

from shawn_brain_v4 import SHawnBrainV4
import sbi_pipeline

class ResearchEngine:
    def __init__(self):
        # 최신 v4.5 아키텍처 사용
        self.brain = SHawnBrainV4(use_ensemble=False)
        self.pipeline = sbi_pipeline.SBIPipeline()
        self.bio_root = root_dir # 상위 루트 (01~04 폴더 포함)

    async def meta_analyze(self, topic: str, is_debate: bool = False) -> str:
        """관련된 모든 문서(OneDrive RAG + Local md)를 찾아 통합 분석 수행"""
        logger.info(f"Starting {'Debate' if is_debate else 'Meta-Analysis'} for: {topic}")
        
        # 1. 문서 검색 (Vector DB - OneDrive)
        matched_content = []
        try:
            rag_hits = self.pipeline.search(topic, n_results=5)
            for hit in rag_hits:
                matched_content.append(f"Source (OneDrive): {hit['source']}\nContent:\n{hit['content'][:1000]}")
        except Exception as e:
            logger.error(f"RAG Search failed: {e}")

        # 2. 문서 검색 (Local md - 전문 구조 탐색)
        search_dirs = ["01-Analysis", "02-Literature", "03-Vault"]
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
                                if topic.lower() in content.lower():
                                    matched_content.append(f"Source ({sub}/{file}): {content[:1000]}...")
                                    if len(matched_content) >= 10: break
                        except Exception as e:
                            logger.error(f"Error reading {file}: {e}")
                if len(matched_content) >= 10: break

        if not matched_content:
            return "🔍 관련 문서를 찾을 수 없습니다. 주제를 더 광범위하게 입력해 보세요."

        combined_context = "\n\n".join(matched_content[:8])
        
        # 3. 분석/토론 프롬프트 구성
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

        # SHawnBrainV4.think 호출 (v4.5 아키텍처)
        response, info = await self.brain.think(prompt, task_type=task_type)
        return response

    def get_stats(self):
        """SBI 시스템 통계 반환"""
        return self.pipeline.get_status()

if __name__ == "__main__":
    engine = ResearchEngine()
    print("ResearchEngine v3.5 Ready.")
