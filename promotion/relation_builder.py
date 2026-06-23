from __future__ import annotations

from typing import Any

from collector.config.tracking_universe import (
    INDUSTRY_BY_NAME,
    INSTITUTION_BY_CODE,
    MACRO_TOPIC_BY_ID,
    STOCK_BY_CODE,
)
from collector.utils.time_utils import now_iso

RELATION_TYPES = ("industry", "stock", "event", "macro_topic", "institution_watch")


def build_event_relations(event_row: dict[str, Any], packet: dict[str, Any]) -> list[dict[str, Any]]:
    return _build_relations(
        parent_key="event_id",
        parent_id=event_row.get("event_id", ""),
        relation_sets={
            "industry": packet.get("related_industries", []) or [],
            "stock": packet.get("related_stocks", []) or [],
            "event": packet.get("related_events", []) or [],
            "macro_topic": packet.get("related_macro_topics", []) or [],
            "institution_watch": packet.get("related_institution_watch", []) or [],
        },
    )


def build_report_relations(report_row: dict[str, Any], packet: dict[str, Any]) -> list[dict[str, Any]]:
    return _build_relations(
        parent_key="report_id",
        parent_id=report_row.get("report_id", ""),
        relation_sets={
            "industry": packet.get("related_industries", []) or [],
            "stock": packet.get("related_stocks", []) or [],
            "event": packet.get("related_events", []) or [],
            "macro_topic": packet.get("related_macro_topics", []) or [],
            "institution_watch": packet.get("related_institution_watch", []) or [],
        },
    )


def _build_relations(*, parent_key: str, parent_id: str, relation_sets: dict[str, list[Any]]) -> list[dict[str, Any]]:
    relations: list[dict[str, Any]] = []
    seen: set[tuple[str, str]] = set()
    for relation_type, values in relation_sets.items():
        if relation_type not in RELATION_TYPES:
            continue
        for value in values:
            cleaned = str(value).strip()
            if not cleaned:
                continue
            if not _is_valid_relation_value(relation_type, cleaned):
                continue
            relation_key = (relation_type, cleaned)
            if relation_key in seen:
                continue
            seen.add(relation_key)
            relations.append(
                {
                    parent_key: parent_id,
                    "relation_type": relation_type,
                    "relation_value": cleaned,
                    "created_at": now_iso(),
                }
            )
    return relations


def _is_valid_relation_value(relation_type: str, value: str) -> bool:
    if relation_type == "industry":
        return value in INDUSTRY_BY_NAME
    if relation_type == "stock":
        return value in STOCK_BY_CODE
    if relation_type == "macro_topic":
        return value in MACRO_TOPIC_BY_ID
    if relation_type == "institution_watch":
        return value in INSTITUTION_BY_CODE
    if relation_type == "event":
        return bool(value)
    return False
