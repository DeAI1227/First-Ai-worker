# Backend API Contract Pack

Frontend reads Supabase views directly.
n8n calls FastAPI to trigger backend pipeline.
FastAPI does not replace Supabase as the frontend data source.

## System flow

```text
n8n
→ FastAPI /pipeline/run
→ LangGraph Collector
→ output packets
→ ingestion
→ Supabase staging
→ promotion
→ Supabase production/views
→ frontend reads Supabase
```

## Contract layers

### Current sync contract

This is the live API shape implemented in the project today.

- `GET /health`
- `POST /collect/run`
- `POST /ingestion/run`
- `POST /promotion/run`
- `POST /pipeline/run`

All protected endpoints use the same auth rule:

```text
Authorization: Bearer <API_AUTH_TOKEN>
```

If `API_AUTH_TOKEN` is empty, protected endpoints are not callable.

### Future async contract

Async job endpoints are reserved for later. They are not implemented yet, but the response envelope keeps room for them:

- `POST /collect/jobs`
- `GET /collect/jobs/{job_id}`
- `POST /ingestion/jobs`
- `GET /ingestion/jobs/{job_id}`
- `POST /promotion/jobs`
- `GET /promotion/jobs/{job_id}`

`job_id` stays `null` in the current sync version.

## Shared response envelope

All major API endpoints return the same outer shape:

```json
{
  "status": "success | partial_success | failed | accepted",
  "execution_mode": "sync",
  "job_id": null,
  "message": "human readable message",
  "data": {},
  "errors": []
}
```

### Response rules

- `success` means the endpoint completed successfully.
- `partial_success` means the main action succeeded, but one or more sub-steps produced warnings or recoverable errors.
- `failed` means the request or pipeline failed.
- `accepted` is reserved for future async job submission.
- `errors` is always an array.
- `job_id` is `null` for the sync MVP.

`errors` use this normalized item shape:

```json
{
  "stage": "auth | validate_request | collect | ingestion | promotion | internal",
  "message": "error message",
  "severity": "info | warning | error",
  "details": {}
}
```

## Endpoint reference

### `GET /health`

Purpose: lightweight readiness check.

Request body: none.

Response:

```json
{
  "status": "ok",
  "service": "investment_research_collector",
  "version": "mvp"
}
```

This endpoint does not require auth.

### `POST /collect/run`

Purpose: run the collector synchronously for a single task, a batch slice, or the default task set.

Current request model:

```json
{
  "mode": "daily",
  "scope": "industry",
  "scope_name": "散熱",
  "stock_code": "6230",
  "stock_name": "尼得科超眾",
  "source_mode": "hybrid",
  "summarizer_mode": "mock",
  "llm_provider": "auto",
  "search_provider": "auto",
  "batch": null,
  "dry_run": false
}
```

Batch request example:

```json
{
  "batch": "industries",
  "source_mode": "hybrid",
  "summarizer_mode": "mock",
  "llm_provider": "auto",
  "search_provider": "auto",
  "dry_run": false
}
```

Current response `data` fields:

```json
{
  "mode": "daily",
  "batch": null,
  "output_files": [],
  "run_errors": [],
  "batch_report": {}
}
```

Notes:

- `batch` controls batch generation.
- `scope` and `scope_name` are used for single-task or three-day runs.
- `three_day` mode requires `scope` and `scope_name`.
- Future async collect jobs may reuse the same envelope with `accepted` and a non-null `job_id`.

### `POST /ingestion/run`

Purpose: read packet JSON files from `output/`, map them to staging rows, and either dry-run or write to Supabase staging.

Current request model:

```json
{
  "input_path": "output/",
  "packet_type": "all",
  "dry_run": true
}
```

Current response `data` is the ingestion batch report object.

Notes:

- `dry_run=true` does not require Supabase credentials.
- `dry_run=false` requires `SUPABASE_URL` and `SUPABASE_SERVICE_ROLE_KEY`.

### `POST /promotion/run`

Purpose: promote staging-style packets into production tables or dry-run the mapping.

Current request model:

```json
{
  "input_path": "output/",
  "packet_type": "all",
  "dry_run": true
}
```

Current response `data` is the promotion report object.

Notes:

- `dry_run=true` only maps packets.
- `dry_run=false` writes to production tables and requires Supabase credentials.

### `POST /pipeline/run`

Purpose: one-shot orchestration for collect → ingestion → promotion.

Current request model:

```json
{
  "scope": "all",
  "source_mode": "hybrid",
  "summarizer_mode": "auto",
  "ingestion_dry_run": false,
  "promotion_dry_run": false,
  "collect": {
    "batch": "all",
    "source_mode": "hybrid",
    "summarizer_mode": "auto",
    "llm_provider": "auto",
    "search_provider": "auto"
  },
  "ingestion": {
    "enabled": true,
    "input_path": "output/",
    "packet_type": "all",
    "dry_run": true
  },
  "promotion": {
    "enabled": true,
    "input_path": "output/",
    "packet_type": "all",
    "dry_run": true
  }
}
```

Current response `data` fields:

```json
{
  "collect_result": {},
  "ingestion_result": {},
  "promotion_result": {},
  "pipeline_report": {}
}
```

Current top-level autonomous flags:

```json
{
  "autonomous_ready": true,
  "collect_ran": true,
  "ingestion_ran": true,
  "promotion_ran": true,
  "wrote_to_supabase": false
}
```

The `pipeline_report` is written to `output/logs/` and the path is returned inside the response data.

## OpenAPI / Swagger

FastAPI serves interactive docs at:

- `/docs`
- `/openapi.json`

If a request or response field changes in code, update the Pydantic schemas in `api/schemas.py` so Swagger stays accurate.

## Practical notes for n8n and operators

- n8n should branch on `status`.
- `success` means continue.
- `partial_success` means notify for inspection.
- `failed` means stop and alert.
- Do not treat `output/` JSON as a frontend data source.
- Do not treat these endpoints as the frontend read path; they are orchestration endpoints only.
