from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from collector.constants import VALID_MVP_STOCKS
from collector.sources.base import clean_text, normalize_source_item
from collector.sources.search.base_provider import BaseSearchProvider


class MockSearchProvider(BaseSearchProvider):
    provider_name = "mock"

    def search(self, task: dict[str, Any], keywords: list[str], state: dict[str, Any] | None = None) -> list[dict[str, Any]]:
        scope = clean_text(task.get("scope", ""))
        scope_name = clean_text(task.get("scope_name", ""))
        stock_code = clean_text(task.get("target_stock_code", ""))
        stock_name = clean_text(task.get("target_stock_name", ""))
        primary_keyword = keywords[0] if keywords else scope_name or scope or "research"
        secondary_keyword = keywords[1] if len(keywords) > 1 else stock_name or stock_code or scope_name or scope

        if scope == "stock" and stock_code not in VALID_MVP_STOCKS:
            return []

        if scope == "macro":
            items = [
                {
                    "title": f"{primary_keyword} 牽動全球風險偏好",
                    "source_name": "Mock Search Macro",
                    "source_url": "https://example.com/search/mock/macro-fed-cpi",
                    "published_at": _now_iso(),
                    "content": "聯準會、CPI、美元指數與十年期美債殖利率仍是市場觀察焦點。",
                    "source_type": "search",
                },
                {
                    "title": "美國通膨與利率預期持續變化",
                    "source_name": "Mock Search Macro",
                    "source_url": "https://example.com/search/mock/macro-dxy-yield",
                    "published_at": _now_iso(),
                    "content": "通膨與利率預期可能影響資金流向與風險資產評價。",
                    "source_type": "search",
                },
            ]
        else:
            items = [
                {
                    "title": f"{scope_name or secondary_keyword} 出現 AI 伺服器散熱研究訊號",
                    "source_name": "Mock Search Industry",
                    "source_url": "https://example.com/search/mock/thermal-ai-server-liquid-cooling",
                    "published_at": _now_iso(),
                    "content": "AI 伺服器、液冷與供應鏈驗證仍是產業追蹤主軸。",
                    "source_type": "search",
                },
                {
                    "title": f"{stock_code or secondary_keyword} 相關供應鏈動態",
                    "source_name": "Mock Search Industry",
                    "source_url": "https://example.com/search/mock/thermal-supply-chain",
                    "published_at": _now_iso(),
                    "content": "English technology coverage highlights data center cooling solution trends and component qualification progress.",
                    "source_type": "search",
                },
            ]

        if keywords:
            query_summary = "、".join(keywords[:5])
            for item in items:
                item["content"] = f'{item["content"]} 追蹤關鍵字：{query_summary}'

        return [normalize_source_item(item, "search") for item in items]


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()
