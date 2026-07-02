from __future__ import annotations

from collections.abc import Iterable
from typing import Any

from collector.constants import PROHIBITED_TERMS
from collector.utils.text_utils import clamp_text


def clean_text(value: object) -> str:
    if value is None:
        return ""
    return " ".join(str(value).split()).strip()


def sanitize_text(value: str) -> str:
    text = clean_text(value)
    for term in PROHIBITED_TERMS:
        if term:
            text = text.replace(term, "")
    return " ".join(text.split()).strip()


def join_non_empty(parts: Iterable[str], separator: str = " ") -> str:
    return separator.join(part for part in parts if clean_text(part))


def clamp_and_sanitize(value: str, max_chars: int = 1500) -> str:
    return clamp_text(sanitize_text(value), max_chars)


def dedupe_preserve_order(values: Iterable[str]) -> list[str]:
    seen: set[str] = set()
    ordered: list[str] = []
    for value in values:
        cleaned = clean_text(value)
        if not cleaned or cleaned in seen:
            continue
        seen.add(cleaned)
        ordered.append(cleaned)
    return ordered


def extract_source_strings(sources: list[dict[str, Any]]) -> list[str]:
    parts: list[str] = []
    for source in sources:
        title = clean_text(source.get("title", ""))
        content = clean_text(source.get("content", ""))
        if title:
            parts.append(title)
        if content:
            parts.append(content)
    return parts


def build_topic_tags(state: dict, sources: list[dict[str, Any]]) -> list[str]:
    keywords = [clean_text(keyword) for keyword in state.get("search_keywords", []) if clean_text(keyword)]
    scope_name = clean_text(state.get("scope_name", ""))
    stock_name = clean_text(state.get("target_stock_name", ""))
    stock_code = clean_text(state.get("target_stock_code", ""))
    source_names = [clean_text(source.get("source_name", "")) for source in sources[:3]]

    tags = dedupe_preserve_order(
        keywords
        + [
            scope_name,
            stock_name,
            stock_code,
            *source_names,
        ]
    )

    if len(tags) < 3:
        tags.extend(fallback_tags_for_scope(state))

    return dedupe_preserve_order(tags)[:8]


def source_overview(sources: list[dict[str, Any]], max_items: int = 3) -> str:
    snippets: list[str] = []
    for source in sources[:max_items]:
        title = clean_text(source.get("title", ""))
        content = clean_text(source.get("content", ""))
        if title and content:
            snippets.append(f"{title} {content}")
        elif title:
            snippets.append(title)
        elif content:
            snippets.append(content)
    return join_non_empty(snippets, " ")


def fallback_tags_for_scope(state: dict) -> list[str]:
    scope = clean_text(state.get("scope", ""))
    if scope == "macro":
        return ["大環境", "總體經濟", "研究摘要"]
    if scope == "industry":
        return ["產業", "供應鏈", "研究摘要"]
    if scope == "stock":
        return ["個股", "公司事件", "研究摘要"]
    if scope in {"institution", "institution_watch"}:
        return ["大行關注", "法人焦點", "研究摘要"]
    return ["研究摘要", "公開資訊", "事件脈絡"]
