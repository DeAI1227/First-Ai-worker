from __future__ import annotations

import unittest

from collector.sources.stock_entrypoints import (
    build_stock_source_rules,
    build_taiwan_stock_news_url,
    build_taiwan_stock_news_urls,
)


class StockEntrypointTests(unittest.TestCase):
    def test_build_taiwan_stock_news_url_uses_yahoo_format(self) -> None:
        self.assertEqual(
            build_taiwan_stock_news_url("2330"),
            "https://tw.stock.yahoo.com/quote/2330.TW/news",
        )

    def test_build_stock_source_rules_includes_yahoo_only(self) -> None:
        rules = build_stock_source_rules("2330", "???")

        self.assertEqual(len(rules), 1)
        self.assertEqual(rules[0]["kind"], "yahoo_stock_news")
        self.assertEqual(rules[0]["url"], "https://tw.stock.yahoo.com/quote/2330.TW/news")
        self.assertNotIn("cnyes", rules[0]["kind"])

    def test_build_taiwan_stock_news_urls_cover_all_tracked_and_watchlist_stocks(self) -> None:
        urls = build_taiwan_stock_news_urls()

        self.assertEqual(len(urls), 45)
        self.assertEqual(len(urls), len(set(urls)))
        self.assertIn("https://tw.stock.yahoo.com/quote/2330.TW/news", urls)
        self.assertIn("https://tw.stock.yahoo.com/quote/3665.TW/news", urls)


if __name__ == "__main__":
    unittest.main()
