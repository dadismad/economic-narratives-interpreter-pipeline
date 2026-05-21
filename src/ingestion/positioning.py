from __future__ import annotations

import csv
import io
from datetime import datetime, timezone
from urllib.request import Request, urlopen


def fetch_cftc_finfutwk(max_rows: int = 300):
    url = 'https://www.cftc.gov/dea/newcot/FinFutWk.txt'
    req = Request(url, headers={'User-Agent': 'NarrativePipeline/1.0'})
    with urlopen(req, timeout=30) as r:  # nosec B310
        text = r.read().decode('utf-8', 'replace')

    now = datetime.now(timezone.utc).isoformat()
    out = []
    for i, row in enumerate(csv.reader(io.StringIO(text))):
        if i >= max_rows:
            break
        out.append({'source': 'cftc_finfutwk', 'row_index': i, 'raw': row, 'ingested_at': now})
    return out
