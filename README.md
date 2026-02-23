# SHawn-BIO

SHawn-BIO는 바이오 리서치용 지식 검색(SBI)과 메타 분석(ResearchEngine)을 제공하는 Python 워크스페이스입니다.

## 현재 구조 (실제 기준)

```text
SHawn-BIO/
├── tools/                     # 실행 핵심 모듈
│   ├── sbi_pipeline.py        # OneDrive 문서 인덱싱 + FAISS 검색
│   ├── research_engine.py     # RAG + Brain 연계 메타 분석
│   ├── verify_brain.py        # 연동/환경 점검
│   └── test_sbi_research.py   # 통합 테스트 스크립트
├── bio_cartridge.py           # Bio cartridge 통합 인터페이스
├── knowledge/                 # 벡터 인덱스/메타데이터 저장 위치(기본)
├── analysis/                  # 분석 출력 저장소
├── data/                      # 데이터 저장소
├── 99-System/                 # SHawn-BOT 연동 레이어 문서
├── legacy_imports/            # 과거 프로젝트 및 자동화 스크립트 보관
├── manifest.yaml              # cartridge manifest
├── GEMINI.md                  # 운영 프로토콜
└── requirements.txt           # Python 의존성
```

자세한 폴더별 기능은 `PROJECT_MAP.md`를 참고하세요.

## 핵심 컴포넌트

- `tools/sbi_pipeline.py`
  - OneDrive의 PDF/TXT를 파싱해 벡터 인덱스를 생성
  - 기본 DB 경로: `knowledge/`
  - 구버전 `knowledge_base/`가 있으면 로드 호환
- `tools/research_engine.py`
  - SBI 검색 결과 + 로컬 문서를 결합해 메타 분석
  - SHawnBrainV4/SHawnBrain이 있으면 연결, 없으면 graceful fallback
- `bio_cartridge.py`
  - Memory/Values/Skills/Tools 구조의 바이오 도메인 인터페이스

## 환경 설정

```bash
# 가상환경/의존성
uv venv
uv pip install -r requirements.txt

# 선택: OneDrive 경로 지정
export ONEDRIVE_PATH="/path/to/OneDrive"

# 선택: SHawn-BOT 연동 경로
export PYTHONPATH="/path/to/SHawn-BOT:$PYTHONPATH"

# 권장: SHawn-BOT/Brain 루트 지정 (자동 탐지 보조)
export SHAWN_BOT_PATH="/path/to/SHawn-BOT"

# 선택: 지식 DB 경로 오버라이드
export SBI_DB_PATH="/path/to/custom/knowledge"
```

## 실행 가이드

```bash
# 1) 연동 상태 점검
uv run python tools/verify_brain.py

# 2) 문서 인덱싱
uv run python tools/sbi_pipeline.py

# 3) 통합 테스트
uv run python tools/test_sbi_research.py

# 4) cartridge 단독 테스트
uv run python bio_cartridge.py
```

## 참고

- `legacy_imports/`는 현재 운영 코드가 아닌 과거 자산 보관용입니다.
- CI는 `.github/workflows/ci-uv.yml`에서 `py_compile` 스모크 체크를 수행합니다.
