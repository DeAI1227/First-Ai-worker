from __future__ import annotations

from pathlib import Path
from typing import Any

from promotion.packet_promoter import promote_packets


def run_promotion_sync(*, input_path: str | Path, packet_type: str = "all", dry_run: bool = True) -> dict[str, Any]:
    report = promote_packets(input_path=input_path, packet_type_filter=packet_type, dry_run=dry_run)
    report["wrote_to_supabase"] = bool(report.get("wrote_to_supabase", False))
    if dry_run:
        report["message"] = "Promotion dry run completed."
    elif report.get("status") == "failed":
        report["message"] = "Promotion write mode failed."
    elif report.get("status") == "partial_success":
        report["message"] = "Promotion write mode completed with warnings."
    else:
        report["message"] = "Promotion write mode completed."
    return report
