from __future__ import annotations

import subprocess
import sys
import unittest
from tempfile import TemporaryDirectory
from pathlib import Path

from collector.batch_runner import build_batch_summary, write_batch_summary
from collector.nodes.writer import scope_output_dir
from collector.task_batches import generate_batch_tasks
from collector.tasks import make_task


class BatchRegistryCliTests(unittest.TestCase):
    @property
    def project_root(self) -> Path:
        return Path(__file__).resolve().parents[1]

    def test_generate_batch_tasks_returns_all_slices(self) -> None:
        tasks = generate_batch_tasks("all")
        scopes = {task["scope"] for task in tasks}
        self.assertTrue({"macro", "industry", "stock", "institution_watch"}.issubset(scopes))
        self.assertGreater(len(tasks), 20)

    def test_generate_batch_tasks_includes_sample_and_real_targets(self) -> None:
        tasks = generate_batch_tasks("stocks")
        stock_codes = {task.get("target_stock_code", "") for task in tasks if task.get("target_stock_code")}
        institution_tasks = generate_batch_tasks("institution_watch")
        self.assertIn("6230", stock_codes)
        self.assertIn("3227", stock_codes)
        self.assertTrue(any(task.get("target_stock_code") == "3665" for task in institution_tasks))

    def test_main_batch_industries_cli_runs(self) -> None:
        result = subprocess.run(
            [sys.executable, "main.py", "--batch", "industries"],
            cwd=self.project_root,
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="ignore",
        )
        self.assertEqual(result.returncode, 0, msg=result.stderr)

    def test_main_batch_all_cli_runs(self) -> None:
        result = subprocess.run(
            [sys.executable, "main.py", "--batch", "all"],
            cwd=self.project_root,
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="ignore",
        )
        self.assertEqual(result.returncode, 0, msg=result.stderr)

    def test_stock_scope_uses_dedicated_output_dir(self) -> None:
        task = make_task("stock", "台積電", stock_code="2330", stock_name="台積電")
        path = scope_output_dir(task)
        self.assertIn("daily", str(path))
        self.assertIn("stocks", str(path))
        self.assertIn("2330_台積電", str(path))

    def test_batch_summary_can_be_written(self) -> None:
        summary = build_batch_summary(
            batch_id="batch_20260617_172226",
            batch_type="all",
            started_at="2026-06-17T17:22:26+08:00",
            finished_at="2026-06-17T17:22:27+08:00",
            tasks=[{"status": "success"}, {"status": "failed"}, {"status": "partial_success"}],
            output_files=["output/daily/散熱/event.json"],
            run_errors=["boom"],
        )
        self.assertEqual(summary["total_tasks"], 3)
        self.assertEqual(summary["success_tasks"], 1)
        self.assertEqual(summary["partial_success_tasks"], 1)
        self.assertEqual(summary["failed_tasks"], 1)
        self.assertEqual(summary["batch_type"], "all")
        self.assertEqual(summary["output_files"], ["output/daily/散熱/event.json"])

        with TemporaryDirectory() as tmpdir:
            path = write_batch_summary(
                summary | {"finished_at": "2026-06-17T17:22:27+08:00"},
                output_root=Path(tmpdir),
            )
            self.assertTrue(path.startswith(tmpdir))
            self.assertTrue(path.endswith(".json"))


if __name__ == "__main__":
    unittest.main()
