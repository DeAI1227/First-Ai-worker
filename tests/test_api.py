from __future__ import annotations

import os
from contextlib import ExitStack
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import patch

from fastapi.testclient import TestClient

from api.main import app
from api.services import pipeline_service
from collector import batch_runner, coverage_report
from collector.nodes import writer
from ingestion import batch_report as ingestion_batch_report
from promotion import packet_promoter, promotion_report


class ApiTests(unittest.TestCase):
    def setUp(self) -> None:
        self._original_token = getattr(app.state, "api_auth_token", "")
        app.state.api_auth_token = "test-token"
        self.client = TestClient(app)

    def tearDown(self) -> None:
        app.state.api_auth_token = self._original_token

    def _open_pipeline_output_patches(self, output_root: Path):
        stack = ExitStack()
        stack.enter_context(patch.object(writer, "OUTPUT_ROOT", output_root))
        stack.enter_context(patch.object(batch_runner, "OUTPUT_ROOT", output_root))
        stack.enter_context(patch.object(batch_runner, "BATCH_LOGS_ROOT", output_root / "logs"))
        stack.enter_context(patch.object(coverage_report, "OUTPUT_ROOT", output_root))
        stack.enter_context(patch.object(coverage_report, "COVERAGE_LOGS_ROOT", output_root / "logs"))
        stack.enter_context(patch.object(ingestion_batch_report, "OUTPUT_ROOT", output_root))
        stack.enter_context(patch.object(ingestion_batch_report, "BATCH_LOGS_ROOT", output_root / "ingestion_logs"))
        stack.enter_context(patch.object(packet_promoter, "OUTPUT_ROOT", output_root))
        stack.enter_context(patch.object(packet_promoter, "PROMOTION_LOGS_ROOT", output_root / "promotion_logs"))
        stack.enter_context(patch.object(promotion_report, "OUTPUT_ROOT", output_root))
        stack.enter_context(patch.object(promotion_report, "PROMOTION_LOGS_ROOT", output_root / "promotion_logs"))
        stack.enter_context(patch.object(pipeline_service, "OUTPUT_ROOT", output_root))
        return stack

    def assert_api_envelope(self, body: dict, *, expected_statuses: set[str] | None = None) -> None:
        self.assertIn(body["status"], expected_statuses or {"success", "partial_success", "failed", "accepted"})
        self.assertIn(body["execution_mode"], {"sync", "async"})
        self.assertIsNone(body["job_id"])
        self.assertIsInstance(body["message"], str)
        self.assertIsInstance(body["data"], dict)
        self.assertIsInstance(body["errors"], list)
        for error in body["errors"]:
            self.assertIn(error["stage"], {"auth", "validate_request", "collect", "ingestion", "promotion", "internal"})
            self.assertIn(error["severity"], {"info", "warning", "error"})
            self.assertIsInstance(error["message"], str)
            self.assertIsInstance(error["details"], dict)

    def test_health_ok(self) -> None:
        response = self.client.get("/health")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            response.json(),
            {
                "status": "ok",
                "service": "investment_research_collector",
                "version": "mvp",
            },
        )

    def test_protected_endpoint_without_token_is_rejected(self) -> None:
        response = self.client.post("/collect/run", json={"mode": "daily"})
        self.assertIn(response.status_code, (401, 403))

    def test_collect_run_single_task_sync_response(self) -> None:
        response = self.client.post(
            "/collect/run",
            headers={"Authorization": "Bearer test-token"},
            json={
                "mode": "daily",
                "scope": "industry",
                "scope_name": "散熱",
                "source_mode": "mock",
                "summarizer_mode": "mock",
                "llm_provider": "auto",
                "search_provider": "mock",
                "dry_run": False,
            },
        )
        self.assertEqual(response.status_code, 200, msg=response.text)
        body = response.json()
        self.assert_api_envelope(body)
        self.assertIsInstance(body["data"]["output_files"], list)
        self.assertIsInstance(body["data"]["run_errors"], list)
        self.assertIsInstance(body["data"]["batch_report"], dict)
        self.assertEqual(body["data"]["batch"], None)
        self.assertEqual(body["data"]["mode"], "daily")

    def test_collect_run_batch_industries_sync_response(self) -> None:
        response = self.client.post(
            "/collect/run",
            headers={"Authorization": "Bearer test-token"},
            json={
                "batch": "industries",
                "source_mode": "mock",
                "summarizer_mode": "mock",
                "dry_run": False,
            },
        )
        self.assertEqual(response.status_code, 200, msg=response.text)
        body = response.json()
        self.assert_api_envelope(body)
        self.assertEqual(body["data"]["batch"], "industries")
        self.assertIsInstance(body["data"]["batch_report"], dict)
        self.assertGreaterEqual(len(body["data"]["output_files"]), 0)
        self.assertEqual(body["data"]["mode"], "daily")

    def test_collect_run_three_day_without_scope_returns_validate_error_envelope(self) -> None:
        response = self.client.post(
            "/collect/run",
            headers={"Authorization": "Bearer test-token"},
            json={
                "mode": "three_day",
                "source_mode": "mock",
                "summarizer_mode": "mock",
                "dry_run": False,
            },
        )
        self.assertEqual(response.status_code, 400, msg=response.text)
        body = response.json()
        self.assert_api_envelope(body, expected_statuses={"failed"})
        self.assertEqual(body["status"], "failed")
        self.assertEqual(body["errors"][0]["stage"], "validate_request")
        self.assertIn("--scope and --scope_name are required for three_day mode", body["message"])

    def test_ingestion_run_dry_run(self) -> None:
        with TemporaryDirectory() as tmpdir:
            input_root = Path(tmpdir)
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
            response = self.client.post(
                "/ingestion/run",
                headers={"Authorization": "Bearer test-token"},
                json={"input_path": str(input_root), "packet_type": "all", "dry_run": True},
            )
            self.assertEqual(response.status_code, 200, msg=response.text)
            body = response.json()
            self.assert_api_envelope(body)
            self.assertEqual(body["data"]["mode"], "dry_run")
            self.assertIn("batch_id", body["data"])

    def test_promotion_run_dry_run(self) -> None:
        with TemporaryDirectory() as tmpdir:
            input_root = Path(tmpdir)
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
            response = self.client.post(
                "/promotion/run",
                headers={"Authorization": "Bearer test-token"},
                json={"input_path": str(input_root), "packet_type": "all", "dry_run": True},
            )
            self.assertEqual(response.status_code, 200, msg=response.text)
            body = response.json()
            self.assert_api_envelope(body)
            self.assertEqual(body["data"]["mode"], "dry_run")
            self.assertIn("batch_id", body["data"])

    def test_promotion_run_write_mode_returns_clear_message(self) -> None:
        with patch.dict(os.environ, {}, clear=True):
            response = self.client.post(
                "/promotion/run",
                headers={"Authorization": "Bearer test-token"},
                json={"input_path": "output/", "packet_type": "all", "dry_run": False},
            )
        self.assertEqual(response.status_code, 200, msg=response.text)
        body = response.json()
        self.assert_api_envelope(body, expected_statuses={"failed"})
        self.assertEqual(body["status"], "failed")
        self.assertEqual(body["data"].get("mode"), "write")
        self.assertEqual(body["data"].get("status"), "failed")
        self.assertIn("Promotion write mode failed", body["message"])
        self.assertTrue(body["data"].get("errors"))

    def test_pipeline_run_requires_token(self) -> None:
        response = self.client.post(
            "/pipeline/run",
            json={
                "collect": {"batch": "industries", "source_mode": "mock", "summarizer_mode": "mock"},
                "ingestion": {"enabled": True, "input_path": "output/", "packet_type": "all", "dry_run": True},
                "promotion": {"enabled": True, "input_path": "output/", "packet_type": "all", "dry_run": True},
            },
        )
        self.assertIn(response.status_code, (401, 403))

    def test_pipeline_run_sync_collect_ingestion_promotion(self) -> None:
        with TemporaryDirectory() as tmpdir:
            output_root = Path(tmpdir) / "output"
            output_root.mkdir(parents=True, exist_ok=True)
            patches = self._open_pipeline_output_patches(output_root)
            try:
                response = self.client.post(
                    "/pipeline/run",
                    headers={"Authorization": "Bearer test-token"},
                    json={
                        "collect": {"batch": "industries", "source_mode": "mock", "summarizer_mode": "mock"},
                        "ingestion": {"enabled": True, "input_path": str(output_root), "packet_type": "all", "dry_run": True},
                        "promotion": {"enabled": True, "input_path": str(output_root), "packet_type": "all", "dry_run": True},
                    },
                )
            finally:
                patches.close()

            self.assertEqual(response.status_code, 200, msg=response.text)
            body = response.json()
            self.assert_api_envelope(body)
            self.assertEqual(body["execution_mode"], "sync")
            self.assertIsNone(body["job_id"])
            self.assertIsInstance(body["errors"], list)
            self.assertIn("collect_result", body["data"])
            self.assertIn("ingestion_result", body["data"])
            self.assertIn("promotion_result", body["data"])
            self.assertIn("pipeline_report", body["data"])
            self.assertIsInstance(body["data"]["collect_result"], dict)
            self.assertIsInstance(body["data"]["ingestion_result"], dict)
            self.assertIsInstance(body["data"]["promotion_result"], dict)
            self.assertIsInstance(body["data"]["pipeline_report"], dict)
            pipeline_report = body["data"]["pipeline_report"]
            self.assertIn(pipeline_report["status"], {"success", "partial_success"})
            self.assertEqual(pipeline_report["collect_status"], body["data"]["collect_result"]["status"])
            self.assertEqual(pipeline_report["ingestion_status"], body["data"]["ingestion_result"]["status"])
            self.assertEqual(pipeline_report["promotion_status"], body["data"]["promotion_result"]["status"])
            self.assertTrue(Path(pipeline_report["pipeline_report_path"]).exists())

    def test_pipeline_run_disabled_stages_are_skipped(self) -> None:
        with TemporaryDirectory() as tmpdir:
            output_root = Path(tmpdir) / "output"
            output_root.mkdir(parents=True, exist_ok=True)
            patches = self._open_pipeline_output_patches(output_root)
            try:
                response = self.client.post(
                    "/pipeline/run",
                    headers={"Authorization": "Bearer test-token"},
                    json={
                        "collect": {"batch": "industries", "source_mode": "mock", "summarizer_mode": "mock"},
                        "ingestion": {"enabled": False, "input_path": str(output_root), "packet_type": "all", "dry_run": True},
                        "promotion": {"enabled": False, "input_path": str(output_root), "packet_type": "all", "dry_run": True},
                    },
                )
            finally:
                patches.close()

            self.assertEqual(response.status_code, 200, msg=response.text)
            body = response.json()
            self.assert_api_envelope(body)
            self.assertEqual(body["execution_mode"], "sync")
            self.assertIsNone(body["job_id"])
            pipeline_report = body["data"]["pipeline_report"]
            self.assertEqual(pipeline_report["ingestion_status"], "skipped")
            self.assertEqual(pipeline_report["promotion_status"], "skipped")
            self.assertTrue(Path(pipeline_report["pipeline_report_path"]).exists())

    def test_pipeline_run_supports_promotion_write_mode(self) -> None:
        with TemporaryDirectory() as tmpdir:
            output_root = Path(tmpdir) / "output"
            output_root.mkdir(parents=True, exist_ok=True)
            patches = self._open_pipeline_output_patches(output_root)
            try:
                with patch.dict(os.environ, {}, clear=True):
                    response = self.client.post(
                        "/pipeline/run",
                        headers={"Authorization": "Bearer test-token"},
                        json={
                            "collect": {"batch": "industries", "source_mode": "mock", "summarizer_mode": "mock"},
                            "ingestion": {"enabled": True, "input_path": str(output_root), "packet_type": "all", "dry_run": True},
                            "promotion": {"enabled": True, "input_path": str(output_root), "packet_type": "all", "dry_run": False},
                        },
                    )
            finally:
                patches.close()

            self.assertEqual(response.status_code, 200, msg=response.text)
            body = response.json()
            self.assert_api_envelope(body)
            self.assertEqual(body["execution_mode"], "sync")
            self.assertIsNone(body["job_id"])
            self.assertEqual(body["data"]["promotion_result"]["mode"], "write")
            self.assertEqual(body["data"]["promotion_result"]["status"], "failed")
            self.assertEqual(body["data"]["pipeline_report"]["promotion_status"], "failed")
            self.assertEqual(body["data"]["pipeline_report"]["status"], "partial_success")
            self.assertFalse(body["autonomous_ready"])
            self.assertFalse(body["wrote_to_supabase"])

    def test_pipeline_run_supports_flat_autonomous_body(self) -> None:
        with TemporaryDirectory() as tmpdir:
            output_root = Path(tmpdir) / "output"
            output_root.mkdir(parents=True, exist_ok=True)
            patches = self._open_pipeline_output_patches(output_root)
            try:
                with patch.dict(os.environ, {}, clear=True):
                    response = self.client.post(
                        "/pipeline/run",
                        headers={"Authorization": "Bearer test-token"},
                        json={
                            "scope": "all",
                            "source_mode": "hybrid",
                            "summarizer_mode": "auto",
                            "ingestion_dry_run": False,
                            "promotion_dry_run": False,
                        },
                    )
            finally:
                patches.close()

            self.assertEqual(response.status_code, 200, msg=response.text)
            body = response.json()
            self.assert_api_envelope(body)
            self.assertEqual(body["execution_mode"], "sync")
            self.assertIsNone(body["job_id"])
            self.assertFalse(body["autonomous_ready"])
            self.assertTrue(body["collect_ran"])
            self.assertTrue(body["ingestion_ran"])
            self.assertTrue(body["promotion_ran"])
            self.assertFalse(body["wrote_to_supabase"])
            self.assertIn("collect_result", body["data"])
            self.assertIn("ingestion_result", body["data"])
            self.assertIn("promotion_result", body["data"])
            self.assertIn("pipeline_report", body["data"])

    def test_protected_endpoint_without_configured_token_is_rejected(self) -> None:
        original = getattr(app.state, "api_auth_token", "")
        try:
            app.state.api_auth_token = ""
            response = self.client.post("/pipeline/run", json={})
        finally:
            app.state.api_auth_token = original
        self.assertIn(response.status_code, (401, 403))


if __name__ == "__main__":
    unittest.main()
