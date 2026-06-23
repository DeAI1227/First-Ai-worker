# GitHub Actions 7:00 Asia/Taipei Schedule

This repository uses GitHub Actions as one possible free scheduler for the backend pipeline.

## Purpose

Trigger the backend pipeline every day at 07:00 Taipei time without requiring your computer to stay on.

## Current workflow file

- `.github/workflows/daily-pipeline.yml`

## Workflow behavior

The workflow:

1. Runs on a scheduled cron.
2. Uses the `Asia/Taipei` timezone in the schedule definition.
3. Reads these required secrets:
   - `FASTAPI_BASE_URL`
   - `API_AUTH_TOKEN`
4. Calls `POST /pipeline/run` on the FastAPI backend.
5. Prints the response and fails cleanly when the response status is `failed`.
6. Warns when the response status is `partial_success`.

## Required GitHub secrets

Set these in the repository settings under **Settings → Secrets and variables → Actions**:

- `FASTAPI_BASE_URL`
- `API_AUTH_TOKEN`

Do not hardcode the token in the workflow file.

## What to expect

A successful run should show:

- `status=success`
- `execution_mode=sync`
- `job_id=null`
- `errors=0`

A partial success is still a valid run, but it should be inspected.

## When to use GitHub Actions vs n8n

- Use GitHub Actions if you want a free cloud scheduler with no extra server to maintain.
- Use n8n if you already have a self-hosted or paid automation stack and want more workflow branching.

For this project, both can trigger the same FastAPI endpoint.
