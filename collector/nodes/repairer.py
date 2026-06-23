from __future__ import annotations

from collector.constants import COLLECTOR_NAME, DEFAULT_LANGUAGE, VALID_INDUSTRIES, VALID_MVP_STOCKS
from collector.utils.text_utils import clamp_text


def repair_event_packet(state: dict) -> dict:
    packet = dict(state.get("event_packet", {}))
    state["repair_attempts"] = state.get("repair_attempts", 0) + 1

    packet["packet_type"] = "event"
    packet["collector"] = COLLECTOR_NAME
    packet["language"] = DEFAULT_LANGUAGE
    packet["ai_summary"] = clamp_text(packet.get("ai_summary", ""), 500)
    packet.setdefault("tags", [])

    industries = packet.get("related_industries") or []
    stocks = packet.get("related_stocks") or []

    fixed_industries = []
    fixed_stocks = []

    for value in industries:
        if value in VALID_INDUSTRIES:
            fixed_industries.append(value)
        elif value in VALID_MVP_STOCKS:
            fixed_stocks.append(value)

    for value in stocks:
        if value in VALID_MVP_STOCKS:
            fixed_stocks.append(value)
        elif value in VALID_INDUSTRIES:
            fixed_industries.append(value)

    packet["related_industries"] = sorted(set(fixed_industries), key=fixed_industries.index)
    packet["related_stocks"] = sorted(set(fixed_stocks), key=fixed_stocks.index)
    packet.setdefault("related_macro_topics", [])
    packet.setdefault("related_institution_watch", [])

    state["event_packet"] = packet
    return state
