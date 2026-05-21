# Connector Backlog Bootstrap (2026-05-21)

## Legend
- status: live_ok | key_required | blocked | unstable
- speed: S0 (same day), S1 (1-2 days), S2 (3-5 days)

## Core connectors (validated)
- FRED API | macro | status=key_required | speed=S0 | note=reachable but requires API key
- SEC submissions JSON (data.sec.gov) | filings | status=live_ok | speed=S0 | note=sample pull succeeded
- SEC companyfacts (XBRL) | fundamentals | status=live_ok | speed=S0 | note=sample pull succeeded
- CFTC FinFutWk.txt | positioning/capital flows proxy | status=live_ok | speed=S0 | note=sample pull succeeded
- World Bank API | macro global | status=live_ok | speed=S0 | note=sample pull succeeded
- BLS API | inflation/labor | status=live_ok | speed=S0 | note=sample pull succeeded
- ECB SDMX API | FX/rates | status=live_ok | speed=S0 | note=sample pull succeeded (XML)
- OpenAlex API | scientific papers | status=live_ok | speed=S0 | note=sample pull succeeded
- Crossref API | scientific metadata | status=live_ok | speed=S0 | note=sample pull succeeded
- PubMed E-utilities | scientific papers/biomed | status=live_ok | speed=S0 | note=sample pull succeeded
- DeFiLlama API | crypto capital-flow proxy | status=live_ok | speed=S0 | note=sample pull succeeded

## Connectors with friction / blocks
- arXiv API export endpoint | papers | status=unstable | speed=S1 | note=429/timeout from this environment; use arxiv abs/html fallback + retry window
- Semantic Scholar API | papers/citations | status=unstable | speed=S1 | note=429 in this environment; requires pacing and/or key
- SEC RSS feeds | regulatory news | status=blocked | speed=S1 | note=403 from current user-agent; use sec submissions + sec news webpages as fallback
- GDELT API | global news | status=unstable | speed=S1 | note=429 rate limit, needs throttling
- EPO OPS API | patents | status=blocked | speed=S2 | note=403; registration required
- USPTO developer IBD endpoint | patents | status=unstable | speed=S2 | note=503 observed

## Downloads HTML ingestion follow-up (2026-05-21)
- Converted the latest Downloads HTML to supported formats:
  - `/Users/alexandersolianin/Downloads/index (5) (1).txt`
  - `/Users/alexandersolianin/Downloads/index (5) (1).md`
- Full scan report: `docs/downloads_html_conversion_and_source_scan_2026-05-21.json`
- Result: no additional investable data-source APIs/RSS endpoints discovered from top-level Downloads HTML files (mostly website/front-end assets and static media links).

## Bootstrap data written
- data/raw_bootstrap/sec_submissions_20260521T163402Z.jsonl
- data/raw_bootstrap/cftc_finfutwk_20260521T163402Z.jsonl
- data/raw_bootstrap/bls_cpi_20260521T163402Z.jsonl
- data/raw_bootstrap/openalex_20260521T163402Z.jsonl
- data/raw_bootstrap/crossref_20260521T163402Z.jsonl
- data/raw_bootstrap/pubmed_20260521T163402Z.jsonl
- data/raw_bootstrap/ecb_exr_20260521T163402Z.xml
