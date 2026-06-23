from __future__ import annotations

import json
import unittest
from pathlib import Path

from api.main import app


class ApiContractPackTests(unittest.TestCase):
    @property
    def project_root(self) -> Path:
        return Path(__file__).resolve().parents[1]

    def test_api_contract_doc_exists_and_mentions_endpoints(self) -> None:
        text = (self.project_root / "docs" / "api_contract.md").read_text(encoding="utf-8")
        self.assertIn("GET /health", text)
        self.assertIn("POST /collect/run", text)
        self.assertIn("POST /ingestion/run", text)
        self.assertIn("POST /promotion/run", text)
        self.assertIn("POST /pipeline/run", text)
        self.assertIn("POST /collect/jobs", text)
        self.assertIn("Frontend reads Supabase views directly.", text)

    def test_n8n_usage_doc_exists_and_mentions_status_branching(self) -> None:
        text = (self.project_root / "docs" / "n8n_api_usage.md").read_text(encoding="utf-8")
        self.assertIn("POST /pipeline/run", text)
        self.assertIn("success -> record success and finish", text)
        self.assertIn("partial_success -> notify a human", text)
        self.assertIn("failed -> alert immediately", text)

    def test_api_examples_exist_and_are_valid_json(self) -> None:
        examples = [
            "pipeline_dry_run.json",
            "pipeline_write_mode.json",
            "collect_all_mock.json",
            "ingestion_dry_run.json",
            "promotion_dry_run.json",
        ]
        api_examples_root = self.project_root / "api_examples"
        self.assertTrue(api_examples_root.exists())
        for name in examples:
            payload = json.loads((api_examples_root / name).read_text(encoding="utf-8"))
            self.assertIsInstance(payload, dict)
        write_mode = json.loads((api_examples_root / "pipeline_write_mode.json").read_text(encoding="utf-8"))
        self.assertEqual(write_mode["scope"], "all")
        self.assertFalse(write_mode["ingestion_dry_run"])
        self.assertFalse(write_mode["promotion_dry_run"])

    def test_openapi_includes_required_endpoints(self) -> None:
        schema = app.openapi()
        paths = schema["paths"]
        self.assertIn("/health", paths)
        self.assertIn("/collect/run", paths)
        self.assertIn("/ingestion/run", paths)
        self.assertIn("/promotion/run", paths)
        self.assertIn("/pipeline/run", paths)


if __name__ == "__main__":
    unittest.main()
