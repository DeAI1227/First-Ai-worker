import unittest
from pathlib import Path

from collector.graph import run_collector_task
from collector.tasks import make_task


class GraphFlowTests(unittest.TestCase):
    def test_graph_flow_writes_output_files(self):
        state = run_collector_task(
            make_task("industry", "散熱", stock_code="6230", stock_name="尼得科超眾")
        )
        self.assertEqual(state["validation_errors"], [])
        self.assertGreaterEqual(len(state["output_paths"]), 3)
        for path in state["output_paths"]:
            self.assertTrue(Path(path).exists(), path)


if __name__ == "__main__":
    unittest.main()
