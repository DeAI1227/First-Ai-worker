from __future__ import annotations

from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
OUTPUT_ROOT = PROJECT_ROOT / "output"

PACKET_TARGET_TABLES = {
    "event_packet": "staging_events",
    "daily_digest_packet": "staging_daily_digests",
    "report_packet": "staging_reports",
    "crawl_run_packet": "staging_crawl_runs",
    "rejected_source": "staging_rejected_sources",
}

PACKET_TYPE_ALIASES = {
    "event": "event_packet",
    "daily_digest": "daily_digest_packet",
    "report": "report_packet",
    "crawl_run": "crawl_run_packet",
    "rejected_source": "rejected_source",
}

SUPPORTED_PACKET_TYPES = tuple(PACKET_TARGET_TABLES.keys())
SUPPORTED_SHORT_PACKET_TYPES = tuple(PACKET_TYPE_ALIASES.keys())

