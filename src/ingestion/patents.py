from __future__ import annotations

from datetime import datetime, timezone
from urllib.request import Request, urlopen


def _fetch_html(url: str) -> str:
    req = Request(url, headers={'User-Agent': 'NarrativePipeline/1.0'})
    with urlopen(req, timeout=30) as r:  # nosec B310
        return r.read().decode('utf-8', 'replace')


def fetch_uspto_bulk_page():
    html = _fetch_html('https://www.uspto.gov/learning-and-resources/bulk-data-products')
    return {
        'source': 'uspto_bulk',
        'title_hint': 'USPTO bulk data products',
        'html_sample': html[:2000],
        'ingested_at': datetime.now(timezone.utc).isoformat(),
    }


def fetch_wipo_patentscope_page():
    html = _fetch_html('https://patentscope.wipo.int/search/en/search.jsf')
    return {
        'source': 'wipo_patentscope',
        'title_hint': 'WIPO Patentscope',
        'html_sample': html[:2000],
        'ingested_at': datetime.now(timezone.utc).isoformat(),
    }


def fetch_google_patents_page(query: str = 'battery'):
    html = _fetch_html(f'https://patents.google.com/?q={query}')
    return {
        'source': 'google_patents',
        'query': query,
        'html_sample': html[:2000],
        'ingested_at': datetime.now(timezone.utc).isoformat(),
    }
