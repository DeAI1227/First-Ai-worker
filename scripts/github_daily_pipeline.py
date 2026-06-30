from __future__ import annotations

import argparse
import os
import sys
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Any


PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from project_env import load_project_env

load_project_env(PROJECT_ROOT)

from api.schemas import CollectRunRequest
from api.services.collector_service import run_collect_sync
from api.services.ingestion_service import run_ingestion_sync
from api.services.promotion_service import run_promotion_sync
from collector.config.tracking_universe import TRACKING_INDUSTRIES


DEFAULT_SOURCE_MODE = "hybrid"
DEFAULT_SUMMARIZER_MODE = "auto"
DEFAULT_LL_PROVIDER = "auto"
DEFAULT_SEARCH_PROVIDER = "firecrawl"
DEFAULT_INPUT_PATH = "output/"
DEFAULT_COLLECT_BATCHES = ("macro", "industries", "stocks", "institution_watch")
DAILY_BATCH_CHOICES = ("macro", "industries", "stocks", "institution_watch")


@dataclass(frozen=True)
class PipelineStep:
    name: str
    endpoint: str
    payload: dict[str, Any]


def build_collect_batch_payload(batch: str) -> dict[str, Any]:
    return {
        "mode": "daily",
        "batch": batch,
        "source_mode": DEFAULT_SOURCE_MODE,
        "summarizer_mode": DEFAULT_SUMMARIZER_MODE,
        "llm_provider": DEFAULT_LL_PROVIDER,
        "search_provider": DEFAULT_SEARCH_PROVIDER,
        "dry_run": False,
    }


def build_three_day_collect_payload(scope: str, scope_name: str) -> dict[str, Any]:
    return {
        "mode": "three_day",
        "scope": scope,
        "scope_name": scope_name,
        "source_mode": DEFAULT_SOURCE_MODE,
        "summarizer_mode": DEFAULT_SUMMARIZER_MODE,
        "llm_provider": DEFAULT_LL_PROVIDER,
        "search_provider": DEFAULT_SEARCH_PROVIDER,
        "dry_run": False,
    }


def build_ingestion_payload() -> dict[str, Any]:
    return {
        "input_path": DEFAULT_INPUT_PATH,
        "packet_type": "all",
        "dry_run": False,
    }


def build_promotion_payload() -> dict[str, Any]:
    return {
        "input_path": DEFAULT_INPUT_PATH,
        "packet_type": "all",
        "dry_run": False,
    }


def build_pipeline_steps(
    *,
    daily_batches: tuple[str, ...],
    include_three_day_industries: bool,
    include_three_day_macro: bool,
) -> list[PipelineStep]:
    steps: list[PipelineStep] = []

    for batch in daily_batches:
        steps.append(
            PipelineStep(
                name=f"collect:{batch}",
                endpoint="/collect/run",
                payload=build_collect_batch_payload(batch),
            )
        )

    if include_three_day_industries:
        for industry in TRACKING_INDUSTRIES:
            if not industry.get("enabled", True):
                continue
            steps.append(
                PipelineStep(
                    name=f"collect:three_day:industry:{industry['industry_id']}",
                    endpoint="/collect/run",
                    payload=build_three_day_collect_payload("industry", str(industry["industry_name"])),
                )
            )

    if include_three_day_macro:
        steps.append(
            PipelineStep(
                name="collect:three_day:macro:macro_environment",
                endpoint="/collect/run",
                payload=build_three_day_collect_payload("macro", "macro_environment"),
            )
        )

    steps.append(
        PipelineStep(
            name="ingestion:write",
            endpoint="/ingestion/run",
            payload=build_ingestion_payload(),
        )
    )
    steps.append(
        PipelineStep(
            name="promotion:write",
            endpoint="/promotion/run",
            payload=build_promotion_payload(),
        )
    )
    return steps


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run a segmented GitHub Actions backend pipeline.")
    parser.add_argument(
        "--daily-batch",
        action="append",
        choices=DAILY_BATCH_CHOICES,
        dest="daily_batches",
        help="Daily collect batch to run. Repeat to run multiple batches.",
    )
    parser.add_argument(
        "--three-day-industries",
        action="store_true",
        help="Run three-day report refresh for all enabled industries.",
    )
    parser.add_argument(
        "--three-day-macro",
        action="store_true",
        help="Run three-day macro report refresh.",
    )
    return parser.parse_args()


def run_local_pipeline_steps(steps: list[PipelineStep]) -> list[dict[str, Any]]:
    results: list[dict[str, Any]] = []
    for step in steps:
        started_at = time.perf_counter()
        print(f"[pipeline] starting {step.name} ({step.endpoint})", flush=True)
        try:
            result = run_local_step(step)
        except Exception as exc:  # pragma: no cover - defensive
            result = {
                "step": step.name,
                "endpoint": step.endpoint,
                "status": "failed",
                "message": str(exc),
                "wrote_to_supabase": False,
                "run_errors": [
                    {
                        "stage": _step_stage(step),
                        "message": str(exc),
                        "severity": "error",
                        "details": {"payload": step.payload},
                    }
                ],
                "output_files": [],
            }
        normalized = normalize_local_result(step, result)
        elapsed = time.perf_counter() - started_at
        print(
            f"[pipeline] finished {step.name} status={normalized['status']} "
            f"wrote_to_supabase={normalized['wrote_to_supabase']} "
            f"outputs={len(normalized['output_files'])} elapsed={elapsed:.1f}s",
            flush=True,
        )
        results.append(normalized)
    return results


def run_local_step(step: PipelineStep) -> dict[str, Any]:
    if step.endpoint == "/collect/run":
        request = CollectRunRequest.model_validate(step.payload)
        return run_collect_sync(request)
    if step.endpoint == "/ingestion/run":
        return run_ingestion_sync(
            input_path=step.payload.get("input_path", DEFAULT_INPUT_PATH),
            packet_type=str(step.payload.get("packet_type", "all")),
            dry_run=bool(step.payload.get("dry_run", True)),
        )
    if step.endpoint == "/promotion/run":
        return run_promotion_sync(
            input_path=step.payload.get("input_path", DEFAULT_INPUT_PATH),
            packet_type=str(step.payload.get("packet_type", "all")),
            dry_run=bool(step.payload.get("dry_run", True)),
        )
    raise ValueError(f"Unsupported pipeline endpoint: {step.endpoint}")


def normalize_local_result(step: PipelineStep, result: dict[str, Any]) -> dict[str, Any]:
    payload_status = str(result.get("status") or "").strip().lower() or "failed"
    errors = result.get("run_errors") if isinstance(result.get("run_errors"), list) else result.get("errors")
    errors = errors if isinstance(errors, list) else []
    output_files = extract_output_files(result, result.get("batch_report", {}) if isinstance(result.get("batch_report"), dict) else {})

    return {
        "step": step.name,
        "endpoint": step.endpoint,
        "status": payload_status,
        "http_status": 200 if payload_status != "failed" else 500,
        "message": str(result.get("message") or ""),
        "wrote_to_supabase": bool(result.get("wrote_to_supabase", False)),
        "errors": errors,
        "data": result.get("data") if isinstance(result.get("data"), dict) else {},
        "output_files": output_files,
    }


def _step_stage(step: PipelineStep) -> str:
    if step.endpoint == "/collect/run":
        return "collect"
    if step.endpoint == "/ingestion/run":
        return "ingestion"
    if step.endpoint == "/promotion/run":
        return "promotion"
    return "internal"

"""
Legacy remote HTTP runner helpers were intentionally removed from the GitHub
Actions path. The scheduled workflow now executes the collector pipeline
directly inside the runner to avoid Render 502/timeout issues on long-running
daily jobs.
"""
def extract_output_files(envelope: dict[str, Any], data: dict[str, Any]) -> list[str]:
    files: list[str] = []
    for container in (envelope, data, data.get("batch_report", {}), data.get("pipeline_report", {})):
        if not isinstance(container, dict):
            continue
        for key in ("output_files", "output_paths"):
            value = container.get(key)
            if isinstance(value, list):
                files.extend(str(item).strip() for item in value if str(item).strip())
        for key in ("batch_report_path", "coverage_report_path", "pipeline_report_path"):
            value = container.get(key)
            if isinstance(value, str) and value.strip():
                files.append(value.strip())
    return unique_strings(files)


def render_summary(results: list[dict[str, Any]]) -> dict[str, Any]:
    status_counts = {"success": 0, "partial_success": 0, "failed": 0}
    wrote_to_supabase = False
    output_files: list[str] = []

    for item in results:
        status = str(item.get("status") or "failed").strip().lower()
        status_counts[status if status in status_counts else "failed"] += 1
        wrote_to_supabase = wrote_to_supabase or bool(item.get("wrote_to_supabase", False))
        output_files.extend(item.get("output_files", []))

    if status_counts["failed"] > 0:
        overall_status = "partial_success" if (status_counts["success"] > 0 or status_counts["partial_success"] > 0) else "failed"
    elif status_counts["partial_success"] > 0:
        overall_status = "partial_success"
    else:
        overall_status = "success"

    return {
        "status": overall_status,
        "wrote_to_supabase": wrote_to_supabase,
        "success_steps": status_counts["success"],
        "partial_success_steps": status_counts["partial_success"],
        "failed_steps": status_counts["failed"],
        "output_files": unique_strings(output_files),
        "steps": results,
    }


def write_step_summary(summary: dict[str, Any]) -> None:
    text = [
        "## Daily AI Research Pipeline",
        "",
        f"- Status: `{summary['status']}`",
        f"- Wrote to Supabase: `{summary['wrote_to_supabase']}`",
        f"- Success steps: `{summary['success_steps']}`",
        f"- Partial success steps: `{summary['partial_success_steps']}`",
        f"- Failed steps: `{summary['failed_steps']}`",
        f"- Output files captured: `{len(summary['output_files'])}`",
        "",
        "### Steps",
    ]
    for step in summary["steps"]:
        text.append(
            f"- `{step['step']}` -> `{step.get('status')}` "
            f"(HTTP {step.get('http_status')}, wrote_to_supabase={step.get('wrote_to_supabase', False)})"
        )

    step_summary = "\n".join(text) + "\n"
    summary_path = os.getenv("GITHUB_STEP_SUMMARY", "").strip()
    if summary_path:
        Path(summary_path).write_text(step_summary, encoding="utf-8")

    print(step_summary)


def should_exit_successfully(summary: dict[str, Any]) -> bool:
    status = str(summary.get("status") or "failed").strip().lower()
    if status == "success":
        return True
    if status != "partial_success":
        return False
    return bool(summary.get("wrote_to_supabase")) or bool(summary.get("output_files"))


def unique_strings(values: list[str]) -> list[str]:
    seen: set[str] = set()
    unique: list[str] = []
    for value in values:
        text = str(value).strip()
        if not text or text in seen:
            continue
        seen.add(text)
        unique.append(text)
    return unique


def main() -> int:
    args = parse_args()
    if args.daily_batches:
        daily_batches = tuple(args.daily_batches)
        include_three_day_industries = bool(args.three_day_industries)
        include_three_day_macro = bool(args.three_day_macro)
    else:
        daily_batches = DEFAULT_COLLECT_BATCHES
        include_three_day_industries = True
        include_three_day_macro = True

    steps = build_pipeline_steps(
        daily_batches=daily_batches,
        include_three_day_industries=include_three_day_industries,
        include_three_day_macro=include_three_day_macro,
    )
    results = run_local_pipeline_steps(steps)
    summary = render_summary(results)
    write_step_summary(summary)

    return 0 if should_exit_successfully(summary) else 1


if __name__ == "__main__":
    raise SystemExit(main())
