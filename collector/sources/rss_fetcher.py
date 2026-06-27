from __future__ import annotations

from datetime import datetime, timezone
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen
import ssl
import xml.etree.ElementTree as ET

try:  # pragma: no cover - optional dependency
    import feedparser  # type: ignore
except ImportError:  # pragma: no cover - optional dependency
    feedparser = None

from collector.sources.base import clean_text, extract_feed_override, normalize_source_item, parse_datetime_value
from collector.sources.config import get_rss_source_configs
from collector.sources.http_fetcher import fetch_http_sources

RSS_FETCH_TIMEOUT_SECONDS = 10
RSS_ARTICLE_ENRICH_MIN_CONTENT_CHARS = 160


def fetch_rss_sources(task: dict, state: dict | None = None) -> list[dict]:
    if state is None:
        state = {}
    rss_feeds = state.get("rss_feeds")
    if rss_feeds is None:
        rss_feeds = get_rss_source_configs(task.get("scope", ""), task.get("scope_name", ""))

    if not rss_feeds:
        return []

    raw_sources: list[dict] = []
    for feed in rss_feeds:
        feed_url = clean_text(feed.get("feed_url", ""))
        source_name = clean_text(feed.get("source_name", "RSS Source")) or "RSS Source"
        if not feed_url:
            state.setdefault("run_errors", []).append(f"rss feed missing url: {source_name}")
            continue
        try:
            xml_text = extract_feed_override(state.get("rss_feed_documents"), feed_url)
            if xml_text is None:
                xml_text = _download_rss_feed(feed_url)
            raw_sources.extend(_parse_rss_document(task, state, xml_text, feed_url, source_name))
        except (HTTPError, URLError, TimeoutError, OSError, ValueError, ET.ParseError) as exc:
            state.setdefault("run_errors", []).append(f"rss fetch failed for {feed_url}: {exc}")
        except Exception as exc:  # pragma: no cover - defensive
            state.setdefault("run_errors", []).append(f"rss fetch unexpected error for {feed_url}: {exc}")

    return raw_sources


def _download_rss_feed(feed_url: str) -> str:
    request = Request(feed_url, headers={"User-Agent": "Mozilla/5.0 (RSS Fetcher MVP)"})
    context = ssl._create_unverified_context()
    with urlopen(request, timeout=RSS_FETCH_TIMEOUT_SECONDS, context=context) as response:
        charset = response.headers.get_content_charset() or "utf-8"
        return response.read().decode(charset, errors="replace")


def _parse_rss_document(task: dict, state: dict, xml_text: str, feed_url: str, fallback_source_name: str) -> list[dict]:
    if feedparser is not None:
        return _parse_with_feedparser(task, state, xml_text, feed_url, fallback_source_name)
    return _parse_with_elementtree(task, state, xml_text, feed_url, fallback_source_name)


def _parse_with_feedparser(task: dict, state: dict, xml_text: str, feed_url: str, fallback_source_name: str) -> list[dict]:
    parsed = feedparser.parse(xml_text)
    feed_title = ""
    if getattr(parsed, "feed", None):
        feed_title = clean_text(getattr(parsed.feed, "title", "") or parsed.feed.get("title", ""))
    resolved_source_name = feed_title or fallback_source_name

    raw_sources: list[dict] = []
    for entry in parsed.entries:
        rss_source = normalize_source_item(
            {
                "title": clean_text(entry.get("title", "")),
                "source_name": resolved_source_name,
                "source_url": clean_text(entry.get("link", "")) or feed_url,
                "published_at": _extract_feedparser_datetime(entry),
                "content": _extract_entry_content(entry),
            },
            "rss",
        )
        raw_sources.append(_enrich_rss_source(task, state, rss_source))
    return raw_sources


def _parse_with_elementtree(task: dict, state: dict, xml_text: str, feed_url: str, fallback_source_name: str) -> list[dict]:
    root = ET.fromstring(xml_text)
    raw_sources: list[dict] = []

    channel = root.find("channel")
    if channel is not None:
        feed_title = clean_text(_find_text(channel, "title")) or fallback_source_name
        for item in channel.findall("item"):
            rss_source = normalize_source_item(
                {
                    "title": clean_text(_find_text(item, "title")),
                    "source_name": feed_title,
                    "source_url": clean_text(_find_text(item, "link")) or feed_url,
                    "published_at": parse_datetime_value(_find_text(item, "pubDate") or _find_text(item, "published")),
                    "content": clean_text(_find_text(item, "description") or _find_text(item, "summary")),
                },
                "rss",
            )
            raw_sources.append(_enrich_rss_source(task, state, rss_source))
        return raw_sources

    atom_namespace = "{http://www.w3.org/2005/Atom}"
    feed_title = clean_text(_find_text(root, f"{atom_namespace}title")) or fallback_source_name
    for entry in root.findall(f"{atom_namespace}entry"):
        link_element = entry.find(f"{atom_namespace}link")
        link = ""
        if link_element is not None:
            link = clean_text(link_element.get("href", "")) or clean_text(link_element.text or "")
        rss_source = normalize_source_item(
            {
                "title": clean_text(_find_text(entry, f"{atom_namespace}title")),
                "source_name": feed_title,
                "source_url": link or feed_url,
                "published_at": parse_datetime_value(_find_text(entry, f"{atom_namespace}updated") or _find_text(entry, f"{atom_namespace}published")),
                "content": clean_text(_find_text(entry, f"{atom_namespace}summary") or _find_text(entry, f"{atom_namespace}content")),
            },
            "rss",
        )
        raw_sources.append(_enrich_rss_source(task, state, rss_source))
    return raw_sources


def _enrich_rss_source(task: dict, state: dict, rss_source: dict) -> dict:
    content = clean_text(rss_source.get("content", ""))
    source_url = clean_text(rss_source.get("source_url", ""))
    if not source_url or len(content) >= RSS_ARTICLE_ENRICH_MIN_CONTENT_CHARS:
        return rss_source

    article_sources = fetch_http_sources(task, urls=[source_url], state=state)
    if not article_sources:
        return rss_source

    article_source = article_sources[0]
    article_content = clean_text(article_source.get("content", ""))
    if len(article_content) <= len(content):
        return rss_source

    enriched = dict(rss_source)
    enriched["content"] = article_content
    article_title = clean_text(article_source.get("title", ""))
    if article_title and len(article_title) > len(clean_text(enriched.get("title", ""))):
        enriched["title"] = article_title
    if not clean_text(enriched.get("published_at", "")):
        enriched["published_at"] = clean_text(article_source.get("published_at", ""))
    if not clean_text(enriched.get("source_name", "")):
        enriched["source_name"] = clean_text(article_source.get("source_name", ""))
    return normalize_source_item(enriched, "rss")


def _find_text(element: ET.Element, tag_name: str) -> str:
    child = element.find(tag_name)
    if child is None or child.text is None:
        return ""
    return child.text


def _extract_entry_content(entry: Any) -> str:
    content_candidates = [
        entry.get("content", []),
        entry.get("summary", ""),
        entry.get("description", ""),
        entry.get("subtitle", ""),
    ]
    for candidate in content_candidates:
        if isinstance(candidate, list):
            for item in candidate:
                if isinstance(item, dict):
                    value = clean_text(item.get("value", "") or item.get("content", ""))
                    if value:
                        return value
        else:
            value = clean_text(candidate)
            if value:
                return value
    return ""


def _extract_feedparser_datetime(entry: Any) -> str:
    for key in ("published_parsed", "updated_parsed"):
        parsed_value = entry.get(key)
        if parsed_value:
            try:
                return datetime(*parsed_value[:6], tzinfo=timezone.utc).isoformat()
            except Exception:
                continue

    for key in ("published", "updated", "pubDate"):
        value = clean_text(entry.get(key, ""))
        if value:
            parsed = parse_datetime_value(value)
            if parsed:
                return parsed
    return ""
