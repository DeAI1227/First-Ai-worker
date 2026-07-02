from __future__ import annotations

from collector.sources.config import get_http_source_configs, get_rss_source_configs, get_source_mode_config, resolve_source_key
from collector.sources.entrypoints import (
    build_stock_source_rules,
    build_taiwan_stock_news_url,
    build_taiwan_stock_news_urls,
    build_taiwan_stock_source_catalog,
)
from collector.sources.http_fetcher import fetch_http_sources
from collector.sources.mock_fetcher import fetch_mock_sources
from collector.sources.registry import fetch_raw_sources
from collector.sources.rss_fetcher import fetch_rss_sources
from collector.sources.search_fetcher import fetch_search_sources

__all__ = [
    "fetch_http_sources",
    "fetch_mock_sources",
    "fetch_raw_sources",
    "fetch_rss_sources",
    "fetch_search_sources",
    "build_stock_source_rules",
    "build_taiwan_stock_news_url",
    "build_taiwan_stock_news_urls",
    "build_taiwan_stock_source_catalog",
    "get_http_source_configs",
    "get_rss_source_configs",
    "get_source_mode_config",
    "resolve_source_key",
]
