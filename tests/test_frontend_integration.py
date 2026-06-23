from __future__ import annotations

import unittest
from pathlib import Path


class FrontendIntegrationTests(unittest.TestCase):
    @property
    def project_root(self) -> Path:
        return Path(__file__).resolve().parents[1]

    def test_frontend_integration_folder_exists(self) -> None:
        self.assertTrue((self.project_root / "frontend_integration").exists())

    def test_required_files_exist(self) -> None:
        folder = self.project_root / "frontend_integration"
        self.assertTrue((folder / "README.md").exists())
        self.assertTrue((folder / "supabase_views_contract.md").exists())
        self.assertTrue((folder / "supabase_query_examples.md").exists())
        self.assertTrue((folder / "types.ts").exists())

    def test_readme_mentions_supabase_only_frontend(self) -> None:
        readme_text = (self.project_root / "frontend_integration" / "README.md").read_text(encoding="utf-8")
        self.assertIn("future Supabase-only frontend", readme_text)
        self.assertIn("production views only", readme_text)
        self.assertIn("not a way to read `output/` JSON from the UI", readme_text)

    def test_types_file_contains_stock_card(self) -> None:
        types_text = (self.project_root / "frontend_integration" / "types.ts").read_text(encoding="utf-8")
        self.assertIn("export type StockCard", types_text)
        self.assertIn("export type DashboardEvent", types_text)
        self.assertIn("export type ReadStatus", types_text)

    def test_contract_mentions_stock_cards_and_no_fake_events(self) -> None:
        contract_text = (self.project_root / "frontend_integration" / "supabase_views_contract.md").read_text(encoding="utf-8")
        self.assertIn("股票清單頁 -> `view_stock_cards`", contract_text)
        self.assertIn("Do not generate fake no-news events.", contract_text)

    def test_query_examples_include_read_updates(self) -> None:
        query_text = (self.project_root / "frontend_integration" / "supabase_query_examples.md").read_text(encoding="utf-8")
        self.assertIn('from("view_stock_cards")', query_text)
        self.assertIn('from("user_read_status").upsert', query_text)


if __name__ == "__main__":
    unittest.main()
