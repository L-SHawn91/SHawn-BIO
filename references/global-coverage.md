# Global Coverage Matrix

## Papers

- PubMed (NCBI)
- Scopus (Elsevier, API key)
- Google Scholar (SerpAPI, API key)
- Europe PMC
- OpenAlex
- Crossref

## Datasets

- GEO (NCBI)
- SRA (NCBI)
- BioProject (NCBI)
- ArrayExpress/BioStudies (EBI)
- PRIDE (EBI)
- ENA (EBI ENA Portal API)
- BIGD/GSA (NGDC/CNCB)
- CNGBdb (best-effort public/AJAX parsing)
- DDBJ (best-effort public parsing)

## Coverage notes

- This is a broad global public-API coverage set for biomedical literature and omics datasets.
- ENA and BIGD generally return accession-level hits.
- CNGBdb and DDBJ can be rate-limited or JS-only, so automation may return partial or empty parsable records.
- Some major regional/commercial sources (e.g., CNKI, Wanfang, SinoMed, Embase full API, Web of Science full API) require separate licenses or restricted integrations.
- Use this stack for reproducible, scriptable, and legally safer automation first.
