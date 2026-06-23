from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from collector.graph import run_three_day_report_task
from collector.nodes import report_builder, writer
from collector.nodes.report_builder import load_recent_daily_digests, summarize_digests
from collector.schemas.report_packet import validate_report_packet
from collector.tasks import make_task


def digest_payload(date: str, scope: str, scope_name: str, importance: str = "general", source_url: str = "https://example.com/a") -> dict:
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
        "key_takeaways": [f"{scope_name} takeaway 6230 {date}"],
        "source_urls": [source_url],
        "created_at": f"{date}T07:00:00+08:00",
        "language": "zh-TW",
    }


class ReportPacketValidatorTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.output_root = Path(self.tmp.name) / "output"
        self.patch_report = patch.object(report_builder, "OUTPUT_ROOT", self.output_root)
        self.patch_writer = patch.object(writer, "OUTPUT_ROOT", self.output_root)
        self.patch_report.start()
        self.patch_writer.start()

    def tearDown(self):
        self.patch_report.stop()
        self.patch_writer.stop()
        self.tmp.cleanup()

    def write_digest(self, scope_name: str, payload: dict) -> Path:
        digest_dir = self.output_root / "daily" / scope_name
        digest_dir.mkdir(parents=True, exist_ok=True)
        path = digest_dir / f"digest_{payload['digest_date']}_{payload['scope']}.json"
        path.write_text(json.dumps(payload, ensure_ascii=False), encoding="utf-8")
        return path

    def build_report(self, scope: str, scope_name: str, digests: list[dict]):
        for digest in digests:
            self.write_digest(scope_name, digest)
        state = run_three_day_report_task(make_task(scope, scope_name))
        return state["report_packet"], state

    def test_valid_industry_report_validator_passes(self):
        packet, _ = self.build_report("industry", "散熱", [digest_payload("2026-06-16", "thermal", "散熱", "important")])
        self.assertEqual(validate_report_packet(packet), [])

    def test_valid_macro_report_validator_passes(self):
        packet, _ = self.build_report("macro", "大環境", [digest_payload("2026-06-16", "macro", "大環境", "general")])
        self.assertEqual(validate_report_packet(packet), [])

    def test_packet_type_error_fails(self):
        packet, _ = self.build_report("industry", "散熱", [digest_payload("2026-06-16", "thermal", "散熱", "important")])
        packet["packet_type"] = "event"
        errors = validate_report_packet(packet)
        self.assertTrue(any("packet_type" in error for error in errors))

    def test_collector_error_fails(self):
        packet, _ = self.build_report("industry", "散熱", [digest_payload("2026-06-16", "thermal", "散熱", "important")])
        packet["collector"] = "kuse"
        errors = validate_report_packet(packet)
        self.assertTrue(any("collector" in error for error in errors))

    def test_report_type_error_fails(self):
        packet, _ = self.build_report("macro", "大環境", [digest_payload("2026-06-16", "macro", "大環境", "general")])
        packet["report_type"] = "bad_type"
        errors = validate_report_packet(packet)
        self.assertTrue(any("report_type" in error for error in errors))

    def test_importance_error_fails(self):
        packet, _ = self.build_report("macro", "大環境", [digest_payload("2026-06-16", "macro", "大環境", "general")])
        packet["importance"] = "urgent"
        errors = validate_report_packet(packet)
        self.assertTrue(any("importance" in error for error in errors))

    def test_industry_stock_confusion_fails(self):
        packet, _ = self.build_report("industry", "散熱", [digest_payload("2026-06-16", "thermal", "散熱", "important")])
        packet["related_industries"] = ["6230"]
        packet["related_stocks"] = ["散熱"]
        errors = validate_report_packet(packet)
        self.assertTrue(any("related_industries" in error for error in errors))
        self.assertTrue(any("related_stocks" in error for error in errors))

    def test_prohibited_terms_fail(self):
        packet, _ = self.build_report("industry", "散熱", [digest_payload("2026-06-16", "thermal", "散熱", "important")])
        packet["report_body"] += "\n買進"
        errors = validate_report_packet(packet)
        self.assertTrue(any("prohibited terms" in error for error in errors))

    def test_critical_count_sets_report_importance_critical(self):
        packet, state = self.build_report(
            "industry",
            "散熱",
            [
                digest_payload("2026-06-16", "thermal", "散熱", "critical"),
                digest_payload("2026-06-17", "thermal", "散熱", "important"),
                digest_payload("2026-06-18", "thermal", "散熱", "general"),
            ],
        )
        self.assertEqual(state["digest_summary"]["critical_count"], 1)
        self.assertEqual(packet["importance"], "critical")

    def test_important_count_sets_report_importance_important(self):
        packet, _ = self.build_report("industry", "散熱", [digest_payload("2026-06-16", "thermal", "散熱", "important")])
        self.assertEqual(packet["importance"], "important")

    def test_general_only_sets_report_importance_general(self):
        packet, _ = self.build_report("macro", "大環境", [digest_payload("2026-06-16", "macro", "大環境", "general")])
        self.assertEqual(packet["importance"], "general")

    def test_insufficient_digest_days_still_produces_report_with_warning(self):
        packet, _ = self.build_report("industry", "散熱", [digest_payload("2026-06-16", "thermal", "散熱", "important")])
        self.assertIn("資料天數不足", packet["executive_summary"])
        self.assertIn("資料天數不足", packet["report_body"])

    def test_source_count_is_correct(self):
        packet, _ = self.build_report("industry", "散熱", [digest_payload("2026-06-16", "thermal", "散熱", "important")])
        self.assertEqual(packet["source_count"], 1)

    def test_recent_three_digests_reader_limits_to_three_days(self):
        self.write_digest("散熱", digest_payload("2026-06-10", "thermal", "散熱", "general"))
        self.write_digest("散熱", digest_payload("2026-06-14", "thermal", "散熱", "general"))
        self.write_digest("散熱", digest_payload("2026-06-15", "thermal", "散熱", "general"))
        self.write_digest("散熱", digest_payload("2026-06-16", "thermal", "散熱", "general"))
        digests = load_recent_daily_digests("散熱", anchor_date="2026-06-16")
        summary = summarize_digests(digests)
        self.assertEqual(len(digests), 3)
        self.assertEqual(summary["digest_count"], 3)


if __name__ == "__main__":
    unittest.main()
