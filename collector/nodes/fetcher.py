from __future__ import annotations

from collector.sources import fetch_http_sources, fetch_mock_sources, fetch_raw_sources, fetch_rss_sources, fetch_search_sources


def fetch_sources(state: dict) -> dict:
    state["raw_sources"] = fetch_raw_sources(state)
    return state


def mock_fetcher(state: dict) -> list[dict]:
    task = {
        "scope": state.get("scope", ""),
        "scope_name": state.get("scope_name", ""),
        "target_stock_code": state.get("target_stock_code", ""),
        "target_stock_name": state.get("target_stock_name", ""),
    }
    return fetch_mock_sources(task)


def rss_fetcher(state: dict) -> list[dict]:
    task = {
        "scope": state.get("scope", ""),
        "scope_name": state.get("scope_name", ""),
        "target_stock_code": state.get("target_stock_code", ""),
        "target_stock_name": state.get("target_stock_name", ""),
    }
    return fetch_rss_sources(task, state)


def http_fetcher(state: dict) -> list[dict]:
    task = {
        "scope": state.get("scope", ""),
        "scope_name": state.get("scope_name", ""),
        "target_stock_code": state.get("target_stock_code", ""),
        "target_stock_name": state.get("target_stock_name", ""),
    }
    return fetch_http_sources(task, urls=state.get("http_urls"), state=state)


def search_api_fetcher(state: dict) -> list[dict]:
    task = {
        "scope": state.get("scope", ""),
        "scope_name": state.get("scope_name", ""),
        "target_stock_code": state.get("target_stock_code", ""),
        "target_stock_name": state.get("target_stock_name", ""),
    }
    return fetch_search_sources(task, state.get("search_keywords", []), state=state)
