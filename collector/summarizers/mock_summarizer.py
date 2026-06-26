from __future__ import annotations

from typing import Any

from collector.constants import DEFAULT_LANGUAGE
from collector.summarizers.base import build_topic_tags, clamp_and_sanitize, clean_text


def summarize_with_mock(state: dict[str, Any], sources: list[dict[str, Any]]) -> dict[str, Any]:
    """Deterministic summarizer used when no LLM key is available.

    It summarizes the whole task batch, not each source independently. That keeps
    one stock with many news items as one readable research brief.
    """

    scope = clean_text(state.get("scope", ""))
    scope_name = clean_text(state.get("scope_name", "")) or scope or "研究主題"
    stock_code = clean_text(state.get("target_stock_code", ""))
    stock_name = clean_text(state.get("target_stock_name", ""))
    label = _task_label(scope, scope_name, stock_code, stock_name)

    source_count = len(sources)
    source_titles = _source_titles(sources, max_items=5)
    source_names = _source_names(sources, max_items=4)

    if source_titles:
        title_text = "；".join(source_titles)
        source_text = "、".join(source_names) if source_names else "多個來源"
        ai_summary = (
            f"{label} 本次共整理 {source_count} 則可用來源，主要訊息包含：{title_text}。"
            f"目前先將內容收斂為事件脈絡與後續觀察方向，來源包含 {source_text}。"
        )
    else:
        ai_summary = f"{label} 目前沒有足夠可用來源形成研究摘要。"

    possible_impact = _possible_impact(scope, label)
    risk_note = (
        "本摘要只整理公開資訊與事件脈絡，仍需交叉比對原始來源、公告內容與後續更新。"
        "不得把單一事件直接解讀為價格方向。"
    )

    return {
        "ai_summary": clamp_and_sanitize(ai_summary, 500),
        "possible_impact": clamp_and_sanitize(possible_impact, 500),
        "risk_note": clamp_and_sanitize(risk_note, 500),
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
        return f"{label} 相關事件可能影響市場風險偏好、資金流向與產業估值敘事，需要搭配後續總體數據觀察。"
    if scope == "industry":
        return f"{label} 相關事件可能影響產業供需、訂單能見度、供應鏈角色或客戶拉貨節奏。"
    if scope == "stock":
        return f"{label} 相關事件可能影響公司基本面研究、供應鏈定位或市場對後續營運的理解。"
    if scope in {"institution", "institution_watch"}:
        return f"{label} 相關事件可能反映法人關注方向、產業資金焦點或大型權值股敘事變化。"
    return f"{label} 相關事件可能影響後續研究判讀，仍需搭配更多資料驗證。"
