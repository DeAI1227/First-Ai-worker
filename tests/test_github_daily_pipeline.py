from __future__ import annotations

import unittest

from collector.config.tracking_universe import TRACKING_INDUSTRIES
from scripts.github_daily_pipeline import (
    DEFAULT_COLLECT_BATCHES,
    build_collect_batch_payload,
    build_pipeline_steps,
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


if __name__ == "__main__":
    unittest.main()
