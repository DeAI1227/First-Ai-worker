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
