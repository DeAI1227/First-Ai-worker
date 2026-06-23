from __future__ import annotations

from datetime import datetime
from pathlib import Path
from typing import Any

from collector.coverage_report import build_coverage_report, write_coverage_report
from collector.graph import run_collector_task, run_three_day_report_task
from collector.utils.file_utils import write_json
from collector.utils.time_utils import now_iso, today_date, taipei_now

PROJECT_ROOT = Path(__file__).resolve().parents[1]
OUTPUT_ROOT = PROJECT_ROOT / "output"
BATCH_LOGS_ROOT = OUTPUT_ROOT / "logs"


def run_batch_tasks(
    tasks: list[dict[str, Any]],
    *,
    batch_type: str,
) -> dict[str, Any]:
    started_at = now_iso()
    batch_id = f"batch_{today_date().replace('-', '')}_{taipei_now().strftime('%H%M%S')}"
    results: list[dict[str, Any]] = []
    output_files: list[str] = []
    run_errors: list[str] = []

    for task in tasks:
        try:
            runner = run_three_day_report_task if task.get("run_mode") == "three_day" else run_collector_task
            state = runner(task)
            results.append(state)
            output_files.extend(state.get("output_paths", []))
            run_errors.extend(str(error) for error in state.get("run_errors", []))
        except Exception as exc:  # pragma: no cover - defensive batch guard
            results.append(
                {
                    "task_id": task.get("task_id", ""),
                    "status": "failed",
                    "output_paths": [],
                    "run_errors": [str(exc)],
                }
            )
            run_errors.append(str(exc))

    summary = build_batch_summary(
        batch_id=batch_id,
        batch_type=batch_type,
        started_at=started_at,
        finished_at=now_iso(),
        tasks=results,
        output_files=output_files,
        run_errors=run_errors,
    )
    coverage_report = build_coverage_report(tasks, results, coverage_date=today_date())
    summary["coverage_report"] = coverage_report
    summary["coverage_report_path"] = write_coverage_report(coverage_report)
    summary["batch_report_path"] = write_batch_summary(summary)
    return summary


def build_batch_summary(
    *,
    batch_id: str,
    batch_type: str,
    started_at: str,
    finished_at: str,
    tasks: list[dict[str, Any]],
    output_files: list[str],
    run_errors: list[str],
) -> dict[str, Any]:
    status_counts = {"success": 0, "partial_success": 0, "failed": 0}
    for task in tasks:
        status = str(task.get("status", "failed"))
        if status in status_counts:
            status_counts[status] += 1
        else:
            status_counts["failed"] += 1

    if not tasks:
        status = "failed"
    elif status_counts["failed"] > 0:
        status = "partial_success" if (status_counts["success"] > 0 or status_counts["partial_success"] > 0) else "failed"
    elif status_counts["partial_success"] > 0:
        status = "partial_success"
    elif run_errors:
        status = "partial_success"
    else:
        status = "success"

    return {
        "batch_id": batch_id,
        "batch_type": batch_type,
        "started_at": started_at,
        "finished_at": finished_at,
        "status": status,
        "total_tasks": len(tasks),
        "success_tasks": status_counts["success"],
        "partial_success_tasks": status_counts["partial_success"],
        "failed_tasks": status_counts["failed"],
        "output_files": dedupe_preserve_order(output_files),
        "run_errors": dedupe_preserve_order(run_errors),
    }


def write_batch_summary(summary: dict[str, Any], *, output_root: Path | None = None) -> str:
    timestamp = _timestamp_for_filename(summary.get("finished_at") or summary.get("started_at"))
    root = output_root or BATCH_LOGS_ROOT
    path = root / f"batch_run_{timestamp}.json"
    return write_json(path, summary)


def dedupe_preserve_order(values: list[str]) -> list[str]:
    ordered: list[str] = []
    seen: set[str] = set()
    for value in values:
        cleaned = str(value).strip()
        if not cleaned or cleaned in seen:
            continue
        seen.add(cleaned)
        ordered.append(cleaned)
    return ordered


def _timestamp_for_filename(value: Any) -> str:
    text = str(value or now_iso())
    try:
        dt = datetime.fromisoformat(text.replace("Z", "+00:00"))
    except ValueError:
        dt = taipei_now()
    return dt.strftime("%Y-%m-%d_%H%M%S")
