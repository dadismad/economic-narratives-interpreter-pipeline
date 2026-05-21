from __future__ import annotations

import os
from dataclasses import dataclass
from typing import List

from src.key_parser import discover_api_keys


def _split_csv(value: str) -> List[str]:
    return [v.strip() for v in value.split(',') if v.strip()]


@dataclass
class Settings:
    data_dir: str
    fred_api_key: str
    fred_series_ids: List[str]
    rss_urls: List[str]
    openai_api_key: str
    openai_model: str
    openai_enabled: bool
    openai_max_items: int


def load_settings() -> Settings:
    data_dir = os.getenv('DATA_DIR', 'data')
    fred_series_ids = _split_csv(os.getenv('FRED_SERIES_IDS', 'CPIAUCSL,UNRATE,FEDFUNDS'))
    rss_urls = _split_csv(os.getenv('RSS_URLS', ''))

    discovered = discover_api_keys(extra_env_files=['.env', '.env.local'])
    fred_key = os.getenv('FRED_API_KEY', '') or discovered.get('FRED_API_KEY', '')
    openai_key = os.getenv('OPENAI_API_KEY', '') or discovered.get('OPENAI_API_KEY', '')

    return Settings(
        data_dir=data_dir,
        fred_api_key=fred_key,
        fred_series_ids=fred_series_ids,
        rss_urls=rss_urls,
        openai_api_key=openai_key,
        openai_model=os.getenv('OPENAI_MODEL', 'gpt-4.1-mini'),
        openai_enabled=os.getenv('OPENAI_ENABLED', 'false').lower() in {'1', 'true', 'yes'},
        openai_max_items=int(os.getenv('OPENAI_MAX_ITEMS', '25')),
    )
