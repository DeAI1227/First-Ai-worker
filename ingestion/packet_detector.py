from __future__ import annotations

from typing import Any

from ingestion.config import PACKET_TYPE_ALIASES


def detect_packet_type(packet: dict[str, Any]) -> str:
    explicit = str(packet.get("packet_type", "")).strip().lower()
    if explicit:
        if explicit in PACKET_TYPE_ALIASES:
            return PACKET_TYPE_ALIASES[explicit]
        if explicit in PACKET_TYPE_ALIASES.values():
            return explicit

    if "quality_level" in packet and "quality_reasons" in packet and "raw_source" in packet:
        return "rejected_source"
    if "report_id" in packet:
        return "report_packet"
    if "digest_id" in packet:
        return "daily_digest_packet"
    if "event_id" in packet:
        return "event_packet"
    if "run_id" in packet and (
        "source_mode" in packet
        or "quality_summary" in packet
        or "output_files" in packet
        or "run_errors" in packet
        or "accepted_sources_count" in packet
        or "rejected_sources_count" in packet
    ):
        return "crawl_run_packet"
    return "unknown"

