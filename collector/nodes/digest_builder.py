from __future__ import annotations

from collector.schemas.daily_digest_packet import build_daily_digest_packet


def build_daily_digest(state: dict) -> dict:
    state["daily_digest_packet"] = build_daily_digest_packet(state)
    return state
