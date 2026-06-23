from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from ingestion.error_logger import build_ingestion_error

_SKIP_JSON_PREFIXES = (
    "batch_run_",
    "coverage_report_",
    "pipeline_run_",
    "promotion_run_",
    "ingestion_batch_",
    "e2e_smoke_",
    "failed_",
)
_SKIP_JSON_PARENT_DIRS = {
    "ingestion_logs",
    "promotion_logs",
    "failed",
}


def find_json_files(input_path: str | Path) -> list[Path]:
    root = Path(input_path)
    if not root.exists():
        return []
    return sorted(path for path in root.rglob("*.json") if path.is_file() and not _should_skip_json_file(path))


def _should_skip_json_file(path: Path) -> bool:
    name = path.name.lower()
    if any(name.startswith(prefix) for prefix in _SKIP_JSON_PREFIXES):
        return True
    return any(parent.name.lower() in _SKIP_JSON_PARENT_DIRS for parent in path.parents)


def load_json_packets(input_path: str | Path) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    packets: list[dict[str, Any]] = []
    errors: list[dict[str, Any]] = []

    for path in find_json_files(input_path):
        try:
            payload = json.loads(path.read_text(encoding="utf-8"))
        except Exception as exc:  # pragma: no cover - defensive, covered by tests
            errors.append(
                build_ingestion_error(
                    packet_type="unknown",
                    packet_id=path.stem,
                    target_table="packet_loader",
                    error_message=f"Failed to load JSON from {path}: {exc}",
                    raw_packet={"file_path": str(path)},
                )
            )
            continue

        if isinstance(payload, list):
            items = payload
        else:
            items = [payload]

        for index, item in enumerate(items):
            if not isinstance(item, dict):
                errors.append(
                    build_ingestion_error(
                        packet_type="unknown",
                        packet_id=f"{path.stem}[{index}]",
                        target_table="packet_loader",
                        error_message=f"JSON item is not an object: {path}",
                        raw_packet=item,
                    )
                )
                continue

            packets.append(
                {
                    "packet": item,
                    "source_file": str(path),
                    "packet_index": index,
                }
            )

    return packets, errors
