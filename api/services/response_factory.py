from __future__ import annotations

from typing import Any

from api.response import ApiEnvelope, normalize_api_errors


def build_api_envelope(
    *,
    status: str,
    message: str,
    data: dict[str, Any] | None = None,
    raw_errors: list[Any] | None = None,
    default_stage: str = "internal",
    execution_mode: str = "sync",
    job_id: str | None = None,
) -> ApiEnvelope:
    return ApiEnvelope(
        status=status,  # type: ignore[arg-type]
        execution_mode=execution_mode,  # type: ignore[arg-type]
        job_id=job_id,
        message=message,
        data=data or {},
        errors=normalize_api_errors(raw_errors or [], default_stage=default_stage),
    )


def build_validate_request_envelope(message: str) -> ApiEnvelope:
    return ApiEnvelope(
        status="failed",
        execution_mode="sync",
        job_id=None,
        message=message,
        data={},
        errors=[{"stage": "validate_request", "message": message, "severity": "error", "details": {}}],
    )
