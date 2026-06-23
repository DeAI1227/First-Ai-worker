from __future__ import annotations

from collector.config.tracking_universe import build_batch_task
from collector.task_batches import all_daily_tasks, generate_batch_tasks


def make_task(
    scope: str,
    scope_name: str,
    stock_code: str = "",
    stock_name: str = "",
    run_mode: str = "daily",
    source_mode: str = "mock",
    summarizer_mode: str = "mock",
    llm_provider: str = "auto",
    search_provider: str = "auto",
    search_keywords: list[str] | None = None,
    industry_name: str = "",
) -> dict:
    return build_batch_task(
        scope=scope,
        scope_name=scope_name,
        stock_code=stock_code,
        stock_name=stock_name,
        industry_name=industry_name,
        run_mode=run_mode,
        source_mode=source_mode,
        summarizer_mode=summarizer_mode,
        llm_provider=llm_provider,
        search_provider=search_provider,
        search_keywords=search_keywords,
    )


def default_tasks(
    source_mode: str = "hybrid",
    summarizer_mode: str = "mock",
    llm_provider: str = "auto",
    search_provider: str = "auto",
) -> list[dict]:
    return all_daily_tasks(
        source_mode=source_mode,
        summarizer_mode=summarizer_mode,
        llm_provider=llm_provider,
        search_provider=search_provider,
    )


__all__ = ["make_task", "default_tasks", "generate_batch_tasks"]
