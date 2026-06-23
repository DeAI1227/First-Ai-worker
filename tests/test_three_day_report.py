import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from collector.nodes import report_builder
from collector.nodes.report_builder import load_recent_daily_digests, summarize_digests
from collector.nodes import writer
from collector.graph import run_three_day_report_task
from collector.tasks import make_task


def digest_payload(date, scope, scope_name, importance="general", source_url="https://example.com/a"):
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


class ThreeDayReportTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.output_root = Path(self.tmp.name) / "output"
        self.patcher_report = patch.object(report_builder, "OUTPUT_ROOT", self.output_root)
        self.patcher_writer = patch.object(writer, "OUTPUT_ROOT", self.output_root)
        self.patcher_report.start()
        self.patcher_writer.start()

    def tearDown(self):
        self.patcher_report.stop()
        self.patcher_writer.stop()
        self.tmp.cleanup()

    def write_digest(self, scope_name, payload):
        digest_dir = self.output_root / "daily" / scope_name
        digest_dir.mkdir(parents=True, exist_ok=True)
        path = digest_dir / f"digest_{payload['digest_date']}_{payload['scope']}.json"
        path.write_text(json.dumps(payload, ensure_ascii=False), encoding="utf-8")
        return path

    def test_can_read_daily_digest(self):
        payload = digest_payload("2026-06-16", "thermal", "散熱", "important")
        self.write_digest("散熱", payload)
        digests = load_recent_daily_digests("散熱", anchor_date="2026-06-16")
        self.assertEqual(len(digests), 1)
        self.assertEqual(digests[0]["scope_name"], "散熱")

    def test_importance_summary_uses_digest_counts(self):
        self.write_digest("散熱", digest_payload("2026-06-14", "thermal", "散熱", "general"))
        self.write_digest("散熱", digest_payload("2026-06-15", "thermal", "散熱", "important"))
        self.write_digest("散熱", digest_payload("2026-06-16", "thermal", "散熱", "critical"))
        summary = summarize_digests(load_recent_daily_digests("散熱", anchor_date="2026-06-16"))
        self.assertEqual(summary["critical_count"], 1)
        self.assertEqual(summary["important_count"], 1)
        self.assertEqual(summary["general_count"], 1)

    def test_can_generate_industry_report_and_write_json(self):
        self.write_digest("散熱", digest_payload("2026-06-16", "thermal", "散熱", "important"))
        state = run_three_day_report_task(make_task("industry", "散熱"))
        packet = state["report_packet"]
        self.assertEqual(packet["packet_type"], "report")
        self.assertEqual(packet["collector"], "langgraph")
        self.assertEqual(packet["language"], "zh-TW")
        self.assertEqual(packet["report_type"], "industry_report")
        self.assertEqual(packet["importance"], "important")
        self.assertEqual(packet["related_industries"], ["散熱"])
        self.assertEqual(packet["related_stocks"], ["6230"])
        self.assertEqual(packet["source_count"], 1)
        report_paths = [Path(path) for path in state["output_paths"] if "three_day" in path]
        self.assertEqual(len(report_paths), 1)
        self.assertTrue(report_paths[0].exists())

    def test_can_generate_macro_report(self):
        self.write_digest("大環境", digest_payload("2026-06-16", "macro", "大環境", "general"))
        state = run_three_day_report_task(make_task("macro", "大環境"))
        packet = state["report_packet"]
        self.assertEqual(packet["report_type"], "macro_report")
        self.assertEqual(packet["related_industries"], [])
        self.assertEqual(packet["related_stocks"], [])
        self.assertEqual(packet["related_macro_topics"], ["macro_environment"])
        self.assertEqual(packet["source_count"], 1)


if __name__ == "__main__":
    unittest.main()
