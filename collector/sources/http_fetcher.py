from __future__ import annotations

from collections.abc import Iterable
from html.parser import HTMLParser
from typing import Any
from urllib.parse import urljoin, urlparse
import re

import requests

from collector.sources.base import clean_text, normalize_source_item, parse_datetime_value

try:  # pragma: no cover - optional dependency
    from bs4 import BeautifulSoup  # type: ignore
except ImportError:  # pragma: no cover - optional dependency
    BeautifulSoup = None

HTTP_FETCH_TIMEOUT_SECONDS = 10
HTTP_MAX_CONTENT_CHARS = 3000
HTTP_MIN_PARAGRAPH_LENGTH = 20
YAHOO_STOCK_NEWS_HOST = "tw.stock.yahoo.com"
YAHOO_STOCK_NEWS_LIST_PATH_PREFIX = "/quote/"
YAHOO_STOCK_NEWS_LIST_PATH_SUFFIX = "/news"
YAHOO_STOCK_NEWS_MAX_ARTICLES = 10
CNYES_NEWS_HOST = "news.cnyes.com"
CNYES_NEWS_CATEGORY_PATH_PREFIX = "/news/cat/"
CNYES_NEWS_ID_REGEX = re.compile(r"/news/(?:id/)?(?P<news_id>\d+)", flags=re.IGNORECASE)
CNYES_NEWS_MAX_ARTICLES = 12


def fetch_http_sources(task: dict, urls: list[str] | None = None, state: dict | None = None) -> list[dict]:
    if state is None:
        state = {}
    resolved_urls = _resolve_urls(task, urls, state)
    if not resolved_urls:
        return []

    raw_sources: list[dict] = []
    for url in resolved_urls:
        try:
            response = requests.get(
                url,
                timeout=HTTP_FETCH_TIMEOUT_SECONDS,
                headers={"User-Agent": "Mozilla/5.0 (HTTP Fetcher MVP)"},
            )
            response.raise_for_status()
            html_text = response.text
            list_page_sources = _extract_yahoo_stock_news_list_sources(url, html_text, state)
            if list_page_sources:
                raw_sources.extend(list_page_sources)
                continue

            cnyes_page_sources = _extract_cnyes_category_sources(url, html_text, task, state)
            if cnyes_page_sources:
                raw_sources.extend(cnyes_page_sources)
                continue

            extracted = _extract_http_payload(url, html_text)
            if not extracted:
                state.setdefault("run_errors", []).append(f"http fetch produced no usable content for {url}")
                continue
            raw_sources.append(normalize_source_item(extracted, "http"))
        except Exception as exc:  # pragma: no cover - defensive
            state.setdefault("run_errors", []).append(f"http fetch failed for {url}: {exc}")

    return raw_sources


def _resolve_urls(task: dict, urls: list[str] | None, state: dict) -> list[str]:
    if urls:
        return [url for url in urls if url]
    task_urls = task.get("http_urls")
    if isinstance(task_urls, list) and task_urls:
        return [url for url in task_urls if url]
    state_urls = state.get("http_urls")
    if isinstance(state_urls, list) and state_urls:
        return [url for url in state_urls if url]
    return []


def _extract_yahoo_stock_news_list_sources(page_url: str, html_text: str, state: dict) -> list[dict]:
    if not _is_yahoo_stock_news_list_url(page_url):
        return []

    article_urls = _extract_yahoo_stock_news_links(page_url, html_text)
    if not article_urls:
        return []

    raw_sources: list[dict] = []
    for article_url in article_urls[:YAHOO_STOCK_NEWS_MAX_ARTICLES]:
        try:
            response = requests.get(
                article_url,
                timeout=HTTP_FETCH_TIMEOUT_SECONDS,
                headers={"User-Agent": "Mozilla/5.0 (HTTP Fetcher MVP)"},
            )
            response.raise_for_status()
            extracted = _extract_http_payload(article_url, response.text)
            if not extracted:
                state.setdefault("run_errors", []).append(
                    f"yahoo article produced no usable content for {article_url}"
                )
                continue
            raw_sources.append(normalize_source_item(extracted, "http"))
        except Exception as exc:  # pragma: no cover - defensive
            state.setdefault("run_errors", []).append(f"yahoo article fetch failed for {article_url}: {exc}")

    if not raw_sources:
        state.setdefault("run_errors", []).append(f"yahoo stock news list produced no usable articles for {page_url}")
    return raw_sources


def _extract_cnyes_category_sources(page_url: str, html_text: str, task: dict, state: dict) -> list[dict]:
    if not _is_cnyes_category_url(page_url):
        return []

    article_urls = _extract_cnyes_article_links(page_url, html_text)
    if not article_urls:
        return []

    keywords = _build_cnyes_relevance_keywords(task, state)
    raw_sources: list[dict] = []
    for article_url in article_urls[:CNYES_NEWS_MAX_ARTICLES]:
        try:
            response = requests.get(
                article_url,
                timeout=HTTP_FETCH_TIMEOUT_SECONDS,
                headers={"User-Agent": "Mozilla/5.0 (HTTP Fetcher MVP)"},
            )
            response.raise_for_status()
            extracted = _extract_http_payload(article_url, response.text)
            if not extracted:
                state.setdefault("run_errors", []).append(f"cnyes article produced no usable content for {article_url}")
                continue
            if not _is_relevant_cnyes_article(extracted, keywords):
                continue
            raw_sources.append(normalize_source_item(extracted, "http"))
        except Exception as exc:  # pragma: no cover - defensive
            state.setdefault("run_errors", []).append(f"cnyes article fetch failed for {article_url}: {exc}")

    if not raw_sources:
        state.setdefault("run_errors", []).append(f"cnyes category produced no usable articles for {page_url}")
    return raw_sources


def _is_cnyes_category_url(page_url: str) -> bool:
    parsed = urlparse(page_url)
    if parsed.netloc.lower() != CNYES_NEWS_HOST:
        return False
    path = parsed.path.rstrip("/")
    return path.startswith(CNYES_NEWS_CATEGORY_PATH_PREFIX)


def _extract_cnyes_article_links(page_url: str, html_text: str) -> list[str]:
    hrefs = re.findall(r'href=["\']([^"\']+)["\']', html_text, flags=re.IGNORECASE)
    article_urls: list[str] = []
    seen: set[str] = set()
    for href in hrefs:
        absolute_url = urljoin(page_url, href)
        normalized_url = _normalize_cnyes_article_url(absolute_url)
        if not normalized_url or normalized_url in seen:
            continue
        seen.add(normalized_url)
        article_urls.append(normalized_url)
    return article_urls


def _normalize_cnyes_article_url(article_url: str) -> str:
    parsed = urlparse(article_url)
    if parsed.netloc.lower() != CNYES_NEWS_HOST:
        return ""
    match = CNYES_NEWS_ID_REGEX.search(parsed.path)
    if not match:
        return ""
    news_id = match.group("news_id")
    return f"https://{CNYES_NEWS_HOST}/news/id/{news_id}"


def _build_cnyes_relevance_keywords(task: dict, state: dict) -> list[str]:
    keywords: list[str] = []
    for source in (
        state.get("search_keywords", []),
        task.get("search_keywords", []),
        [task.get("scope_name", "")],
        [task.get("target_stock_code", "")],
        [task.get("target_stock_name", "")],
        [task.get("industry_name", "")],
        [task.get("macro_topic_name", "")],
    ):
        if isinstance(source, list):
            keywords.extend([clean_text(item) for item in source if clean_text(item)])
        else:
            cleaned = clean_text(source)
            if cleaned:
                keywords.append(cleaned)
    seen: set[str] = set()
    unique_keywords: list[str] = []
    for keyword in keywords:
        normalized = keyword.lower()
        if normalized in seen:
            continue
        seen.add(normalized)
        unique_keywords.append(keyword)
    return unique_keywords


def _is_relevant_cnyes_article(article: dict[str, Any], keywords: list[str]) -> bool:
    if not keywords:
        return True
    haystack = f"{article.get('title', '')} {article.get('content', '')}".lower()
    if not haystack.strip():
        return False
    for keyword in keywords:
        cleaned = clean_text(keyword).lower()
        if cleaned and cleaned in haystack:
            return True
    return False


def _is_yahoo_stock_news_list_url(page_url: str) -> bool:
    parsed = urlparse(page_url)
    if parsed.netloc.lower() != YAHOO_STOCK_NEWS_HOST:
        return False
    path = parsed.path.rstrip("/")
    return path.startswith(YAHOO_STOCK_NEWS_LIST_PATH_PREFIX) and path.endswith(YAHOO_STOCK_NEWS_LIST_PATH_SUFFIX)


def _extract_yahoo_stock_news_links(page_url: str, html_text: str) -> list[str]:
    hrefs = re.findall(r'href=["\']([^"\']+)["\']', html_text, flags=re.IGNORECASE)
    article_urls: list[str] = []
    seen: set[str] = set()
    for href in hrefs:
        absolute_url = urljoin(page_url, href)
        if not _is_yahoo_stock_article_url(absolute_url):
            continue
        if absolute_url in seen:
            continue
        seen.add(absolute_url)
        article_urls.append(absolute_url)
    return article_urls


def _is_yahoo_stock_article_url(article_url: str) -> bool:
    parsed = urlparse(article_url)
    if parsed.netloc.lower() != YAHOO_STOCK_NEWS_HOST:
        return False
    path = parsed.path.rstrip("/")
    return "/news/" in path and not path.endswith(YAHOO_STOCK_NEWS_LIST_PATH_SUFFIX)


def _extract_http_payload(page_url: str, html_text: str) -> dict[str, Any]:
    soup = BeautifulSoup(html_text, "html.parser") if BeautifulSoup is not None else None
    if soup is not None:
        payload = _extract_with_bs4(page_url, soup)
    else:
        payload = _extract_with_fallback_parser(page_url, html_text)

    if not payload.get("title") or not payload.get("content"):
        return {}
    return payload


def _extract_with_bs4(page_url: str, soup: Any) -> dict[str, Any]:
    title = _first_non_empty(
        [
            _text_from_node(soup.title),
            _meta_content(soup, "property", "og:title"),
            _meta_content(soup, "name", "title"),
        ]
    )
    source_name = _first_non_empty(
        [
            _meta_content(soup, "property", "og:site_name"),
            _meta_content(soup, "name", "application-name"),
            _hostname_from_url(page_url),
        ]
    )
    description = _first_non_empty(
        [
            _meta_content(soup, "name", "description"),
            _meta_content(soup, "property", "og:description"),
        ]
    )
    published_at = _first_non_empty(
        [
            _meta_content(soup, "property", "article:published_time"),
            _meta_content(soup, "property", "article:modified_time"),
            _meta_content(soup, "name", "pubdate"),
            _meta_content(soup, "name", "date"),
        ]
    )
    content = _extract_main_content_bs4(soup)
    merged_content = " ".join(part for part in [description, content] if part)

    return {
        "title": title,
        "source_name": source_name,
        "source_url": page_url,
        "published_at": parse_datetime_value(published_at),
        "content": _trim_content(merged_content),
    }


def _extract_main_content_bs4(soup: Any) -> str:
    texts: list[str] = []

    article = soup.find("article")
    if article is not None:
        texts.extend(_collect_paragraph_texts(article.stripped_strings))
    else:
        for paragraph in soup.find_all("p"):
            text = clean_text(paragraph.get_text(" ", strip=True))
            if len(text) >= HTTP_MIN_PARAGRAPH_LENGTH:
                texts.append(text)

    if not texts:
        main = soup.find("main")
        if main is not None:
            texts.extend(_collect_paragraph_texts(main.stripped_strings))

    return " ".join(texts)


def _extract_with_fallback_parser(page_url: str, html_text: str) -> dict[str, Any]:
    parser = _SimpleHTMLExtractor()
    parser.feed(html_text)
    title = parser.title or _hostname_from_url(page_url)
    description = parser.meta_description
    source_name = parser.site_name or _hostname_from_url(page_url)
    published_at = parser.published_at
    content = " ".join(parser.paragraphs)
    merged_content = " ".join(part for part in [description, content] if part)

    return {
        "title": title,
        "source_name": source_name,
        "source_url": page_url,
        "published_at": parse_datetime_value(published_at),
        "content": _trim_content(merged_content),
    }


def _collect_paragraph_texts(texts: Iterable[str]) -> list[str]:
    collected: list[str] = []
    for text in texts:
        cleaned = clean_text(text)
        if len(cleaned) >= HTTP_MIN_PARAGRAPH_LENGTH:
            collected.append(cleaned)
    return collected


def _text_from_node(node: Any) -> str:
    if node is None:
        return ""
    return clean_text(node.get_text(" ", strip=True))


def _meta_content(soup: Any, attr_name: str, attr_value: str) -> str:
    tag = soup.find("meta", attrs={attr_name: attr_value})
    if tag is None:
        return ""
    return clean_text(tag.get("content", ""))


def _first_non_empty(values: list[str]) -> str:
    for value in values:
        if value:
            return value
    return ""


def _hostname_from_url(page_url: str) -> str:
    hostname = urlparse(page_url).netloc
    return hostname or "HTTP Source"


def _trim_content(content: str) -> str:
    cleaned = clean_text(content)
    if len(cleaned) > HTTP_MAX_CONTENT_CHARS:
        return cleaned[:HTTP_MAX_CONTENT_CHARS].rstrip()
    return cleaned


class _SimpleHTMLExtractor(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self.title = ""
        self.meta_description = ""
        self.site_name = ""
        self.published_at = ""
        self.paragraphs: list[str] = []
        self._in_title = False
        self._in_paragraph = False
        self._title_buffer: list[str] = []
        self._text_buffer: list[str] = []

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        attrs_dict = {key: value or "" for key, value in attrs}
        if tag == "title":
            self._in_title = True
        elif tag == "p":
            self._in_paragraph = True
            self._text_buffer = []
        elif tag == "meta":
            self._capture_meta(attrs_dict)

    def handle_endtag(self, tag: str) -> None:
        if tag == "title":
            self.title = clean_text(" ".join(self._title_buffer)) or self.title
            self._title_buffer = []
            self._in_title = False
        elif tag == "p":
            text = clean_text(" ".join(self._text_buffer))
            if len(text) >= HTTP_MIN_PARAGRAPH_LENGTH:
                self.paragraphs.append(text)
            self._text_buffer = []
            self._in_paragraph = False

    def handle_data(self, data: str) -> None:
        text = clean_text(data)
        if not text:
            return
        if self._in_title:
            self._title_buffer.append(text)
        elif self._in_paragraph:
            self._text_buffer.append(text)

    def _capture_meta(self, attrs: dict[str, str]) -> None:
        name = attrs.get("name", "").lower()
        prop = attrs.get("property", "").lower()
        content = clean_text(attrs.get("content", ""))
        if not content:
            return
        if prop in {"og:title", "twitter:title"} and not self.title:
            self.title = content
        elif prop == "og:site_name" and not self.site_name:
            self.site_name = content
        elif name == "description" and not self.meta_description:
            self.meta_description = content
        elif prop in {"og:description", "twitter:description"} and not self.meta_description:
            self.meta_description = content
        elif prop in {"article:published_time", "article:modified_time"} and not self.published_at:
            self.published_at = content
        elif name in {"pubdate", "date"} and not self.published_at:
            self.published_at = content
