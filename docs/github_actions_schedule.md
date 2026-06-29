# GitHub Actions 7:00 Asia/Taipei Schedule

This repository uses GitHub Actions as the official free scheduler for the backend pipeline.

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
4. Warms the backend with `GET /health` before the main run.
5. Calls `POST /pipeline/run` several times in smaller chunks instead of one huge synchronous request:
   - daily industry batch
   - daily stock batch
   - daily macro batch
   - daily institution-watch batch
   - three-day industry reports
   - three-day macro report
6. Retries transient `502 / 503 / 504` responses so Render cold-starts are less likely to fail the run.
7. Prints the response and fails cleanly when the response status is `failed`.
8. Warns when the response status is `partial_success`.

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

The key operational change is that the workflow no longer sends one giant request that can sit on a cold Render instance for too long. It now breaks the work into smaller requests so the backend has a better chance to finish before timeout.

## Why GitHub Actions is the official scheduler

- It is free for this project.
- It runs in the cloud even when your laptop is off.
- It already has a committed workflow file in this repo.

## Legacy note

- `n8n` / `Umbrella` are no longer the main automation route for this project.
- Older n8n docs are kept only as reference material.
