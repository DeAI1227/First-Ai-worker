from __future__ import annotations

from abc import ABC, abstractmethod
import os
from typing import Any


class LLMProviderError(RuntimeError):
    """Raised when a provider cannot complete a summarize request."""


class LLMProviderUnavailableError(LLMProviderError):
    """Raised when the provider is selected but credentials are missing."""


class BaseLLMProvider(ABC):
    provider_name = "base"
    api_key_env = ""
    model_env = ""
    default_model = ""

    def __init__(self) -> None:
        self.request_timeout_seconds = 30

    @abstractmethod
    def summarize(self, prompt: str, state: dict[str, Any], sources: list[dict[str, Any]]) -> str:
        """Return the raw model response text."""

    def is_available(self) -> bool:
        return bool(self.get_api_key())

    def get_api_key(self) -> str:
        if not self.api_key_env:
            return ""
        return os.getenv(self.api_key_env, "").strip()

    def get_model_name(self) -> str:
        if self.model_env:
            override = os.getenv(self.model_env, "").strip()
            if override:
                return override
        return self.default_model

    def unavailable_message(self) -> str:
        return f"{self.provider_name} provider requires {self.api_key_env}"
