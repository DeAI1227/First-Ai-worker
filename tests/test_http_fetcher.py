from __future__ import annotations

import unittest
from unittest.mock import Mock, patch

import requests

from collector.graph import run_collector_task
from collector.sources import fetch_raw_sources
from collector.sources import registry as source_registry
from collector.sources.entrypoints import build_cnyes_category_rules, build_stock_source_rules
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

    def test_source_registry_can_resolve_http_urls_from_stock_source_rules(self):
        state = {
            "source_mode": "http",
            "scope": "stock",
            "scope_name": "台積電",
            "target_stock_code": "2330",
            "target_stock_name": "台積電",
            "source_rules": build_stock_source_rules("2330", "台積電"),
        }
        with patch.object(source_registry, "fetch_http_sources", return_value=[{"source_type": "http"}]) as mocked_http, patch.object(
            source_registry, "fetch_mock_sources", return_value=[{"source_type": "mock"}]
        ):
            raw_sources = fetch_raw_sources(state)

        self.assertEqual(raw_sources, [{"source_type": "http"}])
        mocked_http.assert_called_once()
        self.assertEqual(mocked_http.call_args.kwargs["urls"], ["https://tw.stock.yahoo.com/quote/2330.TW/news"])

    def test_http_mode_returns_empty_when_no_urls(self):
        state = {
            "source_mode": "http",
            "scope": "industry",
            "scope_name": "散熱",
        }
        with patch.object(source_registry, "fetch_mock_sources", return_value=[{"source_type": "mock"}]) as mocked_mock:
            raw_sources = fetch_raw_sources(state)

        self.assertEqual(raw_sources, [])
        mocked_mock.assert_not_called()
        self.assertTrue(any("http source mode returned no usable sources" in error for error in state["run_errors"]))

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

    def test_hybrid_returns_empty_when_rss_http_and_search_empty(self):
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

        self.assertEqual(raw_sources, [])
        mocked_mock.assert_not_called()
        self.assertTrue(any("mock fallback is disabled" in error for error in state["run_errors"]))

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

    def test_http_fetcher_follows_yahoo_stock_news_list_links(self):
        task = make_task(scope="stock", scope_name="台積電", stock_code="2330", stock_name="台積電", source_mode="http")
        state = {"run_errors": []}

        list_response = Mock()
        list_response.raise_for_status.return_value = None
        list_response.text = """
        <!doctype html>
        <html lang="zh-TW">
          <head><title>台積電新聞頁</title></head>
          <body>
            <a href="https://tw.stock.yahoo.com/news/article-one-1.html">新聞一</a>
            <a href="/news/article-two-2.html">新聞二</a>
            <a href="https://example.com/not-news">廣告</a>
          </body>
        </html>
        """

        article_one = Mock()
        article_one.raise_for_status.return_value = None
        article_one.text = """
        <!doctype html>
        <html lang="zh-TW">
          <head>
            <title>新聞一標題</title>
            <meta property="og:site_name" content="Yahoo Finance">
            <meta property="article:published_time" content="2026-06-24T08:00:00+08:00">
          </head>
          <body>
            <article><p>第一篇新聞內容，這是一段足夠長、可被系統保留的正式段落，用來驗證抓取流程。</p></article>
          </body>
        </html>
        """

        article_two = Mock()
        article_two.raise_for_status.return_value = None
        article_two.text = """
        <!doctype html>
        <html lang="zh-TW">
          <head>
            <title>新聞二標題</title>
            <meta property="og:site_name" content="Yahoo Finance">
          </head>
          <body>
            <article><p>第二篇新聞內容，同樣是一段足夠長的正式段落，用來確認列表頁連結可以往下追進文章頁。</p></article>
          </body>
        </html>
        """

        with patch(
            "collector.sources.http_fetcher.requests.get",
            side_effect=[list_response, article_one, article_two],
        ), patch("collector.sources.http_fetcher.BeautifulSoup", None):
            raw_sources = fetch_http_sources(task, urls=["https://tw.stock.yahoo.com/quote/2330.TW/news"], state=state)

        self.assertEqual(len(raw_sources), 2)
        self.assertTrue(all(item["source_type"] == "http" for item in raw_sources))
        self.assertEqual(raw_sources[0]["source_url"], "https://tw.stock.yahoo.com/news/article-one-1.html")
        self.assertEqual(raw_sources[1]["source_url"], "https://tw.stock.yahoo.com/news/article-two-2.html")
        self.assertIn("新聞一標題", raw_sources[0]["title"])
        self.assertIn("新聞二標題", raw_sources[1]["title"])


    def test_http_fetcher_follows_cnyes_category_links_and_filters_irrelevant_articles(self):
        task = make_task(
            scope="stock",
            scope_name="???",
            stock_code="2330",
            stock_name="???",
            source_mode="http",
            search_keywords=["2330", "???", "???"],
        )
        state = {"run_errors": []}

        category_response = Mock()
        category_response.raise_for_status.return_value = None
        category_response.text = """
        <!doctype html>
        <html lang="zh-TW">
          <body>
            <a href="/news/id/6501001">article one</a>
            <a href="https://news.cnyes.com/news/id/6501002">article two</a>
            <a href="/news/cat/wd_macro">macro category</a>
            <a href="https://example.com/ad">ad</a>
          </body>
        </html>
        """

        relevant_article = Mock()
        relevant_article.raise_for_status.return_value = None
        relevant_article.text = """
        <!doctype html>
        <html lang="zh-TW">
          <head>
            <title>?????????</title>
            <meta property="og:site_name" content="???">
            <meta property="article:published_time" content="2026-06-24T08:00:00+08:00">
          </head>
          <body>
            <article>
              <p>???????????????????????</p>
            </article>
          </body>
        </html>
        """

        irrelevant_article = Mock()
        irrelevant_article.raise_for_status.return_value = None
        irrelevant_article.text = """
        <!doctype html>
        <html lang="zh-TW">
          <head>
            <title>??????</title>
            <meta property="og:site_name" content="???">
          </head>
          <body>
            <article>
              <p>???????????????</p>
            </article>
          </body>
        </html>
        """

        with patch(
            "collector.sources.http_fetcher.requests.get",
            side_effect=[category_response, relevant_article, irrelevant_article],
        ), patch("collector.sources.http_fetcher.BeautifulSoup", None):
            raw_sources = fetch_http_sources(task, urls=["https://news.cnyes.com/news/cat/wd_stock"], state=state)

        self.assertEqual(len(raw_sources), 1)
        self.assertEqual(raw_sources[0]["source_type"], "http")
        self.assertEqual(raw_sources[0]["source_url"], "https://news.cnyes.com/news/id/6501001")
        self.assertIn("???", raw_sources[0]["title"])
        self.assertTrue(raw_sources[0]["title"])


    def test_source_registry_can_resolve_cnyes_urls_from_source_rules(self):
        state = {
            "source_mode": "http",
            "scope": "stock",
            "scope_name": "???",
            "target_stock_code": "2330",
            "target_stock_name": "???",
            "source_rules": build_cnyes_category_rules("stock", "???"),
        }
        with patch.object(source_registry, "fetch_http_sources", return_value=[{"source_type": "http"}]) as mocked_http, patch.object(
            source_registry, "fetch_mock_sources", return_value=[{"source_type": "mock"}]
        ):
            raw_sources = fetch_raw_sources(state)

        self.assertEqual(raw_sources, [{"source_type": "http"}])
        mocked_http.assert_called_once()
        self.assertEqual(
            mocked_http.call_args.kwargs["urls"],
            [
                "https://news.cnyes.com/news/cat/tw_quo",
                "https://news.cnyes.com/news/cat/stock_report",
                "https://news.cnyes.com/news/cat/tw_revenue",
                "https://news.cnyes.com/news/cat/wd_stock",
            ],
        )


if __name__ == "__main__":
    unittest.main()
