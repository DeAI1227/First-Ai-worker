from __future__ import annotations

import os
import unittest
from unittest.mock import Mock, patch

import requests

from collector.sources.search.firecrawl_provider import FirecrawlProvider
from collector.sources.search.mock_search_provider import MockSearchProvider
from collector.sources.search.base_provider import SearchProviderUnavailableError
from collector.sources.search.registry import select_search_provider
from collector.sources.search_fetcher import fetch_search_sources
from collector.tasks import make_task


class FirecrawlSearchProviderTests(unittest.TestCase):
    def test_auto_prefers_firecrawl_when_configured(self):
        with patch.dict(os.environ, {"FIRECRAWL_BASE_URL": "http://localhost:3002"}, clear=True):
            provider_name, provider = select_search_provider("auto", {})

        self.assertEqual(provider_name, "firecrawl")
        self.assertIsInstance(provider, FirecrawlProvider)

    def test_firecrawl_provider_requires_base_url(self):
        with patch.dict(os.environ, {}, clear=True):
            provider = FirecrawlProvider()
            self.assertFalse(provider.is_available())
            with self.assertRaises(SearchProviderUnavailableError):
                provider.search({"scope": "industry"}, ["alpha"], {})

    def test_firecrawl_provider_parses_search_response(self):
        task = make_task(scope="industry", scope_name="thermal", source_mode="search")

        class FakeResponse:
            def raise_for_status(self) -> None:
                return None

            def json(self) -> dict[str, object]:
                return {
                    "success": True,
                    "data": [
                        {
                            "title": "Thermal solution demand grows",
                            "url": "https://example.com/thermal-1",
                            "description": "Cooling demand remains strong.",
                            "markdown": "Cooling demand remains strong across the supply chain.",
                            "metadata": {
                                "title": "Thermal solution demand grows",
                                "sourceURL": "https://example.com/thermal-1",
                            },
                        }
                    ],
                }

        with patch.dict(os.environ, {"FIRECRAWL_BASE_URL": "http://localhost:3002"}, clear=True), patch(
            "collector.sources.search.firecrawl_provider.requests.post", return_value=FakeResponse()
        ) as mocked_post:
            provider = FirecrawlProvider()
            results = provider.search(task, ["thermal"], {})

        self.assertEqual(len(results), 1)
        self.assertEqual(results[0]["source_type"], "search")
        self.assertEqual(results[0]["source_url"], "https://example.com/thermal-1")
        self.assertIn("Cooling demand remains strong", results[0]["content"])
        mocked_post.assert_called_once()

    def test_firecrawl_provider_filters_results_by_allowed_domains(self):
        task = make_task(scope="industry", scope_name="散熱", stock_code="6230", stock_name="尼得科超眾", source_mode="search")

        class FakeResponse:
            def raise_for_status(self) -> None:
                return None

            def json(self) -> dict[str, object]:
                return {
                    "success": True,
                    "data": {
                        "web": [
                            {
                                "title": "Allowed Yahoo result",
                                "url": "https://tw.stock.yahoo.com/news/allowed",
                                "description": "Allowed content",
                                "markdown": "Allowed content",
                                "metadata": {
                                    "title": "Allowed Yahoo result",
                                    "sourceURL": "https://tw.stock.yahoo.com/news/allowed",
                                },
                            },
                            {
                                "title": "Blocked Baidu result",
                                "url": "https://baike.baidu.com/item/blocked",
                                "description": "Blocked content",
                                "markdown": "Blocked content",
                                "metadata": {
                                    "title": "Blocked Baidu result",
                                    "sourceURL": "https://baike.baidu.com/item/blocked",
                                },
                            },
                        ]
                    },
                }

        with patch.dict(os.environ, {"FIRECRAWL_BASE_URL": "http://localhost:3002"}, clear=True), patch(
            "collector.sources.search.firecrawl_provider.requests.post", return_value=FakeResponse()
        ):
            provider = FirecrawlProvider()
            results = provider.search(task, ["散熱"], {})

        self.assertEqual(len(results), 1)
        self.assertEqual(results[0]["source_url"], "https://tw.stock.yahoo.com/news/allowed")

    def test_fetch_search_sources_falls_back_to_mock_when_firecrawl_fails(self):
        task = make_task(scope="industry", scope_name="thermal", source_mode="search")

        with patch.dict(os.environ, {"FIRECRAWL_BASE_URL": "http://localhost:3002"}, clear=True), patch(
            "collector.sources.search.firecrawl_provider.requests.post",
            side_effect=requests.RequestException("boom"),
        ), patch.object(
            MockSearchProvider,
            "search",
            return_value=[
                {
                    "title": "Mock thermal update",
                    "source_name": "Mock Search",
                    "source_url": "https://mock.example.com",
                    "published_at": "",
                    "content": "Cooling demand remains strong.",
                    "source_type": "search",
                }
            ],
        ) as mocked_mock:
            results = fetch_search_sources(task, ["thermal"], state={"search_provider": "firecrawl"})

        self.assertEqual(len(results), 1)
        self.assertEqual(results[0]["source_url"], "https://mock.example.com")
        mocked_mock.assert_called()


if __name__ == "__main__":
    unittest.main()
