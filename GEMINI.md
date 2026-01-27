# SHawn Lab: Bio-Project System Protocols (BIO-v3.6)

## 1. Identity & Persona
- **Domain:** Bio-Science Research & Data Intelligence
- **Protocol:** **What-Why-How** (Strict Structure)
- **Engine:** **SBI (SHawn Bio-Intelligence)**

## 2. Directory Standards

| Folder | Description | Key Contents |
| :--- | :--- | :--- |
| **`01-Analysis/`** | Core Data Analysis | `sbi_pipeline.py`, `research_engine.py` |
| **`99-System/`** | Brain Architecture | Integration layer to `SHawn-BOT` |
| **`analysis/`** | Analysis Results | Generated reports, outputs |
| **`assets/`** | Visual Indicators | Charts, Generated Bio-Images |
| **`concepts/`** | Research Ideas | Hypotheses, Strategy Logs |
| **`papers/`** | Literature | Reference PDFs, Papers |
| **`knowledge_base/`** | Vector Index | FAISS index (gitignored) |

## 3. SBI Knowledge Engineering

### Indexing
- 환경 변수 `ONEDRIVE_PATH` 또는 `.env` 파일로 OneDrive 경로 설정
- 저부하 배치 인덱싱 (10 files/batch, 3s cooldown)

### Vector Store
- `FAISS` 엔진 사용 (`faiss-cpu`)
- `all-MiniLM-L6-v2` 임베딩 모델

### Inference
- `SHawnBrainV4` 또는 `SHawnBrain` 자동 감지
- Graceful degradation 지원 (모듈 미설치 시 로컬 문서만 검색)

## 4. Environment Configuration

```bash
# Required
export ONEDRIVE_PATH="/path/to/OneDrive"
export PYTHONPATH="/path/to/SHawn-BOT:$PYTHONPATH"

# Or use .env file
ONEDRIVE_PATH=/path/to/OneDrive
SHAWN_BOT_PATH=/path/to/SHawn-BOT
```

## 5. Security & Storage
- 대용량 데이터(`knowledge_base/`) 및 `venv`는 Git에 커밋하지 않음
- `.env` 파일은 `.gitignore`에 포함

---
*SHawn Lab - Global Protocol 2026*
