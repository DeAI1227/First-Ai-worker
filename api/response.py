from __future__ import annotations

from typing import Any, Literal

from pydantic import BaseModel, Field


class ApiError(BaseModel):
    stage: Literal["auth", "validate_request", "collect", "ingestion", "promotion", "internal"] = "internal"
    message: str
    severity: Literal["info", "warning", "error"] = "error"
    details: dict[str, Any] = Field(default_factory=dict)


class ApiEnvelope(BaseModel):
    status: Literal["success", "partial_success", "failed", "accepted"]
    execution_mode: Literal["sync", "async"] = "sync"
    job_id: str | None = None
    message: str = ""
    data: dict[str, Any] = Field(default_factory=dict)
    errors: list[ApiError] = Field(default_factory=list)


def normalize_api_error(raw_error: Any, *, default_stage: str) -> ApiError:
    if isinstance(raw_error, ApiError):
        return raw_error

    if isinstance(raw_error, str):
        return ApiError(stage=default_stage, message=raw_error)

    if isinstance(raw_error, dict):
        details = raw_error.get("details") if isinstance(raw_error.get("details"), dict) else {}
        stage = str(raw_error.get("stage") or default_stage)
        if stage not in {"auth", "validate_request", "collect", "ingestion", "promotion", "internal"}:
            details = {**details, "source_stage": stage}
            stage = default_stage
        return ApiError(
            stage=stage,
            message=str(raw_error.get("message") or raw_error.get("error_message") or "Unknown error"),
            severity=str(raw_error.get("severity") or "error"),
            details=details,
        )

    return ApiError(stage=default_stage, message=str(raw_error))


def normalize_api_errors(raw_errors: list[Any], *, default_stage: str) -> list[ApiError]:
    return [normalize_api_error(raw_error, default_stage=default_stage) for raw_error in raw_errors]
