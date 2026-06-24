from __future__ import annotations

from pathlib import Path
from typing import Any

from collector.constants import COLLECTOR_NAME
from collector.utils.time_utils import now_iso, today_date

PROJECT_ROOT = Path(__file__).resolve().parents[2]

VALID_RUN_STATUSES = {"success", "partial_success", "failed"}
VALID_RUN_MODES = {"daily", "three_day"}
VALID_SOURCE_MODES = {"mock", "rss", "http", "search", "hybrid"}
VALID_SUMMARIZER_MODES = {"mock", "llm", "auto"}
VALID_LLM_PROVIDERS = {"mock", "agnes", "gemini", "auto"}
VALID_SEARCH_PROVIDERS = {"mock", "tavily", "serpapi", "firecrawl", "auto"}
VALID_SCOPES = {"macro", "industry", "stock", "institution_watch", "institution"}
VALID_ERROR_STAGES = {"fetch", "filter", "summarize", "validate", "repair", "write", "general"}
VALID_ERROR_SEVERITIES = {"info", "warning", "error"}


def build_crawl_run_packet(state: dict[str, Any]) -> dict[str, Any]:
    normalized_errors = normalize_run_errors(state.get("run_errors", []))
    validation_errors = normalize_run_errors(state.get("validation_errors", []), default_stage="validate", default_severity="error")
    all_errors = normalized_errors + validation_errors
    output_files = normalize_output_files(state.get("output_paths", []))
    main_output_files = [path for path in output_files if "/failed/" not in path.replace("\\", "/")]

    status = determine_status(main_output_files, all_errors)
    quality_summary = normalize_quality_summary(state.get("quality_summary", {}))
    rejected_sources = list(state.get("rejected_sources", []))
    filtered_sources = list(state.get("filtered_sources", []))

    packet = {
        "packet_type": "crawl_run",
        "collector": COLLECTOR_NAME,
        "run_id": state.get("run_id", ""),
        "run_date": state.get("run_date") or today_date(),
        "started_at": state.get("started_at", now_iso()),
        "finished_at": state.get("finished_at", now_iso()),
        "status": status,
        "mode": state.get("run_mode", ""),
        "scope": normalize_scope(state.get("scope", "")),
        "scope_name": state.get("scope_name", ""),
        "source_mode": state.get("source_mode", ""),
        "summarizer_mode": state.get("summarizer_mode", ""),
        "llm_provider": state.get("llm_provider", ""),
        "search_provider": state.get("search_provider", ""),
        "total_sources_count": len(state.get("raw_sources", [])),
        "accepted_sources_count": len(filtered_sources),
        "rejected_sources_count": len(rejected_sources),
        "quality_summary": quality_summary,
        "rejected_reasons": summarize_rejected_reasons(rejected_sources),
        "output_files": output_files,
        "run_errors": all_errors,
    }
    return packet


def validate_crawl_run_packet(packet: dict[str, Any]) -> list[str]:
    errors: list[str] = []

    if packet.get("packet_type") != "crawl_run":
        errors.append("packet_type must be crawl_run")
    if packet.get("collector") != COLLECTOR_NAME:
        errors.append("collector must be langgraph")

    for field in ["run_id", "run_date", "started_at", "finished_at", "mode", "scope", "scope_name", "source_mode", "summarizer_mode", "llm_provider", "search_provider"]:
        value = packet.get(field)
        if not isinstance(value, str) or not value.strip():
            errors.append(f"{field} is required")

    if packet.get("status") not in VALID_RUN_STATUSES:
        errors.append("status is invalid")

    if packet.get("mode") not in VALID_RUN_MODES:
        errors.append("mode is invalid")

    if packet.get("scope") not in VALID_SCOPES:
        errors.append("scope is invalid")

    if packet.get("source_mode") not in VALID_SOURCE_MODES:
        errors.append("source_mode is invalid")

    if packet.get("summarizer_mode") not in VALID_SUMMARIZER_MODES:
        errors.append("summarizer_mode is invalid")

    if packet.get("llm_provider") not in VALID_LLM_PROVIDERS:
        errors.append("llm_provider is invalid")

    if packet.get("search_provider") not in VALID_SEARCH_PROVIDERS:
        errors.append("search_provider is invalid")

    total_sources_count = packet.get("total_sources_count")
    accepted_sources_count = packet.get("accepted_sources_count")
    rejected_sources_count = packet.get("rejected_sources_count")
    if not _is_non_negative_int(total_sources_count):
        errors.append("total_sources_count must be an integer >= 0")
    if not _is_non_negative_int(accepted_sources_count):
        errors.append("accepted_sources_count must be an integer >= 0")
    if not _is_non_negative_int(rejected_sources_count):
        errors.append("rejected_sources_count must be an integer >= 0")

    if not isinstance(packet.get("quality_summary"), dict):
        errors.append("quality_summary is required")
    else:
        quality = packet["quality_summary"]
        for field in ["total_sources", "high", "medium", "low", "rejected"]:
            if not _is_non_negative_int(quality.get(field)):
                errors.append(f"quality_summary.{field} must be an integer >= 0")

    if not isinstance(packet.get("rejected_reasons"), list):
        errors.append("rejected_reasons must be a list")
    if not isinstance(packet.get("output_files"), list):
        errors.append("output_files must be a list")
    if not isinstance(packet.get("run_errors"), list):
        errors.append("run_errors must be a list")

    return errors


def determine_status(output_files: list[str], run_errors: list[dict[str, Any]]) -> str:
    has_main_output = bool(output_files)
    has_error = any(str(error.get("severity", "")).lower() == "error" for error in run_errors)
    has_warning = any(str(error.get("severity", "")).lower() in {"info", "warning"} for error in run_errors)

    if not has_main_output:
        return "failed" if has_error else "success"
    if has_error or has_warning:
        return "partial_success"
    return "success"


def normalize_scope(scope: str) -> str:
    if scope == "institution":
        return "institution_watch"
    return scope


def normalize_quality_summary(summary: dict[str, Any]) -> dict[str, int]:
    return {
        "total_sources": int(summary.get("total_sources", 0) or 0),
        "high": int(summary.get("high", 0) or 0),
        "medium": int(summary.get("medium", 0) or 0),
        "low": int(summary.get("low", 0) or 0),
        "rejected": int(summary.get("rejected", 0) or 0),
    }


def normalize_run_errors(
    errors: list[Any],
    *,
    default_stage: str = "general",
    default_severity: str = "warning",
) -> list[dict[str, str]]:
    normalized: list[dict[str, str]] = []
    for error in errors:
        if isinstance(error, dict):
            stage = _normalize_stage(error.get("stage"), default_stage)
            message = str(error.get("message", "")).strip()
            severity = _normalize_severity(error.get("severity"), default_severity)
        else:
            message = str(error).strip()
            stage = _infer_stage_from_message(message, default_stage)
            severity = _infer_severity_from_message(message, default_severity)

        if not message:
            continue

        normalized.append({
            "stage": stage,
            "message": message,
            "severity": severity,
        })
    return normalized


def summarize_rejected_reasons(rejected_sources: list[dict[str, Any]]) -> list[str]:
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


def normalize_output_files(output_files: list[Any]) -> list[str]:
    normalized: list[str] = []
    for output_file in output_files:
        path = str(output_file).strip()
        if not path:
            continue
        try:
            relative = Path(path).resolve().relative_to(PROJECT_ROOT)
            normalized.append(relative.as_posix())
        except Exception:
            normalized.append(path.replace("\\", "/"))
    return normalized


def _is_non_negative_int(value: Any) -> bool:
    return isinstance(value, int) and not isinstance(value, bool) and value >= 0


def _normalize_stage(value: Any, fallback: str) -> str:
    text = str(value or "").strip().lower()
    if text in VALID_ERROR_STAGES:
        return text
    return fallback


def _normalize_severity(value: Any, fallback: str) -> str:
    text = str(value or "").strip().lower()
    if text in VALID_ERROR_SEVERITIES:
        return text
    return fallback


def _infer_stage_from_message(message: str, fallback: str) -> str:
    lowered = message.lower()
    if any(token in lowered for token in ["rss", "http", "search", "fetch"]):
        return "fetch"
    if any(token in lowered for token in ["filter", "dedupe", "duplicate"]):
        return "filter"
    if "summarizer" in lowered or "summary" in lowered:
        return "summarize"
    if "validate" in lowered or "validation" in lowered:
        return "validate"
    if "repair" in lowered:
        return "repair"
    if "write" in lowered or "output" in lowered:
        return "write"
    return fallback


def _infer_severity_from_message(message: str, fallback: str) -> str:
    lowered = message.lower()
    if any(token in lowered for token in ["failed", "error", "missing", "invalid"]):
        return "error"
    if "fallback" in lowered or "used mock" in lowered:
        return "warning"
    return fallback
