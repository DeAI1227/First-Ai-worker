from __future__ import annotations

import unittest

from collector.sources.stock_entrypoints import (
    build_cnyes_category_rules,
    build_mops_lookup_rule,
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

    def test_build_stock_source_rules_includes_yahoo_and_mops(self) -> None:
        rules = build_stock_source_rules("2330", "台積電")

        self.assertEqual(len(rules), 2)
        self.assertEqual(rules[0]["kind"], "yahoo_stock_news")
        self.assertEqual(rules[0]["url"], "https://tw.stock.yahoo.com/quote/2330.TW/news")
        self.assertEqual(rules[1]["kind"], "mops_company_lookup")
        self.assertEqual(rules[1]["url"], "https://mops.twse.com.tw/mops/web/t146sb05")
        self.assertEqual(rules[1]["stock_code"], "2330")

    def test_build_cnyes_category_rules_returns_expected_urls(self) -> None:
        macro_rules = build_cnyes_category_rules("macro", "FED 利率")
        stock_rules = build_cnyes_category_rules("stock", "台積電")

        self.assertEqual(len(macro_rules), 1)
        self.assertEqual(macro_rules[0]["kind"], "cnyes_category_news")
        self.assertEqual(macro_rules[0]["url"], "https://news.cnyes.com/news/cat/wd_macro")
        self.assertEqual(macro_rules[0]["source_key"], "macro")

        self.assertEqual(len(stock_rules), 4)
        self.assertTrue(all(rule["kind"] == "cnyes_category_news" for rule in stock_rules))
        self.assertEqual(stock_rules[0]["url"], "https://news.cnyes.com/news/cat/tw_quo")
        self.assertEqual(stock_rules[1]["url"], "https://news.cnyes.com/news/cat/stock_report")
        self.assertEqual(stock_rules[2]["url"], "https://news.cnyes.com/news/cat/tw_revenue")
        self.assertEqual(stock_rules[3]["url"], "https://news.cnyes.com/news/cat/wd_stock")

    def test_build_taiwan_stock_news_urls_cover_all_tracked_and_watchlist_stocks(self) -> None:
        urls = build_taiwan_stock_news_urls()

        self.assertEqual(len(urls), 45)
        self.assertEqual(len(urls), len(set(urls)))
        self.assertIn("https://tw.stock.yahoo.com/quote/2330.TW/news", urls)
        self.assertIn("https://tw.stock.yahoo.com/quote/3665.TW/news", urls)

    def test_build_mops_lookup_rule_keeps_query_metadata(self) -> None:
        rule = build_mops_lookup_rule("3665", "貿聯-KY")

        self.assertEqual(rule["kind"], "mops_company_lookup")
        self.assertEqual(rule["stock_code"], "3665")
        self.assertEqual(rule["stock_name"], "貿聯-KY")
        self.assertEqual(rule["query_field"], "公司代號")
        self.assertEqual(rule["query_value"], "3665")


    def test_build_cnyes_rules_can_cover_stock_like_scopes(self) -> None:
        rules = build_cnyes_category_rules("institution", "????")

        self.assertEqual(len(rules), 2)
        self.assertTrue(all(rule["kind"] == "cnyes_category_news" for rule in rules))
        self.assertEqual(rules[0]["source_key"], "institution")
        self.assertEqual(rules[0]["url"], "https://news.cnyes.com/news/cat/wd_stock")


if __name__ == "__main__":
    unittest.main()
