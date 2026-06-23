from __future__ import annotations

from typing import Any

from collector.utils.time_utils import now_iso


def build_ingestion_error(
    *,
    packet_type: str,
    packet_id: str,
    target_table: str,
    error_message: str,
    raw_packet: Any,
) -> dict[str, Any]:
    return {
        "packet_type": packet_type,
        "packet_id": packet_id,
        "target_table": target_table,
        "error_message": error_message,
        "raw_packet": raw_packet,
        "created_at": now_iso(),
    }

