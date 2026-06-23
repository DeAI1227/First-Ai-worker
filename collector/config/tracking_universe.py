from __future__ import annotations

from collections import defaultdict
from copy import deepcopy
from typing import Any

from collector.utils.time_utils import taipei_now


TRACKING_INDUSTRIES: list[dict[str, Any]] = [
    {
        "industry_id": "thermal",
        "industry_name": "散熱",
        "enabled": True,
        "keywords_zh": ["散熱", "液冷", "熱管理", "AI 伺服器"],
        "keywords_en": ["thermal", "cooling", "liquid cooling", "data center cooling"],
        "sample_stock_code": "6230",
        "sample_stock_name": "尼得科超眾",
    },
    {
        "industry_id": "power",
        "industry_name": "電力",
        "enabled": True,
        "keywords_zh": ["電力", "電網", "儲能", "變壓器"],
        "keywords_en": ["power", "power grid", "energy storage", "transformer"],
        "sample_stock_code": "1513",
        "sample_stock_name": "中興電",
    },
    {
        "industry_id": "autodrive",
        "industry_name": "自動駕駛",
        "enabled": True,
        "keywords_zh": ["自動駕駛", "ADAS", "車用電子", "感測器"],
        "keywords_en": ["autonomous driving", "ADAS", "automotive electronics", "sensor"],
        "sample_stock_code": "3227",
        "sample_stock_name": "原相",
    },
    {
        "industry_id": "robot",
        "industry_name": "機器人",
        "enabled": True,
        "keywords_zh": ["機器人", "工業自動化", "運動控制", "伺服"],
        "keywords_en": ["robot", "industrial automation", "motion control", "servo"],
        "sample_stock_code": "2049",
        "sample_stock_name": "上銀",
    },
    {
        "industry_id": "cpo",
        "industry_name": "CPO 光通訊",
        "enabled": True,
        "keywords_zh": ["CPO", "光通訊", "共同封裝光學", "矽光子"],
        "keywords_en": ["CPO", "co-packaged optics", "optical communication", "silicon photonics"],
        "sample_stock_code": "",
        "sample_stock_name": "",
    },
    {
        "industry_id": "networking",
        "industry_name": "網通",
        "enabled": True,
        "keywords_zh": ["網通", "路由器", "交換器", "WiFi"],
        "keywords_en": ["networking", "router", "switch", "Wi-Fi"],
        "sample_stock_code": "5388",
        "sample_stock_name": "中磊",
    },
]

TRACKED_STOCKS: list[dict[str, Any]] = [
    {"stock_code": "6230", "stock_name": "尼得科超眾", "enabled": True},
    {"stock_code": "1513", "stock_name": "中興電", "enabled": True},
    {"stock_code": "1514", "stock_name": "亞力", "enabled": True},
    {"stock_code": "6781", "stock_name": "AES-KY", "enabled": True},
    {"stock_code": "6121", "stock_name": "新普", "enabled": True},
    {"stock_code": "6412", "stock_name": "群電", "enabled": True},
    {"stock_code": "1504", "stock_name": "東元", "enabled": True},
    {"stock_code": "3015", "stock_name": "全漢", "enabled": True},
    {"stock_code": "2371", "stock_name": "大同", "enabled": True},
    {"stock_code": "1609", "stock_name": "大亞", "enabled": True},
    {"stock_code": "3227", "stock_name": "原相", "enabled": True},
    {"stock_code": "6279", "stock_name": "胡連", "enabled": True},
    {"stock_code": "3552", "stock_name": "同致", "enabled": True},
    {"stock_code": "8255", "stock_name": "朋程", "enabled": True},
    {"stock_code": "2497", "stock_name": "怡利電", "enabled": True},
    {"stock_code": "3019", "stock_name": "亞光", "enabled": True},
    {"stock_code": "4976", "stock_name": "佳凌", "enabled": True},
    {"stock_code": "4952", "stock_name": "凌通", "enabled": True},
    {"stock_code": "2049", "stock_name": "上銀", "enabled": True},
    {"stock_code": "4583", "stock_name": "台灣精銳", "enabled": True},
    {"stock_code": "4576", "stock_name": "大銀微系統", "enabled": True},
    {"stock_code": "4571", "stock_name": "鈞興-KY", "enabled": True},
    {"stock_code": "1597", "stock_name": "直得", "enabled": True},
    {"stock_code": "2233", "stock_name": "宇隆", "enabled": True},
    {"stock_code": "4540", "stock_name": "全球傳動", "enabled": True},
    {"stock_code": "2359", "stock_name": "所羅門", "enabled": True},
    {"stock_code": "1536", "stock_name": "和大", "enabled": True},
    {"stock_code": "1583", "stock_name": "程泰", "enabled": True},
    {"stock_code": "6215", "stock_name": "和椿", "enabled": True},
    {"stock_code": "8016", "stock_name": "矽創", "enabled": True},
    {"stock_code": "6732", "stock_name": "昇佳電子", "enabled": True},
    {"stock_code": "5484", "stock_name": "慧友", "enabled": True},
    {"stock_code": "3059", "stock_name": "華晶科", "enabled": True},
    {"stock_code": "2328", "stock_name": "廣宇", "enabled": True},
    {"stock_code": "5388", "stock_name": "中磊", "enabled": True},
    {"stock_code": "3596", "stock_name": "智易", "enabled": True},
    {"stock_code": "6285", "stock_name": "啟碁", "enabled": True},
    {"stock_code": "3380", "stock_name": "明泰", "enabled": True},
    {"stock_code": "2314", "stock_name": "台揚", "enabled": True},
    {"stock_code": "2312", "stock_name": "金寶", "enabled": True},
    {"stock_code": "6546", "stock_name": "正基", "enabled": True},
]

INSTITUTION_WATCH_STOCKS: list[dict[str, Any]] = [
    {"stock_code": "3665", "stock_name": "貿聯-KY", "enabled": True},
    {"stock_code": "2330", "stock_name": "台積電", "enabled": True},
    {"stock_code": "2454", "stock_name": "聯發科", "enabled": True},
    {"stock_code": "2308", "stock_name": "台達電", "enabled": True},
]

MACRO_TOPICS: list[dict[str, Any]] = [
    {
        "topic_id": "fed_rate",
        "topic_name": "FED 利率",
        "enabled": True,
        "keywords_zh": ["聯準會", "利率", "降息", "升息"],
        "keywords_en": ["Fed", "interest rate", "rate cut", "rate hike"],
    },
    {
        "topic_id": "us_cpi",
        "topic_name": "美國 CPI",
        "enabled": True,
        "keywords_zh": ["美國 CPI", "CPI", "通膨"],
        "keywords_en": ["US CPI", "inflation"],
    },
    {
        "topic_id": "us_ppi",
        "topic_name": "美國 PPI",
        "enabled": True,
        "keywords_zh": ["美國 PPI", "PPI", "生產者物價"],
        "keywords_en": ["US PPI", "producer price index"],
    },
    {
        "topic_id": "us_jobs",
        "topic_name": "美國就業數據",
        "enabled": True,
        "keywords_zh": ["就業", "非農", "失業率"],
        "keywords_en": ["employment", "nonfarm payrolls", "unemployment rate"],
    },
    {
        "topic_id": "us_10y_yield",
        "topic_name": "十年期美債殖利率",
        "enabled": True,
        "keywords_zh": ["十年期美債殖利率", "美債殖利率", "公債殖利率"],
        "keywords_en": ["10Y Treasury yield", "yield"],
    },
    {
        "topic_id": "usd_index",
        "topic_name": "美元指數",
        "enabled": True,
        "keywords_zh": ["美元指數", "DXY"],
        "keywords_en": ["USD index", "DXY"],
    },
    {
        "topic_id": "taiwan_weighted_index",
        "topic_name": "台股加權指數環境",
        "enabled": True,
        "keywords_zh": ["台股加權指數", "加權指數", "台股環境"],
        "keywords_en": ["Taiwan Weighted Index", "Taiwan market"],
    },
    {
        "topic_id": "foreign_investor_flows",
        "topic_name": "外資動向",
        "enabled": True,
        "keywords_zh": ["外資", "外資買賣超", "資金流"],
        "keywords_en": ["foreign investor", "capital flow"],
    },
    {
        "topic_id": "ai_capex",
        "topic_name": "AI 資本支出",
        "enabled": True,
        "keywords_zh": ["AI 資本支出", "AI 伺服器", "資本支出"],
        "keywords_en": ["AI capex", "AI server", "capex"],
    },
    {
        "topic_id": "data_center_demand",
        "topic_name": "資料中心需求",
        "enabled": True,
        "keywords_zh": ["資料中心", "雲端", "液冷"],
        "keywords_en": ["data center", "cloud", "liquid cooling"],
    },
]

STOCK_INDUSTRY_RELATIONS: list[dict[str, Any]] = [
    {"stock_code": "6230", "stock_name": "尼得科超眾", "industry_id": "thermal", "industry_name": "散熱"},
    {"stock_code": "1513", "stock_name": "中興電", "industry_id": "power", "industry_name": "電力"},
    {"stock_code": "1514", "stock_name": "亞力", "industry_id": "power", "industry_name": "電力"},
    {"stock_code": "6781", "stock_name": "AES-KY", "industry_id": "power", "industry_name": "電力"},
    {"stock_code": "6121", "stock_name": "新普", "industry_id": "power", "industry_name": "電力"},
    {"stock_code": "6412", "stock_name": "群電", "industry_id": "power", "industry_name": "電力"},
    {"stock_code": "1504", "stock_name": "東元", "industry_id": "power", "industry_name": "電力"},
    {"stock_code": "3015", "stock_name": "全漢", "industry_id": "power", "industry_name": "電力"},
    {"stock_code": "2371", "stock_name": "大同", "industry_id": "power", "industry_name": "電力"},
    {"stock_code": "1609", "stock_name": "大亞", "industry_id": "power", "industry_name": "電力"},
    {"stock_code": "3227", "stock_name": "原相", "industry_id": "autodrive", "industry_name": "自動駕駛"},
    {"stock_code": "3227", "stock_name": "原相", "industry_id": "robot", "industry_name": "機器人"},
    {"stock_code": "6279", "stock_name": "胡連", "industry_id": "autodrive", "industry_name": "自動駕駛"},
    {"stock_code": "3552", "stock_name": "同致", "industry_id": "autodrive", "industry_name": "自動駕駛"},
    {"stock_code": "8255", "stock_name": "朋程", "industry_id": "autodrive", "industry_name": "自動駕駛"},
    {"stock_code": "2497", "stock_name": "怡利電", "industry_id": "autodrive", "industry_name": "自動駕駛"},
    {"stock_code": "3019", "stock_name": "亞光", "industry_id": "autodrive", "industry_name": "自動駕駛"},
    {"stock_code": "4976", "stock_name": "佳凌", "industry_id": "autodrive", "industry_name": "自動駕駛"},
    {"stock_code": "4952", "stock_name": "凌通", "industry_id": "autodrive", "industry_name": "自動駕駛"},
    {"stock_code": "2049", "stock_name": "上銀", "industry_id": "robot", "industry_name": "機器人"},
    {"stock_code": "4583", "stock_name": "台灣精銳", "industry_id": "robot", "industry_name": "機器人"},
    {"stock_code": "4576", "stock_name": "大銀微系統", "industry_id": "robot", "industry_name": "機器人"},
    {"stock_code": "4571", "stock_name": "鈞興-KY", "industry_id": "robot", "industry_name": "機器人"},
    {"stock_code": "1597", "stock_name": "直得", "industry_id": "robot", "industry_name": "機器人"},
    {"stock_code": "2233", "stock_name": "宇隆", "industry_id": "robot", "industry_name": "機器人"},
    {"stock_code": "4540", "stock_name": "全球傳動", "industry_id": "robot", "industry_name": "機器人"},
    {"stock_code": "2359", "stock_name": "所羅門", "industry_id": "robot", "industry_name": "機器人"},
    {"stock_code": "1536", "stock_name": "和大", "industry_id": "robot", "industry_name": "機器人"},
    {"stock_code": "1583", "stock_name": "程泰", "industry_id": "robot", "industry_name": "機器人"},
    {"stock_code": "6215", "stock_name": "和椿", "industry_id": "robot", "industry_name": "機器人"},
    {"stock_code": "8016", "stock_name": "矽創", "industry_id": "robot", "industry_name": "機器人"},
    {"stock_code": "6732", "stock_name": "昇佳電子", "industry_id": "robot", "industry_name": "機器人"},
    {"stock_code": "5484", "stock_name": "慧友", "industry_id": "robot", "industry_name": "機器人"},
    {"stock_code": "3059", "stock_name": "華晶科", "industry_id": "robot", "industry_name": "機器人"},
    {"stock_code": "2328", "stock_name": "廣宇", "industry_id": "robot", "industry_name": "機器人"},
    {"stock_code": "5388", "stock_name": "中磊", "industry_id": "networking", "industry_name": "網通"},
    {"stock_code": "3596", "stock_name": "智易", "industry_id": "networking", "industry_name": "網通"},
    {"stock_code": "6285", "stock_name": "啟碁", "industry_id": "networking", "industry_name": "網通"},
    {"stock_code": "3380", "stock_name": "明泰", "industry_id": "networking", "industry_name": "網通"},
    {"stock_code": "2314", "stock_name": "台揚", "industry_id": "networking", "industry_name": "網通"},
    {"stock_code": "2312", "stock_name": "金寶", "industry_id": "networking", "industry_name": "網通"},
    {"stock_code": "6546", "stock_name": "正基", "industry_id": "networking", "industry_name": "網通"},
]

BATCH_SCOPE_ORDER = ["macro", "industry", "stock", "institution_watch"]

INDUSTRY_BY_NAME = {item["industry_name"]: item for item in TRACKING_INDUSTRIES}
INDUSTRY_BY_ID = {item["industry_id"]: item for item in TRACKING_INDUSTRIES}
STOCK_BY_CODE = {item["stock_code"]: item for item in TRACKED_STOCKS}
INSTITUTION_BY_CODE = {item["stock_code"]: item for item in INSTITUTION_WATCH_STOCKS}
MACRO_TOPIC_BY_ID = {item["topic_id"]: item for item in MACRO_TOPICS}

_industry_stock_map: dict[str, list[dict[str, str]]] = defaultdict(list)
for relation in STOCK_INDUSTRY_RELATIONS:
    _industry_stock_map[relation["industry_name"]].append(
        {
            "code": relation["stock_code"],
            "name": relation["stock_name"],
        }
    )

for industry in TRACKING_INDUSTRIES:
    industry.setdefault("key", industry["industry_id"])
    industry.setdefault("name", industry["industry_name"])
    industry.setdefault(
        "search_keywords",
        list(
            dict.fromkeys(
                [
                    *industry.get("keywords_zh", []),
                    *industry.get("keywords_en", []),
                    industry.get("sample_stock_code", ""),
                    industry.get("sample_stock_name", ""),
                ]
            )
        ),
    )
    industry.setdefault("stocks", deepcopy(_industry_stock_map.get(industry["industry_name"], [])))

TRACKING_MACRO_TOPICS: list[dict[str, Any]] = [
    {
        "key": topic["topic_id"],
        "name": topic["topic_name"],
        "enabled": topic.get("enabled", True),
        "keywords": list(dict.fromkeys([*topic.get("keywords_zh", []), *topic.get("keywords_en", [])])),
    }
    for topic in MACRO_TOPICS
]

TRACKING_INSTITUTION_WATCH: list[dict[str, Any]] = [
    {
        "code": item["stock_code"],
        "name": item["stock_name"],
        "enabled": item.get("enabled", True),
    }
    for item in INSTITUTION_WATCH_STOCKS
]


def resolve_tracking_source_key(scope: str, scope_name: str) -> str:
    if scope == "macro":
        return "macro"
    if scope == "industry":
        industry = INDUSTRY_BY_NAME.get(scope_name)
        if industry:
            return industry["industry_id"]
        return "thermal" if scope_name == "散熱" else "industry"
    if scope == "stock":
        return "stock"
    if scope in {"institution", "institution_watch"}:
        return "institution"
    return "macro"


def get_universe_snapshot() -> dict[str, Any]:
    return {
        "industries": deepcopy(TRACKING_INDUSTRIES),
        "tracked_stocks": deepcopy(TRACKED_STOCKS),
        "institution_watch_stocks": deepcopy(INSTITUTION_WATCH_STOCKS),
        "macro_topics": deepcopy(MACRO_TOPICS),
        "stock_industry_relations": deepcopy(STOCK_INDUSTRY_RELATIONS),
    }


def stock_industries_for_code(stock_code: str) -> list[str]:
    return [
        relation["industry_name"]
        for relation in STOCK_INDUSTRY_RELATIONS
        if relation["stock_code"] == stock_code
    ]


def topic_keywords(topic_id: str) -> list[str]:
    topic = MACRO_TOPIC_BY_ID.get(topic_id)
    if not topic:
        return []
    return list(topic.get("keywords_zh", [])) + list(topic.get("keywords_en", []))


def industry_keywords(industry_name: str) -> list[str]:
    industry = INDUSTRY_BY_NAME.get(industry_name)
    if not industry:
        return []
    return list(industry.get("keywords_zh", [])) + list(industry.get("keywords_en", []))


def build_batch_task(
    *,
    scope: str,
    scope_name: str,
    stock_code: str = "",
    stock_name: str = "",
    industry_name: str = "",
    run_mode: str = "daily",
    source_mode: str = "hybrid",
    summarizer_mode: str = "mock",
    llm_provider: str = "auto",
    search_provider: str = "auto",
    search_keywords: list[str] | None = None,
    **extra: Any,
) -> dict[str, Any]:
    timestamp = taipei_now().strftime("%Y%m%d_%H%M%S")
    stock_part = f"_{stock_code}" if stock_code else ""
    task: dict[str, Any] = {
        "task_id": f"{scope}_{scope_name}{stock_part}_{timestamp}",
        "run_mode": run_mode,
        "source_mode": source_mode,
        "summarizer_mode": summarizer_mode,
        "llm_provider": llm_provider,
        "search_provider": search_provider,
        "scope": scope,
        "scope_name": scope_name,
        "target_stock_code": stock_code,
        "target_stock_name": stock_name,
    }
    if industry_name:
        task["industry_name"] = industry_name
    if search_keywords:
        task["search_keywords"] = [keyword for keyword in search_keywords if str(keyword).strip()]
    task.update(extra)
    return task
