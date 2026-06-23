from __future__ import annotations

from collector.schemas.event_packet import validate_event_packet


def validate_event_packet_node(state: dict) -> dict:
    packet = state.get("event_packet", {})
    state["validation_errors"] = validate_event_packet(packet)
    return state
