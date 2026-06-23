from __future__ import annotations

import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from collector.graph import run_collector_task
from collector.nodes import writer
from collector.nodes.fetcher import mock_fetcher, rss_fetcher
from collector.sources import fetch_raw_sources, fetch_rss_sources
from collector.sources import registry as source_registry
from collector.sources import rss_fetcher as rss_module
from collector.tasks import make_task


FAKE_RSS_XML = """<?xml version="1.0" encoding="UTF-8"?>
<rss version="2.0">
  <channel>
    <title>Thermal News Feed</title>
    <item>
      <title>AI 伺服器散熱需求升溫</title>
      <link>https://example.com/articles/thermal-1</link>
      <pubDate>Tue, 16 Jun 2026 08:00:00 GMT</pubDate>
      <description>散熱、水冷與液冷方案仍是伺服器供應鏈關注焦點。</description>
    </item>
  </channel>
</rss>
"""


class RSSFetcherTests(unittest.TestCase):
    def setUp(self) -> None:
        self.tmp = tempfile.TemporaryDirectory()
        self.output_root = Path(self.tmp.name) / "output"
        self.writer_patch = patch.object(writer, "OUTPUT_ROOT", self.output_root)
        self.writer_patch.start()

    def tearDown(self) -> None:
        self.writer_patch.stop()
        self.tmp.cleanup()

    def test_mock_fetcher_returns_raw_sources(self):
        task = make_task(scope="industry", scope_name="散熱", stock_code="6230", stock_name="尼得科超眾")
        raw_sources = mock_fetcher(task)
        self.assertGreater(len(raw_sources), 0)
        item = raw_sources[0]
        self.assertEqual(item["source_type"], "mock")
        self.assertTrue(item["title"])
        self.assertTrue(item["source_url"])
        self.assertTrue(item["content"])

    def test_rss_fetcher_parses_fake_rss_xml(self):
        task = make_task(scope="industry", scope_name="散熱", stock_code="6230", stock_name="尼得科超眾", source_mode="rss")
        state = {
            "rss_feed_documents": {"https://example.com/rss": FAKE_RSS_XML},
            "rss_feeds": [{"source_name": "Thermal Feed", "feed_url": "https://example.com/rss"}],
        }
        with patch.object(rss_module, "feedparser", None):
            raw_sources = fetch_rss_sources(task, state)

        self.assertEqual(len(raw_sources), 1)
        item = raw_sources[0]
        self.assertEqual(item["title"], "AI 伺服器散熱需求升溫")
        self.assertEqual(item["source_name"], "Thermal News Feed")
        self.assertEqual(item["source_url"], "https://example.com/articles/thermal-1")
        self.assertEqual(item["content"], "散熱、水冷與液冷方案仍是伺服器供應鏈關注焦點。")
        self.assertEqual(item["source_type"], "rss")
        self.assertTrue(item["published_at"])

    def test_rss_failure_does_not_crash_graph(self):
        task = make_task(scope="industry", scope_name="散熱", stock_code="6230", stock_name="尼得科超眾", source_mode="rss")
        with patch.object(rss_module, "_download_rss_feed", side_effect=RuntimeError("network down")):
            state = run_collector_task(task)

        self.assertEqual(state["event_packet"]["packet_type"], "event")
        self.assertGreater(len(state.get("raw_sources", [])), 0)
        self.assertTrue(any("rss fetch" in error for error in state.get("run_errors", [])))

    def test_source_registry_can_select_mock(self):
        state = {"source_mode": "mock", "scope": "industry", "scope_name": "散熱"}
        raw_sources = fetch_raw_sources(state)
        self.assertGreater(len(raw_sources), 0)
        self.assertEqual(raw_sources[0]["source_type"], "mock")

    def test_source_registry_can_select_rss(self):
        state = {
            "source_mode": "rss",
            "scope": "macro",
            "scope_name": "大環境",
            "rss_feed_documents": {"https://example.com/rss": FAKE_RSS_XML},
            "rss_feeds": [{"source_name": "Thermal Feed", "feed_url": "https://example.com/rss"}],
        }
        with patch.object(rss_module, "feedparser", None):
            raw_sources = fetch_raw_sources(state)

        self.assertGreater(len(raw_sources), 0)
        self.assertEqual(raw_sources[0]["source_type"], "rss")

    def test_hybrid_falls_back_to_mock_when_rss_empty(self):
        task = make_task(scope="industry", scope_name="散熱", stock_code="6230", stock_name="尼得科超眾", source_mode="hybrid")
        with patch.object(rss_module, "_download_rss_feed", side_effect=RuntimeError("network down")), patch.object(
            source_registry,
            "fetch_search_sources",
            return_value=[
                {
                    "title": "AI 伺服器散熱需求持續升溫",
                    "source_name": "Mock Search Industry",
                    "source_url": "https://example.com/search/mock/thermal-ai-server-liquid-cooling",
                    "published_at": "2026-06-18T08:00:00+08:00",
                    "content": "AI 伺服器與液冷需求持續推升散熱零組件研究熱度，6230 尼得科超眾為散熱供應鏈中的代表樣本之一。",
                    "source_type": "search",
                }
            ],
        ):
            state = run_collector_task(task)

        self.assertEqual(state["event_packet"]["packet_type"], "event")
        self.assertEqual(state["raw_sources"][0]["source_type"], "search")
        self.assertFalse(any("hybrid fetch used mock fallback" in error for error in state.get("run_errors", [])))

    def test_rss_mode_can_produce_event_packet_for_industry(self):
        task = make_task(scope="industry", scope_name="散熱", stock_code="6230", stock_name="尼得科超眾", source_mode="rss")
        state = run_collector_task(
            task
            | {
                "rss_feed_documents": {"https://example.com/rss": FAKE_RSS_XML},
                "rss_feeds": [{"source_name": "Thermal Feed", "feed_url": "https://example.com/rss"}],
            }
        )

        packet = state["event_packet"]
        self.assertEqual(packet["packet_type"], "event")
        self.assertEqual(packet["collector"], "langgraph")
        self.assertEqual(packet["related_industries"], ["散熱"])
        self.assertEqual(packet["related_stocks"], ["6230"])
        self.assertEqual(state["raw_sources"][0]["source_type"], "rss")

    def test_rss_mode_can_produce_event_packet_for_macro(self):
        task = make_task(scope="macro", scope_name="大環境", source_mode="rss")
        state = run_collector_task(
            task
            | {
                "rss_feed_documents": {"https://example.com/rss": FAKE_RSS_XML},
                "rss_feeds": [{"source_name": "Thermal Feed", "feed_url": "https://example.com/rss"}],
            }
        )

        packet = state["event_packet"]
        self.assertEqual(packet["packet_type"], "event")
        self.assertEqual(packet["collector"], "langgraph")
        self.assertEqual(packet["related_industries"], [])
        self.assertEqual(packet["related_stocks"], [])


if __name__ == "__main__":
    unittest.main()
