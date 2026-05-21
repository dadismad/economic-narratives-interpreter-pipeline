from __future__ import annotations

import json
from datetime import datetime, timezone
from urllib.request import Request, urlopen


def fetch_sec_submissions(cik: str):
    cik = ''.join(ch for ch in cik if ch.isdigit()).zfill(10)
    url = f'https://data.sec.gov/submissions/CIK{cik}.json'
    req = Request(url, headers={'User-Agent': 'NarrativePipeline/1.0'})
    with urlopen(req, timeout=30) as r:  # nosec B310
        payload = json.loads(r.read().decode('utf-8'))

    recent = payload.get('filings', {}).get('recent', {})
    n = len(recent.get('accessionNumber', []))
    now = datetime.now(timezone.utc).isoformat()
    rows = []
    for i in range(min(n, 200)):
        rows.append(
            {
                'source': 'sec_submissions',
                'cik': payload.get('cik', cik),
                'company': payload.get('name', ''),
                'form': recent.get('form', [''])[i],
                'filing_date': recent.get('filingDate', [''])[i],
                'accession': recent.get('accessionNumber', [''])[i],
                'primary_doc': recent.get('primaryDocument', [''])[i],
                'ingested_at': now,
            }
        )
    return rows
