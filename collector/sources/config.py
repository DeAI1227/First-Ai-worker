from __future__ import annotations

from typing import Any

from collector.tracking_universe import resolve_tracking_source_key


RSS_SOURCE_CONFIG: dict[str, list[dict[str, str]]] = {
    "macro": [
        {
            "source_name": "BBC Business",
            "feed_url": "https://feeds.bbci.co.uk/news/business/rss.xml",
        },
    ],
    "thermal": [
        {
            "source_name": "Tom's Hardware",
            "feed_url": "https://www.tomshardware.com/feeds/all",
        },
    ],
    "power": [],
    "autodrive": [],
    "robot": [],
    "cpo": [],
    "networking": [],
    "stock": [],
    "institution": [],
}

HTTP_SOURCE_CONFIG: dict[str, list[dict[str, str]]] = {
    "macro": [],
    "thermal": [],
    "power": [],
    "autodrive": [],
    "robot": [],
    "cpo": [],
    "networking": [],
    "stock": [],
    "institution": [],
}

SOURCE_MODE_PRIORITY = {
    "mock": ["mock"],
    "rss": ["rss", "mock"],
    "http": ["http", "mock"],
    "search": ["search", "mock"],
    "hybrid": ["rss", "http", "search", "mock"],
}


def resolve_source_key(scope: str, scope_name: str) -> str:
    return resolve_tracking_source_key(scope, scope_name)


def get_rss_source_configs(scope: str, scope_name: str) -> list[dict[str, str]]:
    return RSS_SOURCE_CONFIG.get(resolve_source_key(scope, scope_name), [])


def get_http_source_configs(scope: str, scope_name: str) -> list[dict[str, str]]:
    return HTTP_SOURCE_CONFIG.get(resolve_source_key(scope, scope_name), [])


def get_source_mode_config(source_mode: str, scope: str, scope_name: str) -> dict[str, Any]:
    return {
        "source_mode": source_mode,
        "source_key": resolve_source_key(scope, scope_name),
        "rss_feeds": get_rss_source_configs(scope, scope_name),
        "http_urls": get_http_source_configs(scope, scope_name),
        "source_modes": SOURCE_MODE_PRIORITY.get(source_mode, ["mock"]),
    }
