from __future__ import annotations

from typing import Any

from collector.constants import DEFAULT_LANGUAGE
from collector.summarizers.base import build_topic_tags, clamp_and_sanitize, clean_text, source_overview


def summarize_with_mock(state: dict[str, Any], sources: list[dict[str, Any]]) -> dict[str, Any]:
    scope = clean_text(state.get("scope", ""))
    scope_name = clean_text(state.get("scope_name", "")) or scope or "研究"
    stock_code = clean_text(state.get("target_stock_code", ""))
    stock_name = clean_text(state.get("target_stock_name", ""))

    overview = source_overview(sources, max_items=3)
    if not overview:
        overview = f"{scope_name} 目前沒有可用來源，先以結構化占位摘要維持流程可跑。"

    if scope == "macro":
        possible_impact = "此則總體訊息可能影響風險偏好、利率預期、美元與資金流向，但仍需搭配後續資料確認。"
        risk_note = "總體環境變化常伴隨延遲反應與多重因素交錯，不能直接推論成單一方向。"
    elif scope == "industry":
        if stock_code or stock_name:
            possible_impact = f"此產業訊息可能影響 {stock_code or stock_name} 所在供應鏈與市場關注度。"
        else:
            possible_impact = f"此產業訊息可能影響 {scope_name} 的供應鏈節奏與後續研究重點。"
        risk_note = "產業訊息通常需要再對照公司公告、供應鏈驗證與後續事件，避免過早下結論。"
    elif scope == "stock":
        possible_impact = "這則個股事件可能影響市場對該公司營運節奏與研究焦點的重新評估。"
        risk_note = "個股事件容易與產業敘事混在一起，仍需觀察是否有更完整的公司層級證據。"
    else:
        possible_impact = "這則訊息可能影響後續研究安排與資訊追蹤優先順序。"
        risk_note = "資訊仍可能缺少上下文，適合先觀察再補充驗證。"

    ai_summary = clamp_and_sanitize(
        f"{scope_name} 研究摘要：{overview}。"
        " 本次內容先整理為事件脈絡、可能影響與後續追蹤方向，"
        "不直接做投資建議或價格推論。",
        500,
    )

    return {
        "ai_summary": ai_summary,
        "possible_impact": clamp_and_sanitize(possible_impact, 500),
        "risk_note": clamp_and_sanitize(risk_note, 500),
        "tags": build_topic_tags(state, sources),
        "language": DEFAULT_LANGUAGE,
    }
