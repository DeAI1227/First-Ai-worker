import unittest

from collector.graph import run_collector_task
from collector.tasks import make_task


class IndustryStockSeparationTests(unittest.TestCase):
    def test_industry_related_fields_are_separated(self):
        state = run_collector_task(
            make_task("industry", "散熱", stock_code="6230", stock_name="尼得科超眾")
        )
        packet = state["event_packet"]
        self.assertEqual(packet["related_industries"], ["散熱"])
        self.assertEqual(packet["related_stocks"], ["6230"])
        self.assertEqual(state["validation_errors"], [])


if __name__ == "__main__":
    unittest.main()
