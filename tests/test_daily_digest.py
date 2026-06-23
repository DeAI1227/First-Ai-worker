import unittest

from collector.graph import run_collector_task
from collector.tasks import make_task


class DailyDigestTests(unittest.TestCase):
    def test_daily_digest_and_crawl_run_are_built(self):
        state = run_collector_task(make_task("macro", "大環境"))
        self.assertEqual(state["daily_digest_packet"]["packet_type"], "daily_digest")
        self.assertEqual(state["crawl_run_packet"]["packet_type"], "crawl_run")
        self.assertIn(state["crawl_run_packet"]["status"], ["success", "partial_success"])


if __name__ == "__main__":
    unittest.main()
