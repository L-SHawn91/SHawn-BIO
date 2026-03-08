# Dataset Search (Global Omics Sources)

Use `scripts/dataset_search.py` when the user asks for dataset accessions (not just papers), especially for reanalysis-ready evidence.

## Command

```bash
python3 scripts/dataset_search.py \
  --query "endometrial organoid" \
  --organism "Homo sapiens" \
  --assay "RNA-Seq" \
  --max-per-source 25 \
  --out datasets.json
```

## Output fields

Each dataset item includes:

- `repository`: `geo | sra | bioproject | arrayexpress | pride | ena | bigd | cngb | ddbj`
- `accession`
- `title`
- `organism`
- `assay`
- `sample_count`
- `raw_available`
- `processed_available`
- `url`
- `relevance_score`

## Practical guidance

1. Start broad (`query` only), then add `organism` and `assay` to improve precision.
2. Keep `geo+sra+ena+bigd` enabled for accession recall, then down-select by relevance.
3. Treat `cngb` and `ddbj` as best-effort channels because public search interfaces are often JS-driven/rate-limited.
4. For manuscript-ready output, report top 5-15 accessions with reason-to-claim mapping.
