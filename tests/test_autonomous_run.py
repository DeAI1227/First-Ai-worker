from __future__ import annotations

import json
import os
import subprocess
import unittest
from pathlib import Path
from unittest.mock import patch

from scripts.run_autonomous_once import run_autonomous_once


class AutonomousRunTests(unittest.TestCase):
    @property
    def project_root(self) -> Path:
        return Path(__file__).resolve().parents[1]

    def test_autonomous_runner_script_exists(self) -> None:
        self.assertTrue((self.project_root / "scripts" / "run_autonomous_once.py").exists())

    def test_autonomous_runner_returns_required_flags(self) -> None:
        with patch.dict(
            os.environ,
            {
                "SEARCH_PROVIDER": "mock",
                "AUTONOMOUS_SCOPE": "industries",
                "AUTONOMOUS_SOURCE_MODE": "mock",
                "AUTONOMOUS_SUMMARIZER_MODE": "mock",
            },
            clear=False,
        ):
            result = run_autonomous_once()
        self.assertIn(result["status"], {"success", "partial_success", "failed"})
        self.assertIn(result["autonomous_ready"], {True, False})
        self.assertIn(result["collect_ran"], {True, False})
        self.assertIn(result["ingestion_ran"], {True, False})
        self.assertIn(result["promotion_ran"], {True, False})
        self.assertIn(result["wrote_to_supabase"], {True, False})
        self.assertIsInstance(result["errors"], list)

    def test_autonomous_runner_cli_prints_summary_fields(self) -> None:
        env = os.environ.copy()
        env["SEARCH_PROVIDER"] = "mock"
        env["AUTONOMOUS_SCOPE"] = "industries"
        env["AUTONOMOUS_SOURCE_MODE"] = "mock"
        env["AUTONOMOUS_SUMMARIZER_MODE"] = "mock"
        completed = subprocess.run(
            ["python", "scripts/run_autonomous_once.py"],
            cwd=self.project_root,
            capture_output=True,
            text=True,
            check=False,
            env=env,
        )
        self.assertIn(completed.returncode, {0, 1})
        stdout = completed.stdout + completed.stderr
        self.assertIn("collect_ran", stdout)
        self.assertIn("ingestion_ran", stdout)
        self.assertIn("promotion_ran", stdout)
        self.assertIn("wrote_to_supabase", stdout)
        self.assertIn("status", stdout)

    def test_autonomous_runner_output_json_is_valid(self) -> None:
        env = os.environ.copy()
        env["SEARCH_PROVIDER"] = "mock"
        env["AUTONOMOUS_SCOPE"] = "industries"
        env["AUTONOMOUS_SOURCE_MODE"] = "mock"
        env["AUTONOMOUS_SUMMARIZER_MODE"] = "mock"
        completed = subprocess.run(
            ["python", "scripts/run_autonomous_once.py"],
            cwd=self.project_root,
            capture_output=True,
            text=True,
            check=False,
            env=env,
        )
        self.assertIn(completed.returncode, {0, 1})
        parsed = json.loads(completed.stdout.strip())
        self.assertIn(parsed["status"], {"success", "partial_success", "failed"})


if __name__ == "__main__":
    unittest.main()
