from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from typing import Any
from uuid import uuid4

from collector.utils.time_utils import now_iso, taipei_now

PROJECT_ROOT = Path(__file__).resolve().parents[1]
OUTPUT_ROOT = PROJECT_ROOT / "output"
PROMOTION_LOGS_ROOT = OUTPUT_ROOT / "promotion_logs"


def build_promotion_report(batch, *, promoted_rows: list[dict[str, Any]], relation_rows: list[dict[str, Any]], dry_run: bool) -> dict[str, Any]:
    report = {
        "promotion_id": batch.batch_id,
        "batch_id": batch.batch_id,
        "started_at": batch.started_at,
        "finished_at": batch.finished_at or now_iso(),
        "mode": "dry_run" if dry_run else "write",
        "input_path": batch.input_path,
        "packet_type_filter": batch.packet_type_filter,
        "files_scanned": batch.files_scanned,
        "packets_loaded": batch.packets_loaded,
        "promoted_events": batch.promoted.get("events", 0),
        "event_relations_created": batch.promoted.get("event_relations", 0),
        "reports_promoted": batch.promoted.get("reports", 0),
        "report_relations_created": batch.promoted.get("report_relations", 0),
        "crawl_runs_promoted": batch.promoted.get("crawl_runs", 0),
        "rejected_sources_promoted": batch.promoted.get("rejected_sources", 0),
        "skipped_daily_digests": batch.skipped_daily_digests,
        "errors": batch.errors,
    }
    report["status"] = status_from_promotion_report(report)
    return report


def status_from_promotion_report(report: dict[str, Any]) -> str:
    errors = report.get("errors", [])
    promoted_total = sum(
        int(report.get(key, 0) or 0)
        for key in [
            "promoted_events",
            "event_relations_created",
            "reports_promoted",
            "report_relations_created",
            "crawl_runs_promoted",
            "rejected_sources_promoted",
        ]
    )
    if not errors:
        return "success" if promoted_total > 0 else "failed"
    if promoted_total > 0:
        return "partial_success"
    return "failed"


def write_promotion_report(report: dict[str, Any], *, output_root: Path | None = None) -> str:
    root = output_root or OUTPUT_ROOT
    batch_dir = root if root.name == "promotion_logs" else root / "promotion_logs"
    batch_dir.mkdir(parents=True, exist_ok=True)
    timestamp = _timestamp_for_filename(report.get("finished_at") or report.get("started_at"))
    path = batch_dir / f"promotion_run_{timestamp}.json"
    path.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    return str(path)


def build_batch_id() -> str:
    return f"promotion_{taipei_now().strftime('%Y%m%d_%H%M%S')}_{uuid4().hex[:8]}"


def _timestamp_for_filename(value: Any) -> str:
    text = str(value or now_iso())
    try:
        dt = datetime.fromisoformat(text.replace("Z", "+00:00"))
    except ValueError:
        dt = taipei_now()
    return dt.strftime("%Y-%m-%d_%H%M%S")
