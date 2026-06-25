from __future__ import annotations

from collections.abc import Iterable
from typing import Any
from collector.quality.rules import (
    HIGH_LEVEL_MIN,
    LOW_LEVEL_MIN,
    MEDIUM_LEVEL_MIN,
    OFFICIAL_SOURCE_TERMS,
    RESEARCH_TERMS,
    is_quote_style_bulletin,
    is_prohibited_text,
    is_suspicious_signal,
)
from collector.sources.base import clean_text


def score_sources(raw_sources: list[dict[str, Any]], task: dict[str, Any], state: dict[str, Any] | None = None) -> list[dict[str, Any]]:
    state = state or {}
    seen_urls: set[str] = set()
    scored: list[dict[str, Any]] = []

    keywords = _build_keywords(task, state)
    stock_hints = _build_stock_hints(task, state)

    for source in raw_sources:
        scored.append(
            _score_single_source(
                source,
                keywords=keywords,
                stock_hints=stock_hints,
                seen_urls=seen_urls,
            )
        )

    return scored


def summarize_quality(scored_sources: list[dict[str, Any]]) -> dict[str, int]:
    summary = {
        "total_sources": len(scored_sources),
        "high": 0,
        "medium": 0,
        "low": 0,
        "rejected": 0,
    }
    for source in scored_sources:
        level = clean_text(source.get("quality_level", "rejected")).lower() or "rejected"
        if level not in summary:
            level = "rejected"
        summary[level] += 1
    return summary


def _score_single_source(
    source: dict[str, Any],
    *,
    keywords: list[str],
    stock_hints: list[str],
    seen_urls: set[str],
) -> dict[str, Any]:
    normalized = dict(source)
    title = clean_text(normalized.get("title", ""))
    source_url = clean_text(normalized.get("source_url", ""))
    content = clean_text(normalized.get("content", ""))
    published_at = clean_text(normalized.get("published_at", ""))
    source_name = clean_text(normalized.get("source_name", ""))
    source_type = clean_text(normalized.get("source_type", "")).lower()
    combined_text = f"{title} {content} {source_name}"

    reasons: list[str] = []
    score = 0
    rejected = False

    if not source_url:
        reasons.append("missing source_url")
        rejected = True
    elif source_url in seen_urls:
        reasons.append("duplicate source_url")
        rejected = True
    else:
        seen_urls.add(source_url)

    if not title:
        reasons.append("missing title")
        score -= 20
    else:
        score += 10

    if source_url:
        score += 15

    if content:
        score += 15
    else:
        reasons.append("missing content")

    if len(content) < 50:
        reasons.append("content too short")
        score -= 20

    if published_at:
        score += 10

    if source_type in {"rss", "http", "search"}:
        score += 5

    if _is_official_source(source_name, source_url, source_type):
        score += 5

    if _contains_any(combined_text, keywords):
        score += 10
        reasons.append("matches topic keywords")

    if _contains_any(combined_text, stock_hints):
        score += 10
        reasons.append("matches stock/company hints")

    if _contains_any(combined_text, RESEARCH_TERMS):
        score += 10
        reasons.append("contains research terms")

    prohibited = is_prohibited_text(combined_text)
    if prohibited:
        reasons.append("contains prohibited terms: " + ", ".join(sorted(set(prohibited))))
        rejected = True

    if is_suspicious_signal(combined_text):
        reasons.append("suspicious buy/sell or price-target style content")
        rejected = True

    if is_quote_style_bulletin(combined_text):
        reasons.append("contains stock price bulletin / quote-style content")
        rejected = True

    if not source_name:
        reasons.append("missing source_name")
        score -= 10

    if not source_url:
        rejected = True

    if rejected:
        score = min(score, 19)
        score = max(score, 0)
    else:
        score = max(0, min(score, 100))

    quality_level = _quality_level(score, rejected=rejected)

    normalized["title"] = title
    normalized["source_url"] = source_url
    normalized["content"] = content
    normalized["published_at"] = published_at
    normalized["source_name"] = source_name
    normalized["source_type"] = source_type or "mock"
    normalized["quality_score"] = score
    normalized["quality_level"] = quality_level
    normalized["quality_reasons"] = reasons
    return normalized


def _quality_level(score: int, rejected: bool = False) -> str:
    if rejected or score < LOW_LEVEL_MIN:
        return "rejected"
    if score >= HIGH_LEVEL_MIN:
        return "high"
    if score >= MEDIUM_LEVEL_MIN:
        return "medium"
    return "low"


def _build_keywords(task: dict[str, Any], state: dict[str, Any]) -> list[str]:
    raw_keywords = list(task.get("search_keywords", [])) + list(state.get("search_keywords", []))
    raw_keywords.extend([task.get("scope_name", ""), task.get("scope", "")])
    return _unique_clean(raw_keywords)


def _build_stock_hints(task: dict[str, Any], state: dict[str, Any]) -> list[str]:
    hints = [
        task.get("target_stock_code", ""),
        task.get("target_stock_name", ""),
        state.get("target_stock_code", ""),
        state.get("target_stock_name", ""),
    ]
    return _unique_clean(hints)


def _is_official_source(source_name: str, source_url: str, source_type: str) -> bool:
    if source_type == "rss":
        return True
    text = f"{source_name} {source_url}".lower()
    return any(term in text for term in OFFICIAL_SOURCE_TERMS)


def _contains_any(text: str, terms: Iterable[str]) -> bool:
    lowered = text.lower()
    for term in terms:
        cleaned = clean_text(term)
        if cleaned and cleaned.lower() in lowered:
            return True
    return False


def _unique_clean(values: Iterable[Any]) -> list[str]:
    cleaned: list[str] = []
    seen: set[str] = set()
    for value in values:
        text = clean_text(value)
        if not text or text in seen:
            continue
        seen.add(text)
        cleaned.append(text)
    return cleaned


def score_level_counts(scored_sources: list[dict[str, Any]]) -> dict[str, int]:
    return summarize_quality(scored_sources)
