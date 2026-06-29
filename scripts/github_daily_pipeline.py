from __future__ import annotations

import argparse
import json
import os
import sys
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Any
from urllib import error, request


PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from collector.config.tracking_universe import TRACKING_INDUSTRIES
from collector.task_batches import all_daily_tasks


DEFAULT_SOURCE_MODE = "hybrid"
DEFAULT_SUMMARIZER_MODE = "auto"
DEFAULT_LL_PROVIDER = "auto"
DEFAULT_SEARCH_PROVIDER = "firecrawl"
DEFAULT_INPUT_PATH = "output/"
DEFAULT_REQUEST_TIMEOUT = 600


@dataclass(frozen=True)
class PipelineStep:
    name: str
    payload: dict[str, Any]


def build_collect_payload_from_task(task: dict[str, Any]) -> dict[str, Any]:
    scope = str(task.get("scope") or "all").strip() or "all"
    scope_name = str(task.get("scope_name") or task.get("industry_name") or task.get("macro_topic_name") or "").strip()
    stock_code = str(task.get("target_stock_code") or task.get("stock_code") or "").strip()
    stock_name = str(task.get("target_stock_name") or task.get("stock_name") or "").strip()
    return {
        "mode": str(task.get("run_mode") or "daily").strip() or "daily",
        "scope": scope,
        "scope_name": scope_name,
        "stock_code": stock_code,
        "stock_name": stock_name,
        "source_mode": str(task.get("source_mode") or DEFAULT_SOURCE_MODE),
        "summarizer_mode": str(task.get("summarizer_mode") or DEFAULT_SUMMARIZER_MODE),
        "llm_provider": str(task.get("llm_provider") or DEFAULT_LL_PROVIDER),
        "search_provider": str(task.get("search_provider") or DEFAULT_SEARCH_PROVIDER),
        "ingestion_dry_run": False,
        "promotion_dry_run": False,
        "collect": {
            "mode": str(task.get("run_mode") or "daily").strip() or "daily",
            "scope": scope,
            "scope_name": scope_name,
            "stock_code": stock_code,
            "stock_name": stock_name,
            "source_mode": str(task.get("source_mode") or DEFAULT_SOURCE_MODE),
            "summarizer_mode": str(task.get("summarizer_mode") or DEFAULT_SUMMARIZER_MODE),
            "llm_provider": str(task.get("llm_provider") or DEFAULT_LL_PROVIDER),
            "search_provider": str(task.get("search_provider") or DEFAULT_SEARCH_PROVIDER),
            "dry_run": False,
        },
        "ingestion": {
            "enabled": True,
            "input_path": DEFAULT_INPUT_PATH,
            "packet_type": "all",
            "dry_run": False,
        },
        "promotion": {
            "enabled": True,
            "input_path": DEFAULT_INPUT_PATH,
            "packet_type": "all",
            "dry_run": False,
        },
    }


def build_single_task_step(task: dict[str, Any], *, prefix: str = "daily") -> PipelineStep:
    scope = str(task.get("scope") or "all").strip() or "all"
    key = _task_key(task)
    return PipelineStep(f"{prefix}:{scope}:{key}", build_collect_payload_from_task(task))


def build_daily_payload(batch: str) -> dict[str, Any]:
    return {
        "scope": "all",
        "source_mode": DEFAULT_SOURCE_MODE,
        "summarizer_mode": DEFAULT_SUMMARIZER_MODE,
        "ingestion_dry_run": False,
        "promotion_dry_run": False,
        "collect": {
            "batch": batch,
            "source_mode": DEFAULT_SOURCE_MODE,
            "summarizer_mode": DEFAULT_SUMMARIZER_MODE,
            "llm_provider": DEFAULT_LL_PROVIDER,
            "search_provider": DEFAULT_SEARCH_PROVIDER,
        },
        "ingestion": {
            "enabled": True,
            "input_path": DEFAULT_INPUT_PATH,
            "packet_type": "all",
            "dry_run": False,
        },
        "promotion": {
            "enabled": True,
            "input_path": DEFAULT_INPUT_PATH,
            "packet_type": "all",
            "dry_run": False,
        },
    }


def build_three_day_payload(scope: str, scope_name: str) -> dict[str, Any]:
    return {
        "mode": "three_day",
        "scope": scope,
        "scope_name": scope_name,
        "source_mode": DEFAULT_SOURCE_MODE,
        "summarizer_mode": DEFAULT_SUMMARIZER_MODE,
        "ingestion_dry_run": False,
        "promotion_dry_run": False,
        "collect": {
            "mode": "three_day",
            "scope": scope,
            "scope_name": scope_name,
            "source_mode": DEFAULT_SOURCE_MODE,
            "summarizer_mode": DEFAULT_SUMMARIZER_MODE,
            "llm_provider": DEFAULT_LL_PROVIDER,
            "search_provider": DEFAULT_SEARCH_PROVIDER,
        },
        "ingestion": {
            "enabled": True,
            "input_path": DEFAULT_INPUT_PATH,
            "packet_type": "all",
            "dry_run": False,
        },
        "promotion": {
            "enabled": True,
            "input_path": DEFAULT_INPUT_PATH,
            "packet_type": "all",
            "dry_run": False,
        },
    }


def build_pipeline_steps(*, include_three_day: bool = True) -> list[PipelineStep]:
    steps: list[PipelineStep] = [
        build_single_task_step(task, prefix="daily") for task in all_daily_tasks(
            source_mode=DEFAULT_SOURCE_MODE,
            summarizer_mode=DEFAULT_SUMMARIZER_MODE,
            llm_provider=DEFAULT_LL_PROVIDER,
            search_provider=DEFAULT_SEARCH_PROVIDER,
        )
    ]

    if include_three_day:
        for industry in TRACKING_INDUSTRIES:
            if not industry.get("enabled", True):
                continue
            steps.append(
                PipelineStep(
                    f"three_day:industry:{industry['industry_id']}",
                    build_three_day_payload("industry", str(industry["industry_name"])),
                )
            )
        steps.append(PipelineStep("three_day:macro:macro_environment", build_three_day_payload("macro", "macro_environment")))

    return steps


def _task_key(task: dict[str, Any]) -> str:
    scope = str(task.get("scope") or "all").strip().lower()
    if scope == "macro":
        return str(task.get("macro_topic_id") or task.get("scope_name") or "macro").strip()
    if scope == "industry":
        return str(task.get("industry_id") or task.get("target_stock_code") or task.get("scope_name") or "industry").strip()
    if scope == "stock":
        return str(task.get("target_stock_code") or task.get("scope_name") or "stock").strip()
    if scope in {"institution", "institution_watch"}:
        return str(task.get("institution_watch_code") or task.get("target_stock_code") or "institution").strip()
    return str(task.get("scope_name") or scope or "task").strip()

def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run the daily GitHub Actions pipeline with warm-up and retries.")
    parser.add_argument("--base-url", default=os.getenv("FASTAPI_BASE_URL", "").strip(), help="FastAPI base URL")
    parser.add_argument("--token", default=os.getenv("API_AUTH_TOKEN", "").strip(), help="API auth token")
    parser.add_argument("--skip-three-day", action="store_true", help="Run only the daily batches")
    parser.add_argument("--max-retries", type=int, default=3, help="Retries per HTTP call")
    parser.add_argument(
        "--request-timeout",
        type=int,
        default=int(os.getenv("PIPELINE_REQUEST_TIMEOUT_SECONDS", str(DEFAULT_REQUEST_TIMEOUT))),
        help="Timeout in seconds for each /pipeline/run call",
    )
    parser.add_argument("--health-retries", type=int, default=6, help="Retries for the warm-up health check")
    return parser.parse_args()


def require_env(name: str, value: str) -> str:
    cleaned = value.strip()
    if not cleaned:
        raise SystemExit(f"{name} is missing")
    return cleaned


def http_json(
    *,
    method: str,
    url: str,
    token: str | None = None,
    payload: dict[str, Any] | None = None,
    timeout: int = 300,
) -> tuple[int, str]:
    data = None
    headers = {
        "Content-Type": "application/json",
        "Accept": "application/json",
    }
    if token:
        headers["Authorization"] = f"Bearer {token}"
    if payload is not None:
        data = json.dumps(payload).encode("utf-8")
    req = request.Request(url, data=data, headers=headers, method=method)
    try:
        with request.urlopen(req, timeout=timeout) as resp:
            body = resp.read().decode("utf-8", errors="replace")
            return int(resp.status), body
    except error.HTTPError as exc:
        body = exc.read().decode("utf-8", errors="replace")
        return int(exc.code), body
    except TimeoutError as exc:
        return 598, f"Request timed out after {timeout}s: {exc}"
    except error.URLError as exc:
        return 599, f"Network error: {exc}"


def wait_for_health(base_url: str, token: str, retries: int) -> None:
    url = f"{base_url.rstrip('/')}/health"
    for attempt in range(1, retries + 1):
        status, body = http_json(method="GET", url=url, token=token, timeout=30)
        if status == 200:
            print(f"[health] ok on attempt {attempt}")
            return
        print(f"[health] attempt {attempt} failed: HTTP {status}")
        if body.strip():
            print(body)
        if attempt < retries:
            time.sleep(min(30, 5 * attempt))
    raise SystemExit("Backend health check never became ready")


def call_pipeline_step(
    base_url: str,
    token: str,
    step: PipelineStep,
    max_retries: int,
    request_timeout: int,
) -> dict[str, Any]:
    url = f"{base_url.rstrip('/')}/pipeline/run"
    retryable_statuses = {502, 503, 504, 599}

    for attempt in range(1, max_retries + 1):
        status, body = http_json(
            method="POST",
            url=url,
            token=token,
            payload=step.payload,
            timeout=max(request_timeout, 30),
        )
        print(f"[{step.name}] attempt {attempt} -> HTTP {status}")
        if body.strip():
            print(body)

        if status in retryable_statuses:
            if attempt < max_retries:
                sleep_for = min(60, 5 * attempt)
                print(f"[{step.name}] retrying after {sleep_for}s")
                time.sleep(sleep_for)
                continue
            return {
                "step": step.name,
                "status": "failed",
                "http_status": status,
                "message": body[:500],
                "payload": step.payload,
            }

        if status >= 400:
            return {
                "step": step.name,
                "status": "failed",
                "http_status": status,
                "message": body[:500],
                "payload": step.payload,
            }

        try:
            parsed = json.loads(body)
        except json.JSONDecodeError as exc:
            if attempt < max_retries:
                print(f"[{step.name}] invalid JSON response, retrying: {exc}")
                time.sleep(min(30, 5 * attempt))
                continue
            return {
                "step": step.name,
                "status": "failed",
                "http_status": status,
                "message": f"Invalid JSON response: {exc}",
                "payload": step.payload,
            }

        payload_status = str(parsed.get("status") or "").strip().lower()
        execution_mode = str(parsed.get("execution_mode") or "").strip().lower()
        job_id = parsed.get("job_id")
        wrote_to_supabase = bool(parsed.get("wrote_to_supabase", False))
        errors = parsed.get("errors") if isinstance(parsed.get("errors"), list) else []

        print(
            json.dumps(
                {
                    "step": step.name,
                    "status": payload_status,
                    "execution_mode": execution_mode,
                    "job_id": job_id,
                    "wrote_to_supabase": wrote_to_supabase,
                    "errors": len(errors),
                },
                ensure_ascii=False,
            )
        )
        return {
            "step": step.name,
            "status": payload_status or "failed",
            "http_status": status,
            "message": str(parsed.get("message") or ""),
            "execution_mode": execution_mode,
            "job_id": job_id,
            "wrote_to_supabase": wrote_to_supabase,
            "errors": parsed.get("errors", []),
            "data": parsed.get("data", {}),
        }

    return {
        "step": step.name,
        "status": "failed",
        "http_status": 0,
        "message": "Retry budget exhausted",
        "payload": step.payload,
    }


def render_summary(results: list[dict[str, Any]]) -> dict[str, Any]:
    status_counts = {"success": 0, "partial_success": 0, "failed": 0}
    wrote_to_supabase = False
    for item in results:
        status = str(item.get("status") or "failed").strip().lower()
        if status in status_counts:
            status_counts[status] += 1
        else:
            status_counts["failed"] += 1
        wrote_to_supabase = wrote_to_supabase or bool(item.get("wrote_to_supabase", False))

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
        "",
        "### Steps",
    ]
    for step in summary["steps"]:
        text.append(
            f"- `{step['step']}` -> `{step.get('status')}` (HTTP {step.get('http_status')}, wrote_to_supabase={step.get('wrote_to_supabase', False)})"
        )

    step_summary = "\n".join(text) + "\n"
    summary_path = os.getenv("GITHUB_STEP_SUMMARY", "").strip()
    if summary_path:
        Path(summary_path).write_text(step_summary, encoding="utf-8")

    print(step_summary)


def main() -> int:
    args = parse_args()
    base_url = require_env("FASTAPI_BASE_URL", args.base_url)
    token = require_env("API_AUTH_TOKEN", args.token)

    wait_for_health(base_url, token, args.health_retries)

    steps = build_pipeline_steps(include_three_day=not args.skip_three_day)
    results = [call_pipeline_step(base_url, token, step, args.max_retries, args.request_timeout) for step in steps]
    summary = render_summary(results)
    write_step_summary(summary)

    return 0 if summary["status"] == "success" else 1


if __name__ == "__main__":
    raise SystemExit(main())
