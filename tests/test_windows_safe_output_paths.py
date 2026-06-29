from __future__ import annotations

import unittest

from collector.nodes.writer import scope_output_dir
from collector.tasks import make_task


class WindowsSafeOutputPathTests(unittest.TestCase):
    def test_stock_scope_output_dir_uses_safe_segment(self) -> None:
        task = make_task(
            scope="stock",
            scope_name="\u53f0\u7a4d\u96fb",
            stock_code="2330",
            stock_name="\u53f0\u7a4d\u96fb",
        )
        path = scope_output_dir(task)
        self.assertIn("2330_\u53f0\u7a4d\u96fb", str(path))
        self.assertFalse(any(char in path.name for char in '<>:"/\\\\|?*'))

    def test_stock_scope_output_dir_falls_back_for_invalid_name(self) -> None:
        task = make_task(
            scope="stock",
            scope_name="???",
            stock_code="2330",
            stock_name="???",
        )
        path = scope_output_dir(task)
        self.assertIn("2330_unknown", str(path))
        self.assertFalse(any(char in path.name for char in '<>:"/\\\\|?*'))


if __name__ == "__main__":
    unittest.main()
