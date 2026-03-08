# Evidence Schema

Use this output structure for claim verification and hypothesis generation.

## JSON shape

```json
{
  "claim": "string",
  "hypothesis": "string",
  "supporting": [],
  "contradicting": [],
  "uncertain": [],
  "gaps": [],
  "refined_hypotheses": [],
  "warnings": []
}
```

## Paper object

```json
{
  "source": "pubmed|scopus|google_scholar",
  "title": "string",
  "authors": ["string"],
  "year": 2024,
  "doi": "string|null",
  "url": "string",
  "abstract": "string",
  "citations": 123,
  "evidence_score": 0.74,
  "claim_overlap": 0.56,
  "hypothesis_overlap": 0.42,
  "stance": "support|contradict|uncertain"
}
```

## Stance labeling rule

- `support`: abstract directly aligns with the claim direction.
- `contradict`: abstract directly reports opposite direction.
- `uncertain`: relevance exists but direction is unclear.

