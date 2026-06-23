from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from collector.nodes import report_builder
from collector.nodes.report_builder import build_three_day_report, load_recent_daily_digests
import collector.nodes.writer as writer_module
from collector.schemas.daily_digest_packet import build_daily_digest_packet
from collector.graph import run_collector_task
from collector.tasks import make_task


def digest_payload(date: str, scope: str, scope_name: str, importance: str = "general") -> dict:
    return {
        "packet_type": "daily_digest",
        "collector": "langgraph",
        "digest_date": date,
        "scope": scope,
        "scope_name": scope_name,
        "event_count": 1,
        "critical_count": 1 if importance == "critical" else 0,
        "important_count": 1 if importance == "important" else 0,
        "general_count": 1 if importance == "general" else 0,
        "top_events": [f"{scope_name} event {date}"],
        "key_takeaways": [f"{scope_name} takeaway {date}"],
        "source_urls": [f"https://example.com/{scope_name}/{date}"],
        "quality_summary": {
            "total_sources": 3,
            "high": 1,
            "medium": 1,
            "low": 1,
            "rejected": 1,
        },
        "rejected_reasons": ["內容太短", "缺少 source_url"],
        "created_at": f"{date}T07:00:00+08:00",
        "language": "zh-TW",
    }


class QualitySummaryIntegrationTests(unittest.TestCase):
    def setUp(self) -> None:
        self.tmp = tempfile.TemporaryDirectory()
        self.output_root = Path(self.tmp.name) / "output"
        self.patcher_report = patch.object(report_builder, "OUTPUT_ROOT", self.output_root)
        self.patcher_writer = patch.object(writer_module, "OUTPUT_ROOT", self.output_root)
        self.patcher_report.start()
        self.patcher_writer.start()

    def tearDown(self) -> None:
        self.patcher_report.stop()
        self.patcher_writer.stop()
        self.tmp.cleanup()

    def write_digest(self, scope_name: str, payload: dict) -> Path:
        digest_dir = self.output_root / "daily" / scope_name
        digest_dir.mkdir(parents=True, exist_ok=True)
        path = digest_dir / f"digest_{payload['digest_date']}_{payload['scope']}.json"
        path.write_text(json.dumps(payload, ensure_ascii=False), encoding="utf-8")
        return path

    def test_daily_digest_packet_contains_quality_summary_and_rejected_reasons(self):
        state = {
            "scope": "industry",
            "scope_name": "散熱",
            "event_packet": {
                "title": "散熱產業更新",
                "importance": "important",
                "source_url": "https://example.com/a",
                "ai_summary": "摘要",
            },
            "quality_summary": {
                "total_sources": 5,
                "high": 2,
                "medium": 2,
                "low": 1,
                "rejected": 1,
            },
            "rejected_sources": [
                {"quality_reasons": ["內容太短", "缺少 source_url"]},
                {"quality_reasons": ["內容太短"]},
            ],
        }
        packet = build_daily_digest_packet(state)
        self.assertEqual(packet["quality_summary"]["total_sources"], 5)
        self.assertEqual(packet["quality_summary"]["rejected"], 1)
        self.assertEqual(packet["rejected_reasons"], ["內容太短", "缺少 source_url"])

    def test_three_day_report_aggregates_quality_summary_and_reports_body(self):
        self.write_digest("散熱", digest_payload("2026-06-16", "industry", "散熱", "general"))
        self.write_digest("散熱", digest_payload("2026-06-17", "industry", "散熱", "important"))
        self.write_digest("散熱", digest_payload("2026-06-18", "industry", "散熱", "critical"))
        state = build_three_day_report(make_task("industry", "散熱", stock_code="6230", stock_name="尼德科超眰"))
        packet = state["report_packet"]
        self.assertIn("資料品質摘要", packet["report_body"])
        self.assertEqual(packet["quality_summary"]["total_sources"], 9)
        self.assertEqual(packet["quality_summary"]["high"], 3)
        self.assertEqual(packet["quality_summary"]["medium"], 3)
        self.assertEqual(packet["quality_summary"]["low"], 3)
        self.assertEqual(packet["quality_summary"]["rejected"], 3)
        self.assertIn("內容太短", packet["report_body"])
        self.assertIn("缺少 source_url", packet["report_body"])

    def test_three_day_report_warns_when_digest_days_are_insufficient(self):
        self.write_digest("散熱", digest_payload("2026-06-17", "industry", "散熱", "important"))
        state = build_three_day_report(make_task("industry", "散熱", stock_code="6230", stock_name="尼得科超眾"))
        packet = state["report_packet"]
        self.assertIn("資料天數不足三天", packet["report_body"])
        self.assertIn("資料天數不足三天", packet["executive_summary"])

    def test_load_recent_daily_digests_filters_to_three_days(self):
        self.write_digest("散熱", digest_payload("2026-06-13", "industry", "散熱", "general"))
        self.write_digest("散熱", digest_payload("2026-06-15", "industry", "散熱", "general"))
        digests = load_recent_daily_digests("散熱", anchor_date="2026-06-17")
        self.assertEqual(len(digests), 1)
        self.assertEqual(digests[0]["digest_date"], "2026-06-15")

    def test_crawl_run_packet_and_log_include_quality_summary_and_counts(self):
        state = run_collector_task(make_task("industry", "散熱", stock_code="6230", stock_name="尼得科超眾"))
        packet = state["crawl_run_packet"]
        self.assertIn("quality_summary", packet)
        self.assertIn("rejected_reasons", packet)
        self.assertIn("accepted_sources_count", packet)
        self.assertIn("rejected_sources_count", packet)
        self.assertEqual(packet["accepted_sources_count"], len(state.get("filtered_sources", [])))
        self.assertEqual(packet["rejected_sources_count"], len(state.get("rejected_sources", [])))
        log_paths = [Path(path) for path in state["output_paths"] if "crawl_run" in path]
        self.assertTrue(log_paths)
        self.assertTrue(log_paths[0].exists())
        log_payload = json.loads(log_paths[0].read_text(encoding="utf-8"))
        self.assertIn("quality_summary", log_payload)
        self.assertIn("accepted_sources_count", log_payload)
        self.assertIn("rejected_sources_count", log_payload)


if __name__ == "__main__":
    unittest.main()
