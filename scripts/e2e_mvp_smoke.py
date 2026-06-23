from __future__ import annotations

import argparse
import json
import shutil
import sys
from pathlib import Path
from tempfile import TemporaryDirectory
from typing import Any, Iterable

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from collector.batch_runner import run_batch_tasks
from collector.config.tracking_universe import (
    INSTITUTION_WATCH_STOCKS,
    MACRO_TOPICS,
    TRACKED_STOCKS,
    TRACKING_INDUSTRIES,
)
from collector.task_batches import generate_batch_tasks
from collector.utils.time_utils import taipei_now
from ingestion.ingest_outputs import dry_run_ingest
from promotion.packet_promoter import promote_packets

OUTPUT_ROOT = PROJECT_ROOT / "output"
LOGS_ROOT = OUTPUT_ROOT / "logs"
REQUIRED_FRONTEND_VIEWS = [
    "view_dashboard_events",
    "view_industry_cards",
    "view_stock_cards",
    "view_stock_detail_events",
    "view_macro_events",
    "view_institution_watch_events",
    "view_recent_reports",
    "view_unread_counts",
]
FAKE_NO_NEWS_PHRASES = (
    "今日未找到重大更新",
    "無重大更新",
)


def _timestamp() -> str:
    return taipei_now().strftime("%Y-%m-%d_%H%M%S")


def _now_iso() -> str:
    return taipei_now().isoformat(timespec="seconds")


def _write_json(path: Path, payload: dict[str, Any]) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    return path


def _record_error(errors: list[dict[str, Any]], stage: str, message: str, *, severity: str = "error") -> None:
    errors.append({"stage": stage, "message": message, "severity": severity})


def _tracked_stock_codes() -> list[str]:
    codes = {str(item.get("stock_code", "") or "") for item in TRACKED_STOCKS}
    codes.update(str(item.get("stock_code", "") or "") for item in INSTITUTION_WATCH_STOCKS)
    return sorted(code for code in codes if code)


def _scan_for_fake_no_news(paths: Iterable[str]) -> bool:
    for raw_path in paths:
        if not raw_path:
            continue
        path = Path(raw_path)
        if "no_news" in path.name.lower():
            return True
        if not path.exists() or not path.is_file():
            continue
        try:
            text = path.read_text(encoding="utf-8")
        except Exception:
            continue
        for phrase in FAKE_NO_NEWS_PHRASES:
            if phrase in text:
                return True
    return False


def _count_required_views(schema_text: str) -> list[str]:
    return [view for view in REQUIRED_FRONTEND_VIEWS if view not in schema_text]


def _copy_paths_to_staging(paths: Iterable[str], staging_root: Path) -> None:
    for raw_path in paths:
        if not raw_path:
            continue
        source = Path(raw_path)
        if not source.exists() or not source.is_file():
            continue
        try:
            relative = source.relative_to(OUTPUT_ROOT)
        except ValueError:
            relative = Path(source.name)
        destination = staging_root / relative
        destination.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(source, destination)


def run_e2e_smoke() -> dict[str, Any]:
    started_at = _now_iso()
    smoke_id = f"e2e_smoke_{_timestamp()}"
    errors: list[dict[str, Any]] = []
    report: dict[str, Any] = {
        "smoke_id": smoke_id,
        "started_at": started_at,
        "finished_at": "",
        "status": "failed",
        "tracked_stocks_count": len(_tracked_stock_codes()),
        "industries_count": len(TRACKING_INDUSTRIES),
        "macro_topics_count": len(MACRO_TOPICS),
        "institution_watch_count": len(INSTITUTION_WATCH_STOCKS),
        "batch_all_ran": False,
        "ingestion_dry_run_ran": False,
        "promotion_dry_run_ran": False,
        "frontend_views_checked": False,
        "fake_no_news_events_found": False,
        "errors": errors,
    }

    batch_summary: dict[str, Any] = {}
    ingest_summary: dict[str, Any] = {}
    promotion_summary: dict[str, Any] = {}

    try:
        tasks = generate_batch_tasks(
            "all",
            source_mode="mock",
            summarizer_mode="mock",
            search_provider="mock",
        )
        batch_summary = run_batch_tasks(tasks, batch_type="all")
        report["batch_all_ran"] = True
        report["batch_summary_path"] = batch_summary.get("batch_report_path", "")
        report["coverage_report_path"] = batch_summary.get("coverage_report_path", "")
        report["output_files"] = list(batch_summary.get("output_files", []))

        if not report["output_files"]:
            _record_error(errors, "collect", "batch all completed without output files")
        if batch_summary.get("status") == "failed":
            _record_error(errors, "collect", "batch all returned failed status")
        elif batch_summary.get("status") == "partial_success":
            _record_error(errors, "collect", "batch all returned partial_success", severity="warning")
    except Exception as exc:  # pragma: no cover - defensive smoke guard
        _record_error(errors, "collect", str(exc))

    try:
        with TemporaryDirectory() as temp_dir:
            staging_root = Path(temp_dir) / "smoke_input"
            _copy_paths_to_staging(report.get("output_files", []), staging_root)

            ingest_summary = dry_run_ingest(staging_root, packet_type_filter=None)
            report["ingestion_dry_run_ran"] = True
            report["ingestion_summary"] = ingest_summary
            report["ingestion_batch_report_path"] = ingest_summary.get("batch_report_path", "")
            if ingest_summary.get("status") == "failed":
                _record_error(errors, "ingestion", "ingestion dry-run returned failed status")
            elif ingest_summary.get("status") == "partial_success":
                _record_error(errors, "ingestion", "ingestion dry-run returned partial_success", severity="warning")

            promotion_summary = promote_packets(input_path=staging_root, dry_run=True)
            report["promotion_dry_run_ran"] = True
            report["promotion_summary"] = promotion_summary
            report["promotion_report_path"] = promotion_summary.get("batch_report_path", "")
            if promotion_summary.get("status") == "failed":
                _record_error(errors, "promotion", "promotion dry-run returned failed status")
            elif promotion_summary.get("status") == "partial_success":
                _record_error(errors, "promotion", "promotion dry-run returned partial_success", severity="warning")
    except Exception as exc:  # pragma: no cover - defensive smoke guard
        _record_error(errors, "ingestion", str(exc))

    try:
        schema_path = PROJECT_ROOT / "supabase" / "production_schema.sql"
        schema_text = schema_path.read_text(encoding="utf-8")
        missing_views = _count_required_views(schema_text)
        if missing_views:
            _record_error(errors, "frontend_views", f"Missing frontend views: {', '.join(missing_views)}")
        else:
            report["frontend_views_checked"] = True
    except Exception as exc:  # pragma: no cover - defensive smoke guard
        _record_error(errors, "frontend_views", str(exc))

    batch_paths = list(report.get("output_files", []))
    batch_paths.extend(
        path
        for path in [
            report.get("batch_summary_path", ""),
            report.get("coverage_report_path", ""),
            report.get("ingestion_batch_report_path", ""),
            report.get("promotion_report_path", ""),
        ]
        if path
    )
    report["fake_no_news_events_found"] = _scan_for_fake_no_news(batch_paths)
    if report["fake_no_news_events_found"]:
        _record_error(errors, "collect", "fake no-news event detected")

    report["finished_at"] = _now_iso()
    main_steps_ok = any(
        bool(report.get(flag))
        for flag in ("batch_all_ran", "ingestion_dry_run_ran", "promotion_dry_run_ran", "frontend_views_checked")
    )
    substep_statuses = [batch_summary.get("status"), ingest_summary.get("status"), promotion_summary.get("status")]
    if report["fake_no_news_events_found"]:
        report["status"] = "failed"
    elif any(status == "failed" for status in substep_statuses):
        report["status"] = "partial_success" if main_steps_ok else "failed"
    elif any(status == "partial_success" for status in substep_statuses) or errors:
        report["status"] = "partial_success" if main_steps_ok else "failed"
    else:
        report["status"] = "success"

    smoke_report_path = LOGS_ROOT / f"{smoke_id}.json"
    report["smoke_report_path"] = str(smoke_report_path)
    _write_json(smoke_report_path, report)
    return report


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run end-to-end MVP smoke test.")
    return parser.parse_args()


def main() -> int:
    _ = parse_args()
    report = run_e2e_smoke()
    print(json.dumps(report, ensure_ascii=False, indent=2))
    return 0 if report["status"] == "success" else 1


if __name__ == "__main__":
    raise SystemExit(main())
