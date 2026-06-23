from __future__ import annotations

from typing import Any, TypedDict


class CollectorState(TypedDict, total=False):
    task_id: str
    run_date: str
    run_mode: str
    source_mode: str
    summarizer_mode: str
    llm_provider: str
    scope: str
    scope_name: str
    target_stock_code: str
    target_stock_name: str
    search_keywords: list[str]
    search_provider: str
    raw_sources: list[dict[str, Any]]
    scored_sources: list[dict[str, Any]]
    rejected_sources: list[dict[str, Any]]
    quality_summary: dict[str, int]
    filtered_sources: list[dict[str, Any]]
    http_urls: list[str]
    ai_summary: str
    event_type: str
    importance: str
    possible_impact: str
    risk_note: str
    related_industries: list[str]
    related_stocks: list[str]
    related_macro_topics: list[str]
    related_institution_watch: list[str]
    tags: list[str]
    event_packet: dict[str, Any]
    daily_digest_packet: dict[str, Any]
    report_packet: dict[str, Any]
    crawl_run_packet: dict[str, Any]
    validation_errors: list[str]
    repair_attempts: int
    output_paths: list[str]
    run_errors: list[str]
    rss_feeds: list[dict[str, Any]]
    started_at: str
    finished_at: str
    status: str
    items_found: int
    items_written: int
    items_failed: int
