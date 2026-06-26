from __future__ import annotations

from typing import Any

from collector.constants import COLLECTOR_NAME, DEFAULT_LANGUAGE
from collector.utils.time_utils import now_iso, today_date


def build_daily_digest_packet(state: dict[str, Any]) -> dict[str, Any]:
    packet = state.get("event_packet", {})
    importance = packet.get("importance", "general")
    source_urls = packet.get("source_urls") or ([packet.get("source_url")] if packet.get("source_url") else [])
    quality_summary = _normalize_quality_summary(state.get("quality_summary", {}))
    rejected_reasons = _summarize_rejected_reasons(state.get("rejected_sources", []))

    return {
        "packet_type": "daily_digest",
        "collector": COLLECTOR_NAME,
        "digest_date": today_date(),
        "scope": state.get("scope", ""),
        "scope_name": state.get("scope_name", ""),
        "event_count": 1 if packet else 0,
        "critical_count": 1 if importance == "critical" else 0,
        "important_count": 1 if importance == "important" else 0,
        "general_count": 1 if importance == "general" else 0,
        "top_events": [packet.get("title")] if packet else [],
        "key_takeaways": [packet.get("ai_summary", "")] if packet else [],
        "source_urls": source_urls,
        "quality_summary": quality_summary,
        "rejected_reasons": rejected_reasons,
        "created_at": now_iso(),
        "language": DEFAULT_LANGUAGE,
    }


def _normalize_quality_summary(summary: dict[str, Any]) -> dict[str, int]:
    return {
        "total_sources": int(summary.get("total_sources", 0) or 0),
        "high": int(summary.get("high", 0) or 0),
        "medium": int(summary.get("medium", 0) or 0),
        "low": int(summary.get("low", 0) or 0),
        "rejected": int(summary.get("rejected", 0) or 0),
    }


def _summarize_rejected_reasons(rejected_sources: list[dict[str, Any]]) -> list[str]:
    counts: dict[str, int] = {}
    for source in rejected_sources:
        for reason in source.get("quality_reasons", []):
            if not isinstance(reason, str):
                continue
            normalized = reason.strip()
            if not normalized:
                continue
            counts[normalized] = counts.get(normalized, 0) + 1

    ordered = sorted(counts.items(), key=lambda item: (-item[1], item[0]))
    return [reason for reason, _ in ordered[:5]]
