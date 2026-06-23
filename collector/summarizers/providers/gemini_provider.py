from __future__ import annotations

from typing import Any

import requests

from collector.summarizers.providers.base_provider import BaseLLMProvider, LLMProviderUnavailableError


class GeminiProvider(BaseLLMProvider):
    provider_name = "gemini"
    api_key_env = "GEMINI_API_KEY"
    model_env = "GEMINI_MODEL"
    default_model = "gemini-2.5-flash"

    def summarize(self, prompt: str, state: dict[str, Any], sources: list[dict[str, Any]]) -> str:
        api_key = self.get_api_key()
        if not api_key:
            raise LLMProviderUnavailableError("GEMINI_API_KEY is missing")

        model_name = self.get_model_name()
        response = requests.post(
            f"https://generativelanguage.googleapis.com/v1beta/models/{model_name}:generateContent",
            params={"key": api_key},
            json={
                "contents": [
                    {
                        "role": "user",
                        "parts": [
                            {
                                "text": prompt,
                            }
                        ],
                    }
                ],
                "generationConfig": {
                    "temperature": 0.2,
                    "responseMimeType": "application/json",
                },
            },
            timeout=self.request_timeout_seconds,
        )
        response.raise_for_status()
        payload = response.json()
        try:
            candidates = payload["candidates"]
            parts = candidates[0]["content"]["parts"]
        except (KeyError, IndexError, TypeError) as exc:
            raise ValueError(f"Unexpected Gemini response shape: {exc}") from exc

        texts: list[str] = []
        for part in parts:
            if isinstance(part, dict) and part.get("text"):
                texts.append(str(part["text"]))

        content = "\n".join(texts).strip()
        if not content:
            raise ValueError("Gemini returned empty content")
        return content
