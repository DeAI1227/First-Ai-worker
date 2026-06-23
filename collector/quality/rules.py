from __future__ import annotations

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
    "技術分析",
    "K線",
    "成交量",
    "投資建議",
    "買賣建議",
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
    "公告",
    "驗證",
    "出貨",
    "需求",
    "報告",
    "分析",
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
    "news",
    "bloomberg",
    "reuters",
    "bbc",
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

