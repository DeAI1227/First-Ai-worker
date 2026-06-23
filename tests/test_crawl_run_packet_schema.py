from __future__ import annotations

import unittest

from collector.schemas.crawl_run_packet import build_crawl_run_packet, validate_crawl_run_packet


class CrawlRunPacketSchemaTests(unittest.TestCase):
    def test_success_packet_contains_fixed_fields(self):
        state = {
            "run_id": "run-001",
            "run_date": "2026-06-17",
            "run_mode": "daily",
            "scope": "industry",
            "scope_name": "散熱",
            "source_mode": "mock",
            "summarizer_mode": "mock",
            "llm_provider": "auto",
            "search_provider": "auto",
            "started_at": "2026-06-17T08:00:00+08:00",
            "finished_at": "2026-06-17T08:00:05+08:00",
            "raw_sources": [{"source_name": "RSS", "source_url": "output/daily/散熱/a.json"}],
            "filtered_sources": [{"source_name": "RSS", "source_url": "output/daily/散熱/a.json"}],
            "rejected_sources": [],
            "quality_summary": {"total_sources": 1, "high": 1, "medium": 0, "low": 0, "rejected": 0},
            "output_paths": [
                "output/daily/散熱/event_2026-06-17_industry_001.json",
                "output/daily/散熱/digest_2026-06-17_industry.json",
                "output/logs/crawl_run_2026-06-17_industry.json",
            ],
            "run_errors": [],
        }
        packet = build_crawl_run_packet(state)
        self.assertEqual(packet["run_id"], "run-001")
        self.assertEqual(packet["run_date"], "2026-06-17")
        self.assertEqual(packet["status"], "success")
        self.assertEqual(packet["mode"], "daily")
        self.assertEqual(packet["scope"], "industry")
        self.assertEqual(packet["total_sources_count"], 1)
        self.assertEqual(packet["accepted_sources_count"], 1)
        self.assertEqual(packet["rejected_sources_count"], 0)
        self.assertEqual(packet["quality_summary"]["high"], 1)
        self.assertEqual(packet["output_files"], [
            "output/daily/散熱/event_2026-06-17_industry_001.json",
            "output/daily/散熱/digest_2026-06-17_industry.json",
            "output/logs/crawl_run_2026-06-17_industry.json",
        ])
        self.assertEqual(packet["run_errors"], [])
        self.assertEqual(validate_crawl_run_packet(packet), [])

    def test_partial_success_packet_when_warning_exists(self):
        state = {
            "run_id": "run-002",
            "run_date": "2026-06-17",
            "run_mode": "daily",
            "scope": "macro",
            "scope_name": "大環境",
            "source_mode": "hybrid",
            "summarizer_mode": "llm",
            "llm_provider": "auto",
            "search_provider": "auto",
            "started_at": "2026-06-17T08:00:00+08:00",
            "finished_at": "2026-06-17T08:00:05+08:00",
            "raw_sources": [{"source_name": "Mock", "source_url": "output/daily/大環境/a.json"}],
            "filtered_sources": [{"source_name": "Mock", "source_url": "output/daily/大環境/a.json"}],
            "rejected_sources": [],
            "quality_summary": {"total_sources": 1, "high": 0, "medium": 1, "low": 0, "rejected": 0},
            "output_paths": [
                "output/daily/大環境/event_2026-06-17_macro_001.json",
                "output/daily/大環境/digest_2026-06-17_macro.json",
                "output/logs/crawl_run_2026-06-17_macro.json",
            ],
            "run_errors": ["rss fetch returned no items; fallback to mock sources"],
        }
        packet = build_crawl_run_packet(state)
        self.assertEqual(packet["status"], "partial_success")
        self.assertTrue(packet["run_errors"])
        self.assertEqual(packet["run_errors"][0]["stage"], "fetch")
        self.assertEqual(packet["run_errors"][0]["severity"], "warning")

    def test_failed_packet_when_only_failed_output_exists(self):
        state = {
            "run_id": "run-003",
            "run_date": "2026-06-17",
            "run_mode": "daily",
            "scope": "industry",
            "scope_name": "散熱",
            "source_mode": "mock",
            "summarizer_mode": "mock",
            "llm_provider": "auto",
            "search_provider": "auto",
            "started_at": "2026-06-17T08:00:00+08:00",
            "finished_at": "2026-06-17T08:00:05+08:00",
            "raw_sources": [],
            "filtered_sources": [],
            "rejected_sources": [],
            "quality_summary": {"total_sources": 0, "high": 0, "medium": 0, "low": 0, "rejected": 0},
            "output_paths": ["output/failed/failed_2026-06-17_industry_001.json"],
            "run_errors": ["validation failed"],
        }
        packet = build_crawl_run_packet(state)
        self.assertEqual(packet["status"], "failed")
        self.assertEqual(packet["accepted_sources_count"], 0)
        self.assertEqual(packet["rejected_sources_count"], 0)

    def test_validator_rejects_missing_required_fields(self):
        packet = {
            "packet_type": "crawl_run",
            "collector": "langgraph",
            "run_id": "run-004",
            "run_date": "2026-06-17",
            "started_at": "2026-06-17T08:00:00+08:00",
            "finished_at": "2026-06-17T08:00:05+08:00",
            "status": "success",
            "mode": "daily",
            "scope": "industry",
            "scope_name": "散熱",
            "source_mode": "mock",
            "summarizer_mode": "mock",
            "llm_provider": "auto",
            "search_provider": "auto",
            "total_sources_count": 1,
            "accepted_sources_count": 1,
            "rejected_sources_count": 0,
            "quality_summary": {"total_sources": 1, "high": 1, "medium": 0, "low": 0, "rejected": 0},
            "rejected_reasons": [],
            "output_files": ["output/daily/散熱/event_2026-06-17_industry_001.json"],
            "run_errors": [],
        }
        self.assertEqual(validate_crawl_run_packet(packet), [])

        broken = dict(packet)
        broken.pop("run_id")
        self.assertTrue(validate_crawl_run_packet(broken))


if __name__ == "__main__":
    unittest.main()
