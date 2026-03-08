---
name: shawn-bio-search
description: Use this skill for high-precision biomedical paper and dataset search with claim-level evidence scoring, citation sentence support, and hypothesis generation using PubMed, Scopus, Scholar, Europe PMC, OpenAlex, Crossref, and major omics datasets.
---

# SHawn-Bio-Search

## Overview

Use this skill for rigorous paper retrieval when the user needs citation-backed evidence for a sentence, claim-level verification, or hypothesis building. Prioritize PubMed and Scopus for reliability, then use Google Scholar results as recall expansion.

## Source Priority

1. PubMed: Biomedical primary source with stable identifiers.
2. Scopus: Broad coverage and citation metadata for impact filtering.
3. Google Scholar: Recall expansion only, preferably via SerpAPI. Do not rely on direct scraping workflows.
4. Europe PMC, OpenAlex, Crossref: global recall/metadata expansion.

## Workflow

### 1. Frame the claim or hypothesis

Convert user intent into one of these forms:

- Claim check: one sentence needing supporting/contradicting papers.
- Hypothesis build: target mechanism + population + condition + expected direction.
- Exploration: broad topic needing high recall first.

If a sentence is given, preserve exact key entities and outcomes before searching.

### 2. Retrieve candidates with source-aware queries

Use the helper script for normalized multi-source retrieval:

```bash
python3 scripts/gather_papers.py \
  --query "endometrial organoid progesterone resistance" \
  --claim "Progesterone resistance is increased in long-term endometrial organoid culture." \
  --hypothesis "Chronic inflammatory signaling contributes to progesterone resistance in organoids." \
  --max-per-source 20 \
  --out results.json
```

Environment variables:

- `SCOPUS_API_KEY` required for Scopus.
- `SCOPUS_INSTTOKEN` optional institutional token.
- `SERPAPI_API_KEY` required for Google Scholar via SerpAPI.
- `NCBI_API_KEY` optional for higher PubMed throughput.


### 2b. Retrieve datasets for reanalysis

Use the dataset helper when the user asks for accession-level data:

```bash
python3 scripts/dataset_search.py \
  --query "endometrial organoid" \
  --organism "Homo sapiens" \
  --assay "RNA-Seq" \
  --max-per-source 25 \
  --out datasets.json
```

This searches GEO, SRA, BioProject, ArrayExpress/BioStudies, PRIDE, ENA, BIGD/GSA, CNGBdb(best-effort), and DDBJ(best-effort) and ranks accessions by relevance.

### 2c. Fast mode for latency priority

If API 키가 없더라도 **다른 기능보다 먼저** 동작해야 할 때는 `_fast`를 사용해 1차 근거를 빠르게 확보합니다.

- `search_bundle.py --fast`는 기본적으로 **pubmed + europe_pmc + openalex** 중심으로 빠르게 수행
- 데이터셋 검색은 fast 기본 OFF (`--include-datasets`로 강제)
- paper per-source 개수를 자동 상한(기본 8)으로 줄여 지연 최소화
- 결과에는 경고 메시지로 fast 모드/커버리지 제약을 남김

### 3. Rank for evidence quality, not just keyword match

Prefer papers that satisfy more of these:

- Direct overlap with claim entities and outcome terms.
- Recent year, but keep seminal older papers when heavily cited.
- DOI/PMID present and venue quality is clear.
- Abstract explicitly supports or contradicts the sentence.

Use output fields from the script:

- `evidence_score`
- `stage1_score`
- `stage2_score`
- `claim_overlap`
- `hypothesis_overlap`
- `best_support_sentence`
- `best_contradict_sentence`

### 4. Build citation-ready output

Always return:

1. Top supporting papers
2. Top contradicting or uncertain papers
3. Confidence summary and evidence gaps
4. Refined hypothesis candidates

Use the schema in `references/evidence-schema.md`.

## Rules

- For medical or biomedical claims, do not depend on Google Scholar only.
- If Scopus or Scholar keys are missing, continue with PubMed and clearly state coverage limits.
- If source APIs disagree, report disagreement explicitly instead of forcing consensus.
- For sentence-level citations, include exact claim-to-evidence mapping in output.

## References

- Source policy and API behavior: `references/source-integration.md`
- Output structure and evidence tags: `references/evidence-schema.md`
- Dataset-focused retrieval: `references/dataset-search.md`
- Global coverage map: `references/global-coverage.md`



## One-Command Global Search

Use one command to search papers and datasets together:

```bash
python3 scripts/search_bundle.py \
  --query "endometrial organoid" \
  --claim "endometrial organoid progesterone response is altered" \
  --hypothesis "inflammatory signaling contributes to progesterone resistance" \
  --organism "Homo sapiens" \
  --assay "RNA-Seq" \
  --out bundle.json
```

## SHawn-BIO Bridge (Web 연결)

아래 스크립트는 SHawn-BIO의 브리지 CLI를 통해 SHawn-WEB 검색 기능(`author` 동명이인 분류 포함)을 OpenClaw 스킬에서 직접 실행한다.

```bash
./scripts/run_shawn_bio_bridge.sh \
  "endometrial organoid soohyung lee" \
  "Soohyung Lee,Lee SH,이수형" \
  "/tmp/shawn_bio_author.json"
```

- `SHAWN_BIO_ROOT` 환경변수로 SHawn-BIO 경로를 변경할 수 있다.
- 저자 별칭을 생략하면 `broad` 모드로 실행된다.

Fast (latency-first) execution:

```bash
python3 scripts/search_bundle.py \
  --query "endometrial organoid" \
  --claim "endometrial organoid progesterone response is altered" \
  --hypothesis "inflammatory signaling contributes to progesterone resistance" \
  --organism "Homo sapiens" \
  --assay "RNA-Seq" \
  --max-papers-per-source 8 \
  --fast \
  --out bundle_fast.json
```

## Review List 강화

검색 결과(bundle.json)를 리뷰 인용목록으로 자동 정리:

```bash
python3 scripts/build_review_list.py \
  --bundle bundle.json \
  --out review_list.md \
  --top 25 \
  --source-cap 5 \
  --doi-only \
  --include endometr \
  --exclude prostate,colorectal
```

이 단계는 중복 제거, 소스 편향 완화, 섹션별 분류(Foundational/Implantation/Methods 등)를 수행한다.


## One-Command Review Pipeline

아래 한 줄로 논문+데이터셋 검색과 리뷰 인용목록 생성을 끝낼 수 있다:

```bash
./scripts/run_review_pipeline.sh \
  "endometrial organoid" \
  "endometrial organoid progesterone response is altered" \
  "inflammatory signaling contributes to progesterone resistance" \
  "Homo sapiens" \
  "RNA-Seq" \
  "./outputs/endometrial_organoid_pipeline"
```

빠른 통합 모드:

```bash
./scripts/run_review_pipeline.sh \
  "endometrial organoid" \
  "endometrial organoid progesterone response is altered" \
  "inflammatory signaling contributes to progesterone resistance" \
  "Homo sapiens" \
  "RNA-Seq" \
  "./outputs/endometrial_organoid_fast" \
  --fast
```

데이터셋까지 강제 포함:

```bash
./scripts/run_review_pipeline.sh \
  "endometrial organoid" \
  "endometrial organoid progesterone response is altered" \
  "inflammatory signaling contributes to progesterone resistance" \
  "Homo sapiens" \
  "RNA-Seq" \
  "./outputs/endometrial_organoid_fast_with_datasets" \
  --fast --with-datasets
```


## Ultra Outputs

`run_review_pipeline.sh` 실행 시 아래 산출물이 자동 생성된다.

- `<prefix>_bundle.json` : 논문+데이터셋 통합 검색 결과
- `<prefix>_review_list.md` : 리뷰용 정제 인용목록
- `<prefix>_citations.bib` : BibTeX
- `<prefix>_citations.csv` : CSV 인용목록
- `<prefix>_citations.md` : Markdown 인용목록
- `<prefix>_pubmed_trends.csv` : PubMed 연도별 출판 트렌드
