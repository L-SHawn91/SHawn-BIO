# SHawn-BIO Platform Manifest

## Purpose
웹/메타 분석 플랫폼에서 생물정보 검색과 저자 모드/지식 연동 기능을 제공하는 플랫폼 레이어.

## Runtime Contract
- Primary integration points:
  - `tools/web_bio_search.py` (SHawn-WEB adapter)
  - `tools/shawn_bio_search_cli.py` (CLI bridge)
  - `tools/research_engine.py` (analysis engine)

## OpenClaw 연동
- OpenClaw 스킬은 `tools/shawn_bio_search_cli.py`를 브릿지로 사용
- `--as-bundle` 옵션으로 OpenClaw downstream 스키마에 맞춘 번들 출력 가능

## Update (2026-03-09)
- 추가: `--as-bundle` 모드 보강
- 목적: 다른 프로그램이 같은 스키마로 파싱 가능한 결과 형식 제공

## Discovery
Machine-readable metadata: `SYSTEM_PROFILE.json`
