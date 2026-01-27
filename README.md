# SHawn-BIO: Specialized Bio-Research Hub (v3.6)

> **SHawn Lab: High-Performance Bio-Science Research & Intelligence Division**

암 치료, 오가노이드 기술, 정밀 의료 등 첨단 바이오 사이언스 리서치 데이터와 AI 기반의 지능형 분석 파이프라인을 운영하는 전문 리서치 허브입니다.

## Directory Structure

```
SHawn-BIO/
├── 01-Analysis/          # 핵심 분석 엔진 및 파이프라인
│   ├── research_engine.py    # 메타 분석 엔진 (v3.5)
│   ├── sbi_pipeline.py       # FAISS 벡터 검색 파이프라인
│   ├── test_sbi_research.py  # 통합 테스트 스크립트
│   └── verify_brain.py       # Brain 모듈 검증
├── 99-System/            # SHawn-BOT 연동 레이어
├── analysis/             # 분석 결과 저장소
├── assets/               # 시각화 차트 및 이미지
├── concepts/             # 연구 개념 및 가설 메모
├── papers/               # 논문 및 문헌 자료
├── knowledge_base/       # FAISS 벡터 인덱스 (gitignore)
├── requirements.txt      # Python 의존성
└── GEMINI.md            # 시스템 프로토콜
```

## SBI (SHawn Bio-Intelligence)

OneDrive 연동 하이브리드 지식 엔진:

- **Search**: `sbi_pipeline.py` - FAISS 기반 고속 벡터 검색
- **Analyze**: `research_engine.py` - 메타 분석 및 가설 생성

### 환경 설정

```bash
# 1. 의존성 설치
pip install -r requirements.txt

# 2. OneDrive 경로 설정 (선택)
export ONEDRIVE_PATH="/path/to/your/OneDrive"

# 또는 .env 파일 생성
echo 'ONEDRIVE_PATH="/path/to/OneDrive"' > .env
```

### SHawn-BOT 연동

```bash
# PYTHONPATH로 SHawn-BOT 연결
export PYTHONPATH="/path/to/SHawn-BOT:$PYTHONPATH"
```

## Quick Start

```bash
# 1. 환경 검증
python 01-Analysis/verify_brain.py

# 2. 통합 테스트 실행
python 01-Analysis/test_sbi_research.py
```

## Governance

- 모든 연구 결과는 **What-Why-How** 삼단논법 준수
- 상세 운영 규정은 `GEMINI.md` 참조

---
*Powered by SHawn-Bot AI-Intelligence Network (v3.6)*
