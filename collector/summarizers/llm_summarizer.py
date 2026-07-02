from __future__ import annotations

import json
import re
from typing import Any

from collector.constants import DEFAULT_LANGUAGE, EVENT_AI_SUMMARY_MAX_CHARS
from collector.summarizers.base import (
    build_topic_tags,
    clamp_and_sanitize,
    clean_text,
    dedupe_preserve_order,
    fallback_tags_for_scope,
    sanitize_text,
    source_overview,
)
from collector.summarizers.mock_summarizer import summarize_with_mock
from collector.summarizers.providers import AgnesProvider, GeminiProvider

LLM_SUMMARIZATION_PROMPT = """你是一個投資研究摘要助手（AI summary assistant）。
你的任務是根據 raw_sources 整理成一份整合後的研究摘要，而不是逐篇重寫。

請只輸出 JSON，且欄位必須只有：
- ai_summary
- possible_impact
- risk_note
- tags

規則：
1. 不要輸出 markdown 或額外說明。
2. ai_summary 必須在 1500 字以內。
3. ai_summary 需整合多篇來源，形成單一研究簡報。
4. possible_impact 只描述可能影響，不要做買賣建議。
5. risk_note 必須保留不確定性與限制。
6. tags 請提供 3 到 8 個關鍵詞。
7. 內容要用繁體中文，語氣客觀、精簡、可直接放進研究終端。
"""

SUPPORTED_LLM_PROVIDERS = {"auto", "agnes", "gemini", "mock"}


def summarize_with_llm(
    state: dict[str, Any],
    sources: list[dict[str, Any]],
    provider: str | None = None,
) -> dict[str, Any]:
    requested_provider = _normalize_provider_name(provider or state.get("llm_provider") or "auto")
    selected_provider = _select_provider(requested_provider)
    prompt = build_llm_prompt(state, sources)

    if selected_provider == "mock":
        fallback_reason = _fallback_reason(requested_provider)
        if fallback_reason:
            state.setdefault("run_errors", []).append(fallback_reason)
        return summarize_with_mock(state, sources)

    provider_impl = _build_provider(selected_provider)
    try:
        raw_text = provider_impl.summarize(prompt, state, sources)
        payload = _parse_llm_payload(raw_text)
        return _normalize_summary_payload(payload, state, sources)
    except Exception as exc:
        state.setdefault("run_errors", []).append(
            f"LLM provider {selected_provider} failed; fallback to mock summarizer. Reason: {exc}"
        )
        return summarize_with_mock(state, sources)


def build_llm_prompt(state: dict[str, Any], sources: list[dict[str, Any]]) -> str:
    scope = clean_text(state.get("scope", ""))
    scope_name = clean_text(state.get("scope_name", ""))
    stock_code = clean_text(state.get("target_stock_code", ""))
    stock_name = clean_text(state.get("target_stock_name", ""))
    keywords = ", ".join(clean_text(keyword) for keyword in state.get("search_keywords", []) if clean_text(keyword))
    overview = source_overview(sources, max_items=5)
    source_lines = "\n".join(
        f"{index + 1}. {clean_text(item.get('title', ''))} | {clean_text(item.get('source_name', ''))} | {clean_text(item.get('content', ''))}"
        for index, item in enumerate(sources[:5])
    )

    return (
        f"{LLM_SUMMARIZATION_PROMPT}\n\n"
        f"任務上下文:\n"
        f"- scope: {scope}\n"
        f"- scope_name: {scope_name}\n"
        f"- target_stock_code: {stock_code}\n"
        f"- target_stock_name: {stock_name}\n"
        f"- search_keywords: {keywords}\n\n"
        f"來源摘要:\n{overview}\n\n"
        f"raw_sources 預覽:\n{source_lines or '(none)'}\n"
    )


def _build_provider(provider_name: str):
    if provider_name == "agnes":
        return AgnesProvider()
    if provider_name == "gemini":
        return GeminiProvider()
    return None


def _normalize_provider_name(provider: str) -> str:
    candidate = clean_text(provider).lower() or "auto"
    if candidate not in SUPPORTED_LLM_PROVIDERS:
        return "auto"
    return candidate


def _select_provider(requested_provider: str) -> str:
    if requested_provider == "mock":
        return "mock"
    if requested_provider == "auto":
        if AgnesProvider().is_available():
            return "agnes"
        if GeminiProvider().is_available():
            return "gemini"
        return "mock"
    if requested_provider == "agnes":
        return "agnes" if AgnesProvider().is_available() else "mock"
    if requested_provider == "gemini":
        return "gemini" if GeminiProvider().is_available() else "mock"
    return "mock"


def _fallback_reason(requested_provider: str) -> str:
    if requested_provider == "auto":
        return "LLM summarizer requested but no API key found; fallback to mock summarizer."
    if requested_provider == "agnes":
        return "AGNES_API_KEY or AGNES_API_URL/AGNES_BASE_URL is missing; fallback to mock summarizer."
    if requested_provider == "gemini":
        return "GEMINI_API_KEY is missing; fallback to mock summarizer."
    return ""


def _parse_llm_payload(raw_text: str) -> dict[str, Any]:
    text = clean_text(raw_text)
    if not text:
        raise ValueError("LLM response is empty")

    text = _strip_code_fences(text)

    candidates = [text]
    brace_candidates = re.findall(r"\{.*?\}", text, flags=re.DOTALL)
    candidates.extend(brace_candidates)

    for candidate in candidates:
        try:
            payload = json.loads(candidate)
        except json.JSONDecodeError:
            continue
        if isinstance(payload, dict):
            return payload

    raise ValueError("LLM response is not valid JSON")


def _strip_code_fences(text: str) -> str:
    stripped = text.strip()
    if stripped.startswith("```"):
        stripped = re.sub(r"^```(?:json)?\s*", "", stripped, flags=re.IGNORECASE)
        stripped = re.sub(r"\s*```$", "", stripped)
    return stripped.strip()


def _normalize_summary_payload(
    payload: dict[str, Any],
    state: dict[str, Any],
    sources: list[dict[str, Any]],
) -> dict[str, Any]:
    mock_result = summarize_with_mock(state, sources)

    ai_summary = clamp_and_sanitize(
        _as_text(payload.get("ai_summary", "")) or mock_result["ai_summary"],
        EVENT_AI_SUMMARY_MAX_CHARS,
    )
    possible_impact = clamp_and_sanitize(
        _as_text(payload.get("possible_impact", "")) or mock_result["possible_impact"],
        EVENT_AI_SUMMARY_MAX_CHARS,
    )
    risk_note = clamp_and_sanitize(
        _as_text(payload.get("risk_note", "")) or mock_result["risk_note"],
        EVENT_AI_SUMMARY_MAX_CHARS,
    )

    tags = _normalize_tags(payload.get("tags"))
    if len(tags) < 3:
        tags = dedupe_preserve_order(tags + build_topic_tags(state, sources) + fallback_tags_for_scope(state))
    if len(tags) < 3:
        tags = mock_result["tags"]
    tags = tags[:8]

    if not ai_summary:
        ai_summary = mock_result["ai_summary"]
    if not possible_impact:
        possible_impact = mock_result["possible_impact"]
    if not risk_note:
        risk_note = mock_result["risk_note"]

    return {
        "ai_summary": ai_summary,
        "possible_impact": possible_impact,
        "risk_note": risk_note,
        "tags": tags,
        "language": DEFAULT_LANGUAGE,
    }


def _normalize_tags(value: Any) -> list[str]:
    if isinstance(value, list):
        tags = [sanitize_text(clean_text(item)) for item in value if sanitize_text(clean_text(item))]
    elif isinstance(value, str):
        parts = re.split(r"[,\n|;，。]+", value)
        tags = [sanitize_text(clean_text(item)) for item in parts if sanitize_text(clean_text(item))]
    else:
        tags = []
    return dedupe_preserve_order(tags)


def _as_text(value: Any) -> str:
    if value is None:
        return ""
    if isinstance(value, str):
        return value
    return json.dumps(value, ensure_ascii=False)
