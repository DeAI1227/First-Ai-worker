# -*- coding: utf-8 -*-
from __future__ import annotations

from copy import deepcopy
from typing import Any

from collector.tracking_universe import resolve_tracking_source_key


YAHOO_RSS_FEEDS: list[dict[str, str]] = [
    {
        "source_name": "Yahoo 股市 RSS - 台股新聞",
        "feed_url": "https://tw.stock.yahoo.com/rss?category=tw-market",
    },
    {
        "source_name": "Yahoo 股市 RSS - 新聞",
        "feed_url": "https://tw.stock.yahoo.com/rss?category=news",
    },
    {
        "source_name": "Yahoo 股市 RSS - 研究報告",
        "feed_url": "https://tw.stock.yahoo.com/rss?category=research",
    },
    {
        "source_name": "Yahoo 股市 RSS - 國際財經",
        "feed_url": "https://tw.stock.yahoo.com/rss?category=intl-markets",
    },
]

CNYES_MACRO_RSS_FEEDS: list[dict[str, str]] = [
    {
        "source_name": "鉅亨網 RSS - 大環境",
        "feed_url": "https://news.cnyes.com/rss/v1/news/category/wd_macro",
    },
]

CNYES_TW_STOCK_RSS_FEEDS: list[dict[str, str]] = [
    {
        "source_name": "鉅亨網 RSS - 台股總覽",
        "feed_url": "https://news.cnyes.com/rss/v1/news/category/tw_quo",
    },
    {
        "source_name": "鉅亨網 RSS - 個股研究",
        "feed_url": "https://news.cnyes.com/rss/v1/news/category/stock_report",
    },
    {
        "source_name": "鉅亨網 RSS - 營收速報",
        "feed_url": "https://news.cnyes.com/rss/v1/news/category/tw_revenue",
    },
    {
        "source_name": "鉅亨網 RSS - 盤勢新聞",
        "feed_url": "https://news.cnyes.com/rss/v1/news/category/wd_stock",
    },
]


RSS_SOURCE_CONFIG: dict[str, list[dict[str, str]]] = {
    "macro": [
        *deepcopy(CNYES_MACRO_RSS_FEEDS),
        *deepcopy(YAHOO_RSS_FEEDS),
    ],
    "thermal": [
        {
            "source_name": "Tom's Hardware",
            "feed_url": "https://www.tomshardware.com/feeds/all",
        },
        *deepcopy(YAHOO_RSS_FEEDS),
        *deepcopy(CNYES_TW_STOCK_RSS_FEEDS),
    ],
    "power": deepcopy(YAHOO_RSS_FEEDS) + deepcopy(CNYES_TW_STOCK_RSS_FEEDS),
    "autodrive": deepcopy(YAHOO_RSS_FEEDS) + deepcopy(CNYES_TW_STOCK_RSS_FEEDS),
    "robot": deepcopy(YAHOO_RSS_FEEDS) + deepcopy(CNYES_TW_STOCK_RSS_FEEDS),
    "cpo": deepcopy(YAHOO_RSS_FEEDS) + deepcopy(CNYES_TW_STOCK_RSS_FEEDS),
    "networking": deepcopy(YAHOO_RSS_FEEDS) + deepcopy(CNYES_TW_STOCK_RSS_FEEDS),
    "stock": deepcopy(YAHOO_RSS_FEEDS) + deepcopy(CNYES_TW_STOCK_RSS_FEEDS),
    "institution": deepcopy(YAHOO_RSS_FEEDS) + deepcopy(CNYES_TW_STOCK_RSS_FEEDS),
}

HTTP_SOURCE_CONFIG: dict[str, list[dict[str, str]]] = {
    "macro": [
        {
            "source_name": "鉅亨網大環境分類頁",
            "url": "https://news.cnyes.com/news/cat/wd_macro",
        },
    ],
    "thermal": [
        {
            "source_name": "鉅亨網台股分類頁",
            "url": "https://news.cnyes.com/news/cat/tw_quo",
        },
        {
            "source_name": "鉅亨網個股研究分類頁",
            "url": "https://news.cnyes.com/news/cat/stock_report",
        },
        {
            "source_name": "鉅亨網營收速報分類頁",
            "url": "https://news.cnyes.com/news/cat/tw_revenue",
        },
        {
            "source_name": "鉅亨網盤勢新聞分類頁",
            "url": "https://news.cnyes.com/news/cat/wd_stock",
        },
    ],
    "power": [
        {
            "source_name": "鉅亨網台股分類頁",
            "url": "https://news.cnyes.com/news/cat/tw_quo",
        },
        {
            "source_name": "鉅亨網個股研究分類頁",
            "url": "https://news.cnyes.com/news/cat/stock_report",
        },
        {
            "source_name": "鉅亨網營收速報分類頁",
            "url": "https://news.cnyes.com/news/cat/tw_revenue",
        },
        {
            "source_name": "鉅亨網盤勢新聞分類頁",
            "url": "https://news.cnyes.com/news/cat/wd_stock",
        },
    ],
    "autodrive": [],
    "robot": [],
    "cpo": [],
    "networking": [],
    "stock": [
        {
            "source_name": "鉅亨網台股分類頁",
            "url": "https://news.cnyes.com/news/cat/tw_quo",
        },
        {
            "source_name": "鉅亨網個股研究分類頁",
            "url": "https://news.cnyes.com/news/cat/stock_report",
        },
        {
            "source_name": "鉅亨網營收速報分類頁",
            "url": "https://news.cnyes.com/news/cat/tw_revenue",
        },
        {
            "source_name": "鉅亨網盤勢新聞分類頁",
            "url": "https://news.cnyes.com/news/cat/wd_stock",
        },
    ],
    "institution": [
        {
            "source_name": "鉅亨網台股分類頁",
            "url": "https://news.cnyes.com/news/cat/tw_quo",
        },
        {
            "source_name": "鉅亨網個股研究分類頁",
            "url": "https://news.cnyes.com/news/cat/stock_report",
        },
        {
            "source_name": "鉅亨網營收速報分類頁",
            "url": "https://news.cnyes.com/news/cat/tw_revenue",
        },
        {
            "source_name": "鉅亨網盤勢新聞分類頁",
            "url": "https://news.cnyes.com/news/cat/wd_stock",
        },
    ],
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
