# n8n Setup Steps

This document explains how to wire n8n to the backend in a real deployment.

n8n only triggers the backend. It does not contain research logic.

## Goal

```text
Schedule Trigger
→ HTTP Request
→ FastAPI POST /pipeline/run
→ collect
→ ingestion
→ Supabase staging
→ promotion
→ Supabase production/views
```

## 1. Create the workflow

1. Open n8n.
2. Create a new workflow.
3. Name it something clear, for example:
   - `AI Investment Research Daily Pipeline`

## 2. Add a Schedule Trigger

1. Add a `Schedule Trigger` node.
2. Set it to run every day at `07:00`.
3. Use the `Asia/Taipei` timezone if the node supports it.
4. If your n8n instance stores all schedules in UTC, convert 07:00 Taipei time to UTC before saving.

## 3. Add an HTTP Request node

1. Add an `HTTP Request` node after the schedule trigger.
2. Method: `POST`
3. URL:

```text
https://<your-backend-host>/pipeline/run
```

For local testing:

```text
http://localhost:8000/pipeline/run
```

## 4. Add headers

Use these headers:

```text
Authorization: Bearer {{$env.API_AUTH_TOKEN}}
Content-Type: application/json
```

Important:

- Do not hardcode the token in the workflow JSON.
- Do not put `SUPABASE_SERVICE_ROLE_KEY` into n8n.
- n8n should only know the API token needed to call FastAPI.

## 5. Use this request body

```json
{
  "scope": "all",
  "source_mode": "hybrid",
  "summarizer_mode": "auto",
  "ingestion_dry_run": false,
  "promotion_dry_run": false
}
```

## 6. Branch on response status

After the HTTP Request node, add an `IF` node that checks `{{$json.status}}`.

### success

- Record the run.
- Stop the workflow normally.

### partial_success

- Notify a human to inspect the pipeline report.

### failed

- Alert immediately.
- Stop further automation.

## 7. What n8n should read from the response

The response should include at least:

- `status`
- `message`
- `data.pipeline_report`
- `data.collect_result`
- `data.ingestion_result`
- `data.promotion_result`
- `errors`

## 8. If something fails

Check these first:

1. `API_AUTH_TOKEN`
2. FastAPI service is running
3. `SUPABASE_URL`
4. `SUPABASE_SERVICE_ROLE_KEY`
5. `output/` path and logs
6. `pipeline_report`

## 9. What n8n is responsible for

- Scheduling
- Triggering FastAPI
- Routing on success / partial_success / failed
- Notifications and basic orchestration

## 10. What n8n is not responsible for

- Research strategy
- Source selection
- Summarization logic
- Data modeling
- Database schema

## Related files

- `docs/n8n_api_usage.md`
- `docs/deployment_wiring_checklist.md`
- `docs/pipeline_runbook.md`
