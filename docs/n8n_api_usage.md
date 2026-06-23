# n8n API Usage

This guide shows how n8n should call the FastAPI orchestrator.

The frontend reads Supabase production views directly.
n8n calls FastAPI to trigger backend jobs.
FastAPI is not the frontend data source.

## Authorization

Use this header for protected endpoints:

```http
Authorization: Bearer <API_AUTH_TOKEN>
Content-Type: application/json
```

Do not hardcode the token into workflows.
Use n8n credentials or environment variables.

If `API_AUTH_TOKEN` is missing on the backend, protected endpoints are not callable.

## Daily dry-run

Recommended sync call:

```http
POST /pipeline/run
```

Request body:

```json
{
  "scope": "all",
  "source_mode": "hybrid",
  "summarizer_mode": "auto",
  "ingestion_dry_run": true,
  "promotion_dry_run": true,
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

## Daily write mode

Same pipeline call, but write to staging and production:

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
    "dry_run": false
  },
  "promotion": {
    "enabled": true,
    "input_path": "output/",
    "packet_type": "all",
    "dry_run": false
  }
}
```

Write mode requires `SUPABASE_URL` and `SUPABASE_SERVICE_ROLE_KEY` on the backend side.

## Response branching

Use the top-level `status` field:

```text
success -> record success and finish
partial_success -> notify a human to inspect the batch report
failed -> alert immediately and stop further automation
```

Recommended n8n shape:

```text
Cron Trigger
↓
HTTP Request: POST /pipeline/run
↓
IF Node: response.status
├─ success
├─ partial_success
└─ failed
```

## What to inspect when something fails

- API token
- Supabase env vars
- input path
- batch report path
- pipeline report path

The pipeline response includes:

- `collect_result`
- `ingestion_result`
- `promotion_result`
- `pipeline_report`

## Future async job placeholders

The sync-first MVP keeps room for async jobs later:

```text
POST /pipeline/jobs
GET /pipeline/jobs/{job_id}
```

If batch runs become too slow later, n8n can switch from sync call-and-wait to submit-and-poll without changing the overall data flow.
