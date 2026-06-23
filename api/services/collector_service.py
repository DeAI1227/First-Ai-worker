from __future__ import annotations

from typing import Any

from collector.batch_runner import run_batch_tasks
from collector.graph import run_collector_task, run_three_day_report_task
from collector.tasks import default_tasks, generate_batch_tasks, make_task
from api.schemas import CollectRunRequest


def run_collect_sync(request: CollectRunRequest) -> dict[str, Any]:
    if request.batch:
        tasks = generate_batch_tasks(
            request.batch,
            source_mode=request.source_mode,
            summarizer_mode=request.summarizer_mode,
            llm_provider=request.llm_provider,
            search_provider=request.search_provider,
        )
        batch_summary = run_batch_tasks(tasks, batch_type=request.batch)
        return {
            "status": batch_summary.get("status", "failed"),
            "execution_mode": "sync",
            "job_id": None,
            "message": "Collector run completed.",
            "mode": request.mode,
            "batch": request.batch,
            "output_files": batch_summary.get("output_files", []),
            "run_errors": batch_summary.get("run_errors", []),
            "batch_report": batch_summary,
        }

    if request.scope:
        task = make_task(
            scope=request.scope,
            scope_name=request.scope_name or request.scope,
            stock_code=request.stock_code,
            stock_name=request.stock_name,
            run_mode=request.mode,
            source_mode=request.source_mode,
            search_provider=request.search_provider,
            summarizer_mode=request.summarizer_mode,
            llm_provider=request.llm_provider,
        )
        tasks = [task]
    else:
        if request.mode == "three_day":
            raise ValueError("--scope and --scope_name are required for three_day mode")
        tasks = default_tasks(
            source_mode=request.source_mode,
            search_provider=request.search_provider,
            summarizer_mode=request.summarizer_mode,
            llm_provider=request.llm_provider,
        )

    final_state: dict[str, Any] = {}
    for task in tasks:
        state = run_three_day_report_task(task) if request.mode == "three_day" else run_collector_task(task)
        final_state = state

    return {
        "status": str(final_state.get("status") or "failed"),
        "execution_mode": "sync",
        "job_id": None,
        "message": "Collector run completed.",
        "mode": request.mode,
        "batch": None,
        "output_files": list(final_state.get("output_paths", [])),
        "run_errors": list(final_state.get("run_errors", [])),
        "batch_report": dict(final_state.get("crawl_run_packet", {})),
    }

