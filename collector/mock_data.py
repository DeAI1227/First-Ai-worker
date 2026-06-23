from __future__ import annotations

from typing import Any

from collector.constants import VALID_MVP_STOCKS
from collector.tracking_universe import TRACKING_INDUSTRIES, TRACKING_INSTITUTION_WATCH
from collector.utils.time_utils import now_iso


def _source(title: str, source_name: str, source_url: str, content: str) -> dict[str, Any]:
    return {
        "title": title,
        "source_name": source_name,
        "source_url": source_url,
        "published_at": now_iso(),
        "content": content,
        "source_type": "mock",
    }


def _find_industry(scope_name: str) -> dict[str, Any] | None:
    return next((item for item in TRACKING_INDUSTRIES if item["name"] == scope_name), None)


def _find_stock(code: str) -> tuple[dict[str, Any] | None, dict[str, Any] | None]:
    for industry in TRACKING_INDUSTRIES:
        for stock in industry["stocks"]:
            if stock["code"] == code:
                return industry, stock
    return None, None


def _find_institution_watch(code: str) -> dict[str, Any] | None:
    return next((item for item in TRACKING_INSTITUTION_WATCH if item["code"] == code), None)


def get_mock_sources(
    task_or_scope: dict[str, Any] | str,
    scope_name: str | None = None,
    stock_code: str = "",
    stock_name: str = "",
    search_keywords: list[str] | None = None,
) -> list[dict[str, Any]]:
    if isinstance(task_or_scope, dict):
        task = task_or_scope
        scope = str(task.get("scope", "") or "")
        scope_name = str(task.get("scope_name", "") or "")
        stock_code = str(task.get("target_stock_code", "") or "")
        stock_name = str(task.get("target_stock_name", "") or "")
        search_keywords = list(task.get("search_keywords", []) or [])
    else:
        scope = task_or_scope
        scope_name = scope_name or ""
        search_keywords = search_keywords or []

    if scope == "macro":
        return [
            _source(
                "聯準會政策帶動美債與美元波動",
                "Mock Macro Brief",
                "https://example.com/mock/macro/fed-policy",
                "聯準會利率政策、CPI、PPI 與就業數據交互影響美元指數與美債殖利率，市場仍關注 AI 資本支出與資料中心需求。",
            ),
            _source(
                "美元指數與殖利率變化牽動風險資產",
                "Mock Macro Brief",
                "https://example.com/mock/macro/usd-yield-flows",
                "美元指數與十年期美債殖利率變化影響外資流向與台股評價，需同步觀察 Fed 與通膨數據。",
            ),
        ]

    if scope == "industry":
        industry = _find_industry(scope_name or "")
        if industry:
            sample_code = industry["sample_stock_code"]
            sample_name = industry["sample_stock_name"]
            return [
                _source(
                    f"{industry['name']}追蹤：{sample_name or sample_code} 的研究訊號",
                    f"Mock {industry['name']} Brief",
                    f"https://example.com/mock/industry/{industry['key']}",
                    f"{industry['name']}產業出現 AI 伺服器與供應鏈關聯訊號，市場持續追蹤 {sample_name or sample_code} 的相關動態與海外龍頭指引。",
                )
            ]
        if stock_code == "6230" or scope_name == "散熱":
            return [
                _source(
                    "散熱產業追蹤：AI 伺服器與液冷需求升溫",
                    "Mock Industry Brief",
                    "https://example.com/mock/thermal-ai-server-liquid-cooling",
                    "AI 伺服器需求推動散熱與液冷供應鏈持續升溫，市場持續關注 6230 尼得科超眾與整體散熱族群。",
                )
            ]
        return [
            _source(
                f"{scope_name or '產業'}研究速報",
                "Mock Industry Brief",
                f"https://example.com/mock/industry/{scope_name or 'unknown'}",
                f"{scope_name or '產業'}供應鏈與產品結構變化仍是市場主要觀察重點，相關企業後續動能需持續追蹤。",
            )
        ]

    if scope == "stock":
        industry, stock = _find_stock(stock_code)
        if stock:
            if stock_code not in VALID_MVP_STOCKS:
                return []
            if stock_code != "6230":
                return []
            related_industry = industry["name"] if industry else scope_name
            return [
                _source(
                    f"{stock['name']}（{stock['code']}）研究快訊",
                    "Mock Stock Brief",
                    f"https://example.com/mock/stock/{stock['code']}",
                    f"{stock['name']}（{stock['code']}）與 {related_industry} 供應鏈動態相關，市場持續關注基本面事件與研究報告摘要。",
                )
            ]
        return [
            _source(
                f"{stock_name or stock_code or scope_name} 研究快訊",
                "Mock Stock Brief",
                f"https://example.com/mock/stock/{stock_code or scope_name or 'unknown'}",
                f"{stock_name or stock_code or scope_name} 目前尚未對應到明確事件，但仍保留作為追蹤標的的研究快訊占位。",
            )
        ]

    if scope in {"institution", "institution_watch"}:
        watch = _find_institution_watch(stock_code)
        if watch:
            return [
                _source(
                    f"{watch['name']}（{watch['code']}）大行關注快訊",
                    "Mock Institution Brief",
                    f"https://example.com/mock/institution/{watch['code']}",
                    f"{watch['name']}（{watch['code']}）持續受到法人與大行關注，研究端可追蹤籌碼與事件脈絡。",
                )
            ]
        return [
            _source(
                f"{stock_name or stock_code or '大行關注'} 研究快訊",
                "Mock Institution Brief",
                f"https://example.com/mock/institution/{stock_code or 'unknown'}",
                f"{stock_name or stock_code or '大行關注'} 目前僅作為追蹤清單占位，後續會以真實來源補足研究事件。",
            )
        ]

    if search_keywords:
        joined = "、".join(search_keywords[:3])
        return [
            _source(
                f"{scope_name or scope or '研究'}搜尋快訊：{joined}",
                "Mock Search Brief",
                f"https://example.com/mock/search/{scope_name or scope or 'unknown'}",
                f"目前以 {joined} 作為關鍵字模擬研究搜尋，後續可替換成 RSS、HTTP 或 Search API 的真實來源。",
            )
        ]

    return []
