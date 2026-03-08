# Source Integration

## Access model

- PubMed: no key required (key optional for rate/performance).
- Scopus: requires Elsevier API key (`SCOPUS_API_KEY`).
- Google Scholar: no official public API. Use approved intermediaries such as SerpAPI (`SERPAPI_API_KEY`).

## Why this order

- PubMed and Scopus provide better reproducibility and structured metadata.
- Google Scholar improves recall but is less structured and can have duplicate/indirect records.

## Query strategy

1. Run a broad query for recall.
2. Add claim entities and outcome terms for precision.
3. Keep a small synonym expansion set only when recall is too low.

## Error handling

- If one source fails, continue with others.
- Return explicit `warnings` per source.
- Distinguish auth failure (`401/403`) from rate limit (`429`) and not-found behavior.

## Compliance

- Avoid direct scraping workflows for Google Scholar.
- Prefer provider APIs that clearly permit automated access.

