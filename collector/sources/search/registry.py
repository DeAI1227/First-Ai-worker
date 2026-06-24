from __future__ import annotations

from collections.abc import Callable
import os
from typing import Any

from collector.sources.search.base_provider import SearchProviderError, SearchProviderUnavailableError
from collector.sources.search.firecrawl_provider import FirecrawlProvider
from collector.sources.search.mock_search_provider import MockSearchProvider
from collector.sources.search.serpapi_provider import SerpApiProvider
from collector.sources.search.tavily_provider import TavilyProvider


SEARCH_PROVIDER_REGISTRY: dict[str, Callable[[], Any]] = {
    "mock": MockSearchProvider,
    "firecrawl": FirecrawlProvider,
    "tavily": TavilyProvider,
    "serpapi": SerpApiProvider,
}


def resolve_search_provider_name(requested: str | None, state: dict[str, Any] | None = None) -> str:
    candidate = (
        requested
        or (state or {}).get("search_provider")
        or os.getenv("SEARCH_PROVIDER", "")
        or "auto"
    ).strip().lower()
    if candidate in {"mock", "firecrawl", "tavily", "serpapi"}:
        return candidate
    return "auto"


def select_search_provider(requested: str | None, state: dict[str, Any] | None = None) -> tuple[str, Any]:
    provider_name = resolve_search_provider_name(requested, state)
    if provider_name == "auto":
        firecrawl = FirecrawlProvider()
        if firecrawl.is_available():
            return "firecrawl", firecrawl
        return "mock", MockSearchProvider()

    provider_class = SEARCH_PROVIDER_REGISTRY.get(provider_name, MockSearchProvider)
    provider = provider_class()
    if provider_name != "mock" and not provider.is_available():
        return "mock", MockSearchProvider()
    return provider_name, provider


__all__ = [
    "SEARCH_PROVIDER_REGISTRY",
    "resolve_search_provider_name",
    "select_search_provider",
]
