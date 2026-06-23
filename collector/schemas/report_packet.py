from __future__ import annotations

from typing import Any

from collector.constants import (
    COLLECTOR_NAME,
    DEFAULT_LANGUAGE,
    PROHIBITED_TERMS,
    VALID_IMPORTANCE,
    VALID_INDUSTRIES,
    VALID_MVP_STOCKS,
)
from collector.utils.time_utils import now_iso, today_date


def determine_report_importance(summary: dict[str, Any]) -> str:
    if summary.get("critical_count", 0) > 0:
        return "critical"
    if summary.get("important_count", 0) > 0:
        return "important"
    return "general"


def report_type_for_scope(scope: str) -> str:
    if scope == "industry":
        return "industry_report"
    if scope == "macro":
        return "macro_report"
    return "full_report"


def _normalize_quality_summary(summary: dict[str, Any] | None) -> dict[str, int]:
    summary = summary or {}
    return {
        "total_sources": int(summary.get("total_sources", 0) or 0),
        "high": int(summary.get("high", 0) or 0),
        "medium": int(summary.get("medium", 0) or 0),
        "low": int(summary.get("low", 0) or 0),
        "rejected": int(summary.get("rejected", 0) or 0),
    }


def build_report_packet(
    state: dict[str, Any],
    summary: dict[str, Any],
    *,
    quality_summary: dict[str, Any] | None = None,
    rejected_reasons: list[str] | None = None,
) -> dict[str, Any]:
    scope = state.get("scope", "")
    scope_name = state.get("scope_name", "")
    importance = determine_report_importance(summary)
    digest_count = summary.get("digest_count", 0)
    period_start = summary.get("period_start") or today_date()
    period_end = summary.get("period_end") or today_date()
    source_urls = summary.get("source_urls", [])
    top_events = summary.get("top_events", [])
    key_takeaways = summary.get("key_takeaways", [])
    normalized_quality = _normalize_quality_summary(quality_summary or state.get("quality_summary", {}))
    rejected_reasons = list(dict.fromkeys(rejected_reasons or state.get("rejected_reasons", [])))

    if scope == "industry":
        title = f"{scope_name}三日產業研究報告"
        related_industries = [scope_name] if scope_name else []
        related_stocks = ["6230"] if "6230" in " ".join(key_takeaways + top_events) else []
        related_macro_topics: list[str] = []
    elif scope == "macro":
        title = f"{scope_name}三日大環境研究報告"
        related_industries = []
        related_stocks = []
        related_macro_topics = ["macro_environment"]
    else:
        title = f"{scope_name or '研究'}三日研究報告"
        related_industries = []
        related_stocks = []
        related_macro_topics = []

    data_warning = ""
    if digest_count < 3:
        data_warning = f"注意：最近三天僅找到 {digest_count} 份 daily_digest，資料天數不足三天，結論需保守解讀。"

    quality_text = (
        "資料品質摘要：\n"
        f"最近期間共收集 {normalized_quality['total_sources']} 筆來源，其中 "
        f"high {normalized_quality['high']} 筆、medium {normalized_quality['medium']} 筆、"
        f"low {normalized_quality['low']} 筆、rejected {normalized_quality['rejected']} 筆。"
    )
    if rejected_reasons:
        quality_text += f"主要 rejected 原因包含：{'、'.join(rejected_reasons)}。"
    if data_warning:
        quality_text += f" {data_warning}"

    executive_summary = (
        f"本報告彙整 {period_start} 至 {period_end} 的 {scope_name} 研究摘要，"
        f"共 {summary.get('event_count', 0)} 則事件，其中 critical {summary.get('critical_count', 0)} 則、"
        f"important {summary.get('important_count', 0)} 則、general {summary.get('general_count', 0)} 則。"
    )
    if data_warning:
        executive_summary += data_warning

    takeaways_text = "\n".join(f"- {item}" for item in key_takeaways) or "- 目前沒有可彙整的重點。"
    events_text = "\n".join(f"- {item}" for item in top_events) or "- 目前沒有事件標題。"
    sources_text = "\n".join(f"- {url}" for url in source_urls) or "- 無來源 URL。"

    report_body = (
        f"## 報告範圍\n"
        f"- 範圍：{scope_name}\n"
        f"- 期間：{period_start} 至 {period_end}\n"
        f"- digest 數量：{digest_count}\n\n"
        f"## 事件統計\n"
        f"- 事件總數：{summary.get('event_count', 0)}\n"
        f"- critical：{summary.get('critical_count', 0)}\n"
        f"- important：{summary.get('important_count', 0)}\n"
        f"- general：{summary.get('general_count', 0)}\n\n"
        f"## 資料品質摘要\n"
        f"- 最近期間共收集 {normalized_quality['total_sources']} 筆來源，其中 high {normalized_quality['high']} 筆、medium {normalized_quality['medium']} 筆、low {normalized_quality['low']} 筆、rejected {normalized_quality['rejected']} 筆。\n"
        + (f"- 主要 rejected 原因：{'、'.join(rejected_reasons)}。\n\n" if rejected_reasons else "\n")
        + f"## 主要事件\n{events_text}\n\n"
        + f"## 研究重點\n{takeaways_text}\n\n"
        + f"## 風險提醒\n{data_warning or '最近三天資料不足，結論需保守解讀。'}\n\n"
        + f"## 來源\n{sources_text}"
    )

    packet = {
        "packet_type": "report",
        "collector": COLLECTOR_NAME,
        "report_type": report_type_for_scope(scope),
        "title": title,
        "period_start": period_start,
        "period_end": period_end,
        "importance": importance,
        "executive_summary": executive_summary,
        "report_body": report_body,
        "related_industries": related_industries,
        "related_stocks": related_stocks,
        "related_events": top_events,
        "related_macro_topics": related_macro_topics,
        "source_count": len(source_urls),
        "created_at": now_iso(),
        "language": DEFAULT_LANGUAGE,
        "quality_summary": normalized_quality,
    }
    return packet


def validate_report_packet(packet: dict[str, Any]) -> list[str]:
    errors: list[str] = []

    if packet.get("packet_type") != "report":
        errors.append("packet_type must be report")
    if packet.get("collector") != COLLECTOR_NAME:
        errors.append("collector must be langgraph")
    if packet.get("language") != DEFAULT_LANGUAGE:
        errors.append("language must be zh-TW")
    if packet.get("report_type") not in {
        "full_report",
        "urgent_alert",
        "industry_report",
        "stock_report",
        "macro_report",
        "institution_report",
    }:
        errors.append("report_type is invalid")
    if packet.get("importance") not in VALID_IMPORTANCE:
        errors.append("importance is invalid")

    for field in ["title", "executive_summary", "report_body", "period_start", "period_end"]:
        value = packet.get(field)
        if not isinstance(value, str) or not value.strip():
            errors.append(f"{field} is required")

    source_count = packet.get("source_count")
    if not isinstance(source_count, int) or isinstance(source_count, bool) or source_count < 0:
        errors.append("source_count must be an integer >= 0")

    related_industries = packet.get("related_industries", [])
    related_stocks = packet.get("related_stocks", [])
    related_events = packet.get("related_events", [])
    related_macro_topics = packet.get("related_macro_topics", [])

    if not isinstance(related_industries, list):
        errors.append("related_industries must be a list")
        related_industries = []
    if not isinstance(related_stocks, list):
        errors.append("related_stocks must be a list")
        related_stocks = []
    if not isinstance(related_events, list):
        errors.append("related_events must be a list")
    if not isinstance(related_macro_topics, list):
        errors.append("related_macro_topics must be a list")

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

    searchable_values = [
        packet.get("title", ""),
        packet.get("executive_summary", ""),
        packet.get("report_body", ""),
        " ".join(str(item) for item in related_industries),
        " ".join(str(item) for item in related_stocks),
        " ".join(str(item) for item in related_events),
        " ".join(str(item) for item in related_macro_topics),
    ]
    combined_text = " ".join(searchable_values)
    prohibited = [term for term in PROHIBITED_TERMS if term in combined_text]
    if prohibited:
        errors.append("prohibited terms found: " + ", ".join(sorted(set(prohibited))))

    return errors


def build_report_packet_placeholder(state: dict[str, Any]) -> dict[str, Any]:
    summary = {
        "digest_count": 0,
        "period_start": today_date(),
        "period_end": today_date(),
        "event_count": 0,
        "critical_count": 0,
        "important_count": 0,
        "general_count": 0,
        "top_events": [],
        "key_takeaways": [],
        "source_urls": [],
    }
    return build_report_packet(state, summary, quality_summary={"total_sources": 0, "high": 0, "medium": 0, "low": 0, "rejected": 0}, rejected_reasons=[])

