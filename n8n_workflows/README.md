# n8n Workflow Templates

These files are workflow templates and design notes for n8n.

Important notes:

- They are templates, not guaranteed one-click imports for every n8n version.
- Update the API base URL to match your own FastAPI deployment.
- Use `Authorization: Bearer <API_AUTH_TOKEN>` for protected endpoints.
- The dry-run workflow is the safest starting point for testing.
- The write-mode workflow uses Supabase ingestion write mode, so `SUPABASE_URL` and `SUPABASE_SERVICE_ROLE_KEY` must be available on the API side.
- Production deployments must set `API_AUTH_TOKEN`.
- The workflow templates use explicit status branching so `success`, `partial_success`, and `failed` are separated cleanly.

## Files

- `pipeline_daily_dry_run.json`
- `pipeline_daily_write_mode.json`
- `pipeline_status_branching.md`

## Suggested usage

1. Copy one of the workflow JSON files into n8n as a starting point.
2. Replace the API base URL with your FastAPI host.
3. Set the Authorization header with a Bearer token.
4. Use the status branching guide to wire success, partial success, and failure paths.
5. If your n8n version prefers a Switch node, keep the same `status` values and branch one node per outcome.
