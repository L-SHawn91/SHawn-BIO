# test_sbi_research.py
import asyncio
from research_engine import ResearchEngine
from loguru import logger

async def main():
    logger.info("🧪 SHawn-BIO: OneDrive Intelligence Integration Test")
    
    engine = ResearchEngine()
    
    # 원드라이브에 있는 내용과 관련된 주제로 분석 요청
    topic = "오가노이드 기술의 암 치료 적용 및 한계"
    logger.info(f"Target Topic: {topic}")
    
    # 메타 분석 수행 (RAG 작동 여부 확인)
    response = await engine.meta_analyze(topic)
    
    print("\n" + "="*50)
    print("🔬 RESEARCH ENGINE ANALYSIS REPORT")
    print("="*50)
    print(response)
    print("="*50)

if __name__ == "__main__":
    asyncio.run(main())
