from __future__ import annotations

from fastapi import APIRouter, Depends

from api.auth import require_api_token
from api.schemas import PromotionRunRequest, PromotionRunResponse
from api.services.promotion_service import run_promotion_sync
from api.services.response_factory import build_api_envelope

router = APIRouter(prefix="/promotion", dependencies=[Depends(require_api_token)])


@router.post("/run", response_model=PromotionRunResponse)
def promotion_run(payload: PromotionRunRequest) -> PromotionRunResponse:
    report = run_promotion_sync(
        input_path=payload.input_path,
        packet_type=payload.packet_type,
        dry_run=payload.dry_run,
    )
    return PromotionRunResponse.model_validate(
        build_api_envelope(
            status=str(report.get("status") or "failed"),
            message=str(report.get("message") or "Promotion run completed."),
            data=dict(report),
            raw_errors=list(report.get("errors", [])),
            default_stage="promotion",
        ).model_dump()
    )
