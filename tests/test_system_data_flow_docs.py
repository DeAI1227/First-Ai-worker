from __future__ import annotations

import unittest
from pathlib import Path


class SystemDataFlowDocsTests(unittest.TestCase):
    @property
    def project_root(self) -> Path:
        return Path(__file__).resolve().parents[1]

    def test_system_data_flow_doc_exists(self) -> None:
        self.assertTrue((self.project_root / "docs" / "system_data_flow.md").exists())

    def test_system_data_flow_doc_mentions_sups_only_frontend(self) -> None:
        doc_text = (self.project_root / "docs" / "system_data_flow.md").read_text(encoding="utf-8")
        self.assertIn("LangGraph Collector", doc_text)
        self.assertIn("Supabase production tables / views", doc_text)
        self.assertIn("New frontend reads Supabase only", doc_text)
        self.assertIn("The frontend must not read `output/` JSON files directly.", doc_text)

    def test_root_readme_mentions_system_data_flow(self) -> None:
        readme_text = (self.project_root / "README.md").read_text(encoding="utf-8")
        self.assertIn("Official system direction", readme_text)
        self.assertIn("docs/system_data_flow.md", readme_text)
        self.assertIn("The frontend reads only Supabase production views.", readme_text)


if __name__ == "__main__":
    unittest.main()

