from __future__ import annotations

from datetime import datetime
from zoneinfo import ZoneInfo


TAIPEI_TZ = ZoneInfo("Asia/Taipei")


def taipei_now() -> datetime:
    return datetime.now(TAIPEI_TZ)


def now_iso() -> str:
    return taipei_now().isoformat(timespec="seconds")


def today_date() -> str:
    return taipei_now().strftime("%Y-%m-%d")


def run_id() -> str:
    return "langgraph_" + taipei_now().strftime("%Y%m%d_%H%M%S")
