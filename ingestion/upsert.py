from __future__ import annotations

from typing import Any

from ingestion.config import PACKET_TARGET_TABLES
from ingestion.supabase_client import SupabaseClient


UPSERT_KEYS = {
    "staging_events": "event_id",
    "staging_daily_digests": "digest_id",
    "staging_reports": "report_id",
    "staging_crawl_runs": "run_id",
}

APPEND_ONLY_TABLES = {"staging_rejected_sources"}


def target_table_for_packet_type(packet_type: str) -> str:
    return PACKET_TARGET_TABLES[packet_type]


def route_upsert(client: SupabaseClient, packet_type: str, row: dict[str, Any]) -> Any:
    table = target_table_for_packet_type(packet_type)
    if table in APPEND_ONLY_TABLES:
        return client.insert(table, _clean_row(row))
    return client.upsert(table, _clean_row(row), on_conflict=UPSERT_KEYS[table])


def _clean_row(row: dict[str, Any]) -> dict[str, Any]:
    payload = dict(row)
    payload.pop("target_table", None)
    return payload
