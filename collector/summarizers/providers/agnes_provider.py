from __future__ import annotations

import os
from typing import Any

import requests

from collector.summarizers.providers.base_provider import BaseLLMProvider, LLMProviderUnavailableError


class AgnesProvider(BaseLLMProvider):
    provider_name = "agnes"
    api_key_env = "AGNES_API_KEY"
    model_env = "AGNES_MODEL"
    default_model = "agnes"

    def summarize(self, prompt: str, state: dict[str, Any], sources: list[dict[str, Any]]) -> str:
        api_key = self.get_api_key()
        api_url = self.get_api_url()
        if not api_key:
            raise LLMProviderUnavailableError("AGNES_API_KEY is missing")
        if not api_url:
            raise LLMProviderUnavailableError("AGNES_API_URL is missing")

        response = requests.post(
            api_url,
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
                        "content": "你是投資研究摘要助手，只能輸出繁體中文 JSON，不要輸出 markdown。",
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
            raise ValueError(f"Unexpected Agnes response shape: {exc}") from exc
        if not isinstance(content, str) or not content.strip():
            raise ValueError("Agnes returned empty content")
        return content

    def get_api_url(self) -> str:
        raw_url = os.getenv("AGNES_API_URL", "").strip()
        if raw_url:
            return raw_url
        base_url = os.getenv("AGNES_BASE_URL", "").strip()
        if base_url:
            return f"{base_url.rstrip('/')}/v1/chat/completions"
        return ""

    def is_available(self) -> bool:
        return bool(self.get_api_key()) and bool(self.get_api_url())

    def unavailable_message(self) -> str:
        return "AGNES_API_KEY and AGNES_API_URL are required"
