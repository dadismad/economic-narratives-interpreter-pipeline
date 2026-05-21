from __future__ import annotations

import json
from datetime import datetime, timezone
from urllib.parse import urlencode
from urllib.request import Request, urlopen


def fetch_fred_series(series_id: str, api_key: str = ''):
    if not api_key:
        raise ValueError('FRED_API_KEY is required')

    query = urlencode(
        {
            'series_id': series_id,
            'api_key': api_key,
            'file_type': 'json',
            'sort_order': 'desc',
            'limit': 200,
        }
    )
    url = f'https://api.stlouisfed.org/fred/series/observations?{query}'
    req = Request(url, headers={'User-Agent': 'NarrativePipeline/1.0'})
    with urlopen(req, timeout=30) as r:  # nosec B310
        payload = json.loads(r.read().decode('utf-8'))

    now = datetime.now(timezone.utc).isoformat()
    rows = []
    for obs in payload.get('observations', []):
        value = obs.get('value', '.')
        if value in ('.', None, ''):
            continue
        rows.append(
            {
                'source': 'fred',
                'series_id': series_id,
                'date': obs.get('date', ''),
                'value': float(value),
                'ingested_at': now,
            }
        )
    return rows
