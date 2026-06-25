from __future__ import annotations

import re

from collector.constants import PROHIBITED_TERMS as PROJECT_PROHIBITED_TERMS

HIGH_LEVEL_MIN = 80
MEDIUM_LEVEL_MIN = 50
LOW_LEVEL_MIN = 20

QUALITY_PROHIBITED_TERMS = [
    "買進",
    "賣出",
    "目標價",
    "報酬率",
    "漲停",
    "飆股",
    "喊單",
    "買賣建議",
    "投資建議",
    "技術分析",
    "k線",
    "成交量",
]

SUSPICIOUS_SIGNAL_TERMS = [
    "buy now",
    "sell now",
    "target price",
    "price target",
    "stock pick",
    "call option",
    "strong buy",
    "strong sell",
]

RESEARCH_TERMS = [
    "research",
    "研究",
    "產業",
    "供應鏈",
    "政策",
    "法說",
    "公告",
    "資料中心",
    "財報",
    "營收",
    "execution",
]

OFFICIAL_SOURCE_TERMS = [
    "official",
    "government",
    "gov",
    "regulator",
    "company",
    "press release",
    "announcement",
    "公開資訊觀測站",
    "證交所",
    "櫃買中心",
    "經濟部",
    "reuters",
    "bloomberg",
]

QUOTE_BULLETIN_TERMS = [
    "盤中速報",
    "股價",
    "報價",
    "漲幅",
    "跌幅",
    "收盤",
    "開盤",
    "盤中",
    "大漲",
    "大跌",
]

QUOTE_BULLETIN_PATTERNS = [
    re.compile(r"報\s*\d+(?:\.\d+)?\s*元"),
    re.compile(r"\d+(?:\.\d+)?\s*%"),
    re.compile(r"漲\d+(?:\.\d+)?%"),
    re.compile(r"跌\d+(?:\.\d+)?%"),
]


def is_prohibited_text(text: str) -> list[str]:
    lowered = text.lower()
    matches: list[str] = []
    for term in [*QUALITY_PROHIBITED_TERMS, *PROJECT_PROHIBITED_TERMS]:
        cleaned = str(term).strip()
        if cleaned and cleaned.lower() in lowered and cleaned not in matches:
            matches.append(cleaned)
    return matches


def is_suspicious_signal(text: str) -> bool:
    lowered = text.lower()
    return any(term.lower() in lowered for term in SUSPICIOUS_SIGNAL_TERMS)


def is_quote_style_bulletin(text: str) -> bool:
    if any(term in text for term in QUOTE_BULLETIN_TERMS):
        return True
    return any(pattern.search(text) for pattern in QUOTE_BULLETIN_PATTERNS)
