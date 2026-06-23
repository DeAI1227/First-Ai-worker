from __future__ import annotations

import json
import unittest
from pathlib import Path


class FrontendAppScaffoldTests(unittest.TestCase):
    @property
    def project_root(self) -> Path:
        return Path(__file__).resolve().parents[1]

    @property
    def frontend_root(self) -> Path:
        return self.project_root / "frontend"

    def test_frontend_project_files_exist(self) -> None:
        self.assertTrue(self.frontend_root.exists())
        self.assertTrue((self.frontend_root / "package.json").exists())
        self.assertTrue((self.frontend_root / "README.md").exists())
        self.assertTrue((self.frontend_root / "src" / "App.tsx").exists())
        self.assertTrue((self.frontend_root / "src" / "main.tsx").exists())
        self.assertTrue((self.frontend_root / "src" / "lib" / "queries.ts").exists())
        self.assertTrue((self.frontend_root / "src" / "pages" / "DashboardPage.tsx").exists())
        self.assertTrue((self.frontend_root / "src" / "pages" / "StocksPage.tsx").exists())
        self.assertTrue((self.frontend_root / "src" / "pages" / "StockDetailPage.tsx").exists())

    def test_package_json_has_expected_dependencies(self) -> None:
        package_json = json.loads((self.frontend_root / "package.json").read_text(encoding="utf-8"))
        dependencies = package_json["dependencies"]
        self.assertIn("@supabase/supabase-js", dependencies)
        self.assertIn("react", dependencies)
        self.assertIn("react-router-dom", dependencies)
        self.assertIn("lucide-react", dependencies)

    def test_readme_mentions_supabase_only_and_chinese_ui(self) -> None:
        readme = (self.frontend_root / "README.md").read_text(encoding="utf-8")
        self.assertIn("Supabase-first", readme)
        self.assertIn("production views", readme)
        self.assertIn("前端不讀 Python 程式", readme)
        self.assertIn("股票清單頁", readme)

    def test_queries_file_mentions_expected_views(self) -> None:
        query_text = (self.frontend_root / "src" / "lib" / "queries.ts").read_text(encoding="utf-8")
        self.assertIn('view_dashboard_events', query_text)
        self.assertIn('view_industry_cards', query_text)
        self.assertIn('view_stock_cards', query_text)
        self.assertIn('view_stock_detail_events', query_text)
        self.assertIn('view_macro_events', query_text)
        self.assertIn('view_institution_watch_events', query_text)
        self.assertIn('view_recent_reports', query_text)
        self.assertIn('view_unread_counts', query_text)


if __name__ == "__main__":
    unittest.main()

