from __future__ import annotations

from typing import Any

import requests

from collector.summarizers.providers.base_provider import BaseLLMProvider, LLMProviderUnavailableError


class OpenAIProvider(BaseLLMProvider):
    provider_name = "openai"
    api_key_env = "OPENAI_API_KEY"
    model_env = "OPENAI_MODEL"
    default_model = "gpt-4.1-mini"

    def summarize(self, prompt: str, state: dict[str, Any], sources: list[dict[str, Any]]) -> str:
        api_key = self.get_api_key()
        if not api_key:
            raise LLMProviderUnavailableError("OPENAI_API_KEY is missing")

        response = requests.post(
            "https://api.openai.com/v1/chat/completions",
            headers={
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json",
            },
            json={
                "model": self.get_model_name(),
                "temperature": 0.2,
                "response_format": {"type": "json_object"},
                "messages": [
                    {
                        "role": "system",
                        "content": "你是 AI 投資研究摘要器，只能輸出 JSON，不能輸出 markdown 或解說文字。",
                    },
                    {"role": "user", "content": prompt},
                ],
            },
            timeout=self.request_timeout_seconds,
        )
        response.raise_for_status()
        payload = response.json()
        try:
            content = payload["choices"][0]["message"]["content"]
        except (KeyError, IndexError, TypeError) as exc:
            raise ValueError(f"Unexpected OpenAI response shape: {exc}") from exc
        if not isinstance(content, str) or not content.strip():
            raise ValueError("OpenAI returned empty content")
        return content
