from __future__ import annotations

from collector.mock_data import get_mock_sources
from collector.sources.base import normalize_source_item


def fetch_mock_sources(task: dict) -> list[dict]:
    sources = get_mock_sources(task)
    return [normalize_source_item(source, "mock") for source in sources]
