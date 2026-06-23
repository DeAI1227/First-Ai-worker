from __future__ import annotations

from fastapi import APIRouter, Depends
from fastapi.responses import JSONResponse

from api.auth import require_api_token
from api.schemas import CollectRunRequest, CollectRunResponse
from api.services.collector_service import run_collect_sync
from api.services.response_factory import build_api_envelope, build_validate_request_envelope

router = APIRouter(prefix="/collect", dependencies=[Depends(require_api_token)])


@router.post("/run", response_model=CollectRunResponse)
def collect_run(payload: CollectRunRequest) -> CollectRunResponse:
    try:
        result = run_collect_sync(payload)
    except ValueError as exc:
        return JSONResponse(status_code=400, content=build_validate_request_envelope(str(exc)).model_dump())

    data = {
        "mode": result.get("mode", payload.mode),
        "batch": result.get("batch"),
        "output_files": list(result.get("output_files", [])),
        "run_errors": list(result.get("run_errors", [])),
        "batch_report": dict(result.get("batch_report", {})),
    }
    return CollectRunResponse.model_validate(
        build_api_envelope(
            status=str(result.get("status") or "failed"),
            message=str(result.get("message") or "Collector run completed."),
            data=data,
            raw_errors=list(result.get("run_errors", [])),
            default_stage="collect",
            execution_mode="sync",
            job_id=None,
        ).model_dump()
    )
