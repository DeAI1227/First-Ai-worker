from __future__ import annotations

import unittest
from pathlib import Path


class FrontendQueryContractTests(unittest.TestCase):
    @property
    def project_root(self) -> Path:
        return Path(__file__).resolve().parents[1]

    def test_contract_file_exists(self) -> None:
        self.assertTrue((self.project_root / "supabase" / "frontend_query_contract.md").exists())

    def test_contract_lists_page_to_view_mapping(self) -> None:
        text = (self.project_root / "supabase" / "frontend_query_contract.md").read_text(encoding="utf-8")
        for needle in [
            "總覽頁 -> `view_dashboard_events`",
            "產業追蹤頁 -> `view_industry_cards`",
            "股票清單頁 -> `view_stock_cards`",
            "股票詳情頁 -> `view_stock_detail_events`",
            "大環境頁 -> `view_macro_events`",
            "大行關注頁 -> `view_institution_watch_events`",
            "研究報告頁 -> `view_recent_reports`",
            "未讀統計 -> `view_unread_counts`",
        ]:
            self.assertIn(needle, text)

    def test_contract_explains_reference_data_rules(self) -> None:
        text = (self.project_root / "supabase" / "frontend_query_contract.md").read_text(encoding="utf-8")
        for needle in [
            "`stocks` is reference data.",
            "`events` is actual event data.",
            "Stocks without events still exist in `stocks`.",
            "The backend must not generate fake \"today no major update\" events.",
        ]:
            self.assertIn(needle, text)


if __name__ == "__main__":
    unittest.main()
