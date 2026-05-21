from __future__ import annotations

import json
import xml.etree.ElementTree as ET
from datetime import datetime, timezone
from urllib.parse import urlencode
from urllib.request import Request, urlopen


def _get_json(url: str):
    req = Request(url, headers={'User-Agent': 'NarrativePipeline/1.0'})
    with urlopen(req, timeout=30) as r:  # nosec B310
        return json.loads(r.read().decode('utf-8'))


def fetch_openalex(search: str = 'inflation expectations', per_page: int = 20):
    q = urlencode({'search': search, 'per-page': per_page})
    payload = _get_json(f'https://api.openalex.org/works?{q}')
    now = datetime.now(timezone.utc).isoformat()
    out = []
    for it in payload.get('results', []):
        out.append(
            {
                'source': 'openalex',
                'id': it.get('id', ''),
                'title': it.get('title', ''),
                'publication_year': it.get('publication_year', None),
                'cited_by_count': it.get('cited_by_count', None),
                'ingested_at': now,
            }
        )
    return out


def fetch_crossref(search: str = 'capital flows', rows: int = 20):
    q = urlencode({'query': search, 'rows': rows})
    payload = _get_json(f'https://api.crossref.org/works?{q}')
    now = datetime.now(timezone.utc).isoformat()
    out = []
    for it in payload.get('message', {}).get('items', []):
        out.append(
            {
                'source': 'crossref',
                'doi': it.get('DOI', ''),
                'title': (it.get('title') or [''])[0],
                'type': it.get('type', ''),
                'ingested_at': now,
            }
        )
    return out


def fetch_pubmed_ids(term: str = 'financial stress', retmax: int = 20):
    q = urlencode({'db': 'pubmed', 'term': term, 'retmax': retmax, 'retmode': 'json'})
    payload = _get_json(f'https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esearch.fcgi?{q}')
    now = datetime.now(timezone.utc).isoformat()
    return [{'source': 'pubmed', 'pmid': pmid, 'ingested_at': now} for pmid in payload.get('esearchresult', {}).get('idlist', [])]


def fetch_arxiv(search: str = 'economics', max_results: int = 20):
    q = urlencode({'search_query': f'all:{search}', 'max_results': max_results})
    url = f'https://export.arxiv.org/api/query?{q}'
    req = Request(url, headers={'User-Agent': 'NarrativePipeline/1.0'})
    with urlopen(req, timeout=30) as r:  # nosec B310
        xml_text = r.read()

    root = ET.fromstring(xml_text)
    ns = {'a': 'http://www.w3.org/2005/Atom'}
    now = datetime.now(timezone.utc).isoformat()
    out = []
    for e in root.findall('a:entry', ns):
        pid = (e.findtext('a:id', default='', namespaces=ns) or '').split('/abs/')[-1]
        out.append(
            {
                'source': 'arxiv',
                'id': pid,
                'title': (e.findtext('a:title', default='', namespaces=ns) or '').strip().replace('\\n', ' '),
                'published': e.findtext('a:published', default='', namespaces=ns) or '',
                'ingested_at': now,
            }
        )
    return out
