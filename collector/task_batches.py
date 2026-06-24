from __future__ import annotations

from collector.config.tracking_universe import (
    BATCH_SCOPE_ORDER,
    INSTITUTION_WATCH_STOCKS,
    MACRO_TOPICS,
    TRACKED_STOCKS,
    TRACKING_INDUSTRIES,
    build_batch_task,
    industry_keywords,
    stock_industries_for_code,
    topic_keywords,
)
from collector.sources.entrypoints import build_cnyes_category_rules, build_stock_source_rules


def all_macro_tasks(
    *,
    source_mode: str = "hybrid",
    summarizer_mode: str = "mock",
    llm_provider: str = "auto",
    search_provider: str = "auto",
) -> list[dict]:
    tasks: list[dict] = []
    for topic in MACRO_TOPICS:
        tasks.append(
            build_batch_task(
                scope="macro",
                scope_name=topic["topic_name"],
                run_mode="daily",
                source_mode=source_mode,
                summarizer_mode=summarizer_mode,
                llm_provider=llm_provider,
                search_provider=search_provider,
                search_keywords=topic_keywords(topic["topic_id"]),
                macro_topic_id=topic["topic_id"],
                macro_topic_key=topic["topic_id"],
                macro_topic_name=topic["topic_name"],
                source_rules=build_cnyes_category_rules("macro", topic["topic_name"]),
            )
        )
    return tasks


def all_industry_tasks(
    *,
    source_mode: str = "hybrid",
    summarizer_mode: str = "mock",
    llm_provider: str = "auto",
    search_provider: str = "auto",
) -> list[dict]:
    tasks: list[dict] = []
    for industry in TRACKING_INDUSTRIES:
        sample_stock_code = industry.get("sample_stock_code", "")
        sample_stock_name = industry.get("sample_stock_name", "")
        source_rules = build_stock_source_rules(sample_stock_code, sample_stock_name) if sample_stock_code else []
        source_rules.extend(build_cnyes_category_rules(industry["industry_id"], industry["industry_name"]))
        tasks.append(
            build_batch_task(
                scope="industry",
                scope_name=industry["industry_name"],
                stock_code=industry["sample_stock_code"],
                stock_name=industry["sample_stock_name"],
                industry_name=industry["industry_name"],
                run_mode="daily",
                source_mode=source_mode,
                summarizer_mode=summarizer_mode,
                llm_provider=llm_provider,
                search_provider=search_provider,
                search_keywords=industry_keywords(industry["industry_name"]),
                industry_id=industry["industry_id"],
                source_rules=source_rules,
            )
        )
    return tasks


def all_stock_tasks(
    *,
    source_mode: str = "hybrid",
    summarizer_mode: str = "mock",
    llm_provider: str = "auto",
    search_provider: str = "auto",
) -> list[dict]:
    tasks: list[dict] = []
    for stock in TRACKED_STOCKS:
        industries = stock_industries_for_code(stock["stock_code"])
        tasks.append(
            build_batch_task(
                scope="stock",
                scope_name=stock["stock_name"],
                stock_code=stock["stock_code"],
                stock_name=stock["stock_name"],
                industry_name=industries[0] if industries else "",
                run_mode="daily",
                source_mode=source_mode,
                summarizer_mode=summarizer_mode,
                llm_provider=llm_provider,
                search_provider=search_provider,
                search_keywords=[stock["stock_code"], stock["stock_name"], *industries],
                industries=industries,
                source_rules=[
                    *build_stock_source_rules(stock["stock_code"], stock["stock_name"]),
                    *build_cnyes_category_rules("stock", stock["stock_name"]),
                ],
            )
        )
    return tasks


def all_institution_watch_tasks(
    *,
    source_mode: str = "hybrid",
    summarizer_mode: str = "mock",
    llm_provider: str = "auto",
    search_provider: str = "auto",
) -> list[dict]:
    tasks: list[dict] = []
    for stock in INSTITUTION_WATCH_STOCKS:
        tasks.append(
            build_batch_task(
                scope="institution_watch",
                scope_name="大行關注",
                stock_code=stock["stock_code"],
                stock_name=stock["stock_name"],
                run_mode="daily",
                source_mode=source_mode,
                summarizer_mode=summarizer_mode,
                llm_provider=llm_provider,
                search_provider=search_provider,
                search_keywords=[stock["stock_code"], stock["stock_name"], "大行關注"],
                institution_watch_code=stock["stock_code"],
                institution_watch_name=stock["stock_name"],
                source_rules=[
                    *build_stock_source_rules(stock["stock_code"], stock["stock_name"]),
                    *build_cnyes_category_rules("institution", stock["stock_name"]),
                ],
            )
        )
    return tasks


def all_daily_tasks(
    *,
    source_mode: str = "hybrid",
    summarizer_mode: str = "mock",
    llm_provider: str = "auto",
    search_provider: str = "auto",
) -> list[dict]:
    tasks: list[dict] = []
    tasks.extend(
        all_macro_tasks(
            source_mode=source_mode,
            summarizer_mode=summarizer_mode,
            llm_provider=llm_provider,
            search_provider=search_provider,
        )
    )
    tasks.extend(
        all_industry_tasks(
            source_mode=source_mode,
            summarizer_mode=summarizer_mode,
            llm_provider=llm_provider,
            search_provider=search_provider,
        )
    )
    tasks.extend(
        all_stock_tasks(
            source_mode=source_mode,
            summarizer_mode=summarizer_mode,
            llm_provider=llm_provider,
            search_provider=search_provider,
        )
    )
    tasks.extend(
        all_institution_watch_tasks(
            source_mode=source_mode,
            summarizer_mode=summarizer_mode,
            llm_provider=llm_provider,
            search_provider=search_provider,
        )
    )
    return tasks


def generate_batch_tasks(
    batch: str = "all",
    *,
    source_mode: str = "hybrid",
    summarizer_mode: str = "mock",
    llm_provider: str = "auto",
    search_provider: str = "auto",
) -> list[dict]:
    batch = (batch or "all").strip().lower()
    if batch == "macro":
        return all_macro_tasks(
            source_mode=source_mode,
            summarizer_mode=summarizer_mode,
            llm_provider=llm_provider,
            search_provider=search_provider,
        )
    if batch == "industries":
        return all_industry_tasks(
            source_mode=source_mode,
            summarizer_mode=summarizer_mode,
            llm_provider=llm_provider,
            search_provider=search_provider,
        )
    if batch == "stocks":
        return all_stock_tasks(
            source_mode=source_mode,
            summarizer_mode=summarizer_mode,
            llm_provider=llm_provider,
            search_provider=search_provider,
        )
    if batch in {"institution_watch", "institution"}:
        return all_institution_watch_tasks(
            source_mode=source_mode,
            summarizer_mode=summarizer_mode,
            llm_provider=llm_provider,
            search_provider=search_provider,
        )
    if batch == "all":
        return all_daily_tasks(
            source_mode=source_mode,
            summarizer_mode=summarizer_mode,
            llm_provider=llm_provider,
            search_provider=search_provider,
        )
    raise ValueError(f"Unsupported batch: {batch}")


__all__ = [
    "BATCH_SCOPE_ORDER",
    "all_daily_tasks",
    "all_industry_tasks",
    "all_institution_watch_tasks",
    "all_macro_tasks",
    "all_stock_tasks",
    "generate_batch_tasks",
]
