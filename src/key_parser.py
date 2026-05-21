from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Dict, Iterable, Tuple

KEY_HINTS = [
    'FRED_API_KEY',
    'OPENAI_API_KEY',
    'SEMANTIC_SCHOLAR_API_KEY',
    'EPO_OPS_KEY',
    'EPO_OPS_SECRET',
    'WIPO_API_KEY',
]


def _parse_env_file(path: Path) -> Dict[str, str]:
    out: Dict[str, str] = {}
    if not path.exists() or not path.is_file():
        return out

    for raw in path.read_text(encoding='utf-8', errors='ignore').splitlines():
        line = raw.strip()
        if not line or line.startswith('#') or '=' not in line:
            continue
        key, value = line.split('=', 1)
        key = key.strip()
        value = value.strip().strip('"').strip("'")
        if key:
            out[key] = value
    return out


def discover_api_keys(extra_env_files: Iterable[str] = ()) -> Dict[str, str]:
    merged: Dict[str, str] = {}

    # 1) process environment
    for k, v in os.environ.items():
        if any(h in k for h in ('KEY', 'TOKEN', 'SECRET')) and v:
            merged[k] = v

    # 2) common .env files
    candidates = [Path('.env'), Path('.env.local'), Path.home() / '.hermes' / '.env']
    candidates.extend(Path(p) for p in extra_env_files)
    for p in candidates:
        merged.update(_parse_env_file(p))

    # 3) keep only relevant key hints
    focused: Dict[str, str] = {}
    for k, v in merged.items():
        if k in KEY_HINTS or any(h in k for h in KEY_HINTS):
            focused[k] = v
    return focused


def mask(value: str) -> str:
    if not value:
        return ''
    if len(value) <= 8:
        return '*' * len(value)
    return value[:4] + '*' * (len(value) - 8) + value[-4:]


def write_key_audit(keys: Dict[str, str], output_path: str) -> str:
    path = Path(output_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    payload = {
        'found_keys': sorted(keys.keys()),
        'masked_values': {k: mask(v) for k, v in keys.items()},
    }
    path.write_text(json.dumps(payload, indent=2), encoding='utf-8')
    return str(path)
