from __future__ import annotations

import unittest
from unittest.mock import patch

from collector.config.tracking_universe import TRACKING_INDUSTRIES
from scripts.github_daily_pipeline import (
    DEFAULT_COLLECT_BATCHES,
    build_collect_batch_payload,
    build_pipeline_steps,
    should_exit_successfully,
    run_local_pipeline_steps,
)


class GitHubDailyPipelineTests(unittest.TestCase):
    def test_pipeline_steps_are_grouped_not_per_stock(self) -> None:
        steps = build_pipeline_steps(include_three_day=True)
        enabled_industries = [industry for industry in TRACKING_INDUSTRIES if industry.get("enabled", True)]

        expected_total = len(DEFAULT_COLLECT_BATCHES) + len(enabled_industries) + 1 + 2
        self.assertEqual(len(steps), expected_total)

        collect_batch_steps = [step for step in steps if step.name.startswith("collect:") and ":three_day:" not in step.name]
        self.assertEqual([step.name for step in collect_batch_steps], [f"collect:{batch}" for batch in DEFAULT_COLLECT_BATCHES])

    def test_pipeline_ends_with_single_write_pass(self) -> None:
        steps = build_pipeline_steps(include_three_day=True)
        self.assertEqual(steps[-2].name, "ingestion:write")
        self.assertEqual(steps[-2].endpoint, "/ingestion/run")
        self.assertEqual(steps[-1].name, "promotion:write")
        self.assertEqual(steps[-1].endpoint, "/promotion/run")

    def test_collect_batches_target_collect_endpoint(self) -> None:
        steps = build_pipeline_steps(include_three_day=False)
        for step in steps[:-2]:
            self.assertEqual(step.endpoint, "/collect/run")
            self.assertIn(step.payload.get("batch"), DEFAULT_COLLECT_BATCHES)

    def test_collect_batch_payload_uses_write_ready_settings(self) -> None:
        payload = build_collect_batch_payload("stocks")
        self.assertEqual(payload["mode"], "daily")
        self.assertEqual(payload["batch"], "stocks")
        self.assertFalse(payload["dry_run"])
        self.assertEqual(payload["search_provider"], "firecrawl")

    def test_local_runner_dispatches_collect_ingestion_and_promotion_without_http(self) -> None:
        collect_result = {
            "status": "success",
            "message": "collect ok",
            "output_files": ["collect.json"],
            "run_errors": [],
            "batch_report": {},
        }
        ingestion_result = {
            "status": "success",
            "mode": "write",
            "message": "ingestion ok",
            "output_files": ["ingestion.json"],
            "run_errors": [],
            "wrote_to_supabase": True,
        }
        promotion_result = {
            "status": "success",
            "mode": "write",
            "message": "promotion ok",
            "output_files": ["promotion.json"],
            "run_errors": [],
            "wrote_to_supabase": True,
        }

        steps = build_pipeline_steps(include_three_day=False)

        with patch("scripts.github_daily_pipeline.run_collect_sync", return_value=collect_result) as collect_mock, patch(
            "scripts.github_daily_pipeline.run_ingestion_sync", return_value=ingestion_result
        ) as ingestion_mock, patch(
            "scripts.github_daily_pipeline.run_promotion_sync", return_value=promotion_result
        ) as promotion_mock:
            results = run_local_pipeline_steps(steps)

        self.assertEqual(len(results), len(steps))
        self.assertEqual(collect_mock.call_count, len(DEFAULT_COLLECT_BATCHES))
        ingestion_mock.assert_called_once()
        promotion_mock.assert_called_once()
        self.assertTrue(all(result["status"] == "success" for result in results))

    def test_partial_success_with_outputs_is_not_treated_as_workflow_failure(self) -> None:
        summary = {
            "status": "partial_success",
            "wrote_to_supabase": True,
            "output_files": ["output/logs/pipeline_run.json"],
            "success_steps": 2,
            "partial_success_steps": 1,
            "failed_steps": 0,
            "steps": [],
        }

        self.assertTrue(should_exit_successfully(summary))


if __name__ == "__main__":
    unittest.main()
