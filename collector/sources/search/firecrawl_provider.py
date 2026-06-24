from __future__ import annotations

from datetime import datetime, timezone
from typing import Any
from urllib.parse import urlparse

import requests

from collector.sources.base import clean_text, normalize_source_item
from collector.sources.http_fetcher import fetch_http_sources
from collector.sources.search.base_provider import BaseSearchProvider, SearchProviderError, SearchProviderUnavailableError


class FirecrawlProvider(BaseSearchProvider):
    provider_name = "firecrawl"
    base_url_env = "FIRECRAWL_BASE_URL"
    api_key_env = "FIRECRAWL_API_KEY"
    default_timeout_seconds = 20
    default_limit = 10
    default_keyword_limit = 3

    def get_base_url(self) -> str:
        import os

        return clean_text(os.getenv(self.base_url_env, ""))

    def is_available(self) -> bool:
        return bool(self.get_base_url())

    def search(self, task: dict[str, Any], keywords: list[str], state: dict[str, Any] | None = None) -> list[dict[str, Any]]:
        base_url = self.get_base_url()
        if not base_url:
            raise SearchProviderUnavailableError("FIRECRAWL_BASE_URL is missing")

        keyword_list = [clean_text(keyword) for keyword in keywords if clean_text(keyword)]
        if not keyword_list:
            return []
        keyword_list = keyword_list[: _resolve_keyword_limit(state)]

        timeout_seconds = _resolve_timeout_seconds(state)
        limit = _resolve_limit(state)
        api_key = self.get_api_key()
        include_domains = _resolve_include_domains(task, state)

        results: list[dict[str, Any]] = []
        for keyword in keyword_list:
            payload = {
                "query": keyword,
                "limit": limit,
                "timeout": int(timeout_seconds * 1000),
                "ignoreInvalidURLs": True,
            }
            if include_domains:
                payload["includeDomains"] = include_domains
            if _should_scrape_markdown(state):
                payload["scrapeOptions"] = {"formats": ["markdown"]}
            headers = {
                "Content-Type": "application/json",
                "User-Agent": "Mozilla/5.0 (Firecrawl Search Provider)",
                "Authorization": f"Bearer {api_key or 'local-firecrawl'}",
            }

            try:
                response = requests.post(
                    _build_search_endpoint(base_url),
                    json=payload,
                    headers=headers,
                    timeout=timeout_seconds,
                )
                response.raise_for_status()
            except requests.RequestException as exc:  # pragma: no cover - network failure guarded by fallback tests
                raise SearchProviderError(f"Firecrawl request failed for keyword {keyword}: {exc}") from exc

            data = _safe_json(response)
            if not data.get("success", True):
                warning = clean_text(data.get("warning", ""))
                message = warning or f"Firecrawl returned unsuccessful response for keyword {keyword}"
                raise SearchProviderError(message)

            payload = data.get("data", [])
            items: list[Any] = []
            if isinstance(payload, list):
                items = payload
            elif isinstance(payload, dict):
                for key in ("web", "news", "images"):
                    value = payload.get(key, [])
                    if isinstance(value, list):
                        items.extend(value)
            elif payload:
                items = [payload]

            for item in items:
                normalized = _normalize_search_item(item, keyword)
                if normalized:
                    results.append(normalized)

        filtered_results = _filter_results_by_domains(results, include_domains)
        if filtered_results:
            return filtered_results

        fallback_urls = _resolve_fallback_urls(task, state)
        if fallback_urls:
            state.setdefault("run_errors", []).append(
                f"firecrawl search returned no usable items for {keyword_list}; fallback to HTTP source rules"
            )
            http_results = fetch_http_sources(task, urls=fallback_urls, state=state)
            if http_results:
                return http_results

        return results


def _build_search_endpoint(base_url: str) -> str:
    return f"{base_url.rstrip('/')}/v2/search"


def _resolve_timeout_seconds(state: dict[str, Any] | None) -> float:
    raw_timeout = ""
    if isinstance(state, dict):
        raw_timeout = clean_text(state.get("firecrawl_timeout_seconds", ""))
    if not raw_timeout:
        return float(FirecrawlProvider.default_timeout_seconds)
    try:
        return max(1.0, float(raw_timeout))
    except ValueError:
        return float(FirecrawlProvider.default_timeout_seconds)


def _resolve_limit(state: dict[str, Any] | None) -> int:
    raw_limit = ""
    if isinstance(state, dict):
        raw_limit = clean_text(state.get("firecrawl_limit", ""))
    if not raw_limit:
        return FirecrawlProvider.default_limit
    try:
        limit = int(raw_limit)
    except ValueError:
        return FirecrawlProvider.default_limit
    return max(1, min(limit, 100))


def _resolve_keyword_limit(state: dict[str, Any] | None) -> int:
    raw_limit = ""
    if isinstance(state, dict):
        raw_limit = clean_text(state.get("firecrawl_keyword_limit", ""))
    if not raw_limit:
        return FirecrawlProvider.default_keyword_limit
    try:
        limit = int(raw_limit)
    except ValueError:
        return FirecrawlProvider.default_keyword_limit
    return max(1, min(limit, 20))


def _resolve_include_domains(task: dict[str, Any], state: dict[str, Any] | None) -> list[str]:
    candidates: list[str] = []
    for source_rules in (
        (task or {}).get("source_rules", []),
        (state or {}).get("source_rules", []),
    ):
        if not isinstance(source_rules, list):
            continue
        for rule in source_rules:
            if not isinstance(rule, dict):
                continue
            url = clean_text(rule.get("url", ""))
            if not url:
                continue
            hostname = urlparse(url).netloc.strip().lower()
            if hostname:
                candidates.append(hostname)
    seen: set[str] = set()
    include_domains: list[str] = []
    for domain in candidates:
        if domain in seen:
            continue
        seen.add(domain)
        include_domains.append(domain)
    return include_domains


def _resolve_fallback_urls(task: dict[str, Any], state: dict[str, Any] | None) -> list[str]:
    urls: list[str] = []
    seen: set[str] = set()
    for source_rules in (
        (task or {}).get("source_rules", []),
        (state or {}).get("source_rules", []),
    ):
        if not isinstance(source_rules, list):
            continue
        for rule in source_rules:
            if not isinstance(rule, dict):
                continue
            url = clean_text(rule.get("url", ""))
            if not url or url in seen:
                continue
            seen.add(url)
            urls.append(url)
    return urls


def _filter_results_by_domains(items: list[dict[str, Any]], include_domains: list[str]) -> list[dict[str, Any]]:
    if not include_domains:
        return items
    filtered: list[dict[str, Any]] = []
    for item in items:
        source_url = clean_text(item.get("source_url", ""))
        if not source_url:
            continue
        if _matches_any_domain(source_url, include_domains):
            filtered.append(item)
    return filtered


def _matches_any_domain(source_url: str, include_domains: list[str]) -> bool:
    hostname = urlparse(source_url).netloc.strip().lower()
    if not hostname:
        return False
    for domain in include_domains:
        normalized_domain = domain.strip().lower()
        if not normalized_domain:
            continue
        if hostname == normalized_domain or hostname.endswith(f".{normalized_domain}") or normalized_domain in hostname:
            return True
    return False


def _should_scrape_markdown(state: dict[str, Any] | None) -> bool:
    if not isinstance(state, dict):
        return False
    raw_value = clean_text(state.get("firecrawl_scrape_markdown", ""))
    return raw_value.lower() in {"1", "true", "yes", "on"}


def _safe_json(response: requests.Response) -> dict[str, Any]:
    try:
        payload = response.json()
    except ValueError as exc:  # pragma: no cover - defensive
        raise SearchProviderError("Firecrawl returned invalid JSON") from exc
    if isinstance(payload, dict):
        return payload
    raise SearchProviderError("Firecrawl returned unexpected JSON payload")


def _normalize_search_item(item: Any, keyword: str) -> dict[str, Any] | None:
    if not isinstance(item, dict):
        return None

    metadata = item.get("metadata") or {}
    if not isinstance(metadata, dict):
        metadata = {}

    title = clean_text(item.get("title") or metadata.get("title", ""))
    source_url = clean_text(item.get("url") or metadata.get("sourceURL", ""))
    description = clean_text(item.get("description") or metadata.get("description", ""))
    markdown = clean_text(item.get("markdown", ""))
    content = markdown or description
    if not title or not source_url or not content:
        return None

    source_name = _source_name_from_url(source_url)
    published_at = _parse_published_at(
        metadata.get("publishedDate")
        or metadata.get("publishedTime")
        or metadata.get("datePublished")
        or ""
    )

    normalized = normalize_source_item(
        {
            "title": title,
            "source_name": source_name or _source_name_from_url(source_url) or "Firecrawl",
            "source_url": source_url,
            "published_at": published_at,
            "content": f"{content} {_keyword_hint(keyword)}".strip(),
        },
        "search",
    )
    return normalized


def _keyword_hint(keyword: str) -> str:
    keyword = clean_text(keyword)
    if not keyword:
        return ""
    return f"[query: {keyword}]"


def _source_name_from_url(source_url: str) -> str:
    hostname = urlparse(source_url).netloc.strip()
    return hostname or "Firecrawl"


def _parse_published_at(value: Any) -> str:
    text = clean_text(value)
    if not text:
        return ""
    try:
        parsed = datetime.fromisoformat(text.replace("Z", "+00:00"))
        if parsed.tzinfo is None:
            parsed = parsed.replace(tzinfo=timezone.utc)
        return parsed.isoformat()
    except ValueError:
        return ""
