from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any

from collector.constants import DEFAULT_LANGUAGE
from collector.utils.time_utils import today_date


def map_event_packet(packet: dict[str, Any], *, source_file: str | None = None) -> dict[str, Any]:
    scope, scope_name, run_id = _derive_context(packet, source_file)
    return {
        "event_id": str(packet.get("event_id") or _stable_packet_id("event", packet, source_file)),
        "run_id": run_id,
        "event_date": str(packet.get("event_date") or packet.get("collection_date") or _date_from_source_file(source_file) or today_date()),
        "scope": scope,
        "scope_name": scope_name,
        "event_type": str(packet.get("event_type", "") or "industry"),
        "importance": str(packet.get("importance", "") or "general"),
        "language": str(packet.get("language", "") or DEFAULT_LANGUAGE),
        "ai_summary": str(packet.get("ai_summary", "") or ""),
        "possible_impact": str(packet.get("possible_impact", "") or ""),
        "risk_note": str(packet.get("risk_note", "") or ""),
        "tags": _ensure_list(packet.get("tags", [])),
        "related_industries": _ensure_list(packet.get("related_industries", [])),
        "related_stocks": _ensure_list(packet.get("related_stocks", [])),
        "source_urls": _ensure_list(_source_urls_from_event(packet)),
        "raw_packet": packet,
    }


def map_daily_digest_packet(packet: dict[str, Any], *, source_file: str | None = None) -> dict[str, Any]:
    scope, scope_name, run_id = _derive_context(packet, source_file)
    return {
        "digest_id": str(packet.get("digest_id") or _stable_packet_id("digest", packet, source_file)),
        "run_id": run_id,
        "digest_date": str(packet.get("digest_date") or packet.get("created_at", "")[:10] or _date_from_source_file(source_file) or today_date()),
        "scope": scope,
        "scope_name": scope_name,
        "summary": str(packet.get("summary") or _build_digest_summary(packet)),
        "important_events": _ensure_list(packet.get("important_events") or packet.get("top_events", [])),
        "quality_summary": _normalize_quality_summary(packet.get("quality_summary", {})),
        "rejected_reasons": _ensure_list(packet.get("rejected_reasons", [])),
        "raw_packet": packet,
    }


def map_report_packet(packet: dict[str, Any], *, source_file: str | None = None) -> dict[str, Any]:
    scope, scope_name, run_id = _derive_context(packet, source_file)
    return {
        "report_id": str(packet.get("report_id") or _stable_packet_id("report", packet, source_file)),
        "run_id": run_id,
        "report_date": str(packet.get("report_date") or packet.get("period_end") or _date_from_source_file(source_file) or today_date()),
        "report_type": str(packet.get("report_type", "") or "full_report"),
        "scope": scope,
        "scope_name": scope_name,
        "importance": str(packet.get("importance", "") or "general"),
        "report_title": str(packet.get("report_title") or packet.get("title") or ""),
        "report_body": str(packet.get("report_body", "") or ""),
        "quality_summary": _normalize_quality_summary(packet.get("quality_summary", {})),
        "raw_packet": packet,
    }


def map_crawl_run_packet(packet: dict[str, Any], *, source_file: str | None = None) -> dict[str, Any]:
    return {
        "run_id": str(packet.get("run_id") or _stable_packet_id("run", packet, source_file)),
        "run_date": str(packet.get("run_date") or _date_from_source_file(source_file) or today_date()),
        "started_at": str(packet.get("started_at", "") or ""),
        "finished_at": str(packet.get("finished_at", "") or ""),
        "status": str(packet.get("status", "") or "failed"),
        "mode": str(packet.get("mode", "") or packet.get("run_mode", "") or "daily"),
        "scope": str(packet.get("scope", "") or _scope_from_source_file(source_file) or ""),
        "scope_name": str(packet.get("scope_name", "") or _scope_name_from_source_file(source_file) or ""),
        "source_mode": str(packet.get("source_mode", "") or "mock"),
        "summarizer_mode": str(packet.get("summarizer_mode", "") or "mock"),
        "llm_provider": str(packet.get("llm_provider", "") or "auto"),
        "search_provider": str(packet.get("search_provider", "") or "auto"),
        "total_sources_count": int(packet.get("total_sources_count", 0) or 0),
        "accepted_sources_count": int(packet.get("accepted_sources_count", 0) or 0),
        "rejected_sources_count": int(packet.get("rejected_sources_count", 0) or 0),
        "quality_summary": _normalize_quality_summary(packet.get("quality_summary", {})),
        "rejected_reasons": _ensure_list(packet.get("rejected_reasons", [])),
        "output_files": _ensure_list(packet.get("output_files", [])),
        "run_errors": _ensure_list(packet.get("run_errors", [])),
        "raw_packet": packet,
    }


def map_rejected_source(packet: dict[str, Any], *, source_file: str | None = None) -> dict[str, Any]:
    return {
        "run_id": str(packet.get("run_id") or _stable_packet_id("run", packet, source_file)),
        "source_url": str(packet.get("source_url", "") or ""),
        "source_name": str(packet.get("source_name", "") or ""),
        "source_type": str(packet.get("source_type", "") or "unknown"),
        "title": str(packet.get("title", "") or ""),
        "content": str(packet.get("content", "") or ""),
        "quality_score": int(packet.get("quality_score", 0) or 0),
        "quality_level": str(packet.get("quality_level", "") or "rejected"),
        "quality_reasons": _ensure_list(packet.get("quality_reasons", [])),
        "raw_source": packet.get("raw_source", packet),
    }


def _build_digest_summary(packet: dict[str, Any]) -> str:
    parts: list[str] = []
    top_events = [str(item) for item in _ensure_list(packet.get("top_events", [])) if str(item).strip()]
    key_takeaways = [str(item) for item in _ensure_list(packet.get("key_takeaways", [])) if str(item).strip()]
    if top_events:
        parts.append("Top events: " + "; ".join(top_events[:3]))
    if key_takeaways:
        parts.append("Key takeaways: " + "; ".join(key_takeaways[:3]))
    if not parts:
        parts.append(str(packet.get("digest_note", "") or "Daily digest generated from available sources."))
    return " ".join(parts)


def _ensure_list(value: Any) -> list[Any]:
    if isinstance(value, list):
        return value
    if value in (None, ""):
        return []
    return [value]


def _normalize_quality_summary(summary: dict[str, Any] | None) -> dict[str, int]:
    summary = summary or {}
    return {
        "total_sources": int(summary.get("total_sources", 0) or 0),
        "high": int(summary.get("high", 0) or 0),
        "medium": int(summary.get("medium", 0) or 0),
        "low": int(summary.get("low", 0) or 0),
        "rejected": int(summary.get("rejected", 0) or 0),
    }


def _source_urls_from_event(packet: dict[str, Any]) -> list[str]:
    if packet.get("source_urls"):
        return [str(item) for item in _ensure_list(packet["source_urls"])]
    source_url = packet.get("source_url")
    return [str(source_url)] if source_url else []


def _derive_context(packet: dict[str, Any], source_file: str | None) -> tuple[str, str, str]:
    scope = str(packet.get("scope") or _scope_from_source_file(source_file) or "")
    scope_name = str(packet.get("scope_name") or _scope_name_from_source_file(source_file) or scope)
    run_id = str(
        packet.get("run_id")
        or _run_id_from_source_file(source_file)
        or _stable_packet_id("run", packet, source_file)
    )
    return scope, scope_name, run_id


def _scope_from_source_file(source_file: str | None) -> str:
    if not source_file:
        return ""
    name = Path(source_file).name
    if "_macro" in name:
        return "macro"
    if "_industry" in name:
        return "industry"
    if "_stock" in name:
        return "stock"
    if "_institution" in name:
        return "institution_watch"
    return ""


def _scope_name_from_source_file(source_file: str | None) -> str:
    if not source_file:
        return ""
    parent = Path(source_file).parent.name
    if parent in {"daily", "three_day", "logs", "failed"}:
        return ""
    return parent


def _date_from_source_file(source_file: str | None) -> str:
    if not source_file:
        return ""
    name = Path(source_file).name
    for prefix in ("event_", "digest_", "report_", "crawl_run_"):
        if name.startswith(prefix):
            remainder = name.removeprefix(prefix)
            return remainder[:10]
    return ""


def _run_id_from_source_file(source_file: str | None) -> str:
    if not source_file:
        return ""
    name = Path(source_file).name
    if name.startswith("crawl_run_") and name.endswith(".json"):
        return name.removeprefix("crawl_run_").removesuffix(".json")
    return ""


def _stable_packet_id(prefix: str, packet: dict[str, Any], source_file: str | None) -> str:
    payload = json.dumps(
        {
            "prefix": prefix,
            "packet": packet,
            "source_file": source_file or "",
        },
        ensure_ascii=False,
        sort_keys=True,
        default=str,
    ).encode("utf-8")
    digest = hashlib.sha1(payload).hexdigest()[:16]
    return f"{prefix}_{digest}"

