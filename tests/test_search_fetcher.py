from __future__ import annotations

import unittest
from unittest.mock import patch

from collector.graph import run_collector_task
from collector.nodes.filter import filter_sources
from collector.sources import fetch_raw_sources
from collector.sources import registry as source_registry
from collector.sources.search_fetcher import (
    SEARCH_PROVIDER_REGISTRY,
    fetch_search_sources,
    mock_search_provider,
)
from collector.tasks import make_task


class SearchFetcherTests(unittest.TestCase):
    def test_search_fetcher_accepts_search_keywords(self):
        task = make_task(scope="industry", scope_name="散熱", stock_code="6230", stock_name="尼得科超眾", source_mode="search")
        raw_sources = fetch_search_sources(task, ["散熱", "AI 伺服器", "液冷"])

        self.assertGreaterEqual(len(raw_sources), 1)
        self.assertTrue(all(item["source_type"] == "search" for item in raw_sources))
        self.assertTrue(any("散熱" in item["title"] or "散熱" in item["content"] for item in raw_sources))

    def test_search_fetcher_returns_uniform_raw_sources(self):
        task = make_task(scope="macro", scope_name="大環境", source_mode="search")
        raw_sources = fetch_search_sources(task, ["聯準會", "CPI", "美元指數"])

        self.assertGreaterEqual(len(raw_sources), 1)
        item = raw_sources[0]
        self.assertEqual(
            set(item.keys()),
            {"title", "source_name", "source_url", "published_at", "content", "source_type"},
        )
        self.assertEqual(item["source_type"], "search")
        self.assertTrue(item["title"])
        self.assertTrue(item["source_url"])
        self.assertTrue(item["content"])

    def test_search_fetcher_without_provider_falls_back_to_mock_results(self):
        task = make_task(scope="industry", scope_name="散熱", source_mode="search")
        raw_sources = fetch_search_sources(task, ["散熱"], provider="")

        self.assertGreater(len(raw_sources), 0)
        self.assertEqual(raw_sources[0]["source_type"], "search")

    def test_source_registry_can_select_search(self):
        state = {
            "source_mode": "search",
            "scope": "industry",
            "scope_name": "散熱",
            "search_keywords": ["散熱", "AI 伺服器"],
            "search_provider": "mock",
        }
        with patch.object(source_registry, "fetch_search_sources", return_value=[{"source_type": "search"}]) as mocked_search, patch.object(
            source_registry, "fetch_mock_sources", return_value=[{"source_type": "mock"}]
        ):
            raw_sources = fetch_raw_sources(state)

        self.assertEqual(raw_sources, [{"source_type": "search"}])
        mocked_search.assert_called_once()

    def test_search_mode_falls_back_to_mock(self):
        state = {
            "source_mode": "search",
            "scope": "macro",
            "scope_name": "大環境",
            "search_keywords": ["聯準會", "CPI"],
        }
        with patch.object(source_registry, "fetch_search_sources", return_value=[]), patch.object(
            source_registry, "fetch_mock_sources", return_value=[{"source_type": "mock"}]
        ) as mocked_mock:
            raw_sources = fetch_raw_sources(state)

        self.assertEqual(raw_sources, [{"source_type": "mock"}])
        mocked_mock.assert_called_once()

    def test_hybrid_order_is_rss_http_search_mock(self):
        state = {
            "source_mode": "hybrid",
            "scope": "industry",
            "scope_name": "散熱",
            "search_keywords": ["散熱", "液冷"],
            "http_urls": ["https://example.com/http"],
        }
        call_order: list[str] = []

        def fake_rss(task, state=None):
            call_order.append("rss")
            return []

        def fake_http(task, urls=None, state=None):
            call_order.append("http")
            return []

        def fake_search(task, keywords=None, state=None, provider=None):
            call_order.append("search")
            return [{"source_type": "search"}]

        with patch.object(source_registry, "fetch_rss_sources", side_effect=fake_rss), patch.object(
            source_registry, "fetch_http_sources", side_effect=fake_http
        ), patch.object(source_registry, "fetch_search_sources", side_effect=fake_search), patch.object(
            source_registry, "fetch_mock_sources", return_value=[{"source_type": "mock"}]
        ):
            raw_sources = fetch_raw_sources(state)

        self.assertEqual(raw_sources, [{"source_type": "search"}])
        self.assertEqual(call_order, ["rss", "http", "search"])

    def test_filter_sources_accepts_search_source_type(self):
        state = {
            "raw_sources": [
                {
                    "title": "AI 伺服器液冷趨勢補漏",
                    "source_name": "Search Result",
                    "source_url": "https://example.com/search-result",
                    "published_at": "",
                    "content": "Data center cooling demand remains strong across the supply chain.",
                    "source_type": "search",
                }
            ]
        }
        filtered_state = filter_sources(state)
        self.assertEqual(len(filtered_state["filtered_sources"]), 1)
        self.assertEqual(filtered_state["filtered_sources"][0]["source_type"], "search")

    def test_search_mode_can_produce_event_packet(self):
        task = make_task(scope="industry", scope_name="散熱", stock_code="6230", stock_name="尼得科超眾", source_mode="search")
        state = run_collector_task(
            task
            | {
                "search_keywords": ["散熱", "AI 伺服器", "液冷"],
                "search_provider": "mock",
            }
        )

        self.assertEqual(state["event_packet"]["packet_type"], "event")
        self.assertEqual(state["event_packet"]["collector"], "langgraph")
        self.assertEqual(state["event_packet"]["related_industries"], ["散熱"])
        self.assertEqual(state["event_packet"]["related_stocks"], ["6230"])
        self.assertGreater(len(state["raw_sources"]), 0)


if __name__ == "__main__":
    unittest.main()
