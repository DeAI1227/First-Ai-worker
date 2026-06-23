from __future__ import annotations

from collector.schemas.event_packet import build_event_packet


def build_event_packet_node(state: dict) -> dict:
    state["event_packet"] = build_event_packet(state)
    return state
