from __future__ import annotations

from typing import Any

from collector.constants import DEFAULT_LANGUAGE, EVENT_AI_SUMMARY_MAX_CHARS
from collector.summarizers.base import build_topic_tags, clamp_and_sanitize, clean_text


def summarize_with_mock(state: dict[str, Any], sources: list[dict[str, Any]]) -> dict[str, Any]:
    """Deterministic summarizer used when no LLM key is available.

    The mock path summarizes the whole batch into one concise research brief so
    a stock with many news items still renders as a single readable summary.
    """

    scope = clean_text(state.get("scope", ""))
    scope_name = clean_text(state.get("scope_name", "")) or scope or "未命名主題"
    stock_code = clean_text(state.get("target_stock_code", ""))
    stock_name = clean_text(state.get("target_stock_name", ""))
    label = _task_label(scope, scope_name, stock_code, stock_name)

    source_count = len(sources)
    source_titles = _source_titles(sources, max_items=5)
    source_names = _source_names(sources, max_items=4)

    if source_titles:
        title_text = "、".join(source_titles)
        source_text = "、".join(source_names) if source_names else "未標示來源"
        ai_summary = (
            f"{label} 本次共整理 {source_count} 則來源，主要關注的新聞標題包括：{title_text}。"
            f"整體來看，這批資料已彙整為單一研究簡報，重點放在事件脈絡、產業影響與後續追蹤方向，"
            f"並統整自 {source_text} 等來源。"
        )
    else:
        ai_summary = f"{label} 暫時沒有可用來源，先保留為待補充的研究筆記。"

    possible_impact = _possible_impact(scope, label)
    risk_note = (
        "資料來源之間可能存在重複報導或角度差異，仍需搭配後續事件脈絡與公司／產業背景一起判讀。"
        "本摘要僅整理研究訊號，不直接代表價格預測或買賣建議。"
    )

    return {
        "ai_summary": clamp_and_sanitize(ai_summary, EVENT_AI_SUMMARY_MAX_CHARS),
        "possible_impact": clamp_and_sanitize(possible_impact, EVENT_AI_SUMMARY_MAX_CHARS),
        "risk_note": clamp_and_sanitize(risk_note, EVENT_AI_SUMMARY_MAX_CHARS),
        "tags": build_topic_tags(state, sources),
        "language": DEFAULT_LANGUAGE,
    }


def _task_label(scope: str, scope_name: str, stock_code: str, stock_name: str) -> str:
    if scope == "stock" and stock_code:
        return f"{stock_code} {stock_name or scope_name}".strip()
    if scope in {"institution", "institution_watch"} and stock_code:
        return f"大行關注 {stock_code} {stock_name or scope_name}".strip()
    return scope_name


def _source_titles(sources: list[dict[str, Any]], *, max_items: int) -> list[str]:
    titles: list[str] = []
    seen: set[str] = set()
    for source in sources:
        title = clean_text(source.get("title", ""))
        if not title or title in seen:
            continue
        seen.add(title)
        titles.append(title)
        if len(titles) >= max_items:
            break
    return titles


def _source_names(sources: list[dict[str, Any]], *, max_items: int) -> list[str]:
    names: list[str] = []
    seen: set[str] = set()
    for source in sources:
        name = clean_text(source.get("source_name", ""))
        if not name or name in seen:
            continue
        seen.add(name)
        names.append(name)
        if len(names) >= max_items:
            break
    return names


def _possible_impact(scope: str, label: str) -> str:
    if scope == "macro":
        return f"{label} 可能影響整體風險偏好、資金流向與市場對政策路徑的預期。"
    if scope == "industry":
        return f"{label} 可能反映產業景氣、供應鏈進度與同族群後續評價方向。"
    if scope == "stock":
        return f"{label} 可能影響單一公司營運預期、投資人對事件落地節奏的判斷，以及後續觀察重點。"
    if scope in {"institution", "institution_watch"}:
        return f"{label} 可能影響法人資金配置、研究覆蓋與市場對相關族群的關注度。"
    return f"{label} 可能帶來短線研究訊號，後續仍需搭配更多資料驗證。"
