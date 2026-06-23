from __future__ import annotations

from typing import Any

from promotion.supabase_client import SupabaseClient


UPSERT_KEYS = {
    "events": "event_id",
    "reports": "report_id",
    "crawl_runs": "run_id",
    "event_relations": "event_id,relation_type,relation_value",
    "report_relations": "report_id,relation_type,relation_value",
}

APPEND_ONLY_TABLES = {"rejected_sources"}


def upsert_row(client: SupabaseClient, table: str, row: dict[str, Any]) -> Any:
    payload = _clean_row(row)
    if table in APPEND_ONLY_TABLES:
        return client.insert(table, payload)
    if table not in UPSERT_KEYS:
        raise ValueError(f"Unsupported table: {table}")
    return client.upsert(table, payload, on_conflict=UPSERT_KEYS[table])


def _clean_row(row: dict[str, Any]) -> dict[str, Any]:
    payload = dict(row)
    payload.pop("target_table", None)
    return payload
