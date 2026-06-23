from __future__ import annotations

from collector.tracking_universe import TRACKING_INDUSTRIES, TRACKING_MACRO_TOPICS


def generate_search_plan(state: dict) -> dict:
    existing_keywords = [keyword for keyword in state.get("search_keywords", []) if str(keyword).strip()]
    if existing_keywords:
        state["search_keywords"] = existing_keywords
        return state

    scope = state.get("scope")
    scope_name = state.get("scope_name", "")
    stock_code = state.get("target_stock_code", "")
    stock_name = state.get("target_stock_name", "")
    macro_topic_key = state.get("macro_topic_key", "")

    if scope == "macro" and macro_topic_key:
        topic = next((item for item in TRACKING_MACRO_TOPICS if item["key"] == macro_topic_key), None)
        keywords = list(topic["keywords"]) if topic else ["聯準會", "CPI", "美元指數", "利率", "yield"]
    elif scope == "macro":
        keywords = ["聯準會", "CPI", "PPI", "美元指數", "利率", "yield", "外資", "台股"]
    elif scope == "industry":
        industry = next((item for item in TRACKING_INDUSTRIES if item["name"] == scope_name), None)
        if industry:
            keywords = list(industry["search_keywords"])
            if industry["sample_stock_code"]:
                keywords.extend([industry["sample_stock_code"], industry["sample_stock_name"]])
        else:
            keywords = [scope_name, stock_code, stock_name]
            if scope_name == "散熱" or stock_code == "6230":
                keywords.extend(["AI 伺服器", "液冷", "熱管理"])
    else:
        keywords = [scope_name, stock_code, stock_name]

    state["search_keywords"] = [keyword for keyword in keywords if keyword]
    return state
