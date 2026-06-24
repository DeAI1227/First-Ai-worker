from __future__ import annotations

from project_env import load_project_env

load_project_env()

import argparse
import json
import sys

from collector.batch_runner import run_batch_tasks
from collector.graph import run_collector_task, run_three_day_report_task
from collector.tasks import default_tasks, generate_batch_tasks, make_task

try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:
    pass


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="LangGraph Research Collector Agent MVP")
    parser.add_argument("--mode", choices=["daily", "three_day"], default="daily")
    parser.add_argument("--source-mode", choices=["mock", "rss", "http", "search", "hybrid"], default="mock")
    parser.add_argument("--search-provider", choices=["auto", "mock", "tavily", "serpapi", "firecrawl"], default="auto")
    parser.add_argument("--summarizer-mode", choices=["mock", "llm"], default="mock")
    parser.add_argument("--llm-provider", choices=["auto", "agnes", "gemini", "mock"], default="auto")
    parser.add_argument("--batch", choices=["industries", "stocks", "macro", "institution_watch", "all"])
    parser.add_argument("--scope", choices=["macro", "industry", "stock", "institution", "institution_watch"])
    parser.add_argument("--scope-name")
    parser.add_argument("--stock-code", default="")
    parser.add_argument("--stock-name", default="")
    return parser.parse_args()


def print_result(state: dict) -> None:
    quality_summary = state.get("quality_summary", {})
    crawl_run_packet = state.get("crawl_run_packet", {})
    accepted_sources_count = crawl_run_packet.get("accepted_sources_count", 0)
    rejected_sources_count = crawl_run_packet.get("rejected_sources_count", 0)
    report = {
        "task": {
            "task_id": state.get("task_id"),
            "scope": state.get("scope"),
            "scope_name": state.get("scope_name"),
            "target_stock_code": state.get("target_stock_code"),
            "target_stock_name": state.get("target_stock_name"),
            "source_mode": state.get("source_mode"),
            "search_provider": state.get("search_provider"),
            "summarizer_mode": state.get("summarizer_mode"),
            "llm_provider": state.get("llm_provider"),
        },
        "search_keywords": state.get("search_keywords", []),
        "event_packet": state.get("event_packet", {}),
        "daily_digest_packet": state.get("daily_digest_packet", {}),
        "report_packet": state.get("report_packet", {}),
        "crawl_run_packet": crawl_run_packet,
        "quality_summary": quality_summary,
        "validation_errors": state.get("validation_errors", []),
        "run_errors": state.get("run_errors", []),
        "output_paths": state.get("output_paths", []),
        "final_status": state.get("status"),
    }
    print(json.dumps(report, ensure_ascii=False, indent=2))
    if quality_summary:
        print("Source Quality Summary")
        print(f"- total_sources: {quality_summary.get('total_sources', 0)}")
        print(f"- high: {quality_summary.get('high', 0)}")
        print(f"- medium: {quality_summary.get('medium', 0)}")
        print(f"- low: {quality_summary.get('low', 0)}")
        print(f"- rejected: {quality_summary.get('rejected', 0)}")
        print(f"Accepted sources: {accepted_sources_count}")
        print(f"Rejected sources: {rejected_sources_count}")


def main() -> None:
    args = parse_args()
    if args.batch:
        tasks = generate_batch_tasks(
            args.batch,
            source_mode=args.source_mode,
            summarizer_mode=args.summarizer_mode,
            llm_provider=args.llm_provider,
            search_provider=args.search_provider,
        )
        summary = run_batch_tasks(tasks, batch_type=args.batch)
        print(json.dumps(summary, ensure_ascii=False, indent=2))
        print(f"Batch Summary: {summary.get('batch_report_path', '')}")
        if summary.get("coverage_report_path"):
            print(f"Coverage Report: {summary.get('coverage_report_path', '')}")
        return
    if args.scope:
        if not args.scope_name:
            raise SystemExit("--scope-name is required when --scope is provided")
        tasks = [
            make_task(
                scope=args.scope,
                scope_name=args.scope_name,
                stock_code=args.stock_code,
                stock_name=args.stock_name,
                run_mode=args.mode,
                source_mode=args.source_mode,
                search_provider=args.search_provider,
                summarizer_mode=args.summarizer_mode,
                llm_provider=args.llm_provider,
            )
        ]
    else:
        if args.mode == "three_day":
            raise SystemExit("--scope and --scope-name are required for --mode three_day")
        tasks = default_tasks(
            source_mode=args.source_mode,
            search_provider=args.search_provider,
            summarizer_mode=args.summarizer_mode,
            llm_provider=args.llm_provider,
        )

    for task in tasks:
        if args.mode == "three_day":
            state = run_three_day_report_task(task)
        else:
            state = run_collector_task(task)
        print_result(state)


if __name__ == "__main__":
    main()
