# 99-System: SHawn-BOT Integration Layer

이 폴더는 SHawn-BOT 프로젝트와의 연동을 위한 시스템 레이어입니다.

## 연동 방법

### Option 1: PYTHONPATH 설정 (권장)
```bash
export PYTHONPATH="/path/to/SHawn-BOT:$PYTHONPATH"
```

### Option 2: 심볼릭 링크 생성
```bash
# SHawn-BOT 프로젝트 경로에 맞게 수정
ln -s /path/to/SHawn-BOT/shawn_brain_v4.py ./shawn_brain_v4.py
ln -s /path/to/SHawn-BOT/shawn_brain.py ./shawn_brain.py
ln -s /path/to/SHawn-BOT/engines ./engines
ln -s /path/to/SHawn-BOT/utils ./utils
```

### Option 3: .env 파일 사용
프로젝트 루트에 `.env` 파일 생성:
```
SHAWN_BOT_PATH=/path/to/SHawn-BOT
ONEDRIVE_PATH=/path/to/OneDrive
```

## 필요한 모듈
- `shawn_brain_v4.py`: SHawnBrainV4 클래스 (최신 v4.5 아키텍처)
- `shawn_brain.py`: SHawnBrain 클래스 (기본 버전)
- `engines/`: 추론 엔진 모듈
- `utils/`: 유틸리티 함수

---
*SHawn Lab System Integration*
