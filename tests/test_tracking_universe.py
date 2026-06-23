from __future__ import annotations

import unittest

from collector.task_batches import generate_batch_tasks
from collector.tasks import default_tasks, make_task
from collector.tracking_universe import resolve_tracking_source_key


class TrackingUniverseTests(unittest.TestCase):
    def test_generate_batch_tasks_includes_multiple_slices(self) -> None:
        tasks = generate_batch_tasks()
        scopes = {task["scope"] for task in tasks}
        stock_codes = {task.get("target_stock_code", "") for task in tasks if task.get("target_stock_code")}
        macro_topic_keys = {task.get("macro_topic_key", "") for task in tasks if task["scope"] == "macro"}

        self.assertIn("macro", scopes)
        self.assertIn("industry", scopes)
        self.assertIn("stock", scopes)
        self.assertIn("institution_watch", scopes)
        self.assertIn("6230", stock_codes)
        self.assertIn("1513", stock_codes)
        self.assertIn("3227", stock_codes)
        self.assertIn("3665", stock_codes)
        self.assertGreater(len(tasks), 20)
        self.assertIn("fed_rate", macro_topic_keys)
        self.assertIn("us_cpi", macro_topic_keys)

    def test_generate_batch_tasks_keeps_6230_as_sample_not_only_target(self) -> None:
        tasks = generate_batch_tasks()
        thermal_tasks = [task for task in tasks if task["scope"] == "industry" and task["scope_name"] == "散熱"]

        self.assertTrue(any(task.get("target_stock_code") == "6230" for task in thermal_tasks))
        self.assertTrue(any(task.get("target_stock_code") != "6230" for task in tasks if task.get("target_stock_code")))

    def test_resolve_tracking_source_key_maps_industries(self) -> None:
        self.assertEqual(resolve_tracking_source_key("macro", "FED 利率"), "macro")
        self.assertEqual(resolve_tracking_source_key("industry", "散熱"), "thermal")
        self.assertEqual(resolve_tracking_source_key("industry", "電力"), "power")
        self.assertEqual(resolve_tracking_source_key("industry", "自動駕駛"), "autodrive")
        self.assertEqual(resolve_tracking_source_key("industry", "機器人"), "robot")
        self.assertEqual(resolve_tracking_source_key("industry", "CPO 光通訊"), "cpo")
        self.assertEqual(resolve_tracking_source_key("industry", "網通"), "networking")
        self.assertEqual(resolve_tracking_source_key("stock", "台積電"), "stock")
        self.assertEqual(resolve_tracking_source_key("institution", "大行關注"), "institution")
        self.assertEqual(resolve_tracking_source_key("institution_watch", "大行關注"), "institution")

    def test_default_tasks_uses_batch_generation(self) -> None:
        tasks = default_tasks()
        self.assertGreater(len(tasks), 20)

    def test_daily_coverage_targets_are_41_stocks_plus_4_institution_watch(self) -> None:
        from collector.config.tracking_universe import INSTITUTION_WATCH_STOCKS

        self.assertEqual(len(generate_batch_tasks("stocks")), 41)
        self.assertEqual(len(INSTITUTION_WATCH_STOCKS), 4)
        self.assertEqual(len(generate_batch_tasks("stocks")) + len(INSTITUTION_WATCH_STOCKS), 45)

    def test_make_task_can_accept_search_keywords(self) -> None:
        task = make_task("macro", "FED 利率", search_keywords=["聯準會", "CPI"])
        self.assertEqual(task["search_keywords"], ["聯準會", "CPI"])


if __name__ == "__main__":
    unittest.main()
