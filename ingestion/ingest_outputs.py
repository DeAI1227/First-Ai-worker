from __future__ import annotations

import argparse
from pathlib import Path
from typing import Any

from collector.utils.time_utils import now_iso
from ingestion.batch_report import (
    build_batch_error,
    build_batch_report,
    normalize_batch_error,
    write_batch_report,
)
from ingestion.config import OUTPUT_ROOT, PACKET_TARGET_TABLES, PACKET_TYPE_ALIASES
from ingestion.error_logger import build_ingestion_error
from ingestion.mappers import (
    map_crawl_run_packet,
    map_daily_digest_packet,
    map_event_packet,
    map_rejected_source,
    map_report_packet,
)
from ingestion.packet_detector import detect_packet_type
from ingestion.packet_loader import load_json_packets
from ingestion.supabase_client import SupabaseClient, SupabaseConfigError
from ingestion.upsert import route_upsert


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Ingestion for Collector output packets")
    parser.add_argument("--input", default=str(OUTPUT_ROOT))
    parser.add_argument("--packet-type", choices=sorted(PACKET_TYPE_ALIASES.keys()), default="")
    parser.add_argument("--dry-run", action="store_true")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    packet_type_filter = args.packet_type or None
    started_at = now_iso()

    if args.dry_run:
        summary = dry_run_ingest(Path(args.input), packet_type_filter=packet_type_filter)
        finished_at = now_iso()
        batch_report = build_batch_report(
            mode="dry_run",
            input_path=str(Path(args.input)),
            packet_type_filter=_normalize_packet_type_filter_label(packet_type_filter),
            started_at=started_at,
            finished_at=finished_at,
            summary=summary,
            errors=summary.get("error_entries", []),
        )
        batch_report_path = write_batch_report(batch_report)
        summary["batch_report"] = batch_report
        summary["batch_report_path"] = batch_report_path
        summary["status"] = batch_report["status"]
        print_summary(summary, dry_run=True)
        if batch_report["status"] == "failed":
            raise SystemExit(1)
        return

    summary = write_ingest(Path(args.input), packet_type_filter=packet_type_filter)
    finished_at = now_iso()
    batch_report = build_batch_report(
        mode="write",
        input_path=str(Path(args.input)),
        packet_type_filter=_normalize_packet_type_filter_label(packet_type_filter),
        started_at=started_at,
        finished_at=finished_at,
        summary=summary,
        errors=summary.get("error_entries", []),
    )
    batch_report_path = write_batch_report(batch_report)
    summary["batch_report"] = batch_report
    summary["batch_report_path"] = batch_report_path
    summary["status"] = batch_report["status"]
    print_summary(summary, dry_run=False)
    if batch_report["status"] == "failed":
        raise SystemExit(1)


def dry_run_ingest(input_path: str | Path, *, packet_type_filter: str | None = None) -> dict[str, Any]:
    summary = _base_summary(input_path)
    packets, load_errors = load_json_packets(input_path)
    summary["packets_loaded"] = len(packets)
    summary["error_entries"] = [normalize_batch_error(error) for error in load_errors]

    normalized_filter = normalize_filter(packet_type_filter)
    run_index = build_run_index(packets)

    for record in packets:
        packet = record["packet"]
        source_file = record["source_file"]
        packet_type = detect_packet_type(packet)
        if normalized_filter and packet_type != normalized_filter:
            continue

        if packet_type == "unknown":
            summary["unknown_packets"] += 1
            summary["error_entries"].append(
                build_batch_error(
                    stage="detect",
                    packet_type="unknown",
                    packet_id=Path(source_file).stem,
                    target_table="",
                    message="Unknown packet type",
                    severity="warning",
                )
            )
            continue

        enriched_packet = enrich_packet(packet, run_index, source_file)
        _ = map_packet(packet_type, enriched_packet, source_file)
        increment_mapped(summary, packet_type)

    summary["errors"] = len(summary["error_entries"])
    summary["status"] = compute_summary_status(summary, mode="dry_run")
    summary["wrote_to_supabase"] = False
    return summary


def write_ingest(
    input_path: str | Path,
    *,
    packet_type_filter: str | None = None,
    client: SupabaseClient | None = None,
    allow_missing_config: bool = False,
) -> dict[str, Any]:
    summary = _base_summary(input_path)
    packets, load_errors = load_json_packets(input_path)
    summary["packets_loaded"] = len(packets)
    summary["error_entries"] = [normalize_batch_error(error) for error in load_errors]

    write_enabled = True
    if client is None:
        try:
            client = SupabaseClient.from_env()
        except SupabaseConfigError as exc:
            write_enabled = False
            summary["error_entries"].append(
                build_batch_error(
                    stage="write",
                    packet_type="unknown",
                    packet_id="",
                    target_table="",
                    message=str(exc),
                    severity="error",
                )
            )

    normalized_filter = normalize_filter(packet_type_filter)
    run_index = build_run_index(packets)

    for record in packets:
        packet = record["packet"]
        source_file = record["source_file"]
        packet_type = detect_packet_type(packet)
        if normalized_filter and packet_type != normalized_filter:
            continue

        if packet_type == "unknown":
            summary["unknown_packets"] += 1
            summary["error_entries"].append(
                build_batch_error(
                    stage="detect",
                    packet_type="unknown",
                    packet_id=Path(source_file).stem,
                    target_table="",
                    message="Unknown packet type",
                    severity="warning",
                )
            )
            continue

        enriched_packet = enrich_packet(packet, run_index, source_file)
        row = map_packet(packet_type, enriched_packet, source_file)
        increment_mapped(summary, packet_type)

        if not write_enabled or client is None:
            continue

        try:
            route_upsert(client, packet_type, row)
            increment_written(summary, packet_type)
        except Exception as exc:
            increment_failed(summary, packet_type)
            packet_id = packet_identifier(packet_type, row)
            ingestion_error = build_ingestion_error(
                packet_type=packet_type,
                packet_id=packet_id,
                target_table=PACKET_TARGET_TABLES.get(packet_type, "unknown"),
                error_message=str(exc),
                raw_packet=row.get("raw_packet", row),
            )
            summary["error_entries"].append(
                build_batch_error(
                    stage="write",
                    packet_type=packet_type,
                    packet_id=packet_id,
                    target_table=PACKET_TARGET_TABLES.get(packet_type, "unknown"),
                    message=str(exc),
                    severity="error",
                )
            )
            try:
                client.insert_error(ingestion_error)
            except Exception as error_exc:  # pragma: no cover - defensive
                summary["error_entries"].append(
                    build_batch_error(
                        stage="error_log",
                        packet_type=packet_type,
                        packet_id=packet_id,
                        target_table="ingestion_errors",
                        message=f"failed to write ingestion_errors: {error_exc}",
                        severity="error",
                    )
                )
                summary.setdefault("local_errors", []).append(
                    build_ingestion_error(
                        packet_type=ingestion_error["packet_type"],
                        packet_id=ingestion_error["packet_id"],
                        target_table=ingestion_error["target_table"],
                        error_message=f"failed to write ingestion_errors: {error_exc}",
                        raw_packet=ingestion_error,
                    )
                )

    summary["errors"] = len(summary["error_entries"])
    summary["status"] = compute_summary_status(summary, mode="write")
    summary["wrote_to_supabase"] = bool(
        summary["status"] in {"success", "partial_success"}
        and total_written(summary) > 0
    )
    return summary


def map_packet(packet_type: str, packet: dict[str, Any], source_file: str) -> dict[str, Any]:
    if packet_type == "event_packet":
        return map_event_packet(packet, source_file=source_file)
    if packet_type == "daily_digest_packet":
        return map_daily_digest_packet(packet, source_file=source_file)
    if packet_type == "report_packet":
        return map_report_packet(packet, source_file=source_file)
    if packet_type == "crawl_run_packet":
        return map_crawl_run_packet(packet, source_file=source_file)
    if packet_type == "rejected_source":
        return map_rejected_source(packet, source_file=source_file)
    raise ValueError(f"Unsupported packet type: {packet_type}")


def packet_identifier(packet_type: str, row: dict[str, Any]) -> str:
    key_map = {
        "event_packet": "event_id",
        "daily_digest_packet": "digest_id",
        "report_packet": "report_id",
        "crawl_run_packet": "run_id",
        "rejected_source": "source_url",
    }
    key = key_map.get(packet_type, "")
    return str(row.get(key, "") or "")


def _base_summary(input_path: str | Path) -> dict[str, Any]:
    input_root = Path(input_path)
    return {
        "files_scanned": len(list(input_root.rglob("*.json"))) if input_root.exists() else 0,
        "packets_loaded": 0,
        "mapped_events": 0,
        "mapped_daily_digests": 0,
        "mapped_reports": 0,
        "mapped_crawl_runs": 0,
        "mapped_rejected_sources": 0,
        "written_events": 0,
        "written_daily_digests": 0,
        "written_reports": 0,
        "written_crawl_runs": 0,
        "written_rejected_sources": 0,
        "failed_events": 0,
        "failed_daily_digests": 0,
        "failed_reports": 0,
        "failed_crawl_runs": 0,
        "failed_rejected_sources": 0,
        "unknown_packets": 0,
        "errors": 0,
        "error_entries": [],
        "batch_report": {},
        "batch_report_path": "",
        "status": "failed",
        "wrote_to_supabase": False,
    }


def print_summary(summary: dict[str, Any], *, dry_run: bool) -> None:
    header = "Ingestion Dry Run Summary" if dry_run else "Ingestion Write Summary"
    batch_report = summary.get("batch_report", {})
    print(header)
    print(f"- files_scanned: {summary.get('files_scanned', 0)}")
    print(f"- packets_loaded: {summary.get('packets_loaded', 0)}")
    print(f"- mapped total: {sum_counts(batch_report.get('mapped', {})) or total_mapped(summary)}")
    print(f"- written total: {sum_counts(batch_report.get('written', {})) or total_written(summary)}")
    print(f"- failed total: {sum_counts(batch_report.get('failed', {})) or total_failed(summary)}")
    print(f"- errors: {summary.get('errors', 0)}")
    print(f"- status: {batch_report.get('status', summary.get('status', 'unknown'))}")
    print(f"Batch Report: {summary.get('batch_report_path', '')}")
    error_entries = summary.get("error_entries", [])
    if error_entries:
        print("Errors")
        for error in error_entries[:10]:
            message = str(error.get("message", "")).strip()
            stage = str(error.get("stage", "")).strip() or "error"
            severity = str(error.get("severity", "")).strip() or "error"
            print(f"- [{severity}] {stage}: {message}")
    print("Packet Type Targets")
    for packet_type, table in PACKET_TARGET_TABLES.items():
        print(f"- {packet_type} -> {table}")


def normalize_filter(packet_type_filter: str | None) -> str | None:
    if not packet_type_filter:
        return None
    normalized = PACKET_TYPE_ALIASES.get(packet_type_filter, packet_type_filter)
    if normalized == "all":
        return None
    return normalized


def _normalize_packet_type_filter_label(packet_type_filter: str | None) -> str:
    if not packet_type_filter:
        return "all"
    normalized = normalize_filter(packet_type_filter) or packet_type_filter
    if normalized.endswith("_packet"):
        return normalized.removesuffix("_packet")
    return normalized


def compute_summary_status(summary: dict[str, Any], *, mode: str) -> str:
    errors = [normalize_batch_error(error) for error in summary.get("error_entries", [])]
    messages = " ".join(str(error.get("message", "")).lower() for error in errors if isinstance(error, dict))
    mapped_total = total_mapped(summary)
    written_total = total_written(summary)
    failed_total = total_failed(summary)

    if "missing required environment variables" in messages:
        return "failed"

    has_errors = bool(errors)
    has_success = mapped_total > 0 or written_total > 0

    if failed_total > 0:
        return "partial_success" if has_success else "failed"

    if mode == "dry_run":
        if has_errors:
            return "partial_success" if has_success else "failed"
        return "success" if has_success else "failed"

    if has_errors:
        return "partial_success" if has_success else "failed"
    return "success" if has_success else "failed"


def increment_mapped(summary: dict[str, Any], packet_type: str) -> None:
    key_map = {
        "event_packet": "mapped_events",
        "daily_digest_packet": "mapped_daily_digests",
        "report_packet": "mapped_reports",
        "crawl_run_packet": "mapped_crawl_runs",
        "rejected_source": "mapped_rejected_sources",
    }
    summary[key_map[packet_type]] += 1


def increment_written(summary: dict[str, Any], packet_type: str) -> None:
    key_map = {
        "event_packet": "written_events",
        "daily_digest_packet": "written_daily_digests",
        "report_packet": "written_reports",
        "crawl_run_packet": "written_crawl_runs",
        "rejected_source": "written_rejected_sources",
    }
    summary[key_map[packet_type]] += 1


def increment_failed(summary: dict[str, Any], packet_type: str) -> None:
    key_map = {
        "event_packet": "failed_events",
        "daily_digest_packet": "failed_daily_digests",
        "report_packet": "failed_reports",
        "crawl_run_packet": "failed_crawl_runs",
        "rejected_source": "failed_rejected_sources",
    }
    summary[key_map[packet_type]] += 1


def sum_counts(block: dict[str, Any]) -> int:
    return sum(int(value or 0) for value in block.values())


def total_mapped(summary: dict[str, Any]) -> int:
    return sum(
        int(summary.get(key, 0) or 0)
        for key in [
            "mapped_events",
            "mapped_daily_digests",
            "mapped_reports",
            "mapped_crawl_runs",
            "mapped_rejected_sources",
        ]
    )


def total_written(summary: dict[str, Any]) -> int:
    return sum(
        int(summary.get(key, 0) or 0)
        for key in [
            "written_events",
            "written_daily_digests",
            "written_reports",
            "written_crawl_runs",
            "written_rejected_sources",
        ]
    )


def total_failed(summary: dict[str, Any]) -> int:
    return sum(
        int(summary.get(key, 0) or 0)
        for key in [
            "failed_events",
            "failed_daily_digests",
            "failed_reports",
            "failed_crawl_runs",
            "failed_rejected_sources",
        ]
    )


def build_run_index(packets: list[dict[str, Any]]) -> dict[tuple[str, str], str]:
    index: dict[tuple[str, str], str] = {}
    for record in packets:
        packet = record["packet"]
        if detect_packet_type(packet) != "crawl_run_packet":
            continue

        run_id = str(packet.get("run_id", "") or "")
        if not run_id:
            continue

        scope = str(packet.get("scope", "") or "")
        scope_name = str(packet.get("scope_name", "") or "")
        run_date = str(packet.get("run_date", "") or "")

        if scope and scope_name:
            index[(scope, scope_name)] = run_id
        if scope and run_date:
            index[(scope, run_date)] = run_id
    return index


def enrich_packet(packet: dict[str, Any], run_index: dict[tuple[str, str], str], source_file: str) -> dict[str, Any]:
    enriched = dict(packet)
    scope = str(enriched.get("scope") or _scope_from_source_file(source_file) or "")
    scope_name = str(enriched.get("scope_name") or _scope_name_from_source_file(source_file) or scope)
    packet_date = str(
        enriched.get("event_date")
        or enriched.get("digest_date")
        or enriched.get("report_date")
        or enriched.get("run_date")
        or _date_from_source_file(source_file)
        or ""
    )

    if not enriched.get("run_id"):
        guessed_run_id = run_index.get((scope, scope_name)) or run_index.get((scope, packet_date))
        if not guessed_run_id:
            guessed_run_id = _fallback_run_id_from_source_file(source_file)
        if guessed_run_id:
            enriched["run_id"] = guessed_run_id

    if scope and not enriched.get("scope"):
        enriched["scope"] = scope
    if scope_name and not enriched.get("scope_name"):
        enriched["scope_name"] = scope_name
    return enriched


def _scope_from_source_file(source_file: str) -> str:
    name = Path(source_file).name
    if "_macro" in name:
        return "macro"
    if "_industry" in name:
        return "industry"
    if "_stock" in name:
        return "stock"
    if "_institution" in name:
        return "institution_watch"
    return ""


def _scope_name_from_source_file(source_file: str) -> str:
    parent = Path(source_file).parent.name
    if parent in {"daily", "three_day", "logs", "failed", "ingestion_logs"}:
        return ""
    return parent


def _date_from_source_file(source_file: str) -> str:
    name = Path(source_file).name
    for prefix in ("event_", "digest_", "report_", "crawl_run_"):
        if name.startswith(prefix):
            remainder = name.removeprefix(prefix)
            return remainder[:10]
    return ""


def _fallback_run_id_from_source_file(source_file: str) -> str:
    name = Path(source_file).name
    if name.startswith("crawl_run_") and name.endswith(".json"):
        return name.removeprefix("crawl_run_").removesuffix(".json")
    return ""


if __name__ == "__main__":
    main()
