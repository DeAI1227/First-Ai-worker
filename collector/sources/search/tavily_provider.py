from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

import requests

from collector.sources.base import clean_text, normalize_source_item
from collector.sources.search.base_provider import BaseSearchProvider, SearchProviderUnavailableError


class TavilyProvider(BaseSearchProvider):
    provider_name = "tavily"
    api_key_env = "TAVILY_API_KEY"

    def search(self, task: dict[str, Any], keywords: list[str], state: dict[str, Any] | None = None) -> list[dict[str, Any]]:
        api_key = self.get_api_key()
        if not api_key:
            raise SearchProviderUnavailableError("TAVILY_API_KEY is missing")
        results = []
        for keyword in keywords:
            response = requests.post(
                "https://api.tavily.com/search",
                json={
                    "api_key": api_key,
                    "query": keyword,
                    "search_depth": "basic",
                    "include_answer": False,
                    "include_raw_content": False,
                },
                timeout=20,
            )
            response.raise_for_status()
            payload = response.json()
            for item in payload.get("results", []):
                results.append(
                    normalize_source_item(
                        {
                            "title": clean_text(item.get("title", "")),
                            "source_name": clean_text(item.get("source", "")) or "Tavily",
                            "source_url": clean_text(item.get("url", "")),
                            "published_at": _parse_iso(item.get("published_date", "")),
                            "content": clean_text(item.get("content", "") or item.get("raw_content", "")),
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
