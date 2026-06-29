from __future__ import annotations

from collector.sources.base import clean_text
from collector.sources.config import get_http_source_configs
from collector.sources.http_fetcher import fetch_http_sources
from collector.sources.mock_fetcher import fetch_mock_sources
from collector.sources.rss_fetcher import fetch_rss_sources
from collector.sources.search_fetcher import fetch_search_sources


def fetch_raw_sources(state: dict) -> list[dict]:
    source_mode = str(state.get("source_mode", "mock") or "mock").strip().lower()
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
        return _fetch_rss_only(task, state)

    if source_mode == "http":
        return _fetch_http_only(task, state)

    if source_mode == "search":
        return _fetch_search_only(task, state)

    if source_mode == "hybrid":
        return _fetch_hybrid(task, state)

    state.setdefault("run_errors", []).append(f"unknown source_mode: {source_mode}; no sources fetched")
    return []


def _fetch_rss_only(task: dict, state: dict) -> list[dict]:
    sources = fetch_rss_sources(task, state)
    if not sources:
        state.setdefault("run_errors", []).append("rss source mode returned no usable sources")
    return sources


def _fetch_http_only(task: dict, state: dict) -> list[dict]:
    http_urls = _resolve_http_urls(state)
    if not http_urls:
        http_urls = _resolve_http_urls_from_source_rules(state)
    else:
        http_urls = _dedupe_urls([*_resolve_http_urls_from_source_rules(state), *http_urls])
    sources = fetch_http_sources(task, urls=http_urls, state=state)
    if not sources:
        state.setdefault("run_errors", []).append("http source mode returned no usable sources")
    return sources


def _fetch_search_only(task: dict, state: dict) -> list[dict]:
    sources = fetch_search_sources(
        task,
        state.get("search_keywords", []),
        state=state,
        provider=state.get("search_provider"),
    )
    if not sources:
        state.setdefault("run_errors", []).append("search source mode returned no usable sources")
    return sources


def _fetch_hybrid(task: dict, state: dict) -> list[dict]:
    sources = fetch_rss_sources(task, state)
    if sources:
        return sources

    http_urls = _resolve_http_urls(state)
    if not http_urls:
        http_urls = _resolve_http_urls_from_source_rules(state)
    else:
        http_urls = _dedupe_urls([*_resolve_http_urls_from_source_rules(state), *http_urls])
    sources = fetch_http_sources(task, urls=http_urls, state=state)
    if sources:
        return sources

    sources = fetch_search_sources(
        task,
        state.get("search_keywords", []),
        state=state,
        provider=state.get("search_provider"),
    )
    if sources:
        return sources

    state.setdefault("run_errors", []).append(
        "hybrid source mode returned no usable real sources; mock fallback is disabled unless source_mode=mock"
    )
    return []


def _resolve_http_urls(state: dict) -> list[str]:
    http_urls = state.get("http_urls")
    if http_urls:
        return [url for url in http_urls if url]

    scope = state.get("scope", "")
    scope_name = state.get("scope_name", "")
    configured = [item.get("url", "") for item in get_http_source_configs(scope, scope_name) if item.get("url")]
    return _dedupe_urls(configured)


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


def _dedupe_urls(urls: list[str]) -> list[str]:
    deduped: list[str] = []
    seen: set[str] = set()
    for url in urls:
        if not url or url in seen:
            continue
        seen.add(url)
        deduped.append(url)
    return deduped
