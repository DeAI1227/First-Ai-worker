from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from typing import Any
from uuid import uuid4

from collector.utils.time_utils import now_iso, taipei_now


PROJECT_ROOT = Path(__file__).resolve().parents[1]
OUTPUT_ROOT = PROJECT_ROOT / "output"
BATCH_LOGS_ROOT = OUTPUT_ROOT / "ingestion_logs"


def build_batch_error(
    *,
    stage: str,
    packet_type: str,
    packet_id: str,
    target_table: str,
    message: str,
    severity: str = "error",
) -> dict[str, Any]:
    return {
        "stage": stage,
        "packet_type": packet_type,
        "packet_id": packet_id,
        "target_table": target_table,
        "message": message,
        "severity": severity,
    }


def normalize_batch_error(error: Any) -> dict[str, Any]:
    if isinstance(error, dict):
        if {"stage", "packet_type", "packet_id", "target_table", "message", "severity"} <= set(error.keys()):
            return {
                "stage": str(error.get("stage", "error")).strip() or "error",
                "packet_type": str(error.get("packet_type", "") or "unknown"),
                "packet_id": str(error.get("packet_id", "") or ""),
                "target_table": str(error.get("target_table", "") or ""),
                "message": str(error.get("message", "") or ""),
                "severity": _normalize_severity(error.get("severity", "error")),
            }
        return {
            "stage": _infer_stage(error),
            "packet_type": str(error.get("packet_type", "") or "unknown"),
            "packet_id": str(error.get("packet_id", "") or ""),
            "target_table": str(error.get("target_table", "") or ""),
            "message": str(
                error.get("message")
                or error.get("error_message")
                or error.get("reason")
                or ""
            ),
            "severity": _normalize_severity(error.get("severity", "error")),
        }

    message = str(error).strip()
    return build_batch_error(
        stage=_infer_stage({"message": message}),
        packet_type="unknown",
        packet_id="",
        target_table="",
        message=message,
        severity=_infer_severity(message),
    )


def build_batch_report(
    *,
    mode: str,
    input_path: str,
    packet_type_filter: str,
    started_at: str | None = None,
    finished_at: str | None = None,
    summary: dict[str, Any],
    errors: list[Any] | None = None,
) -> dict[str, Any]:
    normalized_errors = [normalize_batch_error(error) for error in (errors or []) if str(error).strip()]
    mapped = {
        "events": int(summary.get("mapped_events", 0) or 0),
        "daily_digests": int(summary.get("mapped_daily_digests", 0) or 0),
        "reports": int(summary.get("mapped_reports", 0) or 0),
        "crawl_runs": int(summary.get("mapped_crawl_runs", 0) or 0),
        "rejected_sources": int(summary.get("mapped_rejected_sources", 0) or 0),
    }
    written = {
        "events": int(summary.get("written_events", 0) or 0),
        "daily_digests": int(summary.get("written_daily_digests", 0) or 0),
        "reports": int(summary.get("written_reports", 0) or 0),
        "crawl_runs": int(summary.get("written_crawl_runs", 0) or 0),
        "rejected_sources": int(summary.get("written_rejected_sources", 0) or 0),
    }
    failed = {
        "events": int(summary.get("failed_events", 0) or 0),
        "daily_digests": int(summary.get("failed_daily_digests", 0) or 0),
        "reports": int(summary.get("failed_reports", 0) or 0),
        "crawl_runs": int(summary.get("failed_crawl_runs", 0) or 0),
        "rejected_sources": int(summary.get("failed_rejected_sources", 0) or 0),
    }

    report = {
        "batch_id": summary.get("batch_id") or build_batch_id(),
        "started_at": started_at or summary.get("started_at") or now_iso(),
        "finished_at": finished_at or summary.get("finished_at") or now_iso(),
        "mode": mode,
        "input_path": str(input_path),
        "packet_type_filter": packet_type_filter or "all",
        "files_scanned": int(summary.get("files_scanned", 0) or 0),
        "packets_loaded": int(summary.get("packets_loaded", 0) or 0),
        "unknown_packets": int(summary.get("unknown_packets", 0) or 0),
        "mapped": mapped,
        "written": written,
        "failed": failed,
        "errors": normalized_errors,
    }
    report["status"] = status_from_batch_report(report)
    return report


def status_from_batch_report(report: dict[str, Any]) -> str:
    errors = report.get("errors", [])
    mapped_total = _sum_counts(report.get("mapped", {}))
    written_total = _sum_counts(report.get("written", {}))
    failed_total = _sum_counts(report.get("failed", {}))

    if any(
        "missing required environment variables" in str(error.get("message", "")).lower()
        for error in errors
        if isinstance(error, dict)
    ):
        return "failed"

    if failed_total > 0:
        return "partial_success" if (mapped_total > 0 or written_total > 0) else "failed"

    if not errors:
        if report.get("mode") == "dry_run":
            return "success" if mapped_total > 0 else "failed"
        return "success" if written_total > 0 or mapped_total > 0 else "failed"

    has_error = any(_normalize_severity(error.get("severity")) == "error" for error in errors if isinstance(error, dict))
    has_success = mapped_total > 0 or written_total > 0
    if has_success and not has_error:
        return "partial_success"
    if has_success and has_error:
        return "partial_success"
    return "failed"


def write_batch_report(report: dict[str, Any], *, output_root: Path | None = None) -> str:
    root = output_root or OUTPUT_ROOT
    batch_dir = root if root.name == "ingestion_logs" else root / "ingestion_logs"
    batch_dir.mkdir(parents=True, exist_ok=True)
    timestamp = _timestamp_for_filename(report.get("finished_at") or report.get("started_at"))
    path = batch_dir / f"ingestion_batch_{timestamp}.json"
    path.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    return str(path)


def build_batch_id() -> str:
    return f"batch_{taipei_now().strftime('%Y%m%d_%H%M%S')}_{uuid4().hex[:8]}"


def _timestamp_for_filename(value: Any) -> str:
    text = str(value or now_iso())
    try:
        dt = datetime.fromisoformat(text.replace("Z", "+00:00"))
    except ValueError:
        dt = taipei_now()
    return dt.strftime("%Y-%m-%d_%H%M%S")


def _sum_counts(block: dict[str, Any]) -> int:
    return sum(int(block.get(key, 0) or 0) for key in block.keys())


def _normalize_severity(value: Any) -> str:
    text = str(value or "").strip().lower()
    if text in {"info", "warning", "error"}:
        return text
    return "error"


def _infer_stage(error: dict[str, Any]) -> str:
    text = " ".join(str(value) for value in error.values()).lower()
    if "load" in text or "json" in text:
        return "load"
    if "detect" in text:
        return "detect"
    if "map" in text:
        return "map"
    if "error_log" in text or "ingestion_errors" in text:
        return "error_log"
    if "write" in text or "supabase" in text:
        return "write"
    return "error"


def _infer_severity(message: str) -> str:
    lowered = message.lower()
    if "missing required environment variables" in lowered:
        return "error"
    if "fallback" in lowered:
        return "warning"
    return "error"
