from __future__ import annotations

from fastapi import APIRouter, Depends

from api.auth import require_api_token
from api.schemas import PipelineRunRequest, PipelineRunResponse
from api.services.pipeline_service import run_pipeline_sync
from api.services.response_factory import build_api_envelope

router = APIRouter(prefix="/pipeline", dependencies=[Depends(require_api_token)])


@router.post("/run", response_model=PipelineRunResponse)
def pipeline_run(payload: PipelineRunRequest) -> PipelineRunResponse:
    result = run_pipeline_sync(payload)
    response_payload = build_api_envelope(
        status=str(result.get("status") or "failed"),
        message=str(result.get("message") or "Pipeline completed."),
        data=dict(result.get("data") or {}),
        raw_errors=list(result.get("errors", [])),
        default_stage="internal",
        execution_mode=str(result.get("execution_mode") or "sync"),
        job_id=result.get("job_id"),
    ).model_dump()
    response_payload.update(
        {
            "autonomous_ready": bool(result.get("autonomous_ready", False)),
            "collect_ran": bool(result.get("collect_ran", False)),
            "ingestion_ran": bool(result.get("ingestion_ran", False)),
            "promotion_ran": bool(result.get("promotion_ran", False)),
            "wrote_to_supabase": bool(result.get("wrote_to_supabase", False)),
        }
    )
    return PipelineRunResponse.model_validate(
        response_payload
    )
