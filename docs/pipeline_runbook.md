# Pipeline Runbook

## Local commands

```bash
uvicorn api.main:app --reload
python main.py --batch all
python -m ingestion.ingest_outputs --input output/ --dry-run
python -m promotion.promote_staging --input output/ --dry-run
python scripts/e2e_mvp_smoke.py
```

## GitHub Actions daily schedule

If you want the pipeline to run every day at **07:00 Asia/Taipei**, the workflow can use a timezone-aware schedule:

```yaml
on:
  schedule:
    - cron: "0 7 * * *"
      timezone: "Asia/Taipei"
```

GitHub Actions `schedule` triggers now support an IANA timezone. That makes the intent clearer than converting 07:00 Taipei time into UTC by hand.

This is the **official** free cloud scheduler for the project.

The daily workflow now does two things in one scheduled run:

1. Runs the daily backend collection/write flow in smaller category batches.
2. Runs the three-day report flow for the main surfaced scopes.

That split is intentional: it keeps each request shorter and makes `502` errors from Render cold starts much less likely.

Recommended workflow file:

- `.github/workflows/daily-pipeline.yml`

Recommended secrets:

- `FASTAPI_BASE_URL`
- `API_AUTH_TOKEN`

## How to use dry-run

- `ingestion --dry-run` reads packets, detects packet types, and maps rows without writing to Supabase.
- `promotion --dry-run` maps staging-style packets into production-style rows without writing to Supabase.
- The smoke test uses dry-run-friendly checks to confirm the local pipeline still connects end to end.

## Legacy n8n references

- Any `n8n`-named workflow docs in this repo are historical only.
- The main automation path now runs through GitHub Actions.

## How to use write mode

- Ingestion write mode requires `SUPABASE_URL` and `SUPABASE_SERVICE_ROLE_KEY`.
- Promotion write mode requires `SUPABASE_URL` and `SUPABASE_SERVICE_ROLE_KEY`.
- If those environment variables are missing, the run should fail cleanly and write a report that explains the problem.

## Why the daily workflow is split into smaller calls

The backend still uses a synchronous `/pipeline/run` endpoint, so a single huge request can time out when:

- Render is cold-starting
- Firecrawl is slow
- the batch contains many tasks

To reduce `502` risk, the GitHub Actions workflow now sends several smaller `/pipeline/run` requests instead of one giant request. That keeps the whole daily pipeline conceptually "one run" while reducing timeout pressure.

## Reports

- Batch report: `output/ingestion_logs/`
- Promotion report: `output/promotion_logs/`
- Pipeline report: `output/logs/`
- Smoke report: `output/logs/`

## What to inspect on failure

- `failed` or `partial_success` in batch reports
- `failed` in promotion reports
- `failed` or `partial_success` in pipeline reports
- errors in `output/logs/e2e_smoke_*.json`
