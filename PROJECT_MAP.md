# Project Map

이 문서는 SHawn-BIO의 폴더/파일 기능을 운영 관점에서 빠르게 파악하기 위한 맵입니다.

## 1) Runtime Layer (현재 사용)

- `tools/sbi_pipeline.py`
  - 역할: OneDrive 문서(PDF/TXT) 인덱싱, FAISS 기반 검색
  - 입력: `ONEDRIVE_PATH` 또는 시스템 기본 OneDrive 경로
  - 출력: `knowledge/faiss_index.bin`, `knowledge/knowledge_data.pkl`
  - 호환: `knowledge_base/`에 기존 인덱스가 있으면 읽을 수 있음

- `tools/research_engine.py`
  - 역할: 검색 컨텍스트 결합 후 메타분석/토론 프롬프트 생성
  - 의존: SHawnBrainV4 또는 SHawnBrain (없으면 fallback)
  - 내부 탐색 경로: `papers/`, `concepts/`, `analysis/` 등 markdown 소스

- `tools/verify_brain.py`
  - 역할: Brain, Pipeline, Engine 연결 상태 점검
  - 사용 시점: 초기 환경 셋업 확인, 장애 원인 분리

- `tools/test_sbi_research.py`
  - 역할: 지정 토픽으로 `ResearchEngine.meta_analyze()` 경로 검증

- `bio_cartridge.py`
  - 역할: BioMemory/BioValues/BioSkills/BioTools 통합 인터페이스
  - 성격: 도메인 규칙/윤리/실험 설계를 담은 상위 모듈

## 2) Data Layer

- `knowledge/`
  - 현재 기본 벡터 저장 위치
  - 대용량 바이너리 포함 가능(FAISS, pickle)

- `analysis/`
  - 분석 산출물 저장 디렉토리(현재 placeholder)

- `data/`
  - 원시/중간 데이터 저장 디렉토리(현재 placeholder)

## 3) Integration Layer

- `99-System/README.md`
  - SHawn-BOT 연동 방법(PYTHONPATH, symlink, .env)

- `manifest.yaml`
  - cartridge 메타데이터, intent 키워드, 경로 매핑

- `GEMINI.md`
  - 응답 규약/운영 프로토콜 문서

## 4) Legacy Layer (보관)

- `legacy_imports/Bioinfo_git_20260221/`
  - 과거 single-cell R 분석 자산
  - 자동화 스크립트 허브(`automation_hub.py`, `run_and_report.py`, `summarize_tree.py`, `git_sync.py`)
  - 현재 루트 런타임에 직접 연결되지 않음(참고/재사용 용도)

## 5) CI / Repository Meta

- `.github/workflows/ci-uv.yml`
  - `uv` 기반 의존성 설치 + `py_compile` 스모크 테스트

- `IMPROVEMENT_BACKLOG.md`
  - 향후 개선 항목(P0/P1/P2)

## 운영 권장 규칙

- 신규 실행 코드는 `tools/` 하위에 통합
- 벡터 DB 경로는 `knowledge/`를 표준으로 사용
- 레거시 재사용 시 `legacy_imports/`에서 복사해 `tools/` 기준으로 리팩토링 후 적용
