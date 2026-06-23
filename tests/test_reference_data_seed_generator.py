from __future__ import annotations

import unittest
from pathlib import Path
from tempfile import TemporaryDirectory

from collector.config.tracking_universe import (
    INSTITUTION_WATCH_STOCKS,
    MACRO_TOPICS,
    STOCK_INDUSTRY_RELATIONS,
    TRACKED_STOCKS,
    TRACKING_INDUSTRIES,
)
from scripts.generate_reference_data_seed import build_seed_sql, write_seed_sql


class ReferenceDataSeedGeneratorTests(unittest.TestCase):
    def test_build_seed_sql_contains_all_required_sections(self) -> None:
        sql = build_seed_sql()
        self.assertIn("-- SECTION: industries", sql)
        self.assertIn("-- SECTION: stocks", sql)
        self.assertIn("-- SECTION: stock_industries", sql)
        self.assertIn("-- SECTION: macro_topics", sql)
        self.assertIn("-- SECTION: institution_watch_stocks", sql)

    def test_build_seed_sql_reflects_tracking_universe(self) -> None:
        sql = build_seed_sql()

        self.assertEqual(sql.count("insert into industries"), 1)
        self.assertEqual(sql.count("insert into stocks"), 1)
        self.assertEqual(sql.count("insert into stock_industries"), 1)
        self.assertEqual(sql.count("insert into macro_topics"), 1)
        self.assertEqual(sql.count("insert into institution_watch_stocks"), 1)

        for industry in TRACKING_INDUSTRIES:
            self.assertIn(industry["industry_id"], sql)
            self.assertIn(industry["industry_name"], sql)

        tracked_codes = {item["stock_code"] for item in TRACKED_STOCKS}
        watch_codes = {item["stock_code"] for item in INSTITUTION_WATCH_STOCKS}
        self.assertEqual(len(tracked_codes | watch_codes), 45)

        for relation in STOCK_INDUSTRY_RELATIONS:
            self.assertIn(relation["stock_code"], sql)
            self.assertIn(relation["industry_name"], sql)

        for topic in MACRO_TOPICS:
            self.assertIn(topic["topic_id"], sql)
            self.assertIn(topic["topic_name"], sql)

    def test_write_seed_sql_writes_file(self) -> None:
        with TemporaryDirectory() as tmpdir:
            output_path = Path(tmpdir) / "seed_reference_data.sql"
            result = write_seed_sql(output_path)
            self.assertEqual(result, output_path)
            self.assertTrue(output_path.exists())
            text = output_path.read_text(encoding="utf-8")
            self.assertIn("Production reference data seed", text)
            self.assertIn("insert into stocks", text)


if __name__ == "__main__":
    unittest.main()
