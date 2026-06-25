from __future__ import annotations

import os
import unittest
from unittest.mock import patch

import requests

from collector.sources.search.firecrawl_provider import FirecrawlProvider
from collector.sources.search.mock_search_provider import MockSearchProvider
from collector.sources.search.registry import select_search_provider
from collector.sources.search_fetcher import fetch_search_sources
from collector.tasks import make_task


class FirecrawlSearchProviderTests(unittest.TestCase):
    def test_auto_prefers_firecrawl_when_key_is_configured(self):
        with patch.dict(os.environ, {"FIRECRAWL_API_KEY": "fc-test-key"}, clear=True):
            provider_name, provider = select_search_provider("auto", {})

        self.assertEqual(provider_name, "firecrawl")
        self.assertIsInstance(provider, FirecrawlProvider)

    def test_firecrawl_provider_is_not_auto_selected_without_configuration(self):
        with patch.dict(os.environ, {}, clear=True):
            provider = FirecrawlProvider()
            self.assertFalse(provider.is_available())
            provider_name, provider_impl = select_search_provider("auto", {})

        self.assertEqual(provider_name, "mock")
        self.assertIsInstance(provider_impl, MockSearchProvider)

    def test_firecrawl_provider_parses_search_response_using_hosted_default_url(self):
        task = {
            "scope": "industry",
            "scope_name": "thermal",
            "source_mode": "search",
            "source_rules": [],
        }

        class FakeResponse:
            def raise_for_status(self) -> None:
                return None

            def json(self) -> dict[str, object]:
                return {
                    "success": True,
                    "data": [
                        {
                            "title": "Thermal solution demand grows",
                            "url": "https://tw.stock.yahoo.com/news/thermal-1",
                            "description": "Cooling demand remains strong.",
                            "markdown": "Cooling demand remains strong across the supply chain.",
                            "metadata": {
                                "title": "Thermal solution demand grows",
                                "sourceURL": "https://tw.stock.yahoo.com/news/thermal-1",
                            },
                        }
                    ],
                }

        with patch.dict(os.environ, {"FIRECRAWL_API_KEY": "fc-test-key"}, clear=True), patch(
            "collector.sources.search.firecrawl_provider.requests.post", return_value=FakeResponse()
        ) as mocked_post:
            provider = FirecrawlProvider()
            results = provider.search(task, ["thermal"], {})

        self.assertTrue(results)
        self.assertTrue(all(item["source_type"] == "search" for item in results))
        matched = [item for item in results if item["source_url"] == "https://tw.stock.yahoo.com/news/thermal-1"]
        self.assertTrue(matched)
        self.assertIn("Cooling demand remains strong", matched[0]["content"])
        self.assertEqual(mocked_post.call_args.args[0], "https://api.firecrawl.dev/v2/search")

    def test_firecrawl_provider_filters_results_by_allowed_domains(self):
        task = make_task(
            scope="industry",
            scope_name="thermal",
            stock_code="6230",
            stock_name="Nidec",
            source_mode="search",
        )

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

        with patch.dict(os.environ, {"FIRECRAWL_API_KEY": "fc-test-key"}, clear=True), patch(
            "collector.sources.search.firecrawl_provider.requests.post", return_value=FakeResponse()
        ):
            provider = FirecrawlProvider()
            results = provider.search(task, ["thermal"], {})

        self.assertEqual(len(results), 1)
        self.assertEqual(results[0]["source_url"], "https://tw.stock.yahoo.com/news/allowed")

    def test_fetch_search_sources_falls_back_to_mock_when_firecrawl_fails(self):
        task = make_task(scope="industry", scope_name="thermal", source_mode="search")

        with patch.dict(os.environ, {"FIRECRAWL_API_KEY": "fc-test-key"}, clear=True), patch(
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
        mocked_mock.assert_called_once()


if __name__ == "__main__":
    unittest.main()
