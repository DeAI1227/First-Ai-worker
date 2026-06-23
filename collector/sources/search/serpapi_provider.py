from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

import requests

from collector.sources.base import clean_text, normalize_source_item
from collector.sources.search.base_provider import BaseSearchProvider, SearchProviderUnavailableError


class SerpApiProvider(BaseSearchProvider):
    provider_name = "serpapi"
    api_key_env = "SERPAPI_API_KEY"

    def search(self, task: dict[str, Any], keywords: list[str], state: dict[str, Any] | None = None) -> list[dict[str, Any]]:
        api_key = self.get_api_key()
        if not api_key:
            raise SearchProviderUnavailableError("SERPAPI_API_KEY is missing")
        results = []
        for keyword in keywords:
            response = requests.get(
                "https://serpapi.com/search.json",
                params={
                    "engine": "google",
                    "q": keyword,
                    "api_key": api_key,
                },
                timeout=20,
            )
            response.raise_for_status()
            payload = response.json()
            for item in payload.get("organic_results", []):
                results.append(
                    normalize_source_item(
                        {
                            "title": clean_text(item.get("title", "")),
                            "source_name": clean_text(item.get("source", "")) or "SerpApi",
                            "source_url": clean_text(item.get("link", "")),
                            "published_at": _parse_iso(item.get("date", "")),
                            "content": clean_text(item.get("snippet", "")),
                        },
                        "search",
                    )
                )
        return results


def _parse_iso(value: Any) -> str:
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
