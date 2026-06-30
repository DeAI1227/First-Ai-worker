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

This is the **official** free cloud scheduler for the project.

The scheduled backend is now split into three workflows:

1. `.github/workflows/daily-core.yml`
2. `.github/workflows/stock-pipeline.yml`
3. `.github/workflows/three-day-refresh.yml`

Schedule mapping:

- `0 23 * * *` → 07:00 Asia/Taipei → daily core
- `20 23 * * *` → 07:20 Asia/Taipei → stock pipeline
- `40 23 * * *` → 07:40 Asia/Taipei → three-day refresh

Recommended secrets:

- `SUPABASE_URL`
- `SUPABASE_SERVICE_ROLE_KEY`
- `GEMINI_API_KEY`
- `GEMINI_MODEL`
- `AGNES_API_KEY`
- `AGNES_API_URL` or `AGNES_BASE_URL`
- `AGNES_MODEL`
- `FIRECRAWL_BASE_URL`
- `FIRECRAWL_API_KEY`

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

## Why the daily workflow is split

The old design packed:

- macro
- industries
- stocks
- institution watch
- three-day reports
- ingestion
- promotion

into one scheduled job.

That made single runs too long. The new split keeps each workflow smaller, easier to observe, and less likely to fail as one giant unit.

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
