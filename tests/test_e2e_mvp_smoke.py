from __future__ import annotations

import unittest
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import patch

import collector.batch_runner as batch_runner
import collector.coverage_report as coverage_report
import ingestion.batch_report as ingestion_batch_report
import promotion.packet_promoter as packet_promoter
import promotion.promotion_report as promotion_report
from collector.config.tracking_universe import (
    INSTITUTION_WATCH_STOCKS,
    MACRO_TOPICS,
    TRACKED_STOCKS,
    TRACKING_INDUSTRIES,
)
from collector.graph import run_collector_task
from collector.task_batches import generate_batch_tasks
from scripts.e2e_mvp_smoke import run_e2e_smoke


class E2EMvpSmokeTests(unittest.TestCase):
    @property
    def project_root(self) -> Path:
        return Path(__file__).resolve().parents[1]

    @property
    def total_tracking_stock_count(self) -> int:
        tracked_codes = {item["stock_code"] for item in TRACKED_STOCKS}
        tracked_codes.update(item["stock_code"] for item in INSTITUTION_WATCH_STOCKS)
        return len(tracked_codes)

    def test_smoke_script_exists(self) -> None:
        self.assertTrue((self.project_root / "scripts" / "e2e_mvp_smoke.py").exists())

    def test_tracking_universe_counts_are_fixed(self) -> None:
        self.assertEqual(self.total_tracking_stock_count, 45)
        self.assertEqual(len(TRACKING_INDUSTRIES), 6)
        self.assertEqual(len(MACRO_TOPICS), 10)
        self.assertEqual(len(INSTITUTION_WATCH_STOCKS), 4)

    def test_smoke_report_has_expected_shape(self) -> None:
        with TemporaryDirectory() as tmpdir:
            output_root = Path(tmpdir) / "output"
            output_root.mkdir(parents=True, exist_ok=True)
            logs_root = output_root / "logs"
            promotion_logs_root = output_root / "promotion_logs"
            ingestion_logs_root = output_root / "ingestion_logs"

            with patch.object(batch_runner, "OUTPUT_ROOT", output_root), \
                 patch.object(batch_runner, "BATCH_LOGS_ROOT", logs_root), \
                 patch.object(coverage_report, "OUTPUT_ROOT", output_root), \
                 patch.object(coverage_report, "COVERAGE_LOGS_ROOT", logs_root), \
                 patch.object(ingestion_batch_report, "OUTPUT_ROOT", output_root), \
                 patch.object(ingestion_batch_report, "BATCH_LOGS_ROOT", ingestion_logs_root), \
                 patch.object(packet_promoter, "OUTPUT_ROOT", output_root), \
                 patch.object(packet_promoter, "PROMOTION_LOGS_ROOT", promotion_logs_root), \
                 patch.object(promotion_report, "OUTPUT_ROOT", output_root), \
                 patch.object(promotion_report, "PROMOTION_LOGS_ROOT", promotion_logs_root), \
                 patch("scripts.e2e_mvp_smoke.OUTPUT_ROOT", output_root), \
                 patch("scripts.e2e_mvp_smoke.LOGS_ROOT", logs_root), \
                 patch("scripts.e2e_mvp_smoke.PROJECT_ROOT", self.project_root):
                report = run_e2e_smoke()
                smoke_report_path = Path(report["smoke_report_path"])
                self.assertTrue(smoke_report_path.exists())

        self.assertIn(report["status"], {"success", "partial_success", "failed"})
        self.assertEqual(report["tracked_stocks_count"], 45)
        self.assertEqual(report["industries_count"], 6)
        self.assertEqual(report["macro_topics_count"], 10)
        self.assertEqual(report["institution_watch_count"], 4)
        self.assertFalse(report["fake_no_news_events_found"])
        self.assertTrue(report["batch_all_ran"])
        self.assertTrue(report["ingestion_dry_run_ran"])
        self.assertTrue(report["promotion_dry_run_ran"])
        self.assertTrue(report["frontend_views_checked"])
        self.assertIn("smoke_report_path", report)

    def test_batch_all_runs_without_fake_no_news_event(self) -> None:
        with TemporaryDirectory() as tmpdir:
            output_root = Path(tmpdir) / "output"
            output_root.mkdir(parents=True, exist_ok=True)
            logs_root = output_root / "logs"
            with patch.object(batch_runner, "OUTPUT_ROOT", output_root), \
                 patch.object(batch_runner, "BATCH_LOGS_ROOT", logs_root), \
                 patch.object(coverage_report, "OUTPUT_ROOT", output_root), \
                 patch.object(coverage_report, "COVERAGE_LOGS_ROOT", logs_root):
                tasks = generate_batch_tasks("all", source_mode="mock", summarizer_mode="mock", search_provider="mock")
                summary = batch_runner.run_batch_tasks(tasks, batch_type="all")

        self.assertIn(summary["status"], {"success", "partial_success", "failed"})
        self.assertIn("coverage_report", summary)
        self.assertFalse(self._summary_has_fake_no_news(summary))

    def test_collector_task_skips_fake_no_news_packets(self) -> None:
        task = {
            "task_id": "stock_smoke_test",
            "run_mode": "daily",
            "scope": "stock",
            "scope_name": TRACKED_STOCKS[0]["stock_name"],
            "target_stock_code": TRACKED_STOCKS[0]["stock_code"],
            "target_stock_name": TRACKED_STOCKS[0]["stock_name"],
            "source_mode": "mock",
            "summarizer_mode": "mock",
            "llm_provider": "auto",
            "search_provider": "mock",
        }
        state = run_collector_task(task)
        self.assertIn(state["status"], {"success", "partial_success", "failed"})
        self.assertFalse(self._state_has_fake_no_news(state))

    @staticmethod
    def _summary_has_fake_no_news(summary: dict[str, object]) -> bool:
        output_files = summary.get("output_files", [])
        if not isinstance(output_files, list):
            return False
        for file_path in output_files:
            path = Path(str(file_path))
            if "no_news" in path.name.lower():
                return True
            if not path.exists() or not path.is_file():
                continue
            text = path.read_text(encoding="utf-8")
            if "今日未找到重大更新" in text or "無重大更新" in text:
                return True
        return False

    @staticmethod
    def _state_has_fake_no_news(state: dict[str, object]) -> bool:
        output_paths = state.get("output_paths", [])
        if not isinstance(output_paths, list):
            return False
        for file_path in output_paths:
            path = Path(str(file_path))
            if "no_news" in path.name.lower():
                return True
            if not path.exists() or not path.is_file():
                continue
            text = path.read_text(encoding="utf-8")
            if "今日未找到重大更新" in text or "無重大更新" in text:
                return True
        return False


if __name__ == "__main__":
    unittest.main()
