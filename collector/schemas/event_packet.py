from __future__ import annotations

from typing import Any

from collector.constants import (
    COLLECTOR_NAME,
    DEFAULT_LANGUAGE,
    VALID_EVENT_TYPES,
    VALID_IMPORTANCE,
    VALID_INDUSTRIES,
    VALID_MVP_STOCKS,
)
from collector.utils.text_utils import contains_prohibited_terms
from collector.utils.time_utils import today_date


def build_event_packet(state: dict[str, Any]) -> dict[str, Any]:
    sources = state.get("filtered_sources", [])
    first_source = sources[0] if sources else {}
    title = first_source.get("title") or f"{state.get('scope_name', '研究')}事件摘要"
    return {
        "packet_type": "event",
        "collector": COLLECTOR_NAME,
        "collection_date": today_date(),
        "title": title,
        "event_type": state.get("event_type", "industry"),
        "importance": state.get("importance", "general"),
        "source_name": first_source.get("source_name", "Mock Source"),
        "source_url": first_source.get("source_url", ""),
        "published_at": first_source.get("published_at", ""),
        "ai_summary": state.get("ai_summary", ""),
        "possible_impact": state.get("possible_impact", ""),
        "risk_note": state.get("risk_note", ""),
        "related_industries": state.get("related_industries", []),
        "related_stocks": state.get("related_stocks", []),
        "related_macro_topics": state.get("related_macro_topics", []),
        "related_institution_watch": state.get("related_institution_watch", []),
        "tags": state.get("tags", []),
        "language": DEFAULT_LANGUAGE,
    }


def validate_event_packet(packet: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    if packet.get("packet_type") != "event":
        errors.append("packet_type must be event")
    if packet.get("collector") != COLLECTOR_NAME:
        errors.append("collector must be langgraph")
    if packet.get("language") != DEFAULT_LANGUAGE:
        errors.append("language must be zh-TW")
    if not packet.get("source_url"):
        errors.append("source_url is required")
    if len(packet.get("ai_summary", "")) > 500:
        errors.append("ai_summary must be <= 500 chars")
    if packet.get("event_type") not in VALID_EVENT_TYPES:
        errors.append("event_type is invalid")
    if packet.get("importance") not in VALID_IMPORTANCE:
        errors.append("importance is invalid")

    related_industries = packet.get("related_industries", [])
    related_stocks = packet.get("related_stocks", [])

    if not isinstance(related_industries, list):
        errors.append("related_industries must be a list")
        related_industries = []
    if not isinstance(related_stocks, list):
        errors.append("related_stocks must be a list")
        related_stocks = []

    for industry in related_industries:
        if industry not in VALID_INDUSTRIES:
            errors.append(f"related_industries contains non-industry: {industry}")
        if industry in VALID_MVP_STOCKS:
            errors.append(f"stock code cannot be in related_industries: {industry}")

    for stock in related_stocks:
        if stock not in VALID_MVP_STOCKS:
            errors.append(f"related_stocks contains non-stock-code: {stock}")
        if stock in VALID_INDUSTRIES:
            errors.append(f"industry cannot be in related_stocks: {stock}")

    prohibited = contains_prohibited_terms(packet)
    if prohibited:
        errors.append("prohibited terms found: " + ", ".join(sorted(set(prohibited))))

    return errors
