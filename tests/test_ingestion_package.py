from __future__ import annotations

import json
import os
import subprocess
import tempfile
import unittest
from pathlib import Path
from unittest.mock import Mock, patch

from ingestion.error_logger import build_ingestion_error
from ingestion.batch_report import build_batch_report, status_from_batch_report, write_batch_report
from ingestion.ingest_outputs import dry_run_ingest, write_ingest
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


class IngestionPackageTests(unittest.TestCase):
    def test_batch_report_builds_summary_dict(self):
        report = build_batch_report(
            mode="dry_run",
            input_path="output/",
            packet_type_filter="event",
            started_at="2026-06-17T01:00:00+08:00",
            finished_at="2026-06-17T01:01:00+08:00",
            summary={
                "files_scanned": 1,
                "packets_loaded": 2,
                "unknown_packets": 0,
                "mapped_events": 1,
                "mapped_daily_digests": 0,
                "mapped_reports": 0,
                "mapped_crawl_runs": 0,
                "mapped_rejected_sources": 0,
                "written_events": 0,
                "written_daily_digests": 0,
                "written_reports": 0,
                "written_crawl_runs": 0,
                "written_rejected_sources": 0,
                "errors": 0,
            },
        )

        self.assertIn("batch_id", report)
        self.assertIn("started_at", report)
        self.assertIn("finished_at", report)
        self.assertEqual(report["mode"], "dry_run")
        self.assertEqual(report["packet_type_filter"], "event")
        self.assertEqual(report["status"], "success")

    def test_write_batch_report_creates_json_file(self):
        report = build_batch_report(
            mode="dry_run",
            input_path="output/",
            packet_type_filter="all",
            started_at="2026-06-17T01:00:00+08:00",
            finished_at="2026-06-17T01:01:00+08:00",
            summary={
                "files_scanned": 0,
                "packets_loaded": 0,
                "unknown_packets": 0,
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
                "errors": 0,
            },
        )

        with tempfile.TemporaryDirectory() as tmpdir:
            path = write_batch_report(report, output_root=Path(tmpdir))
            self.assertTrue(path.endswith(".json"))
            self.assertIn("ingestion_logs", path)
            self.assertTrue(Path(path).exists())

    def test_status_from_batch_report_success(self):
        report = {
            "errors": [],
            "mapped": {"events": 1, "daily_digests": 0, "reports": 0, "crawl_runs": 0, "rejected_sources": 0},
            "written": {"events": 1, "daily_digests": 0, "reports": 0, "crawl_runs": 0, "rejected_sources": 0},
            "failed": {"events": 0, "daily_digests": 0, "reports": 0, "crawl_runs": 0, "rejected_sources": 0},
        }
        self.assertEqual(status_from_batch_report(report), "success")

    def test_status_from_batch_report_partial_success(self):
        report = {
            "errors": [{"message": "fallback"}],
            "mapped": {"events": 1, "daily_digests": 0, "reports": 0, "crawl_runs": 0, "rejected_sources": 0},
            "written": {"events": 1, "daily_digests": 0, "reports": 0, "crawl_runs": 0, "rejected_sources": 0},
            "failed": {"events": 0, "daily_digests": 0, "reports": 0, "crawl_runs": 0, "rejected_sources": 0},
        }
        self.assertEqual(status_from_batch_report(report), "partial_success")

    def test_status_from_batch_report_failed(self):
        report = {
            "errors": [{"message": "boom"}],
            "mapped": {"events": 0, "daily_digests": 0, "reports": 0, "crawl_runs": 0, "rejected_sources": 0},
            "written": {"events": 0, "daily_digests": 0, "reports": 0, "crawl_runs": 0, "rejected_sources": 0},
            "failed": {"events": 0, "daily_digests": 0, "reports": 0, "crawl_runs": 0, "rejected_sources": 0},
        }
        self.assertEqual(status_from_batch_report(report), "failed")

    def test_packet_loader_reads_json(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            (root / "nested").mkdir()
            (root / "nested" / "event.json").write_text(
                json.dumps({"event_id": "event-1", "packet_type": "event"}),
                encoding="utf-8",
            )

            packets, errors = load_json_packets(root)

            self.assertEqual(len(packets), 1)
            self.assertEqual(errors, [])
            self.assertEqual(packets[0]["packet"]["event_id"], "event-1")

    def test_packet_loader_ignores_bad_json(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            (root / "bad.json").write_text("{bad json", encoding="utf-8")

            packets, errors = load_json_packets(root)

            self.assertEqual(packets, [])
            self.assertEqual(len(errors), 1)
            self.assertEqual(errors[0]["target_table"], "packet_loader")

    def test_packet_loader_skips_non_packet_log_files(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            logs_dir = root / "logs"
            logs_dir.mkdir(parents=True)
            (logs_dir / "batch_run_2026-06-22_010203.json").write_text(
                json.dumps({"status": "success"}),
                encoding="utf-8",
            )
            (logs_dir / "crawl_run_2026-06-22_macro.json").write_text(
                json.dumps({"run_id": "run-1", "packet_type": "crawl_run"}),
                encoding="utf-8",
            )

            packets, errors = load_json_packets(root)

            self.assertEqual(len(packets), 1)
            self.assertEqual(errors, [])
            self.assertEqual(packets[0]["packet"]["run_id"], "run-1")

    def test_packet_detector_recognizes_event_packet(self):
        self.assertEqual(detect_packet_type({"event_id": "event-1"}), "event_packet")

    def test_packet_detector_recognizes_daily_digest_packet(self):
        self.assertEqual(detect_packet_type({"digest_id": "digest-1"}), "daily_digest_packet")

    def test_packet_detector_recognizes_report_packet(self):
        self.assertEqual(detect_packet_type({"report_id": "report-1"}), "report_packet")

    def test_packet_detector_recognizes_crawl_run_packet(self):
        self.assertEqual(
            detect_packet_type({"run_id": "run-1", "source_mode": "mock", "quality_summary": {}}),
            "crawl_run_packet",
        )

    def test_mappers_map_event_packet(self):
        packet = {
            "event_id": "event-1",
            "run_id": "run-1",
            "event_date": "2026-06-17",
            "scope": "industry",
            "scope_name": "散熱",
            "event_type": "industry",
            "importance": "important",
            "language": "zh-TW",
            "ai_summary": "summary",
            "possible_impact": "impact",
            "risk_note": "risk",
            "tags": ["thermal"],
            "related_industries": ["散熱"],
            "related_stocks": ["6230"],
            "source_urls": ["https://example.com/a"],
        }

        row = map_event_packet(packet)

        self.assertEqual(row["event_id"], "event-1")
        self.assertEqual(row["raw_packet"], packet)
        self.assertEqual(row["tags"], ["thermal"])

    def test_mappers_generate_stable_ids_without_source_file(self):
        event_packet = {
            "run_id": "run-1",
            "event_date": "2026-06-17",
            "scope": "industry",
            "scope_name": "?q?O",
            "event_type": "industry",
            "importance": "important",
            "language": "zh-TW",
            "ai_summary": "summary",
            "possible_impact": "impact",
            "risk_note": "risk",
            "tags": ["thermal"],
            "related_industries": ["?q?O"],
            "related_stocks": ["1513"],
            "source_urls": ["https://example.com/a"],
        }
        digest_packet = {
            "run_id": "run-1",
            "created_at": "2026-06-17T01:00:00+08:00",
            "digest_date": "2026-06-17",
            "scope": "industry",
            "scope_name": "?q?O",
            "summary": "digest summary",
            "important_events": ["event-1"],
            "quality_summary": {"total_sources": 1},
            "rejected_reasons": ["missing url"],
        }
        report_packet = {
            "run_id": "run-1",
            "created_at": "2026-06-17T01:00:00+08:00",
            "report_date": "2026-06-17",
            "report_type": "industry_report",
            "scope": "industry",
            "scope_name": "?q?O",
            "importance": "important",
            "report_title": "?q?O???i",
            "report_body": "body",
            "quality_summary": {"total_sources": 1},
        }

        event_row_a = map_event_packet(event_packet, source_file="output/daily/?q?O/event_a.json")
        event_row_b = map_event_packet({**event_packet, "run_id": "run-2"}, source_file="output/daily/?q?O/event_b.json")
        digest_row_a = map_daily_digest_packet(digest_packet, source_file="output/daily/?q?O/digest_a.json")
        digest_row_b = map_daily_digest_packet({**digest_packet, "run_id": "run-2", "created_at": "2026-06-17T09:00:00+08:00"}, source_file="output/daily/?q?O/digest_b.json")
        report_row_a = map_report_packet(report_packet, source_file="output/three_day/?q?O/report_a.json")
        report_row_b = map_report_packet({**report_packet, "run_id": "run-2", "created_at": "2026-06-17T09:00:00+08:00"}, source_file="output/three_day/?q?O/report_b.json")

        self.assertEqual(event_row_a["event_id"], event_row_b["event_id"])
        self.assertEqual(digest_row_a["digest_id"], digest_row_b["digest_id"])
        self.assertEqual(report_row_a["report_id"], report_row_b["report_id"])


    def test_mappers_map_daily_digest_packet(self):
        packet = {
            "digest_id": "digest-1",
            "run_id": "run-1",
            "digest_date": "2026-06-17",
            "scope": "industry",
            "scope_name": "散熱",
            "summary": "digest summary",
            "important_events": ["event-1"],
            "quality_summary": {"total_sources": 1},
            "rejected_reasons": ["missing url"],
        }

        row = map_daily_digest_packet(packet)

        self.assertEqual(row["digest_id"], "digest-1")
        self.assertEqual(row["raw_packet"], packet)
        self.assertEqual(
            row["quality_summary"],
            {"total_sources": 1, "high": 0, "medium": 0, "low": 0, "rejected": 0},
        )

    def test_mappers_map_report_packet(self):
        packet = {
            "report_id": "report-1",
            "run_id": "run-1",
            "report_date": "2026-06-17",
            "report_type": "industry_report",
            "scope": "industry",
            "scope_name": "散熱",
            "importance": "important",
            "report_title": "散熱三日報告",
            "report_body": "body",
            "quality_summary": {"total_sources": 1},
        }

        row = map_report_packet(packet)

        self.assertEqual(row["report_id"], "report-1")
        self.assertEqual(row["raw_packet"], packet)

    def test_mappers_map_crawl_run_packet(self):
        packet = {
            "run_id": "run-1",
            "run_date": "2026-06-17",
            "started_at": "2026-06-17T01:00:00+08:00",
            "finished_at": "2026-06-17T01:01:00+08:00",
            "status": "success",
            "mode": "daily",
            "scope": "industry",
            "scope_name": "散熱",
            "source_mode": "mock",
            "summarizer_mode": "mock",
            "llm_provider": "auto",
            "search_provider": "auto",
            "total_sources_count": 1,
            "accepted_sources_count": 1,
            "rejected_sources_count": 0,
            "quality_summary": {"total_sources": 1},
            "rejected_reasons": [],
            "output_files": ["output/daily/散熱/event.json"],
            "run_errors": [],
        }

        row = map_crawl_run_packet(packet)

        self.assertEqual(row["run_id"], "run-1")
        self.assertEqual(row["raw_packet"], packet)
        self.assertEqual(row["output_files"], ["output/daily/散熱/event.json"])

    def test_mappers_map_rejected_source(self):
        packet = {
            "run_id": "run-1",
            "source_url": "https://example.com/rejected",
            "source_name": "Example",
            "source_type": "rss",
            "title": "Rejected",
            "content": "content",
            "quality_score": 10,
            "quality_level": "rejected",
            "quality_reasons": ["missing url"],
            "raw_source": {"title": "Rejected"},
        }

        row = map_rejected_source(packet)

        self.assertEqual(row["run_id"], "run-1")
        self.assertEqual(row["raw_source"], packet["raw_source"])

    def test_dry_run_cli_can_execute(self):
        result = subprocess.run(
            [
                "python",
                "-m",
                "ingestion.ingest_outputs",
                "--input",
                "output/",
                "--dry-run",
            ],
            cwd=Path(__file__).resolve().parents[1],
            capture_output=True,
            text=True,
            check=True,
        )

        self.assertIn("Ingestion Dry Run Summary", result.stdout)
        self.assertIn("mapped total", result.stdout)
        self.assertIn("Batch Report:", result.stdout)

    def test_write_mode_cli_missing_keys_exits_cleanly(self):
        env = os.environ.copy()
        env.pop("SUPABASE_URL", None)
        env.pop("SUPABASE_SERVICE_ROLE_KEY", None)
        result = subprocess.run(
            [
                "python",
                "-m",
                "ingestion.ingest_outputs",
                "--input",
                "output/",
            ],
            cwd=Path(__file__).resolve().parents[1],
            capture_output=True,
            text=True,
            env=env,
        )

        self.assertNotEqual(result.returncode, 0)
        self.assertIn("Missing required environment variables", result.stderr + result.stdout)
        self.assertIn("Batch Report:", result.stderr + result.stdout)
        self.assertIn("Ingestion Write Summary", result.stderr + result.stdout)
        self.assertIn("status: failed", (result.stderr + result.stdout).lower())

    def test_ingestion_error_structure(self):
        error = build_ingestion_error(
            packet_type="event_packet",
            packet_id="event-1",
            target_table="staging_events",
            error_message="boom",
            raw_packet={"event_id": "event-1"},
        )

        self.assertEqual(error["packet_type"], "event_packet")
        self.assertEqual(error["target_table"], "staging_events")
        self.assertIn("created_at", error)

    def test_dry_run_does_not_require_supabase_key(self):
        summary = dry_run_ingest(Path("output"), packet_type_filter="event_packet")
        self.assertIn("files_scanned", summary)

    def test_supabase_client_reads_environment_variables(self):
        env = {
            "SUPABASE_URL": "https://example.supabase.co",
            "SUPABASE_SERVICE_ROLE_KEY": "service-role-key",
        }
        with patch.dict(os.environ, env, clear=True):
            client = SupabaseClient.from_env()

        self.assertEqual(client.url, env["SUPABASE_URL"])
        self.assertEqual(client.key, env["SUPABASE_SERVICE_ROLE_KEY"])

    def test_supabase_client_missing_environment_variables_raises(self):
        with patch.dict(os.environ, {}, clear=True):
            with self.assertRaises(SupabaseConfigError):
                SupabaseClient.from_env()

    def test_route_upsert_uses_event_id_for_event_packet(self):
        client = Mock()
        row = {"event_id": "event-1"}
        route_upsert(client, "event_packet", row)
        client.upsert.assert_called_once()
        args, kwargs = client.upsert.call_args
        self.assertEqual(args[0], "staging_events")
        self.assertEqual(kwargs["on_conflict"], "event_id")

    def test_route_upsert_uses_append_only_for_rejected_source(self):
        client = Mock()
        row = {"run_id": "run-1", "source_url": "https://example.com"}
        route_upsert(client, "rejected_source", row)
        client.insert.assert_called_once()
        args, _ = client.insert.call_args
        self.assertEqual(args[0], "staging_rejected_sources")

    def test_write_mode_missing_keys_creates_failed_summary(self):
        with patch.dict(os.environ, {}, clear=True):
            summary = write_ingest(Path("output"), packet_type_filter="event_packet", client=None, allow_missing_config=False)

        self.assertGreaterEqual(summary["errors"], 1)
        self.assertEqual(summary["status"], "failed")

    def test_write_mode_uses_mock_client_and_records_errors(self):
        fake_client = Mock()
        fake_client.upsert.side_effect = [True]
        fake_client.insert.return_value = True
        fake_client.insert_error.return_value = True

        summary = write_ingest(Path("output"), packet_type_filter="event_packet", client=fake_client, allow_missing_config=True)

        self.assertIn("written_events", summary)
        self.assertGreaterEqual(summary["written_events"], 0)

    def test_write_mode_records_ingestion_error_on_single_failure(self):
        fake_client = Mock()
        fake_client.upsert.side_effect = RuntimeError("boom")
        fake_client.insert_error.return_value = True

        summary = write_ingest(Path("output"), packet_type_filter="event_packet", client=fake_client, allow_missing_config=True)

        self.assertGreaterEqual(summary["errors"], 1)
        fake_client.insert_error.assert_called()


if __name__ == "__main__":
    unittest.main()
