# Supabase Staging Schema

This folder contains the staging schema design for the Investment Research Collector.

For the field-by-field mapping between Collector output JSON and Supabase staging tables, see
[ingestion_mapping.md](./ingestion_mapping.md).

For the future Python ingestion script design, see
[ingestion_script_design.md](./ingestion_script_design.md).

For the future n8n ingestion workflow design, see
[n8n_ingestion_workflow_design.md](./n8n_ingestion_workflow_design.md).

For the future n8n pipeline runbook, see
[n8n_pipeline_runbook.md](./n8n_pipeline_runbook.md).

For the production schema and promotion layer, see:

- [production_schema.sql](./production_schema.sql)
- [production_schema_readme.md](./production_schema_readme.md)
- [frontend_query_contract.md](./frontend_query_contract.md)
- [reference_data_readme.md](./reference_data_readme.md)
- [seed_reference_data.sql](./seed_reference_data.sql)
- [../scripts/generate_reference_data_seed.py](../scripts/generate_reference_data_seed.py)
- [staging_to_production_mapping.md](./staging_to_production_mapping.md)
- [frontend_query_views.sql](./frontend_query_views.sql)

The `ingestion/` package now supports two modes:

- dry-run: reads, detects, and maps packets only
- write mode: performs Supabase writes and records `ingestion_errors` on failure
- both modes produce an ingestion batch report in `output/ingestion_logs/`

## What this is

This is a staging schema, not the final production schema.
Its purpose is to receive raw collector output first, so we can inspect, validate, and curate data before promoting it into production tables.

## Why keep `raw_packet` as JSONB

We keep the full original packet in `raw_packet jsonb` so schema changes in the collector do not destroy the original payload.
If a field changes later, we still have the raw record for debugging, reprocessing, and migration.

## Why also split common fields into columns

Frequently queried fields are stored as columns because they are faster and easier to filter, index, and analyze.
This gives us the best of both worlds:

- flexible raw payload retention
- structured query performance

## Intended flow

```text
Collector output JSON
↓
n8n or ingestion script
↓
Supabase staging tables
↓
manual or automated inspection
↓
production tables
```

## Tables

### `staging_events`

Temporary storage for `event_packet`.

### `staging_daily_digests`

Temporary storage for `daily_digest_packet`.

### `staging_reports`

Temporary storage for `report_packet`.

### `staging_crawl_runs`

Temporary storage for `crawl_run_packet`.
This is the audit record for every execution.

### `staging_rejected_sources`

Temporary storage for rejected sources so data quality problems can be inspected later.

### `ingestion_errors`

Temporary storage for packet write failures so ingestion can continue while preserving error detail.

## Why `staging_crawl_runs` matters

It records each run's status, scope, providers, source counts, quality summary, output files, and errors.
That makes it useful for execution tracking, debugging, and future operational dashboards.

## Why `staging_rejected_sources` matters

It helps us understand why sources were rejected, such as missing URLs, duplicate URLs, short content, or prohibited terms.
This table is especially useful for data quality review and source tuning.

## Why `ingestion_errors` matters

It records packet-level failures without stopping the whole ingestion job.
This makes it easier to debug bad packets, failed writes, and schema drift while preserving the original payload.

## Future direction

The expected flow is:

```text
Collector output JSON
↓
n8n or ingestion script
↓
Supabase staging tables
↓
manual or automated validation
↓
production tables
```

This design keeps the ingest layer conservative and makes later migrations safer.

## n8n pipeline runbook

The practical n8n request templates and failure-checking guide for the one-shot pipeline live in
[n8n_pipeline_runbook.md](./n8n_pipeline_runbook.md).

Use that document when wiring n8n to `POST /pipeline/run`.

## Production promotion layer

The production layer is a separate curated schema. It is built from the staging tables and normalized relation tables.

- `staging_events` -> `events` + `event_relations`
- `staging_reports` -> `reports` + `report_relations`
- `staging_crawl_runs` -> `crawl_runs`
- `staging_rejected_sources` -> `rejected_sources`
- `staging_daily_digests` stays in staging for now

The promotion path is documented in `staging_to_production_mapping.md`.
The read models for the front-end are documented in `frontend_query_views.sql`.

## Promotion write mode

The `promotion/` package also supports dry-run and write mode.

- dry-run: maps staging packets into production-style rows and writes a promotion report
- write mode: writes to production tables using `SUPABASE_URL` and `SUPABASE_SERVICE_ROLE_KEY`

Promotion reports are written to `output/promotion_logs/promotion_run_YYYY-MM-DD_HHMMSS.json`.

The one-shot pipeline can pass `promotion.dry_run = false` when promotion should write to production.
