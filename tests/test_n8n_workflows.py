from __future__ import annotations

import json
import unittest
from pathlib import Path


class N8nWorkflowTemplateTests(unittest.TestCase):
    def setUp(self) -> None:
        self.root = Path(__file__).resolve().parents[1]
        self.workflow_root = self.root / "n8n_workflows"

    def test_n8n_workflows_folder_exists(self) -> None:
        self.assertTrue(self.workflow_root.exists())
        self.assertTrue(self.workflow_root.is_dir())

    def test_pipeline_daily_dry_run_json_is_valid(self) -> None:
        path = self.workflow_root / "pipeline_daily_dry_run.json"
        payload = json.loads(path.read_text(encoding="utf-8"))
        self.assertEqual(payload["name"], "AI Investment Research Pipeline - Daily Dry Run")
        self.assertIn("Cron Trigger", payload["connections"])

    def test_pipeline_daily_write_mode_json_is_valid(self) -> None:
        path = self.workflow_root / "pipeline_daily_write_mode.json"
        payload = json.loads(path.read_text(encoding="utf-8"))
        self.assertEqual(payload["name"], "AI Investment Research Pipeline - Daily Write Mode")
        self.assertIn("HTTP Request: POST /pipeline/run", payload["connections"])

    def test_autonomous_daily_pipeline_json_is_valid(self) -> None:
        path = self.workflow_root / "autonomous_daily_pipeline.json"
        payload = json.loads(path.read_text(encoding="utf-8"))
        self.assertEqual(payload["name"], "AI Investment Research Autonomous Daily Pipeline")
        self.assertIn("Schedule Trigger", payload["connections"])
        http_node = next(node for node in payload["nodes"] if node["name"] == "HTTP Request: POST /pipeline/run")
        self.assertIn("Authorization\":\"Bearer {{$env.API_AUTH_TOKEN}}", http_node["parameters"]["headerParametersJson"])
        self.assertIn('"scope": "all"', http_node["parameters"]["bodyParametersJson"])

    def test_workflow_readme_exists(self) -> None:
        self.assertTrue((self.workflow_root / "README.md").exists())


if __name__ == "__main__":
    unittest.main()
