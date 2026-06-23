# Pipeline Orchestrator Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add a synchronous `/pipeline/run` API that composes collect, ingestion, and promotion, then writes a pipeline report to `output/logs/`.

**Architecture:** Keep the FastAPI route thin and put orchestration into `api/services/pipeline_service.py`. Reuse the existing collector, ingestion, and promotion service functions so CLI and API stay aligned. The pipeline should continue after non-fatal stage failures, aggregate results into one response, and persist a JSON report for n8n and later async upgrades.

**Tech Stack:** FastAPI, Pydantic, existing collector/ingestion/promotion services, JSON file output.

---

### Task 1: Add pipeline request/response schema

**Files:**
- Modify: `api/schemas.py`

- [ ] **Step 1: Extend the API models**

Add nested models that mirror the stage payloads and keep the current sync response shape:

```python
class PipelineCollectRequest(CollectRunRequest):
    enabled: bool = True


class PipelineIngestionRequest(IngestionRunRequest):
    enabled: bool = True


class PipelinePromotionRequest(PromotionRunRequest):
    enabled: bool = True


class PipelineRunRequest(BaseModel):
    collect: PipelineCollectRequest = Field(default_factory=PipelineCollectRequest)
    ingestion: PipelineIngestionRequest = Field(default_factory=PipelineIngestionRequest)
    promotion: PipelinePromotionRequest = Field(default_factory=PipelinePromotionRequest)


class PipelineRunResponse(ApiEnvelope):
    message: str = "Pipeline completed."
```

- [ ] **Step 2: Verify request fields match the existing service inputs**

The collect stage must accept `batch`, `scope`, `scope_name`, `stock_code`, `stock_name`, `source_mode`, `summarizer_mode`, `llm_provider`, and `search_provider`. Ingestion and promotion must accept `input_path`, `packet_type`, and `dry_run`.

### Task 2: Implement the pipeline service

**Files:**
- Create: `api/services/pipeline_service.py`

- [ ] **Step 1: Compose the stage services**

Implement one function that:
1. Calls `run_collect_sync(...)` when `collect.enabled` is true.
2. Calls `run_ingestion_sync(...)` when `ingestion.enabled` is true.
3. Calls `run_promotion_sync(...)` when `promotion.enabled` is true.
4. Catches exceptions per stage and converts them into stage errors instead of crashing.

- [ ] **Step 2: Build stage status and pipeline status**

Use these rules:

```python
collect_status = "skipped" if not collect.enabled else collect_result["status"]
ingestion_status = "skipped" if not ingestion.enabled else ingestion_result["status"]
promotion_status = "skipped" if not promotion.enabled else promotion_result["status"]
```

Pipeline status:
- `failed` if collect fails or no major collect output is produced.
- `partial_success` if at least one stage succeeds but another stage reports warning/failure.
- `success` only when enabled stages complete successfully or are skipped intentionally.

- [ ] **Step 3: Write the pipeline report**

Persist a JSON file to:

```text
output/logs/pipeline_run_YYYY-MM-DD_HHMMSS.json
```

The report should include:

```python
{
    "pipeline_id": "...",
    "started_at": "...",
    "finished_at": "...",
    "status": "...",
    "collect_status": "...",
    "ingestion_status": "...",
    "promotion_status": "...",
    "output_files": [...],
    "errors": [...]
}
```

- [ ] **Step 4: Return a unified response payload**

Return:

```python
{
    "status": pipeline_status,
    "execution_mode": "sync",
    "job_id": None,
    "message": "Pipeline completed.",
    "data": {
        "collect_result": collect_result,
        "ingestion_result": ingestion_result,
        "promotion_result": promotion_result,
        "pipeline_report": pipeline_report,
    },
    "errors": pipeline_errors,
}
```

### Task 3: Add the pipeline route and register it

**Files:**
- Create: `api/routes/pipeline.py`
- Modify: `api/main.py`

- [ ] **Step 1: Add `POST /pipeline/run`**

The route should be protected with the existing API token dependency and call the pipeline service directly.

- [ ] **Step 2: Register the route in `api/main.py`**

Include the new router alongside health, collect, ingestion, and promotion.

### Task 4: Add API coverage

**Files:**
- Modify: `tests/test_api.py`

- [ ] **Step 1: Add a protected-route rejection test**

Confirm missing auth on `/pipeline/run` returns 401/403.

- [ ] **Step 2: Add a synchronous happy-path test**

Send a small pipeline payload and assert:
`status`, `execution_mode == "sync"`, `job_id is None`, and `data` includes `collect_result`, `ingestion_result`, `promotion_result`, and `pipeline_report`.

- [ ] **Step 3: Add a skipped-stage test**

Send a payload with `ingestion.enabled = false` and `promotion.enabled = false`, then assert the returned stage statuses are `skipped`.

- [ ] **Step 4: Assert pipeline report file creation**

Check that the returned `pipeline_report` includes a file path and that the file exists on disk.

### Task 5: Update docs and verify

**Files:**
- Modify: `README.md`

- [ ] **Step 1: Document `/pipeline/run`**

Explain:
- It is synchronous in MVP.
- It composes collect → ingestion → promotion.
- It returns a pipeline report in `output/logs/`.
- It is the preferred n8n entrypoint for one-shot runs.
- Future async endpoints can later be added as `POST /collect/jobs` and `GET /collect/jobs/{job_id}` style flows.

- [ ] **Step 2: Run verification**

Run:

```bash
python main.py --batch industries
python -m ingestion.ingest_outputs --input output/ --dry-run
python -m promotion.promote_staging --input output/ --dry-run
python -m unittest discover -s tests -p "test_*.py" -v
python -m compileall .
```

