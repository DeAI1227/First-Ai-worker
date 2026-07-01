from __future__ import annotations

import json
import os
import sys
import tempfile
from contextlib import ExitStack, redirect_stdout
from pathlib import Path
from typing import Any
from unittest.mock import patch

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from project_env import load_project_env

load_project_env(PROJECT_ROOT)

from api.schemas import PipelineRunRequest
from api.services.pipeline_service import run_pipeline_sync
from api.services import pipeline_service as pipeline_service_module
from collector import batch_runner as batch_runner_module
from collector import coverage_report as coverage_report_module
from collector.nodes import report_builder as report_builder_module
from collector.nodes import writer as writer_module
from ingestion import batch_report as ingestion_batch_report_module
from promotion import packet_promoter as packet_promoter_module
from promotion import promotion_report as promotion_report_module


def _env_flag(name: str, default: bool) -> bool:
    raw = os.getenv(name)
    if raw is None:
        return default
    return raw.strip().lower() in {"1", "true", "yes", "on"}


def run_autonomous_once() -> dict[str, Any]:
    request = PipelineRunRequest(
        scope=os.getenv("AUTONOMOUS_SCOPE", "all"),
        source_mode=os.getenv("AUTONOMOUS_SOURCE_MODE", "hybrid"),
        summarizer_mode=os.getenv("AUTONOMOUS_SUMMARIZER_MODE", "auto"),
        ingestion_dry_run=_env_flag("AUTONOMOUS_INGESTION_DRY_RUN", False),
        promotion_dry_run=_env_flag("AUTONOMOUS_PROMOTION_DRY_RUN", False),
    )
    with tempfile.TemporaryDirectory(prefix="first_ai_worker_autonomous_") as tmpdir:
        output_root = Path(tmpdir) / "output"
        output_root.mkdir(parents=True, exist_ok=True)
        logs_root = output_root / "logs"
        ingestion_logs_root = output_root / "ingestion_logs"
        promotion_logs_root = output_root / "promotion_logs"

        with ExitStack() as stack:
            stack.enter_context(patch.object(writer_module, "OUTPUT_ROOT", output_root))
            stack.enter_context(patch.object(report_builder_module, "OUTPUT_ROOT", output_root))
            stack.enter_context(patch.object(batch_runner_module, "OUTPUT_ROOT", output_root))
            stack.enter_context(patch.object(batch_runner_module, "BATCH_LOGS_ROOT", logs_root))
            stack.enter_context(patch.object(coverage_report_module, "OUTPUT_ROOT", output_root))
            stack.enter_context(patch.object(coverage_report_module, "COVERAGE_LOGS_ROOT", logs_root))
            stack.enter_context(patch.object(ingestion_batch_report_module, "OUTPUT_ROOT", output_root))
            stack.enter_context(patch.object(ingestion_batch_report_module, "BATCH_LOGS_ROOT", ingestion_logs_root))
            stack.enter_context(patch.object(packet_promoter_module, "OUTPUT_ROOT", output_root))
            stack.enter_context(patch.object(packet_promoter_module, "PROMOTION_LOGS_ROOT", promotion_logs_root))
            stack.enter_context(patch.object(promotion_report_module, "OUTPUT_ROOT", output_root))
            stack.enter_context(patch.object(promotion_report_module, "PROMOTION_LOGS_ROOT", promotion_logs_root))
            stack.enter_context(patch.object(pipeline_service_module, "OUTPUT_ROOT", output_root))
            stack.enter_context(patch.object(pipeline_service_module, "PIPELINE_LOGS_ROOT", logs_root))
            return run_pipeline_sync(request)


def main() -> int:
    with redirect_stdout(sys.stderr):
        result = run_autonomous_once()
    payload = {
        "status": result.get("status"),
        "autonomous_ready": result.get("autonomous_ready"),
        "collect_ran": result.get("collect_ran"),
        "ingestion_ran": result.get("ingestion_ran"),
        "promotion_ran": result.get("promotion_ran"),
        "wrote_to_supabase": result.get("wrote_to_supabase"),
        "message": result.get("message"),
        "errors": result.get("errors", []),
    }
    print(json.dumps(payload, ensure_ascii=False, indent=2))
    if payload["status"] == "failed":
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
