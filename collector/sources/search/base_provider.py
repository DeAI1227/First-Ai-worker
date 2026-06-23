from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any


class SearchProviderError(RuntimeError):
    pass


class SearchProviderUnavailableError(SearchProviderError):
    pass


class BaseSearchProvider(ABC):
    provider_name = "base"
    api_key_env = ""
    default_model = ""

    def get_api_key(self) -> str:
        if not self.api_key_env:
            return ""
        import os

        return os.getenv(self.api_key_env, "").strip()

    def is_available(self) -> bool:
        return bool(self.get_api_key())

    @abstractmethod
    def search(self, task: dict[str, Any], keywords: list[str], state: dict[str, Any] | None = None) -> list[dict[str, Any]]:
        raise NotImplementedError
