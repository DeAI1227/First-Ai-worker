from __future__ import annotations

import json
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any

from collector.nodes.writer import OUTPUT_ROOT
from collector.schemas.report_packet import build_report_packet, build_report_packet_placeholder
from collector.utils.time_utils import today_date


def _parse_digest_date(path: Path) -> str | None:
    parts = path.name.split("_")
    if len(parts) < 3:
        return None
    return parts[1]


def recent_three_dates(anchor_date: str | None = None) -> set[str]:
    end = datetime.strptime(anchor_date or today_date(), "%Y-%m-%d").date()
    return {(end - timedelta(days=offset)).isoformat() for offset in range(3)}


def load_recent_daily_digests(scope_name: str, anchor_date: str | None = None) -> list[dict[str, Any]]:
    digest_dir = OUTPUT_ROOT / "daily" / scope_name
    if not digest_dir.exists():
        return []

    loaded: list[dict[str, Any]] = []
    for path in sorted(digest_dir.glob("digest_*.json")):
        try:
            digest = json.loads(path.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            continue
        loaded.append(digest)

    if not loaded:
        return []

    effective_anchor = anchor_date
    if not effective_anchor:
        available_dates = [item.get("digest_date") for item in loaded if item.get("digest_date")]
        effective_anchor = max(available_dates) if available_dates else today_date()

    allowed_dates = recent_three_dates(effective_anchor)
    digests = [item for item in loaded if item.get("digest_date") in allowed_dates]

    return sorted(digests, key=lambda item: item.get("digest_date", ""))


def summarize_digests(digests: list[dict[str, Any]]) -> dict[str, Any]:
    dates = [item.get("digest_date") for item in digests if item.get("digest_date")]
    source_urls: list[str] = []
    top_events: list[str] = []
    key_takeaways: list[str] = []

    for digest in digests:
        source_urls.extend(digest.get("source_urls", []))
        top_events.extend(digest.get("top_events", []))
        key_takeaways.extend(digest.get("key_takeaways", []))

    return {
        "digest_count": len(digests),
        "period_start": min(dates) if dates else today_date(),
        "period_end": max(dates) if dates else today_date(),
        "event_count": sum(int(item.get("event_count", 0)) for item in digests),
        "critical_count": sum(int(item.get("critical_count", 0)) for item in digests),
        "important_count": sum(int(item.get("important_count", 0)) for item in digests),
        "general_count": sum(int(item.get("general_count", 0)) for item in digests),
        "top_events": list(dict.fromkeys(top_events)),
        "key_takeaways": list(dict.fromkeys(key_takeaways)),
        "source_urls": list(dict.fromkeys(source_urls)),
    }


def summarize_quality_from_digests(digests: list[dict[str, Any]]) -> dict[str, int]:
    quality_summary = {
        "total_sources": 0,
        "high": 0,
        "medium": 0,
        "low": 0,
        "rejected": 0,
    }
    for digest in digests:
        digest_quality = digest.get("quality_summary", {}) or {}
        for key in quality_summary:
            quality_summary[key] += int(digest_quality.get(key, 0) or 0)
    return quality_summary


def summarize_rejected_reasons_from_digests(digests: list[dict[str, Any]]) -> list[str]:
    counts: dict[str, int] = {}
    for digest in digests:
        for reason in digest.get("rejected_reasons", []) or []:
            if not isinstance(reason, str):
                continue
            normalized = reason.strip()
            if not normalized:
                continue
            counts[normalized] = counts.get(normalized, 0) + 1

    ordered = sorted(counts.items(), key=lambda item: (-item[1], item[0]))
    return [reason for reason, _ in ordered[:5]]


def build_three_day_report(state: dict) -> dict:
    digests = load_recent_daily_digests(state.get("scope_name", ""))
    summary = summarize_digests(digests)
    quality_summary = summarize_quality_from_digests(digests)
    rejected_reasons = summarize_rejected_reasons_from_digests(digests)

    state["daily_digests"] = digests
    state["digest_summary"] = summary
    state["quality_summary"] = quality_summary
    state["rejected_reasons"] = rejected_reasons
    state["report_packet"] = build_report_packet(
        state,
        summary,
        quality_summary=quality_summary,
        rejected_reasons=rejected_reasons,
    )
    return state


def build_report_placeholder(state: dict) -> dict:
    state["report_packet"] = build_report_packet_placeholder(state)
    return state
