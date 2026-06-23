from __future__ import annotations

from collector.config.tracking_universe import TRACKING_MACRO_TOPICS


def classify_event(state: dict) -> dict:
    scope = state.get("scope")
    scope_name = state.get("scope_name", "")
    stock_code = state.get("target_stock_code", "")

    if scope == "macro":
        state["event_type"] = "macro"
        state["importance"] = "general"
        state["possible_impact"] = "宏觀政策與經濟數據可能影響市場風險偏好與資金配置。"
        state["risk_note"] = "宏觀事件通常具有時效性與解讀差異，仍需持續觀察後續數據與政策表態。"
        state["related_industries"] = []
        state["related_stocks"] = []
        state["related_macro_topics"] = [item["key"] for item in TRACKING_MACRO_TOPICS if item.get("enabled", True)]
        state["related_institution_watch"] = []
        state["tags"] = ["宏觀", "CPI", "利率"]
    elif scope == "industry" and scope_name == "散熱":
        state["event_type"] = "industry"
        state["importance"] = "important"
        state["possible_impact"] = "散熱產業動態可能影響 AI 伺服器與資料中心供應鏈評價與需求預期。"
        state["risk_note"] = "產業消息常受單一事件驅動，仍需交叉比對供應鏈與需求面訊號。"
        state["related_industries"] = ["散熱"]
        state["related_stocks"] = [stock_code] if stock_code else []
        state["related_macro_topics"] = []
        state["related_institution_watch"] = []
        state["tags"] = ["AI伺服器", "液冷", "散熱"]
    elif scope in {"institution", "institution_watch"}:
        state["event_type"] = "institution"
        state["importance"] = "general"
        state["possible_impact"] = "大行關注事件可能反映法人調整持股與資金流向的變化。"
        state["risk_note"] = "法人動向不等於價格趨勢，仍需搭配事件脈絡與基本面觀察。"
        state["related_industries"] = []
        state["related_stocks"] = [stock_code] if stock_code else []
        state["related_macro_topics"] = []
        state["related_institution_watch"] = [stock_code] if stock_code else []
        state["tags"] = ["大行關注", "法人", "資金流向"]
    else:
        state["event_type"] = "industry" if scope == "industry" else "stock" if scope == "stock" else "general"
        state["importance"] = "general"
        state["possible_impact"] = "相關事件可能影響研究判讀，但仍需結合產業與公司脈絡理解。"
        state["risk_note"] = "單一事件不宜過度延伸，仍需等待更多資訊驗證。"
        state["related_industries"] = [scope_name] if scope == "industry" and scope_name else []
        state["related_stocks"] = [stock_code] if stock_code else []
        state["related_macro_topics"] = []
        state["related_institution_watch"] = []
        state["tags"] = []

    return state
