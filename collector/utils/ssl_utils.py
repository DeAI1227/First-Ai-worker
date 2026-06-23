from __future__ import annotations

import os
from pathlib import Path


def parse_bool(value: str | None) -> bool:
    return str(value or "").strip().lower() not in {"0", "false", "no", "off"}


def allow_insecure_ssl() -> bool:
    environment = str(os.getenv("ENVIRONMENT", "development") or "development").strip().lower()
    allow_insecure = parse_bool(os.getenv("ALLOW_INSECURE_SSL", "false"))
    return environment == "development" and allow_insecure


def resolve_ssl_verify_setting() -> bool | str:
    """
    Resolve the SSL verification setting for requests.Session.verify.

    Priority:
    1. SUPABASE_CA_BUNDLE
    2. REQUESTS_CA_BUNDLE
    3. SSL_CERT_FILE
    4. default TLS verification (True)
    """

    for env_name in ("SUPABASE_CA_BUNDLE", "REQUESTS_CA_BUNDLE", "SSL_CERT_FILE"):
        bundle = str(os.getenv(env_name, "") or "").strip()
        if not bundle:
            continue
        bundle_path = Path(bundle).expanduser()
        if not bundle_path.exists():
            raise RuntimeError(f"{env_name} points to a missing file: {bundle_path}")
        return str(bundle_path)
    return True


def supabase_ssl_error_message(context: str) -> str:
    return (
        "SUPABASE_SSL_VERIFICATION_FAILED: SSL verification failed for "
        f"{context}. ALLOW_INSECURE_SSL is false. Refusing to retry with verify=False in production-safe mode. "
        "If HTTPS inspection or a corporate proxy is present, export its root CA and set SUPABASE_CA_BUNDLE, "
        "REQUESTS_CA_BUNDLE, or SSL_CERT_FILE to that certificate path."
    )
