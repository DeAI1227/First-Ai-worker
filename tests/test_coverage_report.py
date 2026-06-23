from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from collector.batch_runner import run_batch_tasks
from collector.config.tracking_universe import INSTITUTION_WATCH_STOCKS, MACRO_TOPICS, TRACKING_INDUSTRIES
from collector.config.tracking_universe import TRACKED_STOCKS
from collector.coverage_report import build_coverage_report
from collector.graph import run_collector_task
from collector.nodes import writer
from collector.task_batches import generate_batch_tasks
from collector.tasks import make_task


class CoverageReportTests(unittest.TestCase):
    def setUp(self) -> None:
        self.tmp = tempfile.TemporaryDirectory()
        self.project_output = Path(self.tmp.name) / "output"
        self.writer_patch = patch.object(writer, "OUTPUT_ROOT", self.project_output)
        self.batch_logs_patch = patch("collector.batch_runner.BATCH_LOGS_ROOT", self.project_output / "logs")
        self.coverage_logs_patch = patch("collector.coverage_report.COVERAGE_LOGS_ROOT", self.project_output / "logs")
        self.writer_patch.start()
        self.batch_logs_patch.start()
        self.coverage_logs_patch.start()

    def tearDown(self) -> None:
        self.writer_patch.stop()
        self.batch_logs_patch.stop()
        self.coverage_logs_patch.stop()
        self.tmp.cleanup()

    def test_stock_without_news_skips_event_and_daily_digest(self) -> None:
        task = make_task(
            scope="stock",
            scope_name="中興電",
            stock_code="1513",
            stock_name="中興電",
            source_mode="mock",
        )
        state = run_collector_task(task)

        self.assertEqual(state["status"], "success")
        self.assertEqual(state.get("event_packet"), {})
        self.assertEqual(state.get("daily_digest_packet"), {})
        self.assertEqual(state.get("report_packet"), {})
        self.assertEqual(len(state.get("output_paths", [])), 1)
        self.assertTrue(state["output_paths"][0].endswith(".json"))
        self.assertIn("crawl_run_", state["output_paths"][0].replace("\\", "/"))

    def test_batch_stocks_writes_coverage_report_with_with_and_without_events(self) -> None:
        tasks = [
            make_task(scope="stock", scope_name="尼得科超眾", stock_code="6230", stock_name="尼得科超眾", source_mode="mock"),
            make_task(scope="stock", scope_name="中興電", stock_code="1513", stock_name="中興電", source_mode="mock"),
        ]
        summary = run_batch_tasks(tasks, batch_type="stocks")

        coverage_path = Path(summary["coverage_report_path"])
        self.assertTrue(coverage_path.exists())

        coverage_report = json.loads(coverage_path.read_text(encoding="utf-8"))
        self.assertEqual(coverage_report["coverage_date"], summary["coverage_report"]["coverage_date"])
        self.assertIn("6230", coverage_report["stocks_with_events"])
        self.assertIn("1513", coverage_report["stocks_without_events"])
        self.assertEqual(coverage_report["total_tracked_stocks"], len(TRACKED_STOCKS))
        self.assertTrue(coverage_report["searched_stocks"])
        self.assertIsInstance(coverage_report["warnings"], list)

    def test_coverage_report_counts_stock_and_institution_targets_together(self) -> None:
        stock = TRACKED_STOCKS[0]
        institution = INSTITUTION_WATCH_STOCKS[0]
        tasks = [
            make_task(
                scope="stock",
                scope_name=stock["stock_name"],
                stock_code=stock["stock_code"],
                stock_name=stock["stock_name"],
                source_mode="mock",
            ),
            make_task(
                scope="institution_watch",
                scope_name=institution["stock_name"],
                stock_code=institution["stock_code"],
                stock_name=institution["stock_name"],
                source_mode="mock",
            ),
        ]
        report = build_coverage_report(
            tasks=tasks,
            results=[
                {"status": "success", "event_packet": {"packet_type": "event"}},
                {"status": "success", "event_packet": {"packet_type": "event"}},
            ],
        )

        self.assertEqual(report["total_tracked_stocks"], len(TRACKED_STOCKS) + len(INSTITUTION_WATCH_STOCKS))
        self.assertIn(stock["stock_code"], report["searched_stocks"])
        self.assertIn(institution["stock_code"], report["searched_stocks"])
        self.assertIn(stock["stock_code"], report["stocks_with_events"])
        self.assertIn(institution["stock_code"], report["stocks_with_events"])
        self.assertFalse(report["stocks_without_events"])

    def test_build_coverage_report_marks_missing_targets_from_config(self) -> None:
        report = build_coverage_report(
            tasks=[
                make_task(scope="stock", scope_name="尼得科超眾", stock_code="6230", stock_name="尼得科超眾"),
            ],
            results=[
                {
                    "status": "success",
                    "event_packet": {"packet_type": "event"},
                }
            ],
        )

        self.assertIn("6230", report["stocks_with_events"])
        self.assertGreater(len(report["missing_search_targets"]), 0)

    def test_generate_batch_tasks_all_covers_every_registered_scope(self) -> None:
        tasks = generate_batch_tasks("all")
        self.assertEqual(
            len(tasks),
            len(MACRO_TOPICS) + len(TRACKING_INDUSTRIES) + len(TRACKED_STOCKS) + len(INSTITUTION_WATCH_STOCKS),
        )
        self.assertTrue({"macro", "industry", "stock", "institution_watch"}.issubset({task["scope"] for task in tasks}))

    def test_generate_batch_tasks_stocks_matches_tracked_stock_registry(self) -> None:
        tasks = generate_batch_tasks("stocks")
        self.assertEqual(len(tasks), len(TRACKED_STOCKS))


if __name__ == "__main__":
    unittest.main()
