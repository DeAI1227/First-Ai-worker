from __future__ import annotations

from typing import Any

from collector.quality import score_sources, summarize_quality


def filter_sources(state: dict[str, Any]) -> dict[str, Any]:
    raw_sources = list(state.get("raw_sources", []))
    scored_sources = score_sources(raw_sources, state, state)
    quality_summary = summarize_quality(scored_sources)

    rejected_sources = [
        source
        for source in scored_sources
        if str(source.get("quality_level", "rejected")).lower() == "rejected"
    ]

    filtered_sources = _select_filtered_sources(scored_sources)

    state["scored_sources"] = scored_sources
    state["rejected_sources"] = rejected_sources
    state["quality_summary"] = quality_summary
    state["filtered_sources"] = filtered_sources
    return state


def _select_filtered_sources(scored_sources: list[dict[str, Any]]) -> list[dict[str, Any]]:
    preferred_levels = {"high", "medium"}
    preferred = [
        source
        for source in scored_sources
        if str(source.get("quality_level", "")).lower() in preferred_levels
    ]

    if not preferred:
        preferred = [
            source
            for source in scored_sources
            if str(source.get("quality_level", "")).lower() == "low"
        ]

    preferred.sort(
        key=lambda source: (
            -int(source.get("quality_score", 0) or 0),
            str(source.get("published_at", "")),
            str(source.get("source_name", "")),
            str(source.get("source_url", "")),
        )
    )
    return _dedupe_by_url(preferred)


def _dedupe_by_url(sources: list[dict[str, Any]]) -> list[dict[str, Any]]:
    deduped: list[dict[str, Any]] = []
    seen_urls: set[str] = set()
    for source in sources:
        source_url = str(source.get("source_url", "")).strip()
        if not source_url or source_url in seen_urls:
            continue
        seen_urls.add(source_url)
        deduped.append(source)
    return deduped

