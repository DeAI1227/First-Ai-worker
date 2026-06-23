from __future__ import annotations

from pathlib import Path
from typing import Any

from collector.utils.time_utils import now_iso
from ingestion.batch_report import build_batch_report, write_batch_report
from ingestion.ingest_outputs import dry_run_ingest, write_ingest


def run_ingestion_sync(*, input_path: str | Path, packet_type: str = "all", dry_run: bool = True) -> dict[str, Any]:
    started_at = now_iso()
    if dry_run:
        summary = dry_run_ingest(Path(input_path), packet_type_filter=None if packet_type == "all" else packet_type)
        batch_report = build_batch_report(
            mode="dry_run",
            input_path=str(input_path),
            packet_type_filter=packet_type,
            started_at=started_at,
            finished_at=now_iso(),
            summary=summary,
            errors=summary.get("error_entries", []),
        )
    else:
        summary = write_ingest(Path(input_path), packet_type_filter=None if packet_type == "all" else packet_type)
        batch_report = build_batch_report(
            mode="write",
            input_path=str(input_path),
            packet_type_filter=packet_type,
            started_at=started_at,
            finished_at=now_iso(),
            summary=summary,
            errors=summary.get("error_entries", []),
        )
    batch_report_path = write_batch_report(batch_report)
    batch_report["batch_report_path"] = batch_report_path
    batch_report["wrote_to_supabase"] = bool(summary.get("wrote_to_supabase", False))
    batch_report["message"] = "Ingestion run completed."
    return batch_report
