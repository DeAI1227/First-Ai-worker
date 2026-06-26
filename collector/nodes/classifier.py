from __future__ import annotations

from collector.config.tracking_universe import TRACKING_MACRO_TOPICS


def classify_event(state: dict) -> dict:
    scope = state.get("scope")
    scope_name = state.get("scope_name", "")
    stock_code = state.get("target_stock_code", "")

    if scope == "macro":
        state["event_type"] = "macro"
        state["importance"] = _importance_from_sources(state)
        state.setdefault("possible_impact", "大環境事件可能影響市場風險偏好、資金流向與產業評價。")
        state.setdefault("risk_note", "總體事件解讀具有時效性，仍需搭配後續數據與政策訊號。")
        state["related_industries"] = []
        state["related_stocks"] = []
        state["related_macro_topics"] = [item["key"] for item in TRACKING_MACRO_TOPICS if item.get("enabled", True)]
        state["related_institution_watch"] = []
        state.setdefault("tags", ["大環境", "總體經濟", "資金流向"])
    elif scope == "industry":
        state["event_type"] = "industry"
        state["importance"] = _importance_from_sources(state)
        state.setdefault("possible_impact", f"{scope_name} 事件可能影響產業供需、供應鏈角色或客戶需求節奏。")
        state.setdefault("risk_note", "產業事件需交叉比對多個來源，避免用單一消息過度延伸。")
        state["related_industries"] = [scope_name] if scope_name else []
        state["related_stocks"] = [stock_code] if stock_code else []
        state["related_macro_topics"] = []
        state["related_institution_watch"] = []
        state.setdefault("tags", [scope_name, "產業事件", "供應鏈"])
    elif scope in {"institution", "institution_watch"}:
        state["event_type"] = "institution"
        state["importance"] = _importance_from_sources(state)
        state.setdefault("possible_impact", "大行關注事件可能反映法人研究焦點、資金敘事或權值股關注方向。")
        state.setdefault("risk_note", "法人關注不等於價格方向，仍需回到事件脈絡與基本面資料。")
        state["related_industries"] = []
        state["related_stocks"] = [stock_code] if stock_code else []
        state["related_macro_topics"] = []
        state["related_institution_watch"] = [stock_code] if stock_code else []
        state.setdefault("tags", ["大行關注", "法人焦點", "研究事件"])
    else:
        state["event_type"] = "stock" if scope == "stock" else "general"
        state["importance"] = _importance_from_sources(state)
        state.setdefault("possible_impact", "相關事件可能影響公司或產業研究判讀，仍需搭配後續資訊驗證。")
        state.setdefault("risk_note", "單一事件不宜過度延伸，需持續追蹤公開資訊與後續更新。")
        state["related_industries"] = list(state.get("industries", []))
        state["related_stocks"] = [stock_code] if stock_code else []
        state["related_macro_topics"] = []
        state["related_institution_watch"] = []
        state.setdefault("tags", [])

    return state


def _importance_from_sources(state: dict) -> str:
    sources = state.get("filtered_sources", [])
    text = " ".join(
        f"{source.get('title', '')} {source.get('content', '')}"
        for source in sources
    )
    critical_terms = ["重大訊息", "法說", "併購", "停工", "裁罰", "財測", "營收"]
    important_terms = ["公告", "訂單", "供應鏈", "AI", "資料中心", "液冷", "CPI", "FED", "外資"]
    if any(term in text for term in critical_terms):
        return "critical"
    if any(term in text for term in important_terms):
        return "important"
    return "general"
