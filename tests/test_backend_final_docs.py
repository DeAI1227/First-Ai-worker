from __future__ import annotations

import unittest
from pathlib import Path


class BackendFinalDocsTests(unittest.TestCase):
    @property
    def project_root(self) -> Path:
        return Path(__file__).resolve().parents[1]

    def test_backend_audit_exists_and_mentions_pipeline(self) -> None:
        text = (self.project_root / "docs" / "backend_final_audit.md").read_text(encoding="utf-8")
        self.assertIn("LangGraph Collector", text)
        self.assertIn("Supabase Production / Views", text)
        self.assertIn("Frontend reads Supabase", text)

    def test_write_path_checklist_exists_and_mentions_env(self) -> None:
        text = (self.project_root / "supabase" / "supabase_write_path_checklist.md").read_text(encoding="utf-8")
        self.assertIn("Collector output JSON", text)
        self.assertIn("SUPABASE_URL", text)
        self.assertIn("VITE_SUPABASE_ANON_KEY", text)

    def test_pipeline_runbook_mentions_core_commands(self) -> None:
        text = (self.project_root / "docs" / "pipeline_runbook.md").read_text(encoding="utf-8")
        self.assertIn("python main.py --batch all", text)
        self.assertIn("python -m ingestion.ingest_outputs --input output/ --dry-run", text)
        self.assertIn("python scripts/e2e_mvp_smoke.py", text)

    def test_mvp_release_checklist_mentions_no_fake_events(self) -> None:
        text = (self.project_root / "docs" / "mvp_release_checklist.md").read_text(encoding="utf-8")
        self.assertIn("45 tracked stocks", text)
        self.assertIn("No fake \"today no major update\" events.", text)
        self.assertIn("Frontend reads Supabase views only.", text)


if __name__ == "__main__":
    unittest.main()

