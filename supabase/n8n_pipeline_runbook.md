# n8n Pipeline Runbook

This runbook explains how n8n should call the FastAPI pipeline endpoint.

## Endpoint

```http
POST http://localhost:8000/pipeline/run
Authorization: Bearer <API_AUTH_TOKEN>
Content-Type: application/json
```

## Batch industries body

```json
{
  "collect": {
    "batch": "industries",
    "source_mode": "hybrid",
    "summarizer_mode": "mock",
    "llm_provider": "auto",
    "search_provider": "mock"
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

## Batch all dry-run body

```json
{
  "collect": {
    "batch": "all",
    "source_mode": "hybrid",
    "summarizer_mode": "mock",
    "llm_provider": "auto",
    "search_provider": "mock"
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

## How to branch on response status

Use the top-level `response.status`:

```text
success -> normal end
partial_success -> notify for inspection
failed -> alert immediately
```

Recommended n8n logic:

```text
HTTP Request: POST /pipeline/run
↓
IF Node: response.status
├─ success
├─ partial_success
└─ failed
```

## What to inspect on failure

If the pipeline fails, check:

1. API token
2. Supabase key
3. output path
4. batch report
5. pipeline report

The pipeline response returns:

- `collect_result`
- `ingestion_result`
- `promotion_result`
- `pipeline_report`

The `pipeline_report_path` in `data.pipeline_report` points to the JSON written under `output/logs/`.

## Future async job shape

This MVP is sync-first. Future versions may add:

- `POST /pipeline/jobs`
- `GET /pipeline/jobs/{job_id}`

That future shape is not implemented yet, but this runbook keeps the sync-first contract stable so n8n can switch later with minimal changes.
