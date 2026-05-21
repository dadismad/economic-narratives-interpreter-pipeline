from __future__ import annotations

import json
from datetime import datetime, timezone
from urllib.request import Request, urlopen


def _get_json(url: str):
    req = Request(url, headers={'User-Agent': 'NarrativePipeline/1.0'})
    with urlopen(req, timeout=30) as r:  # nosec B310
        return json.loads(r.read().decode('utf-8'))


def fetch_defillama_protocols(limit: int = 50):
    payload = _get_json('https://api.llama.fi/protocols')
    now = datetime.now(timezone.utc).isoformat()
    out = []
    for item in payload[:limit]:
        out.append(
            {
                'source': 'defillama',
                'name': item.get('name', ''),
                'symbol': item.get('symbol', ''),
                'category': item.get('category', ''),
                'tvl': item.get('tvl', None),
                'ingested_at': now,
            }
        )
    return out


def fetch_treasury_rates(limit: int = 100):
    payload = _get_json('https://api.fiscaldata.treasury.gov/services/api/fiscal_service/v1/accounting/od/rates_of_exchange')
    now = datetime.now(timezone.utc).isoformat()
    out = []
    for item in payload.get('data', [])[:limit]:
        out.append(
            {
                'source': 'fiscaldata_rates',
                'record_date': item.get('record_date', ''),
                'country': item.get('country', ''),
                'currency': item.get('currency', ''),
                'exchange_rate': item.get('exchange_rate', ''),
                'ingested_at': now,
            }
        )
    return out
