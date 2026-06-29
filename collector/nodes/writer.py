from __future__ import annotations

from pathlib import Path

from collector.utils.file_utils import next_sequence, sanitize_path_segment, write_json
from collector.utils.time_utils import today_date


PROJECT_ROOT = Path(__file__).resolve().parents[2]
OUTPUT_ROOT = PROJECT_ROOT / "output"


def scope_output_dir(state: dict) -> Path:
    scope = state.get("scope") or "unknown"
    if scope == "stock":
        stock_code = sanitize_path_segment(state.get("target_stock_code") or "unknown")
        stock_name = sanitize_path_segment(
            state.get("target_stock_name") or state.get("scope_name") or stock_code,
            fallback="unknown",
        )
        return OUTPUT_ROOT / "daily" / "stocks" / f"{stock_code}_{stock_name}"

    scope_name = sanitize_path_segment(state.get("scope_name") or scope or "unknown")
    return OUTPUT_ROOT / "daily" / scope_name


def write_event_packet(state: dict) -> dict:
    packet = state.get("event_packet", {})
    if state.get("validation_errors"):
        return write_failed_packet(state)

    out_dir = scope_output_dir(state)
    date = today_date()
    scope = sanitize_path_segment(state.get("scope", "scope"))
    seq = next_sequence(out_dir, f"event_{date}_{scope}")
    path = out_dir / f"event_{date}_{scope}_{seq:03d}.json"
    state.setdefault("output_paths", []).append(write_json(path, packet))
    return state


def write_daily_digest(state: dict) -> dict:
    packet = state.get("daily_digest_packet", {})
    out_dir = scope_output_dir(state)
    date = today_date()
    scope = sanitize_path_segment(state.get("scope", "scope"))
    path = out_dir / f"digest_{date}_{scope}.json"
    state.setdefault("output_paths", []).append(write_json(path, packet))
    return state


def write_crawl_run(state: dict) -> dict:
    packet = state.get("crawl_run_packet", {})
    date = today_date()
    scope = sanitize_path_segment(state.get("scope", "scope"))
    path = OUTPUT_ROOT / "logs" / f"crawl_run_{date}_{scope}.json"
    state.setdefault("output_paths", []).append(write_json(path, packet))
    return state


def write_report_packet(state: dict) -> dict:
    packet = state.get("report_packet", {})
    date = today_date()
    scope = sanitize_path_segment(state.get("scope", "scope"))
    scope_name = sanitize_path_segment(state.get("scope_name") or scope)
    path = OUTPUT_ROOT / "three_day" / scope_name / f"report_{date}_{scope}_report.json"
    state.setdefault("output_paths", []).append(write_json(path, packet))
    return state


def write_failed_packet(state: dict) -> dict:
    payload = {
        "task_id": state.get("task_id"),
        "event_packet": state.get("event_packet", {}),
        "validation_errors": state.get("validation_errors", []),
        "run_errors": state.get("run_errors", []),
    }
    date = today_date()
    scope = sanitize_path_segment(state.get("scope", "scope"))
    seq = next_sequence(OUTPUT_ROOT / "failed", f"failed_{date}_{scope}")
    path = OUTPUT_ROOT / "failed" / f"failed_{date}_{scope}_{seq:03d}.json"
    state.setdefault("output_paths", []).append(write_json(path, payload))
    return state
