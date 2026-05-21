# Source Review (sorted) — 2026-05-21

Key parser found: OPENAI_API_KEY

## Priority 1
- BLS CPI API | cat=macro | access=accessible_now | bootstrap=success (28) | registration=no | action=none
- CFTC FinFutWk | cat=positioning | access=accessible_now | bootstrap=success (91) | registration=no | action=none
- ECB SDMX EXR | cat=macro | access=accessible_now | bootstrap=success (1) | registration=no | action=none
- SEC companyfacts JSON | cat=filings | access=accessible_now | bootstrap=success (200) | registration=no | action=none
- SEC submissions JSON | cat=filings | access=accessible_now | bootstrap=success (200) | registration=no | action=none
- World Bank GDP API | cat=macro | access=accessible_now | bootstrap=success (50) | registration=no | action=none
- FRED API (needs key) | cat=macro | access=key_required_or_params | bootstrap=skipped (0) | registration=yes | action=register_and_provide_key

## Priority 2
- Crossref works | cat=papers | access=accessible_now | bootstrap=success (20) | registration=no | action=none
- DeFiLlama protocols | cat=capital_flows | access=accessible_now | bootstrap=success (50) | registration=no | action=none
- Google Patents search page | cat=patents | access=accessible_now | bootstrap=success (1) | registration=no | action=none
- OpenAlex works | cat=papers | access=accessible_now | bootstrap=success (20) | registration=no | action=none
- PubMed esearch | cat=papers | access=accessible_now | bootstrap=success (20) | registration=no | action=none
- Semantic Scholar search | cat=papers | access=rate_limited | bootstrap=not_run (0) | registration=no | action=optional_key_for_rate_limit
- US Treasury FiscalData rates | cat=capital_flows | access=accessible_now | bootstrap=success (100) | registration=no | action=none
- USPTO bulk data page | cat=patents | access=accessible_now | bootstrap=success (1) | registration=no | action=none
- WIPO Patentscope | cat=patents | access=accessible_now | bootstrap=success (1) | registration=no | action=none
- arXiv export api | cat=papers | access=accessible_now | bootstrap=success (20) | registration=no | action=none
- EPO OPS search (auth expected) | cat=patents | access=auth_or_policy_block | bootstrap=not_run (0) | registration=yes | action=register_and_provide_key

## Priority 3
- GDELT DOC api | cat=news_proxy | access=accessible_now | bootstrap=not_run (0) | registration=no | action=none

## Registration needed from you
- FRED API key (required for FRED series ingestion).
- EPO OPS credentials (required for authenticated patent API access).
- Semantic Scholar key is optional (improves rate limits).