from __future__ import annotations

import json
import re
from typing import Any

from collector.constants import DEFAULT_LANGUAGE
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
from collector.summarizers.providers import GeminiProvider, OpenAIProvider

LLM_SUMMARIZATION_PROMPT = """你是 AI 投資研究終端的摘要器。
請根據 raw_sources 產出適合研究終端使用的結構化 JSON。

輸出規則：
1. 只能輸出 JSON，不能加 markdown、解釋文字或前言。
2. 必須包含欄位：ai_summary、possible_impact、risk_note、tags。
3. ai_summary 必須是繁體中文，且不超過 500 字。
4. possible_impact 只能描述可能影響，不要寫買賣建議。
5. risk_note 需保留不確定性與風險。
6. tags 建議 3 到 8 個，使用研究主題關鍵詞。
7. 禁止出現以下詞彙：
   買進、賣出、目標價、報酬率、喊單、飆股、漲停、買賣建議、投資建議、技術分析、K線、成交量、買賣訊號
8. 若資訊不足，請如實說明，不要補造結論。
"""

SUPPORTED_LLM_PROVIDERS = {"auto", "openai", "gemini", "mock"}


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
        f"任務背景:\n"
        f"- scope: {scope}\n"
        f"- scope_name: {scope_name}\n"
        f"- target_stock_code: {stock_code}\n"
        f"- target_stock_name: {stock_name}\n"
        f"- search_keywords: {keywords}\n\n"
        f"來源總覽:\n{overview}\n\n"
        f"raw_sources 前五筆:\n{source_lines or '(無)'}\n"
    )


def _build_provider(provider_name: str):
    if provider_name == "openai":
        return OpenAIProvider()
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
        if OpenAIProvider().is_available():
            return "openai"
        if GeminiProvider().is_available():
            return "gemini"
        return "mock"
    if requested_provider == "openai":
        return "openai" if OpenAIProvider().is_available() else "mock"
    if requested_provider == "gemini":
        return "gemini" if GeminiProvider().is_available() else "mock"
    return "mock"


def _fallback_reason(requested_provider: str) -> str:
    if requested_provider == "auto":
        return "LLM summarizer requested but no API key found; fallback to mock summarizer."
    if requested_provider == "openai":
        return "OPENAI_API_KEY is missing; fallback to mock summarizer."
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

    ai_summary = clamp_and_sanitize(_as_text(payload.get("ai_summary", "")) or mock_result["ai_summary"], 500)
    possible_impact = clamp_and_sanitize(
        _as_text(payload.get("possible_impact", "")) or mock_result["possible_impact"],
        500,
    )
    risk_note = clamp_and_sanitize(_as_text(payload.get("risk_note", "")) or mock_result["risk_note"], 500)

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
        tags = [sanitize_text(clean_text(item)) for item in re.split(r"[,\n、/|]+", value) if sanitize_text(clean_text(item))]
    else:
        tags = []
    return dedupe_preserve_order(tags)


def _as_text(value: Any) -> str:
    if value is None:
        return ""
    if isinstance(value, str):
        return value
    return json.dumps(value, ensure_ascii=False)
