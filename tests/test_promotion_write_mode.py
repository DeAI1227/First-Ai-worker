from __future__ import annotations

import os
import subprocess
import sys
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import patch

from api.services.promotion_service import run_promotion_sync
from collector.config.tracking_universe import TRACKING_INDUSTRIES, TRACKED_STOCKS
from promotion.packet_promoter import promote_packets
from promotion.relation_builder import build_event_relations
from promotion.upsert import upsert_row


class _MockSupabaseClient:
    def __init__(self) -> None:
        self.upserts: list[tuple[str, dict, str | None]] = []
        self.inserts: list[tuple[str, dict]] = []
        self.deletes: list[tuple[str, dict[str, str]]] = []

    def upsert(self, table: str, row: dict, *, on_conflict: str):
        self.upserts.append((table, row, on_conflict))
        return [row]

    def insert(self, table: str, row: dict):
        self.inserts.append((table, row))
        return [row]

    def delete(self, table: str, filters: dict[str, str]):
        self.deletes.append((table, filters))
        return []


def _write_packet(path: Path, payload: dict) -> None:
    path.write_text(__import__("json").dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")


class PromotionWriteModeTests(unittest.TestCase):
    def test_write_mode_missing_supabase_env_fails_cleanly(self) -> None:
        with TemporaryDirectory() as tmpdir:
            input_root = Path(tmpdir)
            _write_packet(
                input_root / "event.json",
                {
                    "event_id": "event_001",
                    "run_id": "run_001",
                    "event_date": "2026-06-17",
                    "scope": "industry",
                    "scope_name": TRACKING_INDUSTRIES[0]["industry_name"],
                    "event_type": "industry",
                    "importance": "important",
                    "language": "zh-TW",
                    "title": "title",
                    "ai_summary": "summary",
                    "possible_impact": "impact",
                    "risk_note": "risk",
                    "tags": ["thermal"],
                    "related_industries": [TRACKING_INDUSTRIES[0]["industry_name"]],
                    "related_stocks": ["6230"],
                    "related_macro_topics": ["fed_rate"],
                    "source_urls": ["https://example.com/a"],
                    "quality_summary": {"total_sources": 1, "high": 1, "medium": 0, "low": 0, "rejected": 0},
                },
            )

            with patch.dict(os.environ, {}, clear=True):
                result = run_promotion_sync(input_path=input_root, dry_run=False)

            self.assertEqual(result["status"], "failed")
            self.assertEqual(result["mode"], "write")
            self.assertEqual(result["message"], "Promotion write mode failed.")
            self.assertTrue(result["errors"])
            self.assertIn("SUPABASE_URL", result["errors"][0]["message"])

    def test_write_mode_with_mock_client_upserts_all_tables(self) -> None:
        with TemporaryDirectory() as tmpdir:
            input_root = Path(tmpdir)
            industry_name = TRACKING_INDUSTRIES[0]["industry_name"]
            stock_code = TRACKED_STOCKS[0]["stock_code"]
            _write_packet(
                input_root / "event.json",
                {
                    "event_id": "event_001",
                    "run_id": "run_001",
                    "event_date": "2026-06-17",
                    "scope": "industry",
                    "scope_name": industry_name,
                    "event_type": "industry",
                    "importance": "important",
                    "language": "zh-TW",
                    "title": "title",
                    "ai_summary": "summary",
                    "possible_impact": "impact",
                    "risk_note": "risk",
                    "tags": ["thermal"],
                    "related_industries": [industry_name],
                    "related_stocks": [stock_code, "2308"],
                    "related_macro_topics": ["fed_rate"],
                    "related_institution_watch": ["2330"],
                    "source_urls": ["https://example.com/a"],
                    "quality_summary": {"total_sources": 1, "high": 1, "medium": 0, "low": 0, "rejected": 0},
                },
            )
            _write_packet(
                input_root / "report.json",
                {
                    "report_id": "report_001",
                    "run_id": "run_001",
                    "report_type": "industry_report",
                    "title": "report title",
                    "period_start": "2026-06-15",
                    "period_end": "2026-06-17",
                    "importance": "important",
                    "executive_summary": "summary",
                    "report_body": "body",
                    "related_industries": [industry_name],
                    "related_stocks": [stock_code, "2308"],
                    "related_events": ["event_001"],
                    "related_macro_topics": ["fed_rate"],
                    "related_institution_watch": ["2330"],
                    "source_count": 1,
                    "created_at": "2026-06-17T08:00:00+08:00",
                    "language": "zh-TW",
                },
            )
            _write_packet(
                input_root / "crawl.json",
                {
                    "run_id": "run_001",
                    "run_date": "2026-06-17",
                    "started_at": "2026-06-17T08:00:00+08:00",
                    "finished_at": "2026-06-17T08:01:00+08:00",
                    "status": "success",
                    "mode": "daily",
                    "scope": "industry",
                    "scope_name": industry_name,
                    "source_mode": "mock",
                    "summarizer_mode": "mock",
                    "llm_provider": "auto",
                    "search_provider": "auto",
                    "total_sources_count": 1,
                    "accepted_sources_count": 1,
                    "rejected_sources_count": 0,
                    "quality_summary": {"total_sources": 1, "high": 1, "medium": 0, "low": 0, "rejected": 0},
                    "rejected_reasons": [],
                    "output_files": [],
                    "run_errors": [],
                    "raw_packet": {},
                },
            )
            _write_packet(
                input_root / "rejected.json",
                {
                    "run_id": "run_001",
                    "source_url": "https://example.com/rejected",
                    "source_name": "Example",
                    "source_type": "rss",
                    "title": "rejected title",
                    "content": "content",
                    "quality_score": 0,
                    "quality_level": "rejected",
                    "quality_reasons": ["too short"],
                    "raw_source": {"source_url": "https://example.com/rejected"},
                },
            )

            client = _MockSupabaseClient()
            report = promote_packets(input_path=input_root, dry_run=False, client=client)

            self.assertEqual(report["status"], "success")
            self.assertEqual(report["promotion_id"], report["batch_id"])
            self.assertEqual(report["promoted_events"], 1)
            self.assertEqual(report["reports_promoted"], 1)
            self.assertEqual(report["crawl_runs_promoted"], 1)
            self.assertEqual(report["rejected_sources_promoted"], 1)
            self.assertGreaterEqual(report["event_relations_created"], 4)
            self.assertGreaterEqual(report["report_relations_created"], 4)
            self.assertIn("promotion_run_", Path(report["batch_report_path"]).name)

            upsert_tables = [table for table, _, _ in client.upserts]
            insert_tables = [table for table, _ in client.inserts]
            self.assertIn("events", upsert_tables)
            self.assertIn("reports", upsert_tables)
            self.assertIn("crawl_runs", upsert_tables)
            self.assertIn("event_relations", upsert_tables)
            self.assertIn("report_relations", upsert_tables)
            self.assertIn("rejected_sources", insert_tables)
            self.assertTrue(any(table == "event_relations" for table, _ in client.deletes))
            self.assertTrue(any(table == "report_relations" for table, _ in client.deletes))

            event_relations = [row for table, row, _ in client.upserts if table == "event_relations"]
            self.assertTrue(any(row["relation_type"] == "industry" and row["relation_value"] == industry_name for row in event_relations))
            self.assertTrue(any(row["relation_type"] == "stock" and row["relation_value"] == stock_code for row in event_relations))
            self.assertFalse(any(row["relation_type"] == "industry" and row["relation_value"] == stock_code for row in event_relations))
            self.assertFalse(any(row["relation_type"] == "stock" and row["relation_value"] == industry_name for row in event_relations))
            self.assertTrue(any(filters.get("event_id") == "eq.event_001" for _, filters in client.deletes))
            self.assertTrue(any(filters.get("report_id") == "eq.report_001" for _, filters in client.deletes))

    def test_relation_builder_skips_mismatched_industry_and_stock_values(self) -> None:
        industry_name = TRACKING_INDUSTRIES[0]["industry_name"]
        stock_code = TRACKED_STOCKS[0]["stock_code"]
        event_packet = {
            "event_id": "event_002",
            "related_industries": [stock_code, industry_name],
            "related_stocks": [industry_name, stock_code],
            "related_macro_topics": ["fed_rate"],
            "related_institution_watch": ["2330"],
        }
        relations = build_event_relations({"event_id": "event_002"}, event_packet)
        self.assertTrue(any(row["relation_type"] == "industry" and row["relation_value"] == industry_name for row in relations))
        self.assertTrue(any(row["relation_type"] == "stock" and row["relation_value"] == stock_code for row in relations))
        self.assertFalse(any(row["relation_type"] == "industry" and row["relation_value"] == stock_code for row in relations))
        self.assertFalse(any(row["relation_type"] == "stock" and row["relation_value"] == industry_name for row in relations))

    def test_promotion_cli_write_mode_missing_keys_fails_cleanly(self) -> None:
        with TemporaryDirectory() as tmpdir:
            input_root = Path(tmpdir) / "input"
            input_root.mkdir(parents=True, exist_ok=True)
            env = os.environ.copy()
            env.pop("SUPABASE_URL", None)
            env.pop("SUPABASE_SERVICE_ROLE_KEY", None)
            result = subprocess.run(
                [sys.executable, "-m", "promotion.promote_staging", "--input", str(input_root)],
                cwd=Path(__file__).resolve().parents[1],
                capture_output=True,
                text=True,
                env=env,
            )
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("Promotion Write Summary", result.stdout)
        self.assertIn("failed", result.stdout.lower())

    def test_upsert_row_routes_to_expected_tables(self) -> None:
        client = _MockSupabaseClient()
        upsert_row(client, "events", {"event_id": "event_001"})
        upsert_row(client, "event_relations", {"event_id": "event_001", "relation_type": "stock", "relation_value": "6230"})
        upsert_row(client, "rejected_sources", {"run_id": "run_001", "source_url": "https://example.com/a"})

        self.assertEqual(client.upserts[0][0], "events")
        self.assertEqual(client.upserts[0][2], "event_id")
        self.assertEqual(client.upserts[1][0], "event_relations")
        self.assertEqual(client.upserts[1][2], "event_id,relation_type,relation_value")
        self.assertEqual(client.inserts[0][0], "rejected_sources")


if __name__ == "__main__":
    unittest.main()
