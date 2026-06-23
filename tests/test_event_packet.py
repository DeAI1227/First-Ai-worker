import unittest

from collector.graph import run_collector_task
from collector.tasks import make_task


class EventPacketTests(unittest.TestCase):
    def test_industry_task_can_build_event_packet(self):
        state = run_collector_task(
            make_task("industry", "散熱", stock_code="6230", stock_name="尼得科超眾")
        )
        self.assertEqual(state["event_packet"]["packet_type"], "event")
        self.assertEqual(state["event_packet"]["collector"], "langgraph")

    def test_macro_task_can_build_event_packet(self):
        state = run_collector_task(make_task("macro", "大環境"))
        self.assertEqual(state["event_packet"]["event_type"], "macro")
        self.assertEqual(state["event_packet"]["language"], "zh-TW")


if __name__ == "__main__":
    unittest.main()
