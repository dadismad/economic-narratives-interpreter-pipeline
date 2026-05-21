# Source Connector Backlog (2026-05-21)

Derived from live endpoint checks at 2026-05-21T19:15:53.851780Z.

## Priority 1 (immediate)

- BLS CPI API | macro | accessible_now | next: onboard_now
- CFTC FinFutWk | positioning | accessible_now | next: onboard_now
- ECB SDMX EXR | macro | accessible_now | next: onboard_now
- SEC companyfacts JSON | filings | accessible_now | next: onboard_now
- SEC submissions JSON | filings | accessible_now | next: onboard_now
- World Bank GDP API | macro | accessible_now | next: onboard_now
- FRED API (needs key) | macro | key_required_or_params | next: add_api_key

## Priority 2 (science/patents/capital flows)

- Crossref works | papers | accessible_now | next: onboard_now
- DeFiLlama protocols | capital_flows | accessible_now | next: onboard_now
- Google Patents search page | patents | accessible_now | next: onboard_now
- OpenAlex works | papers | accessible_now | next: onboard_now
- PubMed esearch | papers | accessible_now | next: onboard_now
- US Treasury FiscalData rates | capital_flows | accessible_now | next: onboard_now
- USPTO bulk data page | patents | accessible_now | next: onboard_now
- WIPO Patentscope | patents | accessible_now | next: onboard_now
- arXiv export api | papers | accessible_now | next: onboard_now
- Semantic Scholar search | papers | rate_limited | next: throttle_and_retry_or_key
- EPO OPS search (auth expected) | patents | auth_or_policy_block | next: registration_or_user_agent

## Priority 3 (news proxy / optional)

- GDELT DOC api | news_proxy | accessible_now | next: onboard_now

## TXT file check result
- Reviewed converted TXT files from Downloads, including the latest attached conversion.
- They contain product/UI/spec text and generic source categories, but no additional concrete API/RSS endpoint inventory to onboard directly.
- Therefore connector decisions are grounded on live endpoint validation above.