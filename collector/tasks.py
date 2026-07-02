from __future__ import annotations

from collector.config.tracking_universe import build_batch_task
from collector.task_batches import all_daily_tasks, generate_batch_tasks
from collector.sources.entrypoints import build_stock_source_rules


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
    **extra,
) -> dict:
    source_rules = extra_source_rules(
        scope=scope,
        scope_name=scope_name,
        stock_code=stock_code,
        stock_name=stock_name,
        industry_name=industry_name,
        search_keywords=search_keywords,
    )
    if source_rules and "source_rules" not in extra:
        extra["source_rules"] = source_rules
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
        **extra,
    )


def extra_source_rules(
    *,
    scope: str,
    scope_name: str,
    stock_code: str = "",
    stock_name: str = "",
    industry_name: str = "",
    search_keywords: list[str] | None = None,
) -> list[dict]:
    if scope == "macro":
        return []
    if scope == "industry":
        if stock_code:
            return build_stock_source_rules(stock_code, stock_name)
        return []
    if scope == "stock":
        if stock_code:
            return build_stock_source_rules(stock_code, stock_name or scope_name)
    if scope in {"institution", "institution_watch"}:
        if stock_code:
            return build_stock_source_rules(stock_code, stock_name or scope_name)
    return []


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


__all__ = ["default_tasks", "extra_source_rules", "generate_batch_tasks", "make_task"]
