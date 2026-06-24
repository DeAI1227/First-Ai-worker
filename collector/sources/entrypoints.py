from __future__ import annotations

from typing import Any

from collector.config.tracking_universe import INSTITUTION_WATCH_STOCKS, TRACKED_STOCKS
from collector.sources.base import clean_text

YAHOO_STOCK_NEWS_URL_TEMPLATE = "https://tw.stock.yahoo.com/quote/{stock_code}.TW/news"
MOPS_COMPANY_LOOKUP_URL = "https://mops.twse.com.tw/mops/web/t146sb05"
CNYES_CATEGORY_NEWS_URLS_BY_SCOPE_KEY: dict[str, list[str]] = {
    "macro": [
        "https://news.cnyes.com/news/cat/wd_macro",
    ],
    "stock": [
        "https://news.cnyes.com/news/cat/tw_quo",
        "https://news.cnyes.com/news/cat/stock_report",
        "https://news.cnyes.com/news/cat/tw_revenue",
        "https://news.cnyes.com/news/cat/wd_stock",
    ],
    "institution": [
        "https://news.cnyes.com/news/cat/wd_stock",
        "https://news.cnyes.com/news/cat/stock_report",
    ],
}


def build_taiwan_stock_news_url(stock_code: str) -> str:
    return YAHOO_STOCK_NEWS_URL_TEMPLATE.format(stock_code=clean_text(stock_code))


def build_mops_lookup_rule(stock_code: str, stock_name: str = "") -> dict[str, str]:
    cleaned_code = clean_text(stock_code)
    cleaned_name = clean_text(stock_name)
    return {
        "kind": "mops_company_lookup",
        "name": f"MOPS 公司基本資料：{cleaned_code} {cleaned_name}".strip(),
        "url": MOPS_COMPANY_LOOKUP_URL,
        "stock_code": cleaned_code,
        "stock_name": cleaned_name,
        "query_field": "公司代號",
        "query_value": cleaned_code,
        "query_hint": "在公司代號或簡稱欄位輸入後查詢",
    }


def build_stock_source_rules(stock_code: str, stock_name: str = "") -> list[dict[str, str]]:
    cleaned_code = clean_text(stock_code)
    cleaned_name = clean_text(stock_name)
    if not cleaned_code:
        return []
    return [
        {
            "kind": "yahoo_stock_news",
            "name": f"Yahoo 個股新聞：{cleaned_code} {cleaned_name}".strip(),
            "url": build_taiwan_stock_news_url(cleaned_code),
            "stock_code": cleaned_code,
            "stock_name": cleaned_name,
        },
        build_mops_lookup_rule(cleaned_code, cleaned_name),
    ]


def build_cnyes_category_rules(source_key: str, label: str = "") -> list[dict[str, str]]:
    cleaned_key = clean_text(source_key) or "stock"
    cleaned_label = clean_text(label)
    urls = CNYES_CATEGORY_NEWS_URLS_BY_SCOPE_KEY.get(cleaned_key, CNYES_CATEGORY_NEWS_URLS_BY_SCOPE_KEY["stock"])
    return [
        {
            "kind": "cnyes_category_news",
            "name": f"Cnyes {cleaned_label or cleaned_key} {index + 1}".strip(),
            "url": url,
            "source_key": cleaned_key,
            "scope_label": cleaned_label,
        }
        for index, url in enumerate(urls)
    ]


def build_taiwan_stock_news_urls(include_institution_watch: bool = True) -> list[str]:
    urls: list[str] = []
    seen: set[str] = set()

    for stock in TRACKED_STOCKS:
        url = build_taiwan_stock_news_url(stock["stock_code"])
        if url not in seen:
            seen.add(url)
            urls.append(url)

    if include_institution_watch:
        for stock in INSTITUTION_WATCH_STOCKS:
            url = build_taiwan_stock_news_url(stock["stock_code"])
            if url not in seen:
                seen.add(url)
                urls.append(url)

    return urls


def build_taiwan_stock_source_catalog(include_institution_watch: bool = True) -> list[dict[str, Any]]:
    catalog: list[dict[str, Any]] = []
    seen: set[str] = set()
    stock_sources = list(TRACKED_STOCKS)
    if include_institution_watch:
        stock_sources.extend(INSTITUTION_WATCH_STOCKS)

    for stock in stock_sources:
        stock_code = clean_text(stock.get("stock_code", ""))
        stock_name = clean_text(stock.get("stock_name", ""))
        if not stock_code or stock_code in seen:
            continue
        seen.add(stock_code)
        catalog.append(
            {
                "stock_code": stock_code,
                "stock_name": stock_name,
                "yahoo_news_url": build_taiwan_stock_news_url(stock_code),
                "source_rules": build_stock_source_rules(stock_code, stock_name),
            }
        )

    return catalog


__all__ = [
    "MOPS_COMPANY_LOOKUP_URL",
    "CNYES_CATEGORY_NEWS_URLS_BY_SCOPE_KEY",
    "YAHOO_STOCK_NEWS_URL_TEMPLATE",
    "build_cnyes_category_rules",
    "build_mops_lookup_rule",
    "build_stock_source_rules",
    "build_taiwan_stock_news_url",
    "build_taiwan_stock_news_urls",
    "build_taiwan_stock_source_catalog",
]
