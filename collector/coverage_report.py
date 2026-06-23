from __future__ import annotations

from pathlib import Path
from typing import Any

from collector.config.tracking_universe import INSTITUTION_WATCH_STOCKS, TRACKED_STOCKS
from collector.utils.file_utils import write_json
from collector.utils.time_utils import today_date


PROJECT_ROOT = Path(__file__).resolve().parents[1]
OUTPUT_ROOT = PROJECT_ROOT / "output"
COVERAGE_LOGS_ROOT = OUTPUT_ROOT / "logs"


def build_coverage_report(tasks: list[dict[str, Any]], results: list[dict[str, Any]], *, coverage_date: str | None = None) -> dict[str, Any]:
    coverage_date = coverage_date or today_date()

    searched_stocks: list[str] = []
    stocks_with_events: list[str] = []
    stocks_without_events: list[str] = []
    industries_searched: list[str] = []
    industries_with_events: list[str] = []
    missing_search_targets: list[str] = []
    warnings: list[str] = []

    macro_searched = False
    macro_has_events = False
    institution_watch_searched = False
    institution_watch_has_events = False

    stock_results_by_code: dict[str, bool] = {}

    for task, result in _pair_tasks_and_results(tasks, results):
        scope = str(task.get("scope", "") or "")
        scope_name = str(task.get("scope_name", "") or "")
        stock_code = str(task.get("target_stock_code", "") or "")
        event_packet = result.get("event_packet") if isinstance(result, dict) else None
        has_event = bool(event_packet and isinstance(event_packet, dict) and event_packet.get("packet_type") == "event")
        status = str(result.get("status", "") or "")

        if scope == "stock":
            if stock_code:
                _append_unique(searched_stocks, stock_code)
                stock_results_by_code[stock_code] = stock_results_by_code.get(stock_code, False) or has_event
            else:
                _append_unique(missing_search_targets, scope_name or "unknown-stock")
            if status == "failed":
                warnings.append(f"stock task failed: {stock_code or scope_name or 'unknown'}")
        elif scope in {"institution", "institution_watch"}:
            if stock_code:
                _append_unique(searched_stocks, stock_code)
                stock_results_by_code[stock_code] = stock_results_by_code.get(stock_code, False) or has_event
            else:
                _append_unique(missing_search_targets, scope_name or "unknown-institution")
            institution_watch_searched = True
            institution_watch_has_events = institution_watch_has_events or has_event
        elif scope == "industry":
            _append_unique(industries_searched, scope_name)
            if has_event:
                _append_unique(industries_with_events, scope_name)
        elif scope == "macro":
            macro_searched = True
            macro_has_events = macro_has_events or has_event
        else:
            if scope:
                warnings.append(f"unsupported scope in coverage report: {scope}")

    coverage_targets = _build_coverage_targets(include_institution_watch=institution_watch_searched)
    for code in coverage_targets:
        if code not in searched_stocks:
            missing_search_targets.append(code)
            continue
        if stock_results_by_code.get(code):
            _append_unique(stocks_with_events, code)
        else:
            _append_unique(stocks_without_events, code)

    expected_stock_count = len(coverage_targets)
    if len(searched_stocks) != expected_stock_count:
        warnings.append(
            f"searched_stocks count {len(searched_stocks)} does not match configured tracked stock count {expected_stock_count}"
        )

    return {
        "coverage_date": coverage_date,
        "total_tracked_stocks": expected_stock_count,
        "searched_stocks": searched_stocks,
        "stocks_with_events": stocks_with_events,
        "stocks_without_events": stocks_without_events,
        "missing_search_targets": _dedupe_preserve_order(missing_search_targets),
        "industries_searched": industries_searched,
        "industries_with_events": industries_with_events,
        "macro_searched": macro_searched,
        "macro_has_events": macro_has_events,
        "institution_watch_searched": institution_watch_searched,
        "institution_watch_has_events": institution_watch_has_events,
        "warnings": _dedupe_preserve_order(warnings),
    }


def write_coverage_report(report: dict[str, Any], *, output_root: Path | None = None) -> str:
    root = output_root or COVERAGE_LOGS_ROOT
    path = root / f"coverage_report_{report.get('coverage_date', today_date())}.json"
    return write_json(path, report)


def _pair_tasks_and_results(tasks: list[dict[str, Any]], results: list[dict[str, Any]]) -> list[tuple[dict[str, Any], dict[str, Any]]]:
    paired: list[tuple[dict[str, Any], dict[str, Any]]] = []
    for index, task in enumerate(tasks):
        result = results[index] if index < len(results) and isinstance(results[index], dict) else {}
        paired.append((task, result))
    return paired


def _append_unique(values: list[str], value: str) -> None:
    cleaned = str(value).strip()
    if not cleaned or cleaned in values:
        return
    values.append(cleaned)


def _dedupe_preserve_order(values: list[str]) -> list[str]:
    ordered: list[str] = []
    for value in values:
        _append_unique(ordered, value)
    return ordered


def _build_coverage_targets(*, include_institution_watch: bool) -> list[str]:
    targets = [str(stock.get("stock_code", "") or "") for stock in TRACKED_STOCKS if str(stock.get("stock_code", "") or "").strip()]
    if include_institution_watch:
        targets.extend(
            str(stock.get("stock_code", "") or "")
            for stock in INSTITUTION_WATCH_STOCKS
            if str(stock.get("stock_code", "") or "").strip()
        )
    return _dedupe_preserve_order(targets)
