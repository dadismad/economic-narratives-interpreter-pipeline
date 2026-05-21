from __future__ import annotations

from datetime import datetime, timezone
from email.utils import parsedate_to_datetime
from typing import Dict, List, Tuple
from urllib.request import Request, urlopen
from urllib.parse import urlsplit, urlunsplit
import xml.etree.ElementTree as ET


def _canonical_url(url: str) -> str:
    try:
        parts = urlsplit(url.strip())
        query = '&'.join(
            q for q in parts.query.split('&') if q and not q.startswith('utm_') and not q.startswith('fbclid=')
        )
        return urlunsplit((parts.scheme, parts.netloc, parts.path, query, ''))
    except Exception:
        return url.strip()


def _to_iso(value: str) -> str:
    if not value:
        return ''
    try:
        dt = parsedate_to_datetime(value)
        return dt.isoformat()
    except Exception:
        return value


def fetch_rss(feed_url: str) -> List[Dict]:
    req = Request(feed_url, headers={'User-Agent': 'NarrativePipeline/1.0'})
    with urlopen(req, timeout=30) as r:  # nosec B310
        xml_text = r.read()

    root = ET.fromstring(xml_text)
    now = datetime.now(timezone.utc).isoformat()
    rows: List[Dict] = []

    # RSS 2.0
    for item in root.findall('.//item'):
        title = (item.findtext('title') or '').strip()
        link = (item.findtext('link') or '').strip()
        summary = (item.findtext('description') or '').strip()
        published = _to_iso((item.findtext('pubDate') or '').strip())
        if title and link:
            rows.append(
                {
                    'source': 'rss',
                    'feed_url': feed_url,
                    'title': title,
                    'link': link,
                    'published': published,
                    'summary': summary,
                    'ingested_at': now,
                }
            )

    # Atom
    ns = {'a': 'http://www.w3.org/2005/Atom'}
    for entry in root.findall('.//a:entry', ns):
        title = (entry.findtext('a:title', default='', namespaces=ns) or '').strip()
        link_node = entry.find('a:link', ns)
        link = (link_node.get('href') if link_node is not None else '').strip()
        summary = (entry.findtext('a:summary', default='', namespaces=ns) or '').strip()
        published = (entry.findtext('a:published', default='', namespaces=ns) or '').strip()
        if title and link:
            rows.append(
                {
                    'source': 'rss',
                    'feed_url': feed_url,
                    'title': title,
                    'link': link,
                    'published': published,
                    'summary': summary,
                    'ingested_at': now,
                }
            )

    return rows


def dedupe_rss_records(rows: List[Dict]) -> Tuple[List[Dict], int]:
    seen = set()
    out: List[Dict] = []
    removed = 0
    for row in rows:
        key = _canonical_url(str(row.get('link', '')))
        if key in seen:
            removed += 1
            continue
        seen.add(key)
        out.append(row)
    return out, removed
