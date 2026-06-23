from __future__ import annotations

from collector.nodes.classifier import classify_event
from collector.nodes.digest_builder import build_daily_digest
from collector.nodes.fetcher import fetch_sources
from collector.nodes.filter import filter_sources
from collector.nodes.packet_builder import build_event_packet_node
from collector.nodes.planner import generate_search_plan
from collector.nodes.repairer import repair_event_packet
from collector.nodes.report_builder import build_report_placeholder, build_three_day_report
from collector.nodes.summarizer import summarize_sources
from collector.nodes.validator import validate_event_packet_node
from collector.nodes.writer import write_crawl_run, write_daily_digest, write_event_packet, write_failed_packet, write_report_packet
from collector.schemas.crawl_run_packet import build_crawl_run_packet
from collector.schemas.report_packet import validate_report_packet
from collector.utils.time_utils import now_iso, run_id
from collector.utils.time_utils import today_date


def load_task(task: dict) -> dict:
    state = dict(task)
    state.setdefault("run_mode", "daily")
    state.setdefault("run_date", today_date())
    state.setdefault("source_mode", "mock")
    state.setdefault("summarizer_mode", "mock")
    state.setdefault("llm_provider", "auto")
    state.setdefault("search_provider", "auto")
    state.setdefault("scored_sources", [])
    state.setdefault("rejected_sources", [])
    state.setdefault("quality_summary", {"total_sources": 0, "high": 0, "medium": 0, "low": 0, "rejected": 0})
    state.setdefault("validation_errors", [])
    state.setdefault("repair_attempts", 0)
    state.setdefault("output_paths", [])
    state.setdefault("run_errors", [])
    state["started_at"] = now_iso()
    state["run_id"] = run_id()
    return state


def run_collector_task(task: dict) -> dict:
    state = load_task(task)
    for node in [
        generate_search_plan,
        fetch_sources,
        filter_sources,
    ]:
        state = node(state)

    if state.get("filtered_sources"):
        for node in [
            summarize_sources,
            classify_event,
            build_event_packet_node,
            validate_event_packet_node,
        ]:
            state = node(state)

        while state.get("validation_errors") and state.get("repair_attempts", 0) < 2:
            state = repair_event_packet(state)
            state = validate_event_packet_node(state)

        if state.get("validation_errors"):
            state = write_failed_packet(state)
        else:
            state = write_event_packet(state)
            state = build_daily_digest(state)
            state = write_daily_digest(state)
    else:
        state["event_packet"] = {}
        state["daily_digest_packet"] = {}
        state["report_packet"] = {}

    if state.get("event_packet"):
        state = build_report_placeholder(state)
    state["crawl_run_packet"] = build_crawl_run_packet(state)
    state = write_crawl_run(state)
    state["status"] = state["crawl_run_packet"]["status"]
    return state


def run_three_day_report_task(task: dict) -> dict:
    state = load_task(task)
    state = build_three_day_report(state)
    state["validation_errors"] = validate_report_packet(state.get("report_packet", {}))
    if state.get("validation_errors"):
        state = write_failed_packet(state)
    else:
        state = write_report_packet(state)
    state["crawl_run_packet"] = build_crawl_run_packet(state)
    state = write_crawl_run(state)
    state["status"] = state["crawl_run_packet"]["status"]
    return state


def build_crawl_run_node(state: dict) -> dict:
    state["crawl_run_packet"] = build_crawl_run_packet(state)
    return state


def route_after_validation(state: dict) -> str:
    if state.get("validation_errors") and state.get("repair_attempts", 0) < 2:
        return "repair_event_packet"
    if state.get("validation_errors"):
        return "write_failed_packet"
    return "write_event_packet"


def build_graph():
    """Return a LangGraph graph when langgraph is installed.

    The MVP runner uses the deterministic `run_collector_task` function so local
    execution still works in environments where langgraph has not been installed yet.
    """
    try:
        from langgraph.graph import END, START, StateGraph

        from collector.state import CollectorState

        graph = StateGraph(CollectorState)
        graph.add_node("load_task", lambda state: load_task(dict(state)))
        graph.add_node("generate_search_plan", generate_search_plan)
        graph.add_node("fetch_sources", fetch_sources)
        graph.add_node("filter_sources", filter_sources)
        graph.add_node("summarize_sources", summarize_sources)
        graph.add_node("classify_event", classify_event)
        graph.add_node("build_event_packet", build_event_packet_node)
        graph.add_node("validate_event_packet", validate_event_packet_node)
        graph.add_node("repair_event_packet", repair_event_packet)
        graph.add_node("write_event_packet", write_event_packet)
        graph.add_node("write_failed_packet", write_failed_packet)
        graph.add_node("build_daily_digest", build_daily_digest)
        graph.add_node("write_daily_digest", write_daily_digest)
        graph.add_node("build_report_placeholder", build_report_placeholder)
        graph.add_node("build_crawl_run", build_crawl_run_node)
        graph.add_node("write_crawl_run", write_crawl_run)
        graph.add_node("skip_event_outputs", skip_event_outputs)

        graph.add_edge(START, "load_task")
        graph.add_edge("load_task", "generate_search_plan")
        graph.add_edge("generate_search_plan", "fetch_sources")
        graph.add_edge("fetch_sources", "filter_sources")
        graph.add_conditional_edges(
            "filter_sources",
            has_event_sources,
            {
                True: "summarize_sources",
                False: "skip_event_outputs",
            },
        )
        graph.add_edge("summarize_sources", "classify_event")
        graph.add_edge("classify_event", "build_event_packet")
        graph.add_edge("build_event_packet", "validate_event_packet")
        graph.add_conditional_edges(
            "validate_event_packet",
            route_after_validation,
            {
                "repair_event_packet": "repair_event_packet",
                "write_failed_packet": "write_failed_packet",
                "write_event_packet": "write_event_packet",
            },
        )
        graph.add_edge("repair_event_packet", "validate_event_packet")
        graph.add_edge("write_event_packet", "build_daily_digest")
        graph.add_edge("build_daily_digest", "write_daily_digest")
        graph.add_edge("write_daily_digest", "build_report_placeholder")
        graph.add_edge("write_failed_packet", "build_report_placeholder")
        graph.add_edge("skip_event_outputs", "build_crawl_run")
        graph.add_edge("build_report_placeholder", "build_crawl_run")
        graph.add_edge("build_crawl_run", "write_crawl_run")
        graph.add_edge("write_crawl_run", END)
        return graph.compile()
    except ImportError:
        return None


def has_event_sources(state: dict) -> bool:
    return bool(state.get("filtered_sources"))


def skip_event_outputs(state: dict) -> dict:
    state["event_packet"] = {}
    state["daily_digest_packet"] = {}
    state["report_packet"] = {}
    return state
