from __future__ import annotations

from typing import Any

from collector.constants import (
    COLLECTOR_NAME,
    DEFAULT_LANGUAGE,
    EVENT_AI_SUMMARY_MAX_CHARS,
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
    source_urls = _source_urls(sources)

    return {
        "packet_type": "event",
        "collector": COLLECTOR_NAME,
        "collection_date": today_date(),
        "title": _event_title(state, len(source_urls)),
        "event_type": state.get("event_type", "industry"),
        "importance": state.get("importance", "general"),
        "source_name": first_source.get("source_name", ""),
        "source_url": first_source.get("source_url", ""),
        "source_urls": source_urls,
        "source_count": len(source_urls),
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
    if len(packet.get("ai_summary", "")) > EVENT_AI_SUMMARY_MAX_CHARS:
        errors.append(f"ai_summary must be <= {EVENT_AI_SUMMARY_MAX_CHARS} chars")
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


def _event_title(state: dict[str, Any], source_count: int) -> str:
    scope = state.get("scope", "")
    scope_name = state.get("scope_name", "") or "研究主題"
    stock_code = state.get("target_stock_code", "")
    stock_name = state.get("target_stock_name", "")

    if scope == "stock" and stock_code:
        label = f"{stock_code} {stock_name or scope_name}".strip()
        return f"{label} 今日研究摘要（{source_count} 則來源）"
    if scope in {"institution", "institution_watch"} and stock_code:
        label = f"{stock_code} {stock_name or scope_name}".strip()
        return f"大行關注 {label} 研究摘要（{source_count} 則來源）"
    if scope == "macro":
        return f"{scope_name} 大環境研究摘要（{source_count} 則來源）"
    if scope == "industry":
        return f"{scope_name} 產業研究摘要（{source_count} 則來源）"
    return f"{scope_name} 研究摘要（{source_count} 則來源）"


def _source_urls(sources: list[dict[str, Any]]) -> list[str]:
    urls: list[str] = []
    seen: set[str] = set()
    for source in sources:
        url = str(source.get("source_url", "") or "").strip()
        if not url or url in seen:
            continue
        seen.add(url)
        urls.append(url)
    return urls
