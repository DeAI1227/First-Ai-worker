from __future__ import annotations

import unittest

from collector.nodes.filter import filter_sources


class SourceFilterTests(unittest.TestCase):
    def test_filter_sources_deduplicates_by_source_url(self):
        state = {
            "raw_sources": [
                {
                    "title": "AI 伺服器散熱需求升溫",
                    "source_name": "RSS A",
                    "source_url": "https://example.com/a",
                    "published_at": "",
                    "content": "散熱內容",
                    "source_type": "rss",
                },
                {
                    "title": "AI 伺服器散熱需求升溫",
                    "source_name": "RSS A",
                    "source_url": "https://example.com/a",
                    "published_at": "",
                    "content": "散熱內容",
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
                    "title": "飆股喊單",
                    "source_name": "Bad Feed",
                    "source_url": "https://example.com/bad",
                    "published_at": "",
                    "content": "買進 目標價 漲停",
                    "source_type": "rss",
                }
            ]
        }
        filtered_state = filter_sources(state)
        self.assertEqual(filtered_state["filtered_sources"], [])


if __name__ == "__main__":
    unittest.main()
