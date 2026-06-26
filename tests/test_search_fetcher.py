from __future__ import annotations

import os
import unittest
from unittest.mock import patch

from collector.graph import run_collector_task
from collector.nodes.filter import filter_sources
from collector.sources import fetch_raw_sources
from collector.sources import registry as source_registry
from collector.sources.search_fetcher import fetch_search_sources
from collector.tasks import make_task


class SearchFetcherTests(unittest.TestCase):
    def test_search_fetcher_accepts_search_keywords_with_explicit_mock_provider(self):
        task = make_task(
            scope="industry",
            scope_name="\u6563\u71b1",
            stock_code="6230",
            stock_name="Nidec Chaun-Choung",
            source_mode="search",
        )
        raw_sources = fetch_search_sources(
            task,
            ["thermal", "AI server", "liquid cooling"],
            state={"search_provider": "mock"},
        )

        self.assertGreaterEqual(len(raw_sources), 1)
        self.assertTrue(all(item["source_type"] == "search" for item in raw_sources))
        self.assertTrue(all(item["title"] and item["source_url"] and item["content"] for item in raw_sources))

    def test_search_fetcher_returns_uniform_raw_sources_with_explicit_mock_provider(self):
        task = make_task(scope="macro", scope_name="macro", source_mode="search")
        raw_sources = fetch_search_sources(
            task,
            ["Fed", "CPI", "US Treasury yield"],
            state={"search_provider": "mock"},
        )

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

    def test_search_fetcher_without_provider_returns_empty(self):
        task = make_task(scope="industry", scope_name="thermal", source_mode="search")
        state: dict = {}
        with patch.dict(os.environ, {}, clear=True):
            raw_sources = fetch_search_sources(task, ["thermal"], state=state, provider="")

        self.assertEqual(raw_sources, [])
        self.assertTrue(any("search provider is unavailable" in error for error in state["run_errors"]))

    def test_source_registry_can_select_search(self):
        state = {
            "source_mode": "search",
            "scope": "industry",
            "scope_name": "thermal",
            "search_keywords": ["thermal", "AI server"],
            "search_provider": "mock",
        }
        with patch.object(source_registry, "fetch_search_sources", return_value=[{"source_type": "search"}]) as mocked_search, patch.object(
            source_registry, "fetch_mock_sources", return_value=[{"source_type": "mock"}]
        ):
            raw_sources = fetch_raw_sources(state)

        self.assertEqual(raw_sources, [{"source_type": "search"}])
        mocked_search.assert_called_once()

    def test_search_mode_returns_empty_when_search_has_no_results(self):
        state = {
            "source_mode": "search",
            "scope": "macro",
            "scope_name": "macro",
            "search_keywords": ["Fed", "CPI"],
        }
        with patch.object(source_registry, "fetch_search_sources", return_value=[]), patch.object(
            source_registry, "fetch_mock_sources", return_value=[{"source_type": "mock"}]
        ) as mocked_mock:
            raw_sources = fetch_raw_sources(state)

        self.assertEqual(raw_sources, [])
        mocked_mock.assert_not_called()
        self.assertTrue(any("search source mode returned no usable sources" in error for error in state["run_errors"]))

    def test_hybrid_order_is_rss_http_search_without_mock_fallback(self):
        state = {
            "source_mode": "hybrid",
            "scope": "industry",
            "scope_name": "thermal",
            "search_keywords": ["thermal", "liquid cooling"],
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
                    "title": "AI server cooling demand update",
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

    def test_search_mode_can_produce_event_packet_with_explicit_mock_provider(self):
        task = make_task(
            scope="industry",
            scope_name="\u6563\u71b1",
            stock_code="6230",
            stock_name="Nidec Chaun-Choung",
            source_mode="search",
        )
        state = run_collector_task(
            task
            | {
                "search_keywords": ["thermal", "AI server", "liquid cooling"],
                "search_provider": "mock",
            }
        )

        self.assertEqual(state["event_packet"]["packet_type"], "event")
        self.assertEqual(state["event_packet"]["collector"], "langgraph")
        self.assertEqual(state["event_packet"]["related_industries"], ["\u6563\u71b1"])
        self.assertEqual(state["event_packet"]["related_stocks"], ["6230"])
        self.assertGreater(len(state["raw_sources"]), 0)


if __name__ == "__main__":
    unittest.main()
