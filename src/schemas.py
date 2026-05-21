from __future__ import annotations

from datetime import datetime
from typing import Any, Dict, List


class SchemaError(ValueError):
    pass


_ALLOWED_FACTORS = {
    'inflation',
    'interest_rates',
    'credit_conditions',
    'liquidity',
    'currency',
    'geopolitical_risk',
    'growth',
}


def _require(record: Dict[str, Any], key: str) -> Any:
    value = record.get(key)
    if value in (None, ''):
        raise SchemaError(f"Missing required field: {key}")
    return value


def validate_rss_record(record: Dict[str, Any]) -> Dict[str, Any]:
    if not isinstance(record, dict):
        raise SchemaError('RSS record must be an object')

    feed_url = str(_require(record, 'feed_url'))
    link = str(_require(record, 'link'))
    title = str(_require(record, 'title'))
    summary = str(record.get('summary', ''))
    published = str(record.get('published', ''))
    ingested_at = str(_require(record, 'ingested_at'))

    if not (feed_url.startswith('http://') or feed_url.startswith('https://')):
        raise SchemaError('feed_url must be http(s)')
    if not (link.startswith('http://') or link.startswith('https://')):
        raise SchemaError('link must be http(s)')

    try:
        datetime.fromisoformat(ingested_at.replace('Z', '+00:00'))
    except ValueError as exc:
        raise SchemaError('ingested_at must be ISO-8601') from exc

    return {
        'source': str(record.get('source', 'rss')),
        'feed_url': feed_url,
        'title': title,
        'link': link,
        'published': published,
        'summary': summary,
        'ingested_at': ingested_at,
    }


def validate_narrative_candidate(item: Dict[str, Any]) -> Dict[str, Any]:
    if not isinstance(item, dict):
        raise SchemaError('Candidate must be an object')

    narrative = str(_require(item, 'narrative')).strip()
    factors = item.get('macro_factors', [])
    confidence = float(item.get('confidence', 0.0))
    method = str(item.get('method', 'keyword_fallback'))

    if not isinstance(factors, list):
        raise SchemaError('macro_factors must be a list')
    factors = [str(f).strip() for f in factors if str(f).strip()]

    for f in factors:
        if f not in _ALLOWED_FACTORS:
            raise SchemaError(f'Unsupported macro factor: {f}')

    if not (0.0 <= confidence <= 1.0):
        raise SchemaError('confidence must be in [0,1]')

    if not narrative:
        raise SchemaError('narrative must be non-empty')

    return {
        'narrative': narrative,
        'macro_factors': factors,
        'confidence': round(confidence, 3),
        'method': method,
    }
