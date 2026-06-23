from __future__ import annotations

import unittest
from unittest.mock import Mock, patch

import requests

from collector.graph import run_collector_task
from collector.sources import fetch_raw_sources
from collector.sources import registry as source_registry
from collector.sources.http_fetcher import fetch_http_sources
from collector.tasks import make_task


FAKE_HTTP_HTML = """
<!doctype html>
<html lang="zh-TW">
  <head>
    <title>散熱供應鏈需求升溫</title>
    <meta name="description" content="AI 伺服器帶動散熱模組與水冷方案持續成長。">
    <meta property="og:site_name" content="Example News">
    <meta property="article:published_time" content="2026-06-16T08:30:00+08:00">
  </head>
    <body>
    <article>
      <p>AI 伺服器的散熱需求升高，供應鏈持續關注水冷、風冷與整機散熱設計。</p>
      <p><strong>第二段</strong> 內容也要能被擷取，並且文字長度要足夠長，才能通過段落篩選規則。</p>
    </article>
  </body>
</html>
"""

FAKE_HTTP_PARAGRAPH_HTML = """
<!doctype html>
<html lang="zh-TW">
  <head>
    <title>政府公告更新</title>
  </head>
  <body>
    <div class="content">
      <p>短句。</p>
      <p>這是一段足夠長的公告內容，描述政策、統計與產業背景，應該可以被保留。</p>
    </div>
  </body>
</html>
"""


class HttpFetcherTests(unittest.TestCase):
    def test_http_fetcher_parses_fake_html(self):
        task = make_task(scope="industry", scope_name="散熱", stock_code="6230", stock_name="尼得科超眾", source_mode="http")
        state = {"run_errors": []}
        response = Mock()
        response.raise_for_status.return_value = None
        response.text = FAKE_HTTP_HTML

        with patch("collector.sources.http_fetcher.requests.get", return_value=response), patch(
            "collector.sources.http_fetcher.BeautifulSoup", None
        ):
            raw_sources = fetch_http_sources(task, urls=["https://example.com/thermal"], state=state)

        self.assertEqual(len(raw_sources), 1)
        item = raw_sources[0]
        self.assertEqual(item["source_type"], "http")
        self.assertEqual(item["title"], "散熱供應鏈需求升溫")
        self.assertEqual(item["source_name"], "Example News")
        self.assertEqual(item["source_url"], "https://example.com/thermal")
        self.assertIn("AI 伺服器的散熱需求升高", item["content"])
        self.assertIn("第二段 內容也要能被擷取，並且文字長度要足夠長，才能通過段落篩選規則。", item["content"])
        self.assertEqual(item["published_at"], "2026-06-16T08:30:00+08:00")

    def test_http_fetcher_extracts_paragraph_content_without_article(self):
        task = make_task(scope="macro", scope_name="大環境", source_mode="http")
        state = {"run_errors": []}
        response = Mock()
        response.raise_for_status.return_value = None
        response.text = FAKE_HTTP_PARAGRAPH_HTML

        with patch("collector.sources.http_fetcher.requests.get", return_value=response), patch(
            "collector.sources.http_fetcher.BeautifulSoup", None
        ):
            raw_sources = fetch_http_sources(task, urls=["https://example.com/government"], state=state)

        self.assertEqual(len(raw_sources), 1)
        item = raw_sources[0]
        self.assertEqual(item["title"], "政府公告更新")
        self.assertEqual(item["source_type"], "http")
        self.assertIn("足夠長的公告內容", item["content"])
        self.assertNotIn("短句。", item["content"])

    def test_http_fetcher_request_failure_records_error(self):
        task = make_task(scope="industry", scope_name="散熱", source_mode="http")
        state = {"run_errors": []}

        with patch(
            "collector.sources.http_fetcher.requests.get",
            side_effect=requests.RequestException("network down"),
        ):
            raw_sources = fetch_http_sources(task, urls=["https://example.com/fail"], state=state)

        self.assertEqual(raw_sources, [])
        self.assertTrue(any("http fetch failed for https://example.com/fail" in error for error in state["run_errors"]))

    def test_source_registry_can_select_http(self):
        state = {
            "source_mode": "http",
            "scope": "industry",
            "scope_name": "散熱",
            "http_urls": ["https://example.com/http-source"],
        }
        with patch.object(source_registry, "fetch_http_sources", return_value=[{"source_type": "http"}]) as mocked_http, patch.object(
            source_registry, "fetch_mock_sources", return_value=[{"source_type": "mock"}]
        ):
            raw_sources = fetch_raw_sources(state)

        self.assertEqual(raw_sources, [{"source_type": "http"}])
        mocked_http.assert_called_once()

    def test_http_mode_falls_back_to_mock_when_no_urls(self):
        state = {
            "source_mode": "http",
            "scope": "industry",
            "scope_name": "散熱",
        }
        with patch.object(source_registry, "fetch_mock_sources", return_value=[{"source_type": "mock"}]) as mocked_mock:
            raw_sources = fetch_raw_sources(state)

        self.assertEqual(raw_sources[0]["source_type"], "mock")
        mocked_mock.assert_called_once()

    def test_hybrid_tries_http_after_rss_empty(self):
        state = {
            "source_mode": "hybrid",
            "scope": "industry",
            "scope_name": "散熱",
            "http_urls": ["https://example.com/http-source"],
        }
        with patch.object(source_registry, "fetch_rss_sources", return_value=[]), patch.object(
            source_registry, "fetch_http_sources", return_value=[{"source_type": "http"}]
        ) as mocked_http, patch.object(source_registry, "fetch_mock_sources", return_value=[{"source_type": "mock"}]):
            raw_sources = fetch_raw_sources(state)

        self.assertEqual(raw_sources, [{"source_type": "http"}])
        mocked_http.assert_called_once()

    def test_hybrid_falls_back_to_mock_when_rss_and_http_empty(self):
        state = {
            "source_mode": "hybrid",
            "scope": "industry",
            "scope_name": "散熱",
            "http_urls": ["https://example.com/http-source"],
        }
        with patch.object(source_registry, "fetch_rss_sources", return_value=[]), patch.object(
            source_registry, "fetch_http_sources", return_value=[]
        ), patch.object(source_registry, "fetch_search_sources", return_value=[]), patch.object(
            source_registry, "fetch_mock_sources", return_value=[{"source_type": "mock"}]
        ) as mocked_mock:
            raw_sources = fetch_raw_sources(state)

        self.assertEqual(raw_sources, [{"source_type": "mock"}])
        mocked_mock.assert_called_once()

    def test_http_mode_can_produce_event_packet(self):
        task = make_task(scope="industry", scope_name="散熱", stock_code="6230", stock_name="尼得科超眾", source_mode="http")
        response = Mock()
        response.raise_for_status.return_value = None
        response.text = FAKE_HTTP_HTML
        with patch("collector.sources.http_fetcher.requests.get", return_value=response), patch(
            "collector.sources.http_fetcher.BeautifulSoup", None
        ):
            state = run_collector_task(
                task
                | {
                    "http_urls": ["https://example.com/thermal"],
                }
            )

        self.assertEqual(state["event_packet"]["packet_type"], "event")
        self.assertEqual(state["event_packet"]["collector"], "langgraph")
        self.assertGreater(len(state["raw_sources"]), 0)


if __name__ == "__main__":
    unittest.main()
