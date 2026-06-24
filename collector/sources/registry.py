from __future__ import annotations

from collector.sources.base import clean_text
from collector.sources.config import get_http_source_configs, get_rss_source_configs
from collector.sources.http_fetcher import fetch_http_sources
from collector.sources.mock_fetcher import fetch_mock_sources
from collector.sources.rss_fetcher import fetch_rss_sources
from collector.sources.search_fetcher import fetch_search_sources


def fetch_raw_sources(state: dict) -> list[dict]:
    source_mode = state.get("source_mode", "mock")
    task = {
        "scope": state.get("scope", ""),
        "scope_name": state.get("scope_name", ""),
        "target_stock_code": state.get("target_stock_code", ""),
        "target_stock_name": state.get("target_stock_name", ""),
        "source_rules": state.get("source_rules", []),
    }

    if source_mode == "mock":
        return fetch_mock_sources(task)

    if source_mode == "rss":
        rss_sources = fetch_rss_sources(task, state)
        if rss_sources:
            return rss_sources
        return fetch_mock_sources(task)

    if source_mode == "http":
        http_urls = _resolve_http_urls(state)
        if not http_urls:
            http_urls = _resolve_http_urls_from_source_rules(state)
        http_sources = fetch_http_sources(task, urls=http_urls, state=state)
        if http_sources:
            return http_sources
        return fetch_mock_sources(task)

    if source_mode == "search":
        search_sources = fetch_search_sources(
            task,
            state.get("search_keywords", []),
            state=state,
            provider=state.get("search_provider"),
        )
        if search_sources:
            return search_sources
        return fetch_mock_sources(task)

    if source_mode == "hybrid":
        rss_sources = fetch_rss_sources(task, state)
        if rss_sources:
            return rss_sources

        http_urls = _resolve_http_urls(state)
        http_sources = fetch_http_sources(task, urls=http_urls, state=state)
        if http_sources:
            return http_sources

        search_sources = fetch_search_sources(
            task,
            state.get("search_keywords", []),
            state=state,
            provider=state.get("search_provider"),
        )
        if search_sources:
            return search_sources

        return fetch_mock_sources(task)

    state.setdefault("run_errors", []).append(f"unknown source_mode: {source_mode}; fallback to mock sources")
    return fetch_mock_sources(task)


def _resolve_http_urls(state: dict) -> list[str]:
    http_urls = state.get("http_urls")
    if http_urls:
        return [url for url in http_urls if url]

    scope = state.get("scope", "")
    scope_name = state.get("scope_name", "")
    configured = get_http_source_configs(scope, scope_name)
    return [item.get("url", "") for item in configured if item.get("url")]


def _resolve_http_urls_from_source_rules(state: dict) -> list[str]:
    source_rules = state.get("source_rules")
    if not isinstance(source_rules, list) or not source_rules:
        return []

    urls: list[str] = []
    seen: set[str] = set()
    for rule in source_rules:
        if not isinstance(rule, dict):
            continue
        if clean_text(rule.get("kind", "")) not in {"yahoo_stock_news", "cnyes_category_news"}:
            continue
        url = clean_text(rule.get("url", ""))
        if not url or url in seen:
            continue
        seen.add(url)
        urls.append(url)
    return urls
