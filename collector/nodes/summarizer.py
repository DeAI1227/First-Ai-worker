from __future__ import annotations

from collector.summarizers.registry import summarize_sources as summarize_sources_node


def summarize_sources(state: dict) -> dict:
    return summarize_sources_node(state)

