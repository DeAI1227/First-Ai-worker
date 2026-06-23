from __future__ import annotations

import re
import unittest
from pathlib import Path

from collector.config.tracking_universe import (
    INSTITUTION_WATCH_STOCKS,
    MACRO_TOPICS,
    STOCK_INDUSTRY_RELATIONS,
    TRACKED_STOCKS,
    TRACKING_INDUSTRIES,
)


class ReferenceDataSeedTests(unittest.TestCase):
    @property
    def project_root(self) -> Path:
        return Path(__file__).resolve().parents[1]

    @property
    def seed_path(self) -> Path:
        return self.project_root / "supabase" / "seed_reference_data.sql"

    def _section(self, name: str, next_name: str | None = None) -> str:
        text = self.seed_path.read_text(encoding="utf-8")
        start_marker = f"-- SECTION: {name}"
        start = text.index(start_marker)
        end = text.index(f"-- SECTION: {next_name}") if next_name else len(text)
        return text[start:end]

    def test_seed_file_exists(self) -> None:
        self.assertTrue(self.seed_path.exists())

    def test_reference_data_readme_exists(self) -> None:
        self.assertTrue((self.project_root / "supabase" / "reference_data_readme.md").exists())

    def test_seed_includes_six_industries(self) -> None:
        section = self._section("industries", "stocks")
        rows = re.findall(r"^\s*\(", section, flags=re.MULTILINE)
        self.assertEqual(len(rows), len(TRACKING_INDUSTRIES))
        self.assertEqual(len(rows), 6)

    def test_seed_includes_forty_five_unique_stocks(self) -> None:
        section = self._section("stocks", "stock_industries")
        codes = re.findall(r"\('(\d{4})',", section)
        expected_codes = sorted({stock["stock_code"] for stock in TRACKED_STOCKS} | {stock["stock_code"] for stock in INSTITUTION_WATCH_STOCKS})
        self.assertEqual(sorted(codes), expected_codes)
        self.assertEqual(len(codes), 45)

    def test_3227_appears_once_in_stocks_and_has_two_relations(self) -> None:
        stocks_section = self._section("stocks", "stock_industries")
        relations_section = self._section("stock_industries", "macro_topics")

        self.assertEqual(stocks_section.count("('3227',"), 1)
        self.assertEqual(relations_section.count("('3227', '自動駕駛')"), 1)
        self.assertEqual(relations_section.count("('3227', '機器人')"), 1)

    def test_seed_includes_institution_watch_stocks(self) -> None:
        section = self._section("institution_watch_stocks", None)
        for code in ("3665", "2330", "2454", "2308"):
            self.assertIn(f"('{code}',", section)

    def test_seed_includes_macro_topics(self) -> None:
        section = self._section("macro_topics", "institution_watch_stocks")
        rows = re.findall(r"^\s*\(", section, flags=re.MULTILINE)
        self.assertEqual(len(rows), len(MACRO_TOPICS))
        self.assertEqual(len(rows), 10)

    def test_stock_industries_match_tracking_universe_relations(self) -> None:
        section = self._section("stock_industries", "macro_topics")
        for relation in STOCK_INDUSTRY_RELATIONS:
            stock_code = relation["stock_code"]
            industry_name = relation["industry_name"]
            self.assertIn(f"('{stock_code}', '{industry_name}')", section)


if __name__ == "__main__":
    unittest.main()
