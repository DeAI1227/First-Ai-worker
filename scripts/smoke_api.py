from __future__ import annotations

import argparse
import json
import os
from pathlib import Path

from project_env import load_project_env

load_project_env(Path(__file__).resolve().parents[1])

import requests


DEFAULT_BASE_URL = "http://localhost:8000"
API_EXAMPLES_ROOT = Path(__file__).resolve().parents[1] / "api_examples"


def load_json_example(filename: str) -> dict:
    return json.loads((API_EXAMPLES_ROOT / filename).read_text(encoding="utf-8"))


def build_headers() -> dict[str, str]:
    headers = {"Content-Type": "application/json"}
    token = os.getenv("API_AUTH_TOKEN", "").strip()
    if token:
        headers["Authorization"] = f"Bearer {token}"
    return headers


def print_summary(label: str, payload: dict) -> None:
    print(label)
    print(f"- status: {payload.get('status')}")
    print(f"- execution_mode: {payload.get('execution_mode')}")
    print(f"- job_id: {payload.get('job_id')}")
    print(f"- message: {payload.get('message')}")
    errors = payload.get("errors") or []
    print(f"- errors_count: {len(errors)}")
    pipeline_report = (payload.get("data") or {}).get("pipeline_report")
    if isinstance(pipeline_report, dict):
        report_path = pipeline_report.get("pipeline_report_path")
        if report_path:
            print(f"- pipeline_report_path: {report_path}")


def main() -> int:
    parser = argparse.ArgumentParser(description="FastAPI orchestrator smoke test.")
    parser.add_argument("--base-url", default=DEFAULT_BASE_URL)
    args = parser.parse_args()

    base_url = args.base_url.rstrip("/")
    session = requests.Session()

    health = session.get(f"{base_url}/health", timeout=30)
    health.raise_for_status()
    print("Health check:")
    print(json.dumps(health.json(), ensure_ascii=False, indent=2))

    payload = load_json_example("pipeline_batch_industries_dry_run.json")
    response = session.post(
        f"{base_url}/pipeline/run",
        headers=build_headers(),
        json=payload,
        timeout=120,
    )
    response.raise_for_status()
    print_summary("Pipeline smoke test:", response.json())
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
