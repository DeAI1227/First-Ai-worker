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
        "title": "散熱產業傳出新一輪 AI 伺服器液冷需求",
        "source_name": "Mock Search Industry",
        "source_url": "https://example.com/ai-server-liquid-cooling",
        "published_at": "2026-06-16T08:00:00+08:00",
        "content": "供應鏈觀察顯示液冷方案與散熱模組需求同步升溫，仍需持續追蹤後續公告與驗證。",
        "source_type": "search",
    },
    {
        "title": "公司公告更新",
        "source_name": "Mock HTTP",
        "source_url": "https://example.com/company-announcement",
        "published_at": "",
        "content": "這則公告補充了產能、交期與後續營運安排，適合做研究追蹤，不適合作為單一結論。",
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


def _openai_response(content: str) -> FakeResponse:
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


def _gemini_response(content: str) -> FakeResponse:
    return FakeResponse(
        {
            "candidates": [
                {
                    "content": {
                        "parts": [
                            {"text": content},
                        ]
                    }
                }
            ]
        }
    )


class SummarizerTests(unittest.TestCase):
    def test_mock_summarizer_returns_standard_format(self):
        state = {
            "scope": "industry",
            "scope_name": "散熱",
            "target_stock_code": "6230",
            "target_stock_name": "尼得科超眾",
            "search_keywords": ["散熱", "AI 伺服器", "液冷"],
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
            "scope_name": "散熱",
            "target_stock_code": "6230",
            "target_stock_name": "尼得科超眾",
            "search_keywords": ["散熱", "AI 伺服器"],
        }
        prompt = build_llm_prompt(state, FAKE_SOURCES)

        self.assertIn("只能輸出 JSON", LLM_SUMMARIZATION_PROMPT)
        self.assertIn("ai_summary", prompt)
        self.assertIn("散熱", prompt)
        self.assertIn("6230", prompt)
        self.assertIn("raw_sources 前五筆", prompt)

    def test_llm_without_api_key_falls_back_to_mock(self):
        state = {
            "scope": "macro",
            "scope_name": "大環境",
            "search_keywords": ["聯準會", "CPI", "美元指數"],
            "run_errors": [],
        }
        with patch.dict(os.environ, {}, clear=True):
            result = summarize_with_llm(state, FAKE_SOURCES, provider="openai")

        self.assertEqual(result["language"], "zh-TW")
        self.assertTrue(any("OPENAI_API_KEY is missing" in error for error in state["run_errors"]))
        self.assertLessEqual(len(result["ai_summary"]), 500)

    def test_auto_provider_without_key_falls_back_to_mock(self):
        state = {
            "scope": "macro",
            "scope_name": "大環境",
            "search_keywords": ["聯準會", "CPI", "美元指數"],
            "run_errors": [],
        }
        with patch.dict(os.environ, {}, clear=True):
            result = summarize_with_llm(state, FAKE_SOURCES, provider="auto")

        self.assertEqual(result["language"], "zh-TW")
        self.assertTrue(any("fallback to mock summarizer" in error for error in state["run_errors"]))
        self.assertLessEqual(len(result["ai_summary"]), 500)

    def test_auto_provider_uses_openai_when_only_openai_key_exists(self):
        state = {
            "scope": "industry",
            "scope_name": "散熱",
            "target_stock_code": "6230",
            "target_stock_name": "尼得科超眾",
            "search_keywords": ["散熱", "液冷"],
            "run_errors": [],
        }
        payload = json.dumps(
            {
                "ai_summary": "散熱需求升溫，後續仍需追蹤供應鏈驗證。",
                "possible_impact": "可能提高市場對相關供應鏈的研究關注。",
                "risk_note": "資料仍有限，需持續觀察。",
                "tags": ["散熱", "液冷", "供應鏈"],
            },
            ensure_ascii=False,
        )
        with patch.dict(os.environ, {"OPENAI_API_KEY": "test-key", "OPENAI_MODEL": "gpt-4.1-mini"}, clear=True):
            with patch("collector.summarizers.providers.openai_provider.requests.post", return_value=_openai_response(payload)) as mocked_post:
                result = summarize_with_llm(state, FAKE_SOURCES, provider="auto")

        self.assertTrue(mocked_post.called)
        self.assertIn("散熱需求升溫", result["ai_summary"])
        self.assertEqual(result["language"], "zh-TW")

    def test_auto_provider_uses_gemini_when_only_gemini_key_exists(self):
        state = {
            "scope": "macro",
            "scope_name": "大環境",
            "search_keywords": ["聯準會", "CPI"],
            "run_errors": [],
        }
        payload = json.dumps(
            {
                "ai_summary": "宏觀環境仍需關注利率與美元變化。",
                "possible_impact": "可能影響風險偏好與資金流向。",
                "risk_note": "總體變數多，仍需分批驗證。",
                "tags": ["宏觀", "利率", "美元"],
            },
            ensure_ascii=False,
        )
        with patch.dict(os.environ, {"GEMINI_API_KEY": "test-key", "GEMINI_MODEL": "gemini-2.5-flash"}, clear=True):
            with patch("collector.summarizers.providers.gemini_provider.requests.post", return_value=_gemini_response(payload)) as mocked_post:
                result = summarize_with_llm(state, FAKE_SOURCES, provider="auto")

        self.assertTrue(mocked_post.called)
        self.assertIn("宏觀環境", result["ai_summary"] or "宏觀")
        self.assertEqual(result["language"], "zh-TW")

    def test_llm_non_json_output_falls_back_to_mock(self):
        state = {
            "scope": "industry",
            "scope_name": "散熱",
            "target_stock_code": "6230",
            "target_stock_name": "尼得科超眾",
            "search_keywords": ["散熱", "液冷"],
            "run_errors": [],
        }
        with patch.dict(os.environ, {"OPENAI_API_KEY": "test-key"}, clear=True):
            with patch(
                "collector.summarizers.providers.openai_provider.requests.post",
                return_value=_openai_response("這不是 JSON"),
            ):
                result = summarize_with_llm(state, FAKE_SOURCES, provider="openai")

        self.assertTrue(any("fallback to mock summarizer" in error for error in state["run_errors"]))
        self.assertEqual(result["language"], "zh-TW")

    def test_llm_output_is_sanitized_and_clamped(self):
        state = {
            "scope": "industry",
            "scope_name": "散熱",
            "target_stock_code": "6230",
            "target_stock_name": "尼得科超眾",
            "search_keywords": ["散熱", "液冷"],
            "run_errors": [],
        }
        raw_content = json.dumps(
            {
                "ai_summary": "買進" + "A" * 600,
                "possible_impact": "賣出" + "B" * 100,
                "risk_note": "目標價" + "C" * 100,
                "tags": ["散熱", "散熱", "買賣建議"],
            },
            ensure_ascii=False,
        )
        with patch.dict(os.environ, {"OPENAI_API_KEY": "test-key"}, clear=True):
            with patch(
                "collector.summarizers.providers.openai_provider.requests.post",
                return_value=_openai_response(raw_content),
            ):
                result = summarize_with_llm(state, FAKE_SOURCES, provider="openai")

        self.assertLessEqual(len(result["ai_summary"]), 500)
        self.assertNotIn("買進", result["ai_summary"])
        self.assertNotIn("賣出", result["possible_impact"])
        self.assertNotIn("目標價", result["risk_note"])
        self.assertNotIn("買賣建議", " ".join(result["tags"]))

    def test_summarizer_mode_llm_without_key_runs_main_flow(self):
        task = make_task(
            scope="industry",
            scope_name="散熱",
            stock_code="6230",
            stock_name="尼得科超眾",
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
            env={**os.environ, "OPENAI_API_KEY": "", "GEMINI_API_KEY": ""},
        )
        self.assertEqual(result.returncode, 0, msg=result.stderr)
        self.assertIn('"summarizer_mode": "llm"', result.stdout)


if __name__ == "__main__":
    unittest.main()
