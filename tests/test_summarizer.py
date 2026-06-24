from __future__ import annotations

import json
import os
import subprocess
import sys
import unittest
from dataclasses import dataclass
from unittest.mock import patch

from collector.graph import run_collector_task
from collector.summarizers.llm_summarizer import LLM_SUMMARIZATION_PROMPT, build_llm_prompt, summarize_with_llm
from collector.summarizers.mock_summarizer import summarize_with_mock
from collector.tasks import make_task


FAKE_SOURCES = [
    {
        "title": "AI server liquid cooling demand rises",
        "source_name": "Mock Search Industry",
        "source_url": "https://example.com/ai-server-liquid-cooling",
        "published_at": "2026-06-16T08:00:00+08:00",
        "content": "Liquid cooling demand is rising across the data center supply chain.",
        "source_type": "search",
    },
    {
        "title": "Company announcement update",
        "source_name": "Mock HTTP",
        "source_url": "https://example.com/company-announcement",
        "published_at": "",
        "content": "The company mentioned product progress and production updates.",
        "source_type": "http",
    },
]


@dataclass
class FakeResponse:
    payload: dict
    status_code: int = 200

    def raise_for_status(self) -> None:
        if self.status_code >= 400:
            raise RuntimeError(f"HTTP {self.status_code}")

    def json(self) -> dict:
        return self.payload


def _response_with_content(content: str) -> FakeResponse:
    return FakeResponse(
        {
            "choices": [
                {
                    "message": {
                        "content": content,
                    }
                }
            ]
        }
    )


class SummarizerTests(unittest.TestCase):
    def test_mock_summarizer_returns_standard_format(self):
        state = {
            "scope": "industry",
            "scope_name": "thermal",
            "target_stock_code": "6230",
            "target_stock_name": "Nidec Chaun-Choung",
            "search_keywords": ["thermal", "AI server", "liquid cooling"],
        }
        result = summarize_with_mock(state, FAKE_SOURCES)

        self.assertEqual(set(result.keys()), {"ai_summary", "possible_impact", "risk_note", "tags", "language"})
        self.assertEqual(result["language"], "zh-TW")
        self.assertTrue(result["ai_summary"])
        self.assertTrue(result["possible_impact"])
        self.assertTrue(result["risk_note"])
        self.assertGreaterEqual(len(result["tags"]), 3)
        self.assertLessEqual(len(result["ai_summary"]), 500)

    def test_build_llm_prompt_contains_guardrails(self):
        state = {
            "scope": "industry",
            "scope_name": "thermal",
            "target_stock_code": "6230",
            "target_stock_name": "Nidec Chaun-Choung",
            "search_keywords": ["thermal", "AI server"],
        }
        prompt = build_llm_prompt(state, FAKE_SOURCES)

        self.assertIn("AI summary assistant", LLM_SUMMARIZATION_PROMPT)
        self.assertIn("ai_summary", prompt)
        self.assertIn("raw_sources", prompt)
        self.assertIn("6230", prompt)

    def test_llm_without_agnes_key_falls_back_to_mock(self):
        state = {
            "scope": "macro",
            "scope_name": "macro environment",
            "search_keywords": ["Fed", "CPI", "rates"],
            "run_errors": [],
        }
        with patch.dict(os.environ, {}, clear=True):
            result = summarize_with_llm(state, FAKE_SOURCES, provider="agnes")

        self.assertEqual(result["language"], "zh-TW")
        self.assertTrue(any("AGNES_API_KEY or AGNES_API_URL is missing" in error for error in state["run_errors"]))
        self.assertLessEqual(len(result["ai_summary"]), 500)

    def test_auto_provider_without_key_falls_back_to_mock(self):
        state = {
            "scope": "macro",
            "scope_name": "macro environment",
            "search_keywords": ["Fed", "CPI", "rates"],
            "run_errors": [],
        }
        with patch.dict(os.environ, {}, clear=True):
            result = summarize_with_llm(state, FAKE_SOURCES, provider="auto")

        self.assertEqual(result["language"], "zh-TW")
        self.assertTrue(any("fallback to mock summarizer" in error for error in state["run_errors"]))
        self.assertLessEqual(len(result["ai_summary"]), 500)

    def test_auto_provider_uses_agnes_when_only_agnes_key_exists(self):
        state = {
            "scope": "industry",
            "scope_name": "thermal",
            "target_stock_code": "6230",
            "target_stock_name": "Nidec Chaun-Choung",
            "search_keywords": ["thermal", "liquid cooling"],
            "run_errors": [],
        }
        payload = json.dumps(
            {
                "ai_summary": "Cooling demand is increasing and the supply chain may benefit.",
                "possible_impact": "Demand for cooling solutions may rise.",
                "risk_note": "End-market demand still needs monitoring.",
                "tags": ["thermal", "cooling", "supply chain"],
            },
            ensure_ascii=False,
        )
        with patch.dict(
            os.environ,
            {
                "AGNES_API_KEY": "test-key",
                "AGNES_API_URL": "https://agnes.example.com/v1/chat/completions",
                "AGNES_MODEL": "agnes-pro",
            },
            clear=True,
        ):
            with patch("collector.summarizers.providers.agnes_provider.requests.post", return_value=_response_with_content(payload)) as mocked_post:
                result = summarize_with_llm(state, FAKE_SOURCES, provider="auto")

        self.assertTrue(mocked_post.called)
        self.assertIn("Cooling demand is increasing", result["ai_summary"])
        self.assertEqual(result["language"], "zh-TW")

    def test_auto_provider_uses_gemini_when_only_gemini_key_exists(self):
        state = {
            "scope": "macro",
            "scope_name": "macro environment",
            "search_keywords": ["CPI", "rates"],
            "run_errors": [],
        }
        payload = json.dumps(
            {
                "ai_summary": "Inflation and rate expectations remain the market focus.",
                "possible_impact": "Risk assets may improve if inflation cools.",
                "risk_note": "Volatility may increase around data releases.",
                "tags": ["CPI", "rates", "inflation"],
            },
            ensure_ascii=False,
        )
        with patch.dict(os.environ, {"GEMINI_API_KEY": "test-key", "GEMINI_MODEL": "gemini-2.5-flash"}, clear=True):
            with patch(
                "collector.summarizers.providers.gemini_provider.requests.post",
                return_value=FakeResponse({"candidates": [{"content": {"parts": [{"text": payload}]}}]}),
            ) as mocked_post:
                result = summarize_with_llm(state, FAKE_SOURCES, provider="auto")

        self.assertTrue(mocked_post.called)
        self.assertIn("Inflation and rate expectations", result["ai_summary"])
        self.assertEqual(result["language"], "zh-TW")

    def test_llm_non_json_output_falls_back_to_mock(self):
        state = {
            "scope": "industry",
            "scope_name": "thermal",
            "target_stock_code": "6230",
            "target_stock_name": "Nidec Chaun-Choung",
            "search_keywords": ["thermal", "liquid cooling"],
            "run_errors": [],
        }
        with patch.dict(
            os.environ,
            {"AGNES_API_KEY": "test-key", "AGNES_API_URL": "https://agnes.example.com/v1/chat/completions"},
            clear=True,
        ):
            with patch(
                "collector.summarizers.providers.agnes_provider.requests.post",
                return_value=_response_with_content("this is not JSON"),
            ):
                result = summarize_with_llm(state, FAKE_SOURCES, provider="agnes")

        self.assertTrue(any("fallback to mock summarizer" in error for error in state["run_errors"]))
        self.assertEqual(result["language"], "zh-TW")

    def test_llm_output_is_sanitized_and_clamped(self):
        state = {
            "scope": "industry",
            "scope_name": "thermal",
            "target_stock_code": "6230",
            "target_stock_name": "Nidec Chaun-Choung",
            "search_keywords": ["thermal", "liquid cooling"],
            "run_errors": [],
        }
        raw_content = json.dumps(
            {
                "ai_summary": "買進" + "A" * 600,
                "possible_impact": "賣出" + "B" * 100,
                "risk_note": "目標價" + "C" * 100,
                "tags": ["thermal", "thermal", "投資建議"],
            },
            ensure_ascii=False,
        )
        with patch.dict(
            os.environ,
            {"AGNES_API_KEY": "test-key", "AGNES_API_URL": "https://agnes.example.com/v1/chat/completions"},
            clear=True,
        ):
            with patch(
                "collector.summarizers.providers.agnes_provider.requests.post",
                return_value=_response_with_content(raw_content),
            ):
                result = summarize_with_llm(state, FAKE_SOURCES, provider="agnes")

        self.assertLessEqual(len(result["ai_summary"]), 500)
        self.assertNotIn("買進", result["ai_summary"])
        self.assertNotIn("賣出", result["possible_impact"])
        self.assertNotIn("目標價", result["risk_note"])
        self.assertNotIn("投資建議", " ".join(result["tags"]))

    def test_summarizer_mode_llm_without_key_runs_main_flow(self):
        task = make_task(
            scope="industry",
            scope_name="thermal",
            stock_code="6230",
            stock_name="Nidec Chaun-Choung",
            source_mode="hybrid",
            summarizer_mode="llm",
            llm_provider="auto",
        )
        with patch.dict(os.environ, {}, clear=True):
            state = run_collector_task(task)

        self.assertEqual(state["event_packet"]["packet_type"], "event")
        self.assertEqual(state["event_packet"]["collector"], "langgraph")
        self.assertLessEqual(len(state["event_packet"]["ai_summary"]), 500)
        self.assertTrue(any("fallback to mock summarizer" in error for error in state["run_errors"]))

    def test_cli_summarizer_mode_llm_runs(self):
        command = [
            sys.executable,
            "main.py",
            "--summarizer-mode",
            "llm",
            "--llm-provider",
            "auto",
        ]
        result = subprocess.run(
            command,
            cwd=os.path.dirname(os.path.dirname(__file__)),
            capture_output=True,
            text=True,
            env={
                **os.environ,
                "AGNES_API_KEY": "",
                "AGNES_API_URL": "",
                "GEMINI_API_KEY": "",
            },
        )
        self.assertEqual(result.returncode, 0, msg=result.stderr)
        self.assertIn('"summarizer_mode": "llm"', result.stdout)


if __name__ == "__main__":
    unittest.main()
