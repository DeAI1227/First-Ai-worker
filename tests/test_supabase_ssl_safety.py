from __future__ import annotations

import os
import warnings
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest import TestCase
from unittest.mock import Mock, patch

from requests.exceptions import SSLError

from ingestion.ingest_outputs import write_ingest
from ingestion.supabase_client import SupabaseClient as IngestionSupabaseClient
from promotion.packet_promoter import promote_packets
from promotion.supabase_client import SupabaseClient as PromotionSupabaseClient


class SupabaseSSLSafetyTests(TestCase):
    def test_env_example_contains_ssl_safety_flags(self) -> None:
        env_example = Path(__file__).resolve().parents[1] / ".env.example"
        text = env_example.read_text(encoding="utf-8")
        self.assertIn("ENVIRONMENT=development", text)
        self.assertIn("ALLOW_INSECURE_SSL=false", text)
        self.assertIn("SUPABASE_CA_BUNDLE=", text)
        self.assertIn("正式環境不得設定 ALLOW_INSECURE_SSL=true", text)

    def test_ingestion_supabase_client_uses_custom_ca_bundle(self) -> None:
        session = Mock()
        response = Mock()
        response.ok = True
        response.text = "[]"
        response.json.return_value = []
        session.request.return_value = response

        with TemporaryDirectory() as tmpdir:
            ca_bundle = Path(tmpdir) / "ca.pem"
            ca_bundle.write_text("dummy-ca", encoding="utf-8")

            with patch.dict(
                os.environ,
                {
                    "ENVIRONMENT": "production",
                    "ALLOW_INSECURE_SSL": "false",
                    "SUPABASE_CA_BUNDLE": str(ca_bundle),
                },
                clear=True,
            ):
                client = IngestionSupabaseClient("https://example.supabase.co", "service-role-key", session=session)
                client.upsert("events", {"event_id": "event-1"}, on_conflict="event_id")

        self.assertEqual(session.verify, str(ca_bundle))

    def test_ingestion_supabase_client_rejects_insecure_fallback_by_default(self) -> None:
        session = Mock()
        session.request.side_effect = SSLError("certificate verify failed")

        with patch.dict(os.environ, {"ENVIRONMENT": "production", "ALLOW_INSECURE_SSL": "false"}, clear=True):
            client = IngestionSupabaseClient("https://example.supabase.co", "service-role-key", session=session)
            with self.assertRaises(RuntimeError) as ctx:
                client.upsert("events", {"event_id": "event-1"}, on_conflict="event_id")

        self.assertIn("SUPABASE_SSL_VERIFICATION_FAILED", str(ctx.exception))
        self.assertIn("ALLOW_INSECURE_SSL is false", str(ctx.exception))
        self.assertEqual(session.request.call_count, 1)
        self.assertTrue(session.verify)

    def test_ingestion_supabase_client_allows_dev_fallback_only_when_enabled(self) -> None:
        session = Mock()
        response = Mock()
        response.ok = True
        response.text = "[]"
        response.json.return_value = []
        session.request.side_effect = [SSLError("certificate verify failed"), response]

        with patch.dict(os.environ, {"ENVIRONMENT": "development", "ALLOW_INSECURE_SSL": "true"}, clear=True):
            with warnings.catch_warnings(record=True) as caught:
                warnings.simplefilter("always")
                client = IngestionSupabaseClient("https://example.supabase.co", "service-role-key", session=session)
                payload = client.upsert("events", {"event_id": "event-1"}, on_conflict="event_id")

        self.assertEqual(payload, [])
        self.assertEqual(session.request.call_count, 2)
        self.assertFalse(session.verify)
        self.assertTrue(any("insecure SSL fallback enabled" in str(item.message) for item in caught))

    def test_promotion_supabase_client_rejects_insecure_fallback_by_default(self) -> None:
        session = Mock()
        session.request.side_effect = SSLError("certificate verify failed")

        with patch.dict(os.environ, {"ENVIRONMENT": "production", "ALLOW_INSECURE_SSL": "false"}, clear=True):
            client = PromotionSupabaseClient("https://example.supabase.co", "service-role-key", session=session)
            with self.assertRaises(RuntimeError) as ctx:
                client.upsert("events", {"event_id": "event-1"}, on_conflict="event_id")

        self.assertIn("SUPABASE_SSL_VERIFICATION_FAILED", str(ctx.exception))
        self.assertEqual(session.request.call_count, 1)
        self.assertTrue(session.verify)

    def test_write_ingest_marks_supabase_write_false_on_ssl_failure(self) -> None:
        fake_client = Mock()
        fake_client.upsert.side_effect = RuntimeError(
            "SUPABASE_SSL_VERIFICATION_FAILED: SSL verification failed for Supabase request. "
            "ALLOW_INSECURE_SSL is false. Refusing to retry with verify=False in production-safe mode."
        )
        fake_client.insert_error.return_value = True

        with TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            (root / "event.json").write_text(
                """
                {
                  "event_id": "event-1",
                  "run_id": "run-1",
                  "event_date": "2026-06-17",
                  "scope": "industry",
                  "scope_name": "散熱",
                  "event_type": "industry",
                  "importance": "important",
                  "language": "zh-TW",
                  "title": "title",
                  "ai_summary": "summary",
                  "possible_impact": "impact",
                  "risk_note": "risk",
                  "tags": ["thermal"],
                  "related_industries": ["散熱"],
                  "related_stocks": ["6230"],
                  "related_macro_topics": ["fed_rate"],
                  "source_urls": ["https://example.com/a"],
                  "quality_summary": {"total_sources": 1, "high": 1, "medium": 0, "low": 0, "rejected": 0}
                }
                """,
                encoding="utf-8",
            )

            summary = write_ingest(root, packet_type_filter="event_packet", client=fake_client, allow_missing_config=True)

        self.assertEqual(summary["wrote_to_supabase"], False)
        self.assertGreaterEqual(summary["errors"], 1)

    def test_promote_packets_marks_supabase_write_false_on_ssl_failure(self) -> None:
        fake_client = Mock()
        fake_client.upsert.side_effect = RuntimeError(
            "SUPABASE_SSL_VERIFICATION_FAILED: SSL verification failed for Supabase request. "
            "ALLOW_INSECURE_SSL is false. Refusing to retry with verify=False in production-safe mode."
        )
        fake_client.insert.return_value = True

        with TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            (root / "event.json").write_text(
                """
                {
                  "event_id": "event-1",
                  "run_id": "run-1",
                  "event_date": "2026-06-17",
                  "scope": "industry",
                  "scope_name": "散熱",
                  "event_type": "industry",
                  "importance": "important",
                  "language": "zh-TW",
                  "title": "title",
                  "ai_summary": "summary",
                  "possible_impact": "impact",
                  "risk_note": "risk",
                  "tags": ["thermal"],
                  "related_industries": ["散熱"],
                  "related_stocks": ["6230"],
                  "related_macro_topics": ["fed_rate"],
                  "source_urls": ["https://example.com/a"],
                  "quality_summary": {"total_sources": 1, "high": 1, "medium": 0, "low": 0, "rejected": 0}
                }
                """,
                encoding="utf-8",
            )

            report = promote_packets(input_path=root, dry_run=False, client=fake_client)

        self.assertEqual(report["wrote_to_supabase"], False)
        self.assertIn(report["status"], {"failed", "partial_success"})
