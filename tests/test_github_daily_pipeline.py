from __future__ import annotations

import unittest

from scripts.github_daily_pipeline import build_pipeline_steps


class GitHubDailyPipelineTests(unittest.TestCase):
    def test_daily_core_segment_contains_expected_steps(self) -> None:
        steps = build_pipeline_steps(
            daily_batches=("macro", "industries", "institution_watch"),
            include_three_day_industries=False,
            include_three_day_macro=False,
        )
        self.assertEqual(
            [step.name for step in steps],
            [
                "collect:macro",
                "collect:industries",
                "collect:institution_watch",
                "ingestion:write",
                "promotion:write",
            ],
        )

    def test_stock_segment_contains_only_stock_plus_write_steps(self) -> None:
        steps = build_pipeline_steps(
            daily_batches=("stocks",),
            include_three_day_industries=False,
            include_three_day_macro=False,
        )
        self.assertEqual(
            [step.name for step in steps],
            [
                "collect:stocks",
                "ingestion:write",
                "promotion:write",
            ],
        )

    def test_three_day_segment_contains_reports_plus_write_steps(self) -> None:
        steps = build_pipeline_steps(
            daily_batches=(),
            include_three_day_industries=True,
            include_three_day_macro=True,
        )
        names = [step.name for step in steps]
        self.assertIn("collect:three_day:macro:macro_environment", names)
        self.assertIn("ingestion:write", names)
        self.assertIn("promotion:write", names)
        self.assertTrue(any(name.startswith("collect:three_day:industry:") for name in names))
        self.assertEqual(names[-2:], ["ingestion:write", "promotion:write"])


if __name__ == "__main__":
    unittest.main()
