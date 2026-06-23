from __future__ import annotations

from datetime import datetime, timezone
from email.utils import parsedate_to_datetime
from typing import Any


def clean_text(value: Any) -> str:
    if value is None:
        return ""
    if isinstance(value, str):
        return value.strip()
    return str(value).strip()


def normalize_source_item(source: dict[str, Any], source_type: str) -> dict[str, Any]:
    normalized = {
        "title": clean_text(source.get("title", "")),
        "source_name": clean_text(source.get("source_name", "")),
        "source_url": clean_text(source.get("source_url", "")),
        "published_at": clean_text(source.get("published_at", "")),
        "content": clean_text(source.get("content", "")),
        "source_type": source_type,
    }
    return normalized


def parse_datetime_value(value: str) -> str:
    if not value:
        return ""
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
        if parsed.tzinfo is None:
            parsed = parsed.replace(tzinfo=timezone.utc)
        return parsed.isoformat()
    except ValueError:
        pass
    try:
        return parsedate_to_datetime(value).isoformat()
    except (TypeError, ValueError, IndexError):
        return ""


def extract_feed_override(value: Any, feed_url: str) -> str | None:
    if isinstance(value, dict):
        return value.get(feed_url)
    if isinstance(value, list):
        for item in value:
            if isinstance(item, dict) and item.get("feed_url") == feed_url:
                return item.get("xml_text")
    return None
