from __future__ import annotations

import json
from datetime import datetime, timezone
from urllib.request import Request, urlopen


def _get_json(url: str):
    req = Request(url, headers={'User-Agent': 'NarrativePipeline/1.0'})
    with urlopen(req, timeout=30) as r:  # nosec B310
        return json.loads(r.read().decode('utf-8'))


def fetch_bls_cpi(limit: int = 60):
    payload = _get_json('https://api.bls.gov/publicAPI/v2/timeseries/data/CUUR0000SA0')
    rows = payload.get('Results', {}).get('series', [{}])[0].get('data', [])[:limit]
    now = datetime.now(timezone.utc).isoformat()
    return [
        {
            'source': 'bls',
            'series_id': 'CUUR0000SA0',
            'year': r.get('year', ''),
            'period': r.get('period', ''),
            'value': r.get('value', ''),
            'ingested_at': now,
        }
        for r in rows
    ]


def fetch_world_bank_gdp(limit: int = 60):
    payload = _get_json('https://api.worldbank.org/v2/country/US/indicator/NY.GDP.MKTP.CD?format=json')
    values = payload[1][:limit] if isinstance(payload, list) and len(payload) > 1 else []
    now = datetime.now(timezone.utc).isoformat()
    return [
        {
            'source': 'world_bank',
            'indicator': 'NY.GDP.MKTP.CD',
            'date': r.get('date', ''),
            'value': r.get('value', None),
            'ingested_at': now,
        }
        for r in values
    ]


def fetch_ecb_exr_xml() -> str:
    url = 'https://data-api.ecb.europa.eu/service/data/EXR/D.USD.EUR.SP00.A'
    req = Request(url, headers={'User-Agent': 'NarrativePipeline/1.0'})
    with urlopen(req, timeout=30) as r:  # nosec B310
        return r.read().decode('utf-8', 'replace')
