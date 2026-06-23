from __future__ import annotations

from collector.config.tracking_universe import (
    INSTITUTION_WATCH_STOCKS,
    TRACKED_STOCKS,
    TRACKING_MACRO_TOPICS,
    TRACKING_INDUSTRIES,
)


VALID_INDUSTRIES = [item["industry_name"] for item in TRACKING_INDUSTRIES]

VALID_MVP_STOCKS = list(
    dict.fromkeys(
        [
            *(item["stock_code"] for item in TRACKED_STOCKS),
            *(item["stock_code"] for item in INSTITUTION_WATCH_STOCKS),
        ]
    )
)

VALID_EVENT_TYPES = [
    "macro",
    "industry",
    "global_leader",
    "domestic_leader",
    "stock",
    "institution",
]

VALID_IMPORTANCE = ["general", "important", "critical"]

VALID_RUN_MODES = ["daily", "three_day"]

VALID_SCOPES = ["macro", "industry", "stock", "institution", "institution_watch"]

PROHIBITED_TERMS = [
    "買進",
    "賣出",
    "目標價",
    "報酬率",
    "漲停",
    "飆股",
    "喊單",
    "技術分析",
    "K線",
    "成交量",
    "買賣建議",
    "投資建議",
]

SCOPE_DIR_NAMES = {
    "macro": "大環境",
    "industry": "產業",
    "stock": "股票",
    "institution": "大行關注",
}

MACRO_TOPICS = [item["key"] for item in TRACKING_MACRO_TOPICS]

DEFAULT_LANGUAGE = "zh-TW"
COLLECTOR_NAME = "langgraph"

