from __future__ import annotations

from collections.abc import Iterable
from typing import Any
from urllib.parse import parse_qsl, urlencode, urlparse, urlunparse

from collector.sources.base import clean_text, normalize_source_item
from collector.sources.search import SEARCH_PROVIDER_REGISTRY, select_search_provider
from collector.sources.search.firecrawl_provider import FirecrawlProvider
from collector.sources.search.mock_search_provider import MockSearchProvider


def fetch_search_sources(
    task: dict,
    keywords: list[str] | None = None,
    state: dict | None = None,
    provider: str | None = None,
) -> list[dict]:
    if state is None:
        state = {}

    keyword_list = _normalize_keywords(keywords or task.get("search_keywords", []))
    if not keyword_list:
        state.setdefault("run_errors", []).append("search keywords are not configured")
        return []

    provider_name, provider_impl = select_search_provider(provider or state.get("search_provider"), state)
    if provider_impl is None:
        state.setdefault("run_errors", []).append(
            "search provider is unavailable; no mock search fallback unless search_provider=mock"
        )
        return []

    raw_sources: list[dict[str, Any]] = []
    for keyword in keyword_list:
        try:
            results = provider_impl.search(task, [keyword], state)
        except Exception as exc:
            state.setdefault("run_errors", []).append(f"search provider {provider_name} failed for keyword {keyword}: {exc}")
            results = []

        for item in results:
            normalized = _normalize_search_item(item)
            if normalized:
                raw_sources.append(normalized)

    return _dedupe_by_source_url(raw_sources)


def mock_search_provider(task: dict, keywords: list[str], state: dict | None = None) -> list[dict]:
    return MockSearchProvider().search(task, keywords, state)


def tavily_provider(task: dict, keywords: list[str], state: dict | None = None) -> list[dict]:
    provider_name, provider_impl = select_search_provider("tavily", state)
    if provider_impl is None:
        if state is not None:
            state.setdefault("run_errors", []).append("tavily provider is unavailable")
        return []
    return provider_impl.search(task, keywords, state)


def serpapi_provider(task: dict, keywords: list[str], state: dict | None = None) -> list[dict]:
    provider_name, provider_impl = select_search_provider("serpapi", state)
    if provider_impl is None:
        if state is not None:
            state.setdefault("run_errors", []).append("serpapi provider is unavailable")
        return []
    return provider_impl.search(task, keywords, state)


def firecrawl_provider(task: dict, keywords: list[str], state: dict | None = None) -> list[dict]:
    provider = FirecrawlProvider()
    if not provider.is_available():
        if state is not None:
            state.setdefault("run_errors", []).append("firecrawl provider is unavailable")
        return []
    return provider.search(task, keywords, state)


def _normalize_keywords(keywords: Iterable[str]) -> list[str]:
    normalized: list[str] = []
    seen: set[str] = set()
    for keyword in keywords:
        cleaned = clean_text(keyword)
        if not cleaned or cleaned in seen:
            continue
        seen.add(cleaned)
        normalized.append(cleaned)
    return normalized


def _normalize_search_item(item: dict[str, Any]) -> dict[str, Any] | None:
    title = clean_text(item.get("title", ""))
    source_name = clean_text(item.get("source_name", ""))
    source_url = clean_text(item.get("source_url", ""))
    published_at = clean_text(item.get("published_at", ""))
    content = clean_text(item.get("content", ""))
    if not title or not source_url or not content:
        return None
    return normalize_source_item(
        {
            "title": title,
            "source_name": source_name or "Search Source",
            "source_url": source_url,
            "published_at": published_at,
            "content": content,
        },
        "search",
    )


def _dedupe_by_source_url(items: list[dict[str, Any]]) -> list[dict[str, Any]]:
    deduped: list[dict[str, Any]] = []
    seen: set[str] = set()
    for item in items:
        source_url = clean_text(item.get("source_url", ""))
        dedupe_key = _canonicalize_source_url(source_url)
        if not dedupe_key or dedupe_key in seen:
            continue
        seen.add(dedupe_key)
        deduped.append(item)
    return deduped


def _canonicalize_source_url(url: str) -> str:
    cleaned = clean_text(url)
    if not cleaned:
        return ""
    parsed = urlparse(cleaned)
    if not parsed.scheme or not parsed.netloc:
        return cleaned
    filtered_query = [
        (key, value)
        for key, value in parse_qsl(parsed.query, keep_blank_values=True)
        if not key.lower().startswith("utm_") and key.lower() not in {"bcmt", "fbclid", "gclid", "ref"}
    ]
    normalized = parsed._replace(query=urlencode(filtered_query, doseq=True), fragment="")
    return urlunparse(normalized)


__all__ = [
    "SEARCH_PROVIDER_REGISTRY",
    "fetch_search_sources",
    "firecrawl_provider",
    "mock_search_provider",
    "serpapi_provider",
    "tavily_provider",
]
