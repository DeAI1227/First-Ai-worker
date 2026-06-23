from __future__ import annotations

from fastapi import APIRouter, Depends

from api.auth import require_api_token
from api.schemas import IngestionRunRequest, IngestionRunResponse
from api.services.ingestion_service import run_ingestion_sync
from api.services.response_factory import build_api_envelope

router = APIRouter(prefix="/ingestion", dependencies=[Depends(require_api_token)])


@router.post("/run", response_model=IngestionRunResponse)
def ingestion_run(payload: IngestionRunRequest) -> IngestionRunResponse:
    report = run_ingestion_sync(
        input_path=payload.input_path,
        packet_type=payload.packet_type,
        dry_run=payload.dry_run,
    )
    return IngestionRunResponse.model_validate(
        build_api_envelope(
            status=str(report.get("status") or "failed"),
            message=str(report.get("message") or "Ingestion run completed."),
            data=dict(report),
            raw_errors=list(report.get("errors", [])),
            default_stage="ingestion",
        ).model_dump()
    )
