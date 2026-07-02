from __future__ import annotations

import unittest

from collector.nodes.filter import filter_sources


class SourceFilterTests(unittest.TestCase):
    def test_filter_sources_deduplicates_by_source_url(self):
        state = {
            "raw_sources": [
                {
                    "title": "??????",
                    "source_name": "RSS A",
                    "source_url": "https://example.com/a",
                    "published_at": "",
                    "content": "???????",
                    "source_type": "rss",
                },
                {
                    "title": "??????",
                    "source_name": "RSS A",
                    "source_url": "https://example.com/a",
                    "published_at": "",
                    "content": "???????",
                    "source_type": "rss",
                },
            ]
        }
        filtered_state = filter_sources(state)
        self.assertEqual(len(filtered_state["filtered_sources"]), 1)

    def test_filter_sources_blocks_prohibited_words(self):
        state = {
            "raw_sources": [
                {
                    "title": "買進建議",
                    "source_name": "Bad Feed",
                    "source_url": "https://example.com/bad",
                    "published_at": "",
                    "content": "法人建議買進，並給出目標價與報酬率。",
                    "source_type": "rss",
                }
            ]
        }
        filtered_state = filter_sources(state)
        self.assertEqual(filtered_state["filtered_sources"], [])

    def test_filter_sources_blocks_quote_style_bulletins_without_stock_context(self):
        state = {
            "scope": "macro",
            "scope_name": "???",
            "raw_sources": [
                {
                    "title": "?????? 2330 ?? 7.01%",
                    "source_name": "Yahoo Finance",
                    "source_url": "https://example.com/quote-bulletin",
                    "published_at": "2026-06-25T10:00:00+08:00",
                    "content": "????????????????????????????",
                    "source_type": "search",
                }
            ],
        }
        filtered_state = filter_sources(state)
        self.assertEqual(filtered_state["filtered_sources"], [])

    def test_filter_sources_allows_yahoo_stock_articles_that_mention_target_stock(self):
        state = {
            "scope": "stock",
            "scope_name": "???",
            "target_stock_code": "2330",
            "target_stock_name": "???",
            "raw_sources": [
                {
                    "title": "台積電最新動態",
                    "source_name": "Yahoo News",
                    "source_url": "https://tw.stock.yahoo.com/news/tsmc-expansion-1.html",
                    "published_at": "2026-06-24T08:00:00+08:00",
                    "content": "這篇正文提到 2330 台積電 的擴產與供應鏈調整。",
                    "source_type": "http",
                }
            ],
        }
        filtered_state = filter_sources(state)
        self.assertEqual(len(filtered_state["filtered_sources"]), 1)
        self.assertEqual(filtered_state["filtered_sources"][0]["source_url"], "https://tw.stock.yahoo.com/news/tsmc-expansion-1.html")

    def test_filter_sources_blocks_stock_scope_articles_without_target_match(self):
        state = {
            "scope": "stock",
            "scope_name": "???",
            "target_stock_code": "2330",
            "target_stock_name": "???",
            "raw_sources": [
                {
                    "title": "AI thermal supply chain update",
                    "source_name": "Generic News",
                    "source_url": "https://example.com/thermal-supply-chain",
                    "published_at": "2026-06-24T08:00:00+08:00",
                    "content": "Data center cooling trends and supply chain updates without mentioning the target company.",
                    "source_type": "http",
                }
            ],
        }
        filtered_state = filter_sources(state)
        self.assertEqual(filtered_state["filtered_sources"], [])
        self.assertEqual(len(filtered_state["rejected_sources"]), 1)
        self.assertIn("missing target stock match", " ".join(filtered_state["rejected_sources"][0]["quality_reasons"]))


if __name__ == "__main__":
    unittest.main()
