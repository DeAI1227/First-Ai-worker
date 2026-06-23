from __future__ import annotations

import unittest
from pathlib import Path


class FrontendSupabaseWiringTests(unittest.TestCase):
    @property
    def project_root(self) -> Path:
        return Path(__file__).resolve().parents[1]

    def test_frontend_wiring_files_exist(self) -> None:
        folder = self.project_root / "frontend_integration" / "src"
        self.assertTrue((folder / "supabaseClient.ts").exists())
        self.assertTrue((folder / "queries.ts").exists())
        self.assertTrue((folder / "readStatus.ts").exists())

    def test_queries_file_uses_expected_views(self) -> None:
        query_text = (self.project_root / "frontend_integration" / "src" / "queries.ts").read_text(encoding="utf-8")
        self.assertIn('from("view_dashboard_events")', query_text)
        self.assertIn('from("view_industry_cards")', query_text)
        self.assertIn('from("view_stock_cards")', query_text)
        self.assertIn('from("view_stock_detail_events")', query_text)
        self.assertIn('from("view_macro_events")', query_text)
        self.assertIn('from("view_institution_watch_events")', query_text)
        self.assertIn('from("view_recent_reports")', query_text)
        self.assertIn('from("view_unread_counts")', query_text)

    def test_read_status_file_uses_user_read_status(self) -> None:
        read_text = (self.project_root / "frontend_integration" / "src" / "readStatus.ts").read_text(encoding="utf-8")
        self.assertIn('from("user_read_status")', read_text)
        self.assertIn('item_type: "event"', read_text)
        self.assertIn('item_type: "report"', read_text)

    def test_contract_mentions_no_fake_no_news_event(self) -> None:
        contract_text = (self.project_root / "frontend_integration" / "supabase_views_contract.md").read_text(encoding="utf-8")
        self.assertIn("Do not generate fake no-news events.", contract_text)


if __name__ == "__main__":
    unittest.main()
