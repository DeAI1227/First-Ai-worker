from __future__ import annotations

import subprocess
import sys
import unittest
from pathlib import Path
import os
from tempfile import TemporaryDirectory

from promotion.packet_promoter import promote_packets
from promotion.relation_builder import build_event_relations, build_report_relations
from collector.config.tracking_universe import TRACKING_INDUSTRIES, TRACKED_STOCKS


class ProductionPromotionTests(unittest.TestCase):
    @property
    def project_root(self) -> Path:
        return Path(__file__).resolve().parents[1]

    def test_production_schema_files_exist(self) -> None:
        schema = self.project_root / "supabase" / "production_schema.sql"
        readme = self.project_root / "supabase" / "production_schema_readme.md"
        mapping = self.project_root / "supabase" / "staging_to_production_mapping.md"
        views = self.project_root / "supabase" / "frontend_query_views.sql"
        contract = self.project_root / "supabase" / "frontend_query_contract.md"
        self.assertTrue(schema.exists())
        self.assertTrue(readme.exists())
        self.assertTrue(mapping.exists())
        self.assertTrue(views.exists())
        self.assertTrue(contract.exists())

        content = schema.read_text(encoding="utf-8")
        for needle in [
            "create table if not exists industries",
            "create table if not exists events",
            "create table if not exists report_relations",
            "create table if not exists user_read_status",
            "create or replace view view_dashboard_events",
            "create or replace view view_industry_cards",
            "create or replace view view_stock_cards",
            "create or replace view view_stock_detail_events",
            "create or replace view view_macro_events",
            "create or replace view view_institution_watch_events",
            "create or replace view view_recent_reports",
            "create or replace view view_unread_counts",
        ]:
            self.assertIn(needle, content)

    def test_relation_builder_maps_event_and_report_relations(self) -> None:
        event_packet = {
            "event_id": "event_001",
            "related_industries": ["散熱"],
            "related_stocks": ["6230"],
            "related_macro_topics": ["fed_rate"],
            "related_institution_watch": ["2330"],
        }
        report_packet = {
            "report_id": "report_001",
            "related_industries": ["散熱"],
            "related_stocks": ["6230"],
            "related_events": ["event_001"],
            "related_macro_topics": ["fed_rate"],
            "related_institution_watch": ["2330"],
        }

        event_relations = build_event_relations({"event_id": "event_001"}, event_packet)
        report_relations = build_report_relations({"report_id": "report_001"}, report_packet)

        self.assertTrue(any(item["relation_type"] == "industry" and item["relation_value"] == "散熱" for item in event_relations))
        self.assertTrue(any(item["relation_type"] == "stock" and item["relation_value"] == "6230" for item in event_relations))
        self.assertTrue(any(item["relation_type"] == "macro_topic" and item["relation_value"] == "fed_rate" for item in event_relations))
        self.assertTrue(any(item["relation_type"] == "event" and item["relation_value"] == "event_001" for item in report_relations))

    def test_relation_builder_rejects_mismatched_industry_and_stock_values(self) -> None:
        industry_name = TRACKING_INDUSTRIES[0]["industry_name"]
        stock_code = TRACKED_STOCKS[0]["stock_code"]
        event_packet = {
            "event_id": "event_002",
            "related_industries": [stock_code, industry_name],
            "related_stocks": [industry_name, stock_code],
        }

        relations = build_event_relations({"event_id": "event_002"}, event_packet)

        self.assertTrue(any(item["relation_type"] == "industry" and item["relation_value"] == industry_name for item in relations))
        self.assertTrue(any(item["relation_type"] == "stock" and item["relation_value"] == stock_code for item in relations))
        self.assertFalse(any(item["relation_type"] == "industry" and item["relation_value"] == stock_code for item in relations))
        self.assertFalse(any(item["relation_type"] == "stock" and item["relation_value"] == industry_name for item in relations))

    def test_unread_view_uses_user_read_status(self) -> None:
        schema = (self.project_root / "supabase" / "production_schema.sql").read_text(encoding="utf-8")
        self.assertIn("create table if not exists user_read_status", schema)
        self.assertIn("create or replace view view_unread_counts", schema)
        self.assertIn("from user_read_status", schema)

    def test_promotion_dry_run_skips_daily_digest_and_builds_report(self) -> None:
        with TemporaryDirectory() as tmpdir:
            input_root = Path(tmpdir) / "input"
            input_root.mkdir(parents=True, exist_ok=True)
            (input_root / "event.json").write_text(
                """
                {
                  "event_id": "event_001",
                  "run_id": "run_001",
                  "event_date": "2026-06-17",
                  "scope": "industry",
                  "scope_name": "散熱",
                  "event_type": "industry",
                  "importance": "important",
                  "language": "zh-TW",
                  "title": "測試事件",
                  "ai_summary": "摘要",
                  "possible_impact": "影響",
                  "risk_note": "風險",
                  "tags": ["a"],
                  "related_industries": ["散熱"],
                  "related_stocks": ["6230"],
                  "related_macro_topics": ["fed_rate"],
                  "source_urls": ["https://example.com/a"],
                  "quality_summary": {"total_sources": 1, "high": 1, "medium": 0, "low": 0, "rejected": 0}
                }
                """,
                encoding="utf-8",
            )
            (input_root / "digest.json").write_text(
                """
                {
                  "digest_id": "digest_001",
                  "run_id": "run_001",
                  "digest_date": "2026-06-17",
                  "scope": "industry",
                  "scope_name": "散熱",
                  "summary": "摘要",
                  "important_events": [],
                  "quality_summary": {"total_sources": 1, "high": 1, "medium": 0, "low": 0, "rejected": 0},
                  "rejected_reasons": [],
                  "raw_packet": {}
                }
                """,
                encoding="utf-8",
            )

            report = promote_packets(input_path=input_root, dry_run=True)
            self.assertEqual(report["promoted_events"], 1)
            self.assertEqual(report["event_relations_created"], 3)
            self.assertEqual(report["reports_promoted"], 0)
            self.assertEqual(report["skipped_daily_digests"], 1)
            self.assertEqual(report["status"], "success")
            self.assertTrue(report["batch_report_path"].endswith(".json"))

    def test_promotion_cli_runs_in_dry_run_mode(self) -> None:
        with TemporaryDirectory() as tmpdir:
            input_root = Path(tmpdir) / "input"
            input_root.mkdir(parents=True, exist_ok=True)
            (input_root / "crawl.json").write_text(
                """
                {
                  "run_id": "run_001",
                  "run_date": "2026-06-17",
                  "started_at": "2026-06-17T08:00:00+08:00",
                  "finished_at": "2026-06-17T08:01:00+08:00",
                  "status": "success",
                  "mode": "daily",
                  "scope": "macro",
                  "scope_name": "大環境",
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
                  "raw_packet": {}
                }
                """,
                encoding="utf-8",
            )
            result = subprocess.run(
                [sys.executable, "-m", "promotion.promote_staging", "--input", str(input_root), "--dry-run"],
                cwd=self.project_root,
                capture_output=True,
                text=True,
            )
            self.assertEqual(result.returncode, 0, msg=result.stderr)
            self.assertIn("Promotion Dry Run Summary", result.stdout)

    def test_promotion_cli_write_mode_missing_keys_fails_cleanly(self) -> None:
        with TemporaryDirectory() as tmpdir:
            input_root = Path(tmpdir) / "input"
            input_root.mkdir(parents=True, exist_ok=True)
            env = os.environ.copy()
            env.pop("SUPABASE_URL", None)
            env.pop("SUPABASE_SERVICE_ROLE_KEY", None)
            result = subprocess.run(
                [sys.executable, "-m", "promotion.promote_staging", "--input", str(input_root)],
                cwd=self.project_root,
                capture_output=True,
                text=True,
                env=env,
            )
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("Promotion Write Summary", result.stdout)
        self.assertIn("failed", result.stdout.lower())


if __name__ == "__main__":
    unittest.main()
