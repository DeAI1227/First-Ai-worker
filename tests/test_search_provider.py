from __future__ import annotations

import os
import subprocess
import sys
import unittest
from unittest.mock import patch

import main as cli_main
from collector.graph import run_collector_task
from collector.nodes.filter import filter_sources
from collector.sources import fetch_raw_sources
from collector.sources import registry as source_registry
from collector.sources.search.registry import select_search_provider
from collector.sources.search.mock_search_provider import MockSearchProvider
from collector.sources.search_fetcher import fetch_search_sources
from collector.tasks import make_task


class SearchProviderTests(unittest.TestCase):
    def test_mock_search_provider_returns_raw_sources(self):
        task = make_task(scope="industry", scope_name="散熱", stock_code="6230", stock_name="尼得科超眾", source_mode="search")
        provider = MockSearchProvider()
        raw_sources = provider.search(task, ["散熱", "AI 伺服器"], {})

        self.assertGreaterEqual(len(raw_sources), 1)
        self.assertTrue(all(item["source_type"] == "search" for item in raw_sources))
        self.assertTrue(all(item["title"] and item["source_url"] and item["content"] for item in raw_sources))

    def test_auto_provider_without_key_falls_back_to_mock(self):
        with patch.dict(os.environ, {}, clear=True):
            provider_name, provider = select_search_provider("auto", {})

        self.assertEqual(provider_name, "mock")
        self.assertIsInstance(provider, MockSearchProvider)

    def test_search_provider_env_variable_is_respected(self):
        with patch.dict(os.environ, {"SEARCH_PROVIDER": "mock"}, clear=True):
            provider_name, provider = select_search_provider(None, {})

        self.assertEqual(provider_name, "mock")
        self.assertIsInstance(provider, MockSearchProvider)

    def test_tavily_provider_without_key_falls_back_to_mock(self):
        with patch.dict(os.environ, {}, clear=True):
            provider_name, provider = select_search_provider("tavily", {})

        self.assertEqual(provider_name, "mock")
        self.assertIsInstance(provider, MockSearchProvider)

    def test_serpapi_provider_without_key_falls_back_to_mock(self):
        with patch.dict(os.environ, {}, clear=True):
            provider_name, provider = select_search_provider("serpapi", {})

        self.assertEqual(provider_name, "mock")
        self.assertIsInstance(provider, MockSearchProvider)

    def test_search_fetcher_accepts_search_keywords(self):
        task = make_task(scope="industry", scope_name="散熱", stock_code="6230", stock_name="尼得科超眾", source_mode="search")
        raw_sources = fetch_search_sources(task, ["散熱", "AI 伺服器", "液冷"], state={"search_provider": "mock"})

        self.assertGreaterEqual(len(raw_sources), 1)
        self.assertTrue(all(item["source_type"] == "search" for item in raw_sources))
        self.assertTrue(any("散熱" in item["title"] or "散熱" in item["content"] for item in raw_sources))

    def test_search_fetcher_deduplicates_by_source_url(self):
        task = make_task(scope="industry", scope_name="散熱", source_mode="search")
        duplicated = [
            {
                "title": "A",
                "source_name": "Mock Search",
                "source_url": "https://example.com/a",
                "published_at": "",
                "content": "A content",
                "source_type": "search",
            },
            {
                "title": "A duplicate",
                "source_name": "Mock Search",
                "source_url": "https://example.com/a?bcmt=1&utm_source=test",
                "published_at": "",
                "content": "A duplicate content",
                "source_type": "search",
            },
        ]
        with patch.object(MockSearchProvider, "search", return_value=duplicated):
            raw_sources = fetch_search_sources(task, ["散熱"], state={"search_provider": "mock"})

        self.assertEqual(len(raw_sources), 1)
        self.assertEqual(raw_sources[0]["source_url"], "https://example.com/a")

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

    def test_source_registry_passes_source_rules_into_search_task(self):
        source_rules = [
            {
                "kind": "yahoo_stock_news",
                "name": "Yahoo news",
                "url": "https://tw.stock.yahoo.com/quote/6230.TW/news",
                "stock_code": "6230",
                "stock_name": "test-stock",
            }
        ]
        state = {
            "source_mode": "search",
            "scope": "industry",
            "scope_name": "industry",
            "source_rules": source_rules,
            "search_keywords": ["industry", "AI cooling"],
            "search_provider": "mock",
        }
        with patch.object(source_registry, "fetch_search_sources", return_value=[{"source_type": "search"}]) as mocked_search, patch.object(
            source_registry, "fetch_mock_sources", return_value=[{"source_type": "mock"}]
        ):
            fetch_raw_sources(state)

        mocked_search.assert_called_once()
        forwarded_task = mocked_search.call_args.args[0]
        self.assertEqual(forwarded_task.get("source_rules"), source_rules)


    def test_hybrid_mode_tries_search_after_rss_http_empty(self):
        state = {
            "source_mode": "hybrid",
            "scope": "industry",
            "scope_name": "散熱",
            "search_keywords": ["散熱", "液冷"],
            "search_provider": "mock",
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
                    "title": "AI 伺服器散熱需求升溫",
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
        task = make_task(
            scope="industry",
            scope_name="散熱",
            stock_code="6230",
            stock_name="尼得科超眾",
            source_mode="search",
            search_provider="mock",
        )
        state = run_collector_task(task | {"search_keywords": ["散熱", "AI 伺服器", "液冷"]})

        self.assertEqual(state["event_packet"]["packet_type"], "event")
        self.assertEqual(state["event_packet"]["collector"], "langgraph")
        self.assertEqual(state["event_packet"]["related_industries"], ["散熱"])
        self.assertEqual(state["event_packet"]["related_stocks"], ["6230"])
        self.assertGreater(len(state["raw_sources"]), 0)

    def test_search_mode_cli_mock_runs(self):
        result = subprocess.run(
            [
                sys.executable,
                "main.py",
                "--source-mode",
                "search",
                "--search-provider",
                "mock",
            ],
            cwd=os.path.dirname(os.path.dirname(__file__)),
            capture_output=True,
            text=False,
        )
        self.assertEqual(result.returncode, 0, msg=result.stderr)
        stdout = result.stdout.decode("utf-8", errors="replace")
        self.assertIn('"search_provider": "mock"', stdout)

    def test_search_mode_cli_accepts_firecrawl_provider(self):
        with patch.object(sys, "argv", ["main.py", "--search-provider", "firecrawl"]):
            args = cli_main.parse_args()

        self.assertEqual(args.search_provider, "firecrawl")


if __name__ == "__main__":
    unittest.main()
