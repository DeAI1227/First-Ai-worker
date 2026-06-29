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


DEFAULT_SOURCE_MODE = "hybrid"
DEFAULT_SUMMARIZER_MODE = "auto"
DEFAULT_LL_PROVIDER = "auto"
DEFAULT_SEARCH_PROVIDER = "firecrawl"
DEFAULT_INPUT_PATH = "output/"
DEFAULT_REQUEST_TIMEOUT = 600
DEFAULT_COLLECT_BATCHES = ("macro", "industries", "stocks", "institution_watch")


@dataclass(frozen=True)
class PipelineStep:
    name: str
    endpoint: str
    payload: dict[str, Any]
    timeout_seconds: int = DEFAULT_REQUEST_TIMEOUT


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


def build_pipeline_steps(*, include_three_day: bool = True) -> list[PipelineStep]:
    steps: list[PipelineStep] = []

    for batch in DEFAULT_COLLECT_BATCHES:
        steps.append(
            PipelineStep(
                name=f"collect:{batch}",
                endpoint="/collect/run",
                payload=build_collect_batch_payload(batch),
            )
        )

    if include_three_day:
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
    parser = argparse.ArgumentParser(description="Run the GitHub Actions daily + three-day backend pipeline.")
    parser.add_argument("--base-url", default=os.getenv("FASTAPI_BASE_URL", "").strip(), help="FastAPI base URL")
    parser.add_argument("--token", default=os.getenv("API_AUTH_TOKEN", "").strip(), help="API auth token")
    parser.add_argument("--skip-three-day", action="store_true", help="Run only the daily collection batches")
    parser.add_argument("--max-retries", type=int, default=3, help="Retries per HTTP call")
    parser.add_argument(
        "--request-timeout",
        type=int,
        default=int(os.getenv("PIPELINE_REQUEST_TIMEOUT_SECONDS", str(DEFAULT_REQUEST_TIMEOUT))),
        help="Timeout in seconds for each API call",
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


def wait_for_health(base_url: str, retries: int) -> None:
    url = f"{base_url.rstrip('/')}/health"
    for attempt in range(1, retries + 1):
        status, body = http_json(method="GET", url=url, timeout=30)
        if status == 200:
            print(f"[health] ok on attempt {attempt}")
            return
        print(f"[health] attempt {attempt} failed: HTTP {status}")
        if body.strip():
            print(body)
        if attempt < retries:
            time.sleep(min(30, 5 * attempt))
    raise SystemExit("Backend health check never became ready")


def call_api_step(
    base_url: str,
    token: str,
    step: PipelineStep,
    max_retries: int,
    request_timeout: int,
) -> dict[str, Any]:
    url = f"{base_url.rstrip('/')}{step.endpoint}"
    retryable_statuses = {502, 503, 504, 598, 599}

    for attempt in range(1, max_retries + 1):
        status, body = http_json(
            method="POST",
            url=url,
            token=token,
            payload=step.payload,
            timeout=max(step.timeout_seconds, request_timeout, 30),
        )
        print(f"[{step.name}] attempt {attempt} -> HTTP {status}")
        if body.strip():
            print(body)

        if status in retryable_statuses and attempt < max_retries:
            sleep_for = min(60, 5 * attempt)
            print(f"[{step.name}] retrying after {sleep_for}s")
            time.sleep(sleep_for)
            continue

        if status >= 400:
            return {
                "step": step.name,
                "endpoint": step.endpoint,
                "status": "failed",
                "http_status": status,
                "message": body[:1000],
                "payload": step.payload,
                "wrote_to_supabase": False,
                "output_files": [],
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
                "endpoint": step.endpoint,
                "status": "failed",
                "http_status": status,
                "message": f"Invalid JSON response: {exc}",
                "payload": step.payload,
                "wrote_to_supabase": False,
                "output_files": [],
            }

        payload_status = str(parsed.get("status") or "").strip().lower() or "failed"
        errors = parsed.get("errors") if isinstance(parsed.get("errors"), list) else []
        data = parsed.get("data") if isinstance(parsed.get("data"), dict) else {}
        wrote_to_supabase = bool(parsed.get("wrote_to_supabase", False))
        output_files = extract_output_files(parsed, data)

        print(
            json.dumps(
                {
                    "step": step.name,
                    "status": payload_status,
                    "endpoint": step.endpoint,
                    "wrote_to_supabase": wrote_to_supabase,
                    "errors": len(errors),
                    "output_files": len(output_files),
                },
                ensure_ascii=False,
            )
        )

        return {
            "step": step.name,
            "endpoint": step.endpoint,
            "status": payload_status,
            "http_status": status,
            "message": str(parsed.get("message") or ""),
            "wrote_to_supabase": wrote_to_supabase,
            "errors": errors,
            "data": data,
            "output_files": output_files,
        }

    return {
        "step": step.name,
        "endpoint": step.endpoint,
        "status": "failed",
        "http_status": 0,
        "message": "Retry budget exhausted",
        "payload": step.payload,
        "wrote_to_supabase": False,
        "output_files": [],
    }


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
    base_url = require_env("FASTAPI_BASE_URL", args.base_url)
    token = require_env("API_AUTH_TOKEN", args.token)

    wait_for_health(base_url, args.health_retries)

    steps = build_pipeline_steps(include_three_day=not args.skip_three_day)
    results = [call_api_step(base_url, token, step, args.max_retries, args.request_timeout) for step in steps]
    summary = render_summary(results)
    write_step_summary(summary)

    return 0 if summary["status"] == "success" else 1


if __name__ == "__main__":
    raise SystemExit(main())
