from __future__ import annotations

import os
from datetime import datetime
from pathlib import Path
from typing import Any
from uuid import uuid4

from api.schemas import CollectRunRequest, IngestionRunRequest, PipelineRunRequest, PromotionRunRequest
from api.services.collector_service import run_collect_sync
from api.services.ingestion_service import run_ingestion_sync
from api.services.promotion_service import run_promotion_sync
from collector.utils.file_utils import write_json
from collector.utils.time_utils import now_iso, taipei_now


PROJECT_ROOT = Path(__file__).resolve().parents[2]
OUTPUT_ROOT = PROJECT_ROOT / "output"
PIPELINE_LOGS_ROOT = OUTPUT_ROOT / "logs"


def run_pipeline_sync(request: PipelineRunRequest) -> dict[str, Any]:
    started_at = now_iso()
    pipeline_id = f"pipeline_{taipei_now().strftime('%Y%m%d_%H%M%S')}_{uuid4().hex[:8]}"

    collect_request = _resolve_collect_request(request)
    ingestion_request = _resolve_ingestion_request(request)
    promotion_request = _resolve_promotion_request(request)

    collect_result, collect_ran = _run_collect_stage(request, collect_request)
    ingestion_result, ingestion_ran = _run_ingestion_stage(request, ingestion_request)
    promotion_result, promotion_ran = _run_promotion_stage(request, promotion_request)

    collect_status = str(collect_result.get("status") or "failed")
    ingestion_status = str(ingestion_result.get("status") or "failed")
    promotion_status = str(promotion_result.get("status") or "failed")

    pipeline_errors: list[dict[str, Any]] = []
    pipeline_errors.extend(_stage_errors("collect", collect_result))
    pipeline_errors.extend(_stage_errors("ingestion", ingestion_result))
    pipeline_errors.extend(_stage_errors("promotion", promotion_result))

    pipeline_status = _determine_pipeline_status(
        collect_status=collect_status,
        ingestion_status=ingestion_status,
        promotion_status=promotion_status,
    )
    write_requested = bool((not ingestion_request.dry_run) or (not promotion_request.dry_run))
    wrote_to_supabase = _did_write_to_supabase(ingestion_result, promotion_result)
    autonomous_ready = _determine_autonomous_ready(
        pipeline_status=pipeline_status,
        write_requested=write_requested,
        wrote_to_supabase=wrote_to_supabase,
        collect_ran=collect_ran,
        ingestion_ran=ingestion_ran,
        promotion_ran=promotion_ran,
    )

    pipeline_report = {
        "pipeline_id": pipeline_id,
        "started_at": started_at,
        "finished_at": now_iso(),
        "status": pipeline_status,
        "autonomous_ready": autonomous_ready,
        "collect_ran": collect_ran,
        "ingestion_ran": ingestion_ran,
        "promotion_ran": promotion_ran,
        "wrote_to_supabase": wrote_to_supabase,
        "collect_status": collect_status,
        "ingestion_status": ingestion_status,
        "promotion_status": promotion_status,
        "output_files": _collect_output_files(collect_result, ingestion_result, promotion_result),
        "errors": pipeline_errors,
    }
    try:
        pipeline_report_path = write_pipeline_report(pipeline_report)
    except Exception as exc:  # pragma: no cover - defensive
        pipeline_report_path = ""
        pipeline_errors.append(
            {
                "stage": "internal",
                "message": f"Failed to write pipeline report: {exc}",
                "severity": "error",
                "details": {},
            }
        )
        pipeline_status = "failed"
        pipeline_report["status"] = pipeline_status
        pipeline_report["errors"] = pipeline_errors
        pipeline_report["autonomous_ready"] = False
    pipeline_report["pipeline_report_path"] = pipeline_report_path
    pipeline_report["output_files"] = _unique_strings(
        [*pipeline_report["output_files"], pipeline_report_path],
    )

    return {
        "status": pipeline_status,
        "execution_mode": "sync",
        "job_id": None,
        "message": "Pipeline completed.",
        "autonomous_ready": autonomous_ready if pipeline_status != "failed" else False,
        "collect_ran": collect_ran,
        "ingestion_ran": ingestion_ran,
        "promotion_ran": promotion_ran,
        "wrote_to_supabase": wrote_to_supabase,
        "data": {
            "collect_result": collect_result,
            "ingestion_result": ingestion_result,
            "promotion_result": promotion_result,
            "pipeline_report": pipeline_report,
        },
        "errors": pipeline_errors,
    }


def write_pipeline_report(report: dict[str, Any], *, output_root: Path | None = None) -> str:
    root = output_root or OUTPUT_ROOT
    logs_root = root if root.name == "logs" else root / "logs"
    logs_root.mkdir(parents=True, exist_ok=True)
    timestamp = _timestamp_for_filename(report.get("finished_at") or report.get("started_at"))
    path = logs_root / f"pipeline_run_{timestamp}.json"
    return write_json(path, report)


def _run_collect_stage(request: PipelineRunRequest, collect_request: CollectRunRequest | None) -> tuple[dict[str, Any], bool]:
    if collect_request is None:
        return _skipped_stage_result("Collect stage skipped.", mode=request.mode), False

    if request.collect is not None and not request.collect.enabled:
        return _skipped_stage_result("Collect stage skipped.", mode=collect_request.mode, batch=collect_request.batch), False

    try:
        return run_collect_sync(collect_request), True
    except Exception as exc:  # pragma: no cover - defensive
        return (
            _failed_stage_result(
                stage="collect",
                message=str(exc),
                details={"mode": collect_request.mode, "batch": collect_request.batch},
            ),
            True,
        )


def _run_ingestion_stage(
    request: PipelineRunRequest,
    ingestion_request: IngestionRunRequest | None,
) -> tuple[dict[str, Any], bool]:
    if ingestion_request is None:
        return _skipped_stage_result("Ingestion stage skipped.", mode="dry_run"), False

    if request.ingestion is not None and not request.ingestion.enabled:
        return _skipped_stage_result(
            "Ingestion stage skipped.",
            mode="dry_run" if ingestion_request.dry_run else "write",
        ), False

    try:
        return (
            run_ingestion_sync(
                input_path=ingestion_request.input_path,
                packet_type=ingestion_request.packet_type,
                dry_run=ingestion_request.dry_run,
            ),
            True,
        )
    except Exception as exc:  # pragma: no cover - defensive
        return (
            _failed_stage_result(
                stage="ingestion",
                message=str(exc),
                details={"input_path": ingestion_request.input_path, "packet_type": ingestion_request.packet_type},
            ),
            True,
        )


def _run_promotion_stage(
    request: PipelineRunRequest,
    promotion_request: PromotionRunRequest | None,
) -> tuple[dict[str, Any], bool]:
    if promotion_request is None:
        return _skipped_stage_result("Promotion stage skipped.", mode="dry_run"), False

    if request.promotion is not None and not request.promotion.enabled:
        return _skipped_stage_result(
            "Promotion stage skipped.",
            mode="dry_run" if promotion_request.dry_run else "write",
        ), False

    try:
        return (
            run_promotion_sync(
                input_path=promotion_request.input_path,
                packet_type=promotion_request.packet_type,
                dry_run=promotion_request.dry_run,
            ),
            True,
        )
    except Exception as exc:  # pragma: no cover - defensive
        return (
            _failed_stage_result(
                stage="promotion",
                message=str(exc),
                details={"input_path": promotion_request.input_path, "packet_type": promotion_request.packet_type},
            ),
            True,
        )


def _resolve_collect_request(request: PipelineRunRequest) -> CollectRunRequest | None:
    if request.collect is not None:
        return CollectRunRequest.model_validate(request.collect.model_dump(exclude={"enabled"}))

    scope = str(request.scope or "all").strip() or "all"
    kwargs: dict[str, Any] = {
        "mode": request.mode,
        "source_mode": request.source_mode,
        "summarizer_mode": request.summarizer_mode,
        "llm_provider": request.llm_provider,
        "search_provider": request.search_provider,
        "dry_run": True,
    }
    if scope in {"industries", "stocks", "macro", "institution_watch", "all"}:
        kwargs["batch"] = scope
    else:
        kwargs["scope"] = scope
        if request.scope_name:
            kwargs["scope_name"] = request.scope_name
        if request.stock_code:
            kwargs["stock_code"] = request.stock_code
        if request.stock_name:
            kwargs["stock_name"] = request.stock_name
    return CollectRunRequest.model_validate(kwargs)


def _resolve_ingestion_request(request: PipelineRunRequest) -> IngestionRunRequest | None:
    if request.ingestion is not None:
        return IngestionRunRequest.model_validate(request.ingestion.model_dump(exclude={"enabled"}))
    return IngestionRunRequest(input_path=str(OUTPUT_ROOT), packet_type="all", dry_run=bool(request.ingestion_dry_run))


def _resolve_promotion_request(request: PipelineRunRequest) -> PromotionRunRequest | None:
    if request.promotion is not None:
        return PromotionRunRequest.model_validate(request.promotion.model_dump(exclude={"enabled"}))
    return PromotionRunRequest(input_path=str(OUTPUT_ROOT), packet_type="all", dry_run=bool(request.promotion_dry_run))


def _did_write_to_supabase(ingestion_result: dict[str, Any], promotion_result: dict[str, Any]) -> bool:
    if "wrote_to_supabase" in ingestion_result or "wrote_to_supabase" in promotion_result:
        return bool(ingestion_result.get("wrote_to_supabase", False)) or bool(
            promotion_result.get("wrote_to_supabase", False)
        )

    ingestion_wrote = str(ingestion_result.get("mode") or "").lower() == "write" and str(ingestion_result.get("status") or "") in {
        "success",
        "partial_success",
    }
    promotion_wrote = str(promotion_result.get("mode") or "").lower() == "write" and str(promotion_result.get("status") or "") in {
        "success",
        "partial_success",
    }
    return ingestion_wrote or promotion_wrote


def _determine_autonomous_ready(
    *,
    pipeline_status: str,
    write_requested: bool,
    wrote_to_supabase: bool,
    collect_ran: bool,
    ingestion_ran: bool,
    promotion_ran: bool,
) -> bool:
    if not (collect_ran and ingestion_ran and promotion_ran):
        return False
    if write_requested:
        return wrote_to_supabase and pipeline_status in {"success", "partial_success"}
    return pipeline_status in {"success", "partial_success"}


def _determine_pipeline_status(*, collect_status: str, ingestion_status: str, promotion_status: str) -> str:
    stage_statuses = [collect_status, ingestion_status, promotion_status]
    enabled_statuses = [status for status in stage_statuses if status != "skipped"]

    if not enabled_statuses:
        return "failed"

    if collect_status == "failed":
        return "failed"

    if any(status == "failed" for status in enabled_statuses):
        return "partial_success" if any(status == "success" for status in enabled_statuses) else "failed"

    if any(status == "partial_success" for status in enabled_statuses):
        return "partial_success"

    if any(status == "success" for status in enabled_statuses):
        return "success"

    return "failed"


def _stage_errors(stage: str, result: dict[str, Any]) -> list[dict[str, Any]]:
    raw_errors = result.get("run_errors")
    if raw_errors is None:
        raw_errors = result.get("errors")
    if raw_errors is None:
        raw_errors = []

    normalized = []
    for raw_error in raw_errors:
        normalized.append(_normalize_error(stage, raw_error))
    return normalized


def _normalize_error(stage: str, raw_error: Any) -> dict[str, Any]:
    if isinstance(raw_error, dict):
        details = raw_error.get("details") if isinstance(raw_error.get("details"), dict) else {}
        return {
            "stage": str(raw_error.get("stage") or stage),
            "message": str(raw_error.get("message") or raw_error.get("error_message") or "Unknown error"),
            "severity": _normalize_severity(raw_error.get("severity")),
            "details": details,
        }
    return {
        "stage": stage,
        "message": str(raw_error),
        "severity": "error",
        "details": {},
    }


def _failed_stage_result(*, stage: str, message: str, details: dict[str, Any] | None = None) -> dict[str, Any]:
    return {
        "status": "failed",
        "execution_mode": "sync",
        "job_id": None,
        "message": f"{stage.title()} stage failed: {message}",
        "output_files": [],
        "run_errors": [
            {
                "stage": stage,
                "message": message,
                "severity": "error",
                "details": details or {},
            }
        ],
        "batch_report": {},
    }


def _skipped_stage_result(message: str, *, mode: str, batch: str | None = None) -> dict[str, Any]:
    return {
        "status": "skipped",
        "execution_mode": "sync",
        "job_id": None,
        "message": message,
        "mode": mode,
        "batch": batch,
        "output_files": [],
        "run_errors": [],
        "batch_report": {},
    }


def _collect_output_files(*results: dict[str, Any]) -> list[str]:
    files: list[str] = []
    for result in results:
        files.extend(_extract_result_output_files(result))
    return _unique_strings(files)


def _extract_result_output_files(result: dict[str, Any]) -> list[str]:
    files: list[str] = []
    for key in ("output_files", "output_paths"):
        value = result.get(key)
        if isinstance(value, list):
            files.extend([str(item) for item in value if str(item).strip()])
    batch_report = result.get("batch_report")
    if isinstance(batch_report, dict):
        for key in ("batch_report_path", "coverage_report_path", "pipeline_report_path"):
            value = batch_report.get(key)
            if isinstance(value, str) and value.strip():
                files.append(value)
    for key in ("batch_report_path", "pipeline_report_path"):
        value = result.get(key)
        if isinstance(value, str) and value.strip():
            files.append(value)
    return files


def _unique_strings(values: list[str]) -> list[str]:
    seen: set[str] = set()
    unique: list[str] = []
    for value in values:
        text = str(value).strip()
        if not text or text in seen:
            continue
        seen.add(text)
        unique.append(text)
    return unique


def _normalize_severity(value: Any) -> str:
    text = str(value or "error").strip().lower()
    if text in {"info", "warning", "error"}:
        return text
    return "error"


def _timestamp_for_filename(value: Any) -> str:
    text = str(value or now_iso())
    try:
        dt = datetime.fromisoformat(text.replace("Z", "+00:00"))
    except ValueError:
        dt = taipei_now()
    return dt.strftime("%Y-%m-%d_%H%M%S")
