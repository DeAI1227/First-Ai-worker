from __future__ import annotations

import warnings
from typing import Any

import requests
from requests.exceptions import SSLError

from collector.utils.ssl_utils import (
    allow_insecure_ssl,
    resolve_ssl_verify_setting,
    supabase_ssl_error_message,
)
import os


class SupabaseConfigError(RuntimeError):
    pass


class SupabaseClient:
    def __init__(self, url: str, key: str, session: requests.Session | None = None) -> None:
        self.url = url.rstrip("/")
        self.key = key
        self.session = session or requests.Session()
        self.environment = str(os.getenv("ENVIRONMENT", "development") or "development").strip().lower()
        self.allow_insecure_ssl = allow_insecure_ssl()
        self.session.verify = resolve_ssl_verify_setting()
        self._ssl_fallback_used = False

    @classmethod
    def from_env(cls) -> "SupabaseClient":
        url = os.getenv("SUPABASE_URL", "").strip()
        key = os.getenv("SUPABASE_SERVICE_ROLE_KEY", "").strip()
        missing = [name for name, value in [("SUPABASE_URL", url), ("SUPABASE_SERVICE_ROLE_KEY", key)] if not value]
        if missing:
            raise SupabaseConfigError("Missing required environment variables: " + ", ".join(missing))
        return cls(url, key)

    def upsert(self, table: str, row: dict[str, Any], *, on_conflict: str) -> list[dict[str, Any]] | dict[str, Any] | None:
        return self._request(
            "POST",
            table,
            json=[row],
            params={"on_conflict": on_conflict},
            prefer="resolution=merge-duplicates,return=representation",
        )

    def insert(self, table: str, row: dict[str, Any]) -> list[dict[str, Any]] | dict[str, Any] | None:
        return self._request(
            "POST",
            table,
            json=[row],
            prefer="return=representation",
        )

    def delete(self, table: str, filters: dict[str, str]) -> list[dict[str, Any]] | dict[str, Any] | None:
        return self._request(
            "DELETE",
            table,
            params=filters,
            prefer="return=representation",
        )

    def _request(
        self,
        method: str,
        table: str,
        *,
        json: list[dict[str, Any]] | None = None,
        params: dict[str, str] | None = None,
        prefer: str = "",
    ) -> list[dict[str, Any]] | dict[str, Any] | None:
        endpoint = f"{self.url}/rest/v1/{table}"
        headers = {
            "apikey": self.key,
            "Authorization": f"Bearer {self.key}",
            "Content-Type": "application/json",
        }
        if prefer:
            headers["Prefer"] = prefer

        try:
            request_kwargs: dict[str, Any] = {
                "headers": headers,
                "params": params,
                "timeout": 30,
            }
            if json is not None:
                request_kwargs["json"] = json
            response = self.session.request(method, endpoint, **request_kwargs)
        except SSLError:
            if self._can_use_insecure_ssl_fallback() and not self._ssl_fallback_used:
                self._ssl_fallback_used = True
                warnings.warn(
                    "WARNING: insecure SSL fallback enabled by ALLOW_INSECURE_SSL=true",
                    RuntimeWarning,
                )
                self.session.verify = False
                try:
                    request_kwargs = {
                        "headers": headers,
                        "params": params,
                        "timeout": 30,
                    }
                    if json is not None:
                        request_kwargs["json"] = json
                    response = self.session.request(method, endpoint, **request_kwargs)
                except SSLError as retry_exc:
                    raise RuntimeError(supabase_ssl_error_message("Supabase request")) from retry_exc
            else:
                raise RuntimeError(supabase_ssl_error_message("Supabase request")) from None
        if not response.ok:
            raise RuntimeError(f"Supabase write failed for {table}: {response.status_code} {response.text}")
        if not response.text.strip():
            return None
        try:
            return response.json()
        except ValueError:
            return None

    def _can_use_insecure_ssl_fallback(self) -> bool:
        return self.environment == "development" and self.allow_insecure_ssl
