from __future__ import annotations

from dataclasses import dataclass, field
import hashlib
from pathlib import Path
from typing import Any

from collector.utils.time_utils import now_iso, today_date
from ingestion.packet_detector import detect_packet_type
from ingestion.packet_loader import load_json_packets
from promotion.relation_builder import build_event_relations, build_report_relations
from promotion.promotion_report import build_promotion_report, write_promotion_report
from promotion.supabase_client import SupabaseClient, SupabaseConfigError
from promotion.upsert import upsert_row

PROJECT_ROOT = Path(__file__).resolve().parents[1]
OUTPUT_ROOT = PROJECT_ROOT / "output"
PROMOTION_LOGS_ROOT = OUTPUT_ROOT / "promotion_logs"


@dataclass(slots=True)
class PromotionBatch:
    batch_id: str
    started_at: str
    finished_at: str = ""
    input_path: str = ""
    packet_type_filter: str = "all"
    files_scanned: int = 0
    packets_loaded: int = 0
    promoted: dict[str, int] = field(default_factory=lambda: {
        "events": 0,
        "event_relations": 0,
        "reports": 0,
        "report_relations": 0,
        "crawl_runs": 0,
        "rejected_sources": 0,
    })
    skipped_daily_digests: int = 0
    errors: list[dict[str, Any]] = field(default_factory=list)

    def finish(self) -> None:
        self.finished_at = now_iso()


def promote_packets(
    *,
    input_path: str | Path,
    packet_type_filter: str = "all",
    dry_run: bool = True,
    client: SupabaseClient | None = None,
) -> dict[str, Any]:
    batch = PromotionBatch(
        batch_id=f"promotion_{now_iso().replace(':', '').replace('-', '').replace('+', '').replace('T', '_')}",
        started_at=now_iso(),
        input_path=str(input_path),
        packet_type_filter=(packet_type_filter or "all").strip().lower() or "all",
    )
    loaded_packets, load_errors = load_json_packets(input_path)
    batch.files_scanned = len({item["source_file"] for item in loaded_packets}) if loaded_packets else 0
    batch.packets_loaded = len(loaded_packets)
    batch.errors.extend(load_errors)

    promoted_rows: list[dict[str, Any]] = []
    relation_rows: list[dict[str, Any]] = []
    run_index = _build_run_index(loaded_packets)

    write_enabled = not dry_run
    if write_enabled and client is None:
        try:
            client = SupabaseClient.from_env()
        except SupabaseConfigError as exc:
            write_enabled = False
            batch.errors.append(
                {
                    "stage": "write",
                    "packet_type": "unknown",
                    "packet_id": "",
                    "target_table": "",
                    "message": str(exc),
                    "severity": "error",
                }
            )

    crawl_run_items = []
    other_items = []
    for item in loaded_packets:
        packet = item["packet"]
        if detect_packet_type(packet) == "crawl_run_packet":
            crawl_run_items.append(item)
        else:
            other_items.append(item)

    for item in crawl_run_items + other_items:
        packet = item["packet"]
        packet_type = detect_packet_type(packet)
        source_file = str(item.get("source_file") or "")
        if batch.packet_type_filter != "all" and packet_type != f"{batch.packet_type_filter}_packet":
            continue

        try:
            promoted, relations, skipped = promote_packet(
                packet_type,
                _enrich_packet(packet, run_index, source_file),
                source_file=source_file,
            )
        except Exception as exc:  # pragma: no cover - defensive
            batch.errors.append(
                {
                    "stage": "promote",
                    "packet_type": packet_type,
                    "packet_id": _packet_id(packet_type, packet),
                    "target_table": "",
                    "message": str(exc),
                    "severity": "error",
                }
            )
            continue

        if skipped:
            batch.skipped_daily_digests += 1
            continue

        promoted_rows.extend(promoted)
        relation_rows.extend(relations)

        if dry_run:
            for row in promoted:
                _increment_promoted(batch.promoted, row["target_table"])
            for relation in relations:
                relation_key = relation["target_table"]
                batch.promoted[relation_key] = batch.promoted.get(relation_key, 0) + 1
            continue

        if not write_enabled or client is None:
            continue

        try:
            for row in promoted:
                upsert_row(client, row["target_table"], row)
                _increment_promoted(batch.promoted, row["target_table"])
            _replace_child_relations(client, promoted, relations)
            for relation in relations:
                upsert_row(client, relation["target_table"], relation)
                relation_key = relation["target_table"]
                batch.promoted[relation_key] = batch.promoted.get(relation_key, 0) + 1
        except Exception as exc:  # pragma: no cover - defensive
            batch.errors.append(
                {
                    "stage": "write",
                    "packet_type": packet_type,
                    "packet_id": _packet_id(packet_type, packet),
                    "target_table": ",".join(
                        [row["target_table"] for row in promoted] + [relation["target_table"] for relation in relations]
                    ),
                    "message": str(exc),
                    "severity": "error",
                }
            )
            continue

    batch.finish()
    report = build_promotion_report(batch, promoted_rows=promoted_rows, relation_rows=relation_rows, dry_run=dry_run)
    report["wrote_to_supabase"] = bool(
        (not dry_run)
        and report.get("status") in {"success", "partial_success"}
        and sum(
            int(report.get(key, 0) or 0)
            for key in [
                "promoted_events",
                "event_relations_created",
                "reports_promoted",
                "report_relations_created",
                "crawl_runs_promoted",
                "rejected_sources_promoted",
            ]
        )
        > 0
    )
    report["batch_report_path"] = write_promotion_report(report)
    return report


def promote_packet(
    packet_type: str,
    packet: dict[str, Any],
    *,
    source_file: str = "",
) -> tuple[list[dict[str, Any]], list[dict[str, Any]], bool]:
    if packet_type == "event_packet":
        row = map_event_packet(packet, source_file=source_file)
        if not source_file:
            source_file = ""
        relations = [
            {"target_table": "event_relations", **relation}
            for relation in build_event_relations(row, packet)
        ]
        if relations:
            relations = _dedupe_relations(relations, parent_key="event_id", parent_id=row["event_id"])
        return ([{"target_table": "events", **row}], relations, False)
    if packet_type == "report_packet":
        row = map_report_packet(packet, source_file=source_file)
        relations = [
            {"target_table": "report_relations", **relation}
            for relation in build_report_relations(row, packet)
        ]
        if relations:
            relations = _dedupe_relations(relations, parent_key="report_id", parent_id=row["report_id"])
        return ([{"target_table": "reports", **row}], relations, False)
    if packet_type == "crawl_run_packet":
        return ([{"target_table": "crawl_runs", **map_crawl_run_packet(packet, source_file=source_file)}], [], False)
    if packet_type == "rejected_source":
        return ([{"target_table": "rejected_sources", **map_rejected_source(packet, source_file=source_file)}], [], False)
    if packet_type == "daily_digest_packet":
        return ([], [], True)
    return ([], [], False)


def map_event_packet(packet: dict[str, Any], *, source_file: str = "") -> dict[str, Any]:
    scope, scope_name, run_id = _derive_context(packet, source_file)
    event_id = str(packet.get("event_id") or _stable_id("event", packet))
    return {
        "event_id": event_id,
        "run_id": run_id,
        "event_date": str(packet.get("event_date") or packet.get("collection_date") or packet.get("created_at", "")[:10] or today_date()),
        "scope": scope,
        "scope_name": scope_name,
        "event_type": str(packet.get("event_type") or ""),
        "importance": str(packet.get("importance") or ""),
        "language": str(packet.get("language") or "zh-TW"),
        "title": str(packet.get("title") or ""),
        "ai_summary": str(packet.get("ai_summary") or ""),
        "possible_impact": str(packet.get("possible_impact") or ""),
        "risk_note": str(packet.get("risk_note") or ""),
        "tags": list(packet.get("tags") or []),
        "source_urls": list(packet.get("source_urls") or ([packet.get("source_url")] if packet.get("source_url") else [])),
        "quality_summary": dict(packet.get("quality_summary") or {}),
        "raw_packet": packet,
    }


def map_report_packet(packet: dict[str, Any], *, source_file: str = "") -> dict[str, Any]:
    scope, scope_name, run_id = _derive_context(packet, source_file)
    report_id = str(packet.get("report_id") or _stable_id("report", packet))
    return {
        "report_id": report_id,
        "run_id": run_id,
        "report_date": str(packet.get("report_date") or packet.get("period_end") or packet.get("created_at", "")[:10] or today_date()),
        "report_type": str(packet.get("report_type") or ""),
        "scope": scope,
        "scope_name": scope_name,
        "importance": str(packet.get("importance") or ""),
        "report_title": str(packet.get("report_title") or packet.get("title") or ""),
        "report_body": str(packet.get("report_body") or ""),
        "quality_summary": dict(packet.get("quality_summary") or {}),
        "raw_packet": packet,
    }


def map_crawl_run_packet(packet: dict[str, Any], *, source_file: str = "") -> dict[str, Any]:
    return {
        "run_id": str(packet.get("run_id") or _stable_id("run", packet)),
        "run_date": str(packet.get("run_date") or _date_from_source_file(source_file) or today_date()),
        "started_at": str(packet.get("started_at") or now_iso()),
        "finished_at": str(packet.get("finished_at") or now_iso()),
        "status": str(packet.get("status") or "success"),
        "mode": str(packet.get("mode") or "daily"),
        "scope": str(packet.get("scope") or _scope_from_source_file(source_file) or ""),
        "scope_name": str(packet.get("scope_name") or _scope_name_from_source_file(source_file) or ""),
        "source_mode": str(packet.get("source_mode") or "mock"),
        "summarizer_mode": str(packet.get("summarizer_mode") or "mock"),
        "llm_provider": str(packet.get("llm_provider") or "auto"),
        "search_provider": str(packet.get("search_provider") or "auto"),
        "total_sources_count": int(packet.get("total_sources_count", 0) or 0),
        "accepted_sources_count": int(packet.get("accepted_sources_count", 0) or 0),
        "rejected_sources_count": int(packet.get("rejected_sources_count", 0) or 0),
        "quality_summary": dict(packet.get("quality_summary") or {}),
        "rejected_reasons": list(packet.get("rejected_reasons") or []),
        "output_files": list(packet.get("output_files") or []),
        "run_errors": list(packet.get("run_errors") or []),
        "raw_packet": packet,
    }


def map_rejected_source(packet: dict[str, Any], *, source_file: str = "") -> dict[str, Any]:
    _, _, run_id = _derive_context(packet, source_file)
    return {
        "run_id": run_id,
        "source_url": str(packet.get("source_url") or ""),
        "source_name": str(packet.get("source_name") or ""),
        "source_type": str(packet.get("source_type") or ""),
        "title": str(packet.get("title") or ""),
        "content": str(packet.get("content") or ""),
        "quality_score": int(packet.get("quality_score", 0) or 0),
        "quality_level": str(packet.get("quality_level") or "rejected"),
        "quality_reasons": list(packet.get("quality_reasons") or []),
        "raw_source": packet,
    }


def _derive_context(packet: dict[str, Any], source_file: str) -> tuple[str, str, str]:
    scope = str(packet.get("scope") or _scope_from_source_file(source_file) or "")
    scope_name = str(packet.get("scope_name") or _scope_name_from_source_file(source_file) or scope)
    run_id = str(
        packet.get("run_id")
        or _fallback_run_id_from_source_file(source_file)
        or _stable_id("run", packet)
    )
    return scope, scope_name, run_id


def _build_run_index(packets: list[dict[str, Any]]) -> dict[tuple[str, str], str]:
    index: dict[tuple[str, str], str] = {}
    for item in packets:
        packet = item["packet"]
        if detect_packet_type(packet) != "crawl_run_packet":
            continue
        run_id = str(packet.get("run_id") or "")
        if not run_id:
            continue
        scope = str(packet.get("scope") or "")
        scope_name = str(packet.get("scope_name") or "")
        run_date = str(packet.get("run_date") or "")
        if scope and scope_name:
            index[(scope, scope_name)] = run_id
        if scope and run_date:
            index[(scope, run_date)] = run_id
    return index


def _enrich_packet(packet: dict[str, Any], run_index: dict[tuple[str, str], str], source_file: str) -> dict[str, Any]:
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


def _increment_promoted(counter: dict[str, int], target_table: str) -> None:
    if target_table in counter:
        counter[target_table] += 1


def _dedupe_relations(relations: list[dict[str, Any]], *, parent_key: str, parent_id: str) -> list[dict[str, Any]]:
    unique: list[dict[str, Any]] = []
    seen: set[tuple[str, str]] = set()
    for relation in relations:
        relation_type = str(relation.get("relation_type") or "")
        relation_value = str(relation.get("relation_value") or "")
        key = (relation_type, relation_value)
        if key in seen:
            continue
        seen.add(key)
        enriched = dict(relation)
        enriched[parent_key] = parent_id
        unique.append(enriched)
    return unique


def _replace_child_relations(
    client: SupabaseClient,
    promoted_rows: list[dict[str, Any]],
    relations: list[dict[str, Any]],
) -> None:
    if not relations:
        return

    relation_target = relations[0].get("target_table", "")
    if relation_target not in {"event_relations", "report_relations"}:
        return

    parent_key = "event_id" if relation_target == "event_relations" else "report_id"
    parent_ids = {
        str(relation.get(parent_key) or "")
        for relation in relations
        if str(relation.get(parent_key) or "")
    }
    if not parent_ids:
        parent_ids = {
            str(row.get(parent_key) or "")
            for row in promoted_rows
            if row.get("target_table") in {"events", "reports"}
            and str(row.get(parent_key) or "")
        }
    for parent_id in parent_ids:
        client.delete(relation_target, {parent_key: f"eq.{parent_id}"})


def _packet_id(packet_type: str, packet: dict[str, Any]) -> str:
    if packet_type == "event_packet":
        return str(packet.get("event_id") or "")
    if packet_type == "report_packet":
        return str(packet.get("report_id") or "")
    if packet_type == "crawl_run_packet":
        return str(packet.get("run_id") or "")
    if packet_type == "rejected_source":
        return str(packet.get("source_url") or "")
    return ""


def _stable_id(prefix: str, packet: dict[str, Any]) -> str:
    base = packet.get("event_id") or packet.get("report_id") or packet.get("run_id") or packet.get("source_url") or packet.get("title") or prefix
    digest = hashlib.sha1(str(base).encode("utf-8")).hexdigest()[:12]
    return f"{prefix}_{digest}"
