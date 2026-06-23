# Ingestion Script Design

This document describes the future Python ingestion script that will read Collector output JSON and write it into Supabase staging tables.
It is a design document only. It does not connect to Supabase by itself.

## Role of the ingestion script

The ingestion script sits between Collector output and the staging database.

```text
read JSON packets from output/
↓
detect packet type
↓
map packet fields using ingestion_mapping.md
↓
upsert into the matching staging table
↓
write ingestion_errors for failures
```

Its job is to move already validated Collector output into Supabase in a predictable way.
It should not rewrite the packet content itself.

## Supported packet types

The first version should support these packet types:

- `event_packet`
- `daily_digest_packet`
- `report_packet`
- `crawl_run_packet`
- `rejected_source`

### Target tables

| Packet type | Target table |
| --- | --- |
| `event_packet` | `staging_events` |
| `daily_digest_packet` | `staging_daily_digests` |
| `report_packet` | `staging_reports` |
| `crawl_run_packet` | `staging_crawl_runs` |
| `rejected_source` | `staging_rejected_sources` |

## Suggested package structure

The script can later be organized like this:

```text
ingestion/
├─ __init__.py
├─ config.py
├─ supabase_client.py
├─ packet_loader.py
├─ mappers.py
├─ upsert.py
├─ error_logger.py
└─ ingest_outputs.py
```

### File responsibilities

- `config.py`: environment variables and runtime flags
- `supabase_client.py`: Supabase client setup
- `packet_loader.py`: read packets from `output/`
- `mappers.py`: convert packets into staging rows
- `upsert.py`: write rows to the correct staging table
- `error_logger.py`: record failures into `ingestion_errors`
- `ingest_outputs.py`: CLI entry point and orchestration

## Upsert rules

The staging tables should use these keys:

- `staging_events`: `event_id`
- `staging_daily_digests`: `digest_id`
- `staging_reports`: `report_id`
- `staging_crawl_runs`: `run_id`
- `staging_rejected_sources`: initially append-only, later optional dedupe by `run_id + source_url`

### Why these rules matter

- Event, digest, report, and crawl run packets all have stable IDs and should be upsertable.
- `rejected_sources` is better treated as a quality history trail at first, so append-only is safer.
- `raw_packet` and `raw_source` must always be preserved in full.

## Write order

The recommended write order is:

1. `crawl_run_packet`
2. `event_packet`
3. `daily_digest_packet`
4. `report_packet`
5. `rejected_sources`

### Why this order

- `crawl_run_packet` is the primary record for the execution.
- The other packets can all be traced back through `run_id`.
- `rejected_sources` is a quality audit artifact and can be written after the main packets.

## Error handling

The ingestion script should never stop the entire run because one packet failed.

### Required behavior

- validate each packet before writing
- attempt to write one packet at a time
- record failures in `ingestion_errors`
- continue processing the remaining packets
- output a final success / failure summary

## Future `ingestion_errors` table

The planned `ingestion_errors` table can use this structure:

| Field | Type | Purpose |
| --- | --- | --- |
| `id` | `uuid primary key` | Unique row id |
| `packet_type` | `text` | Which packet failed |
| `packet_id` | `text` | The packet identifier |
| `target_table` | `text` | The target staging table |
| `error_message` | `text` | Human-readable error message |
| `raw_packet` | `jsonb` | The original packet payload |
| `created_at` | `timestamptz default now()` | Failure timestamp |

### Error policy

- A single packet failure should not block the whole ingestion run.
- The error should be logged and the script should continue with the next packet.
- The final run summary should include both success and failure counts.

## CLI design

The future CLI can support these entry points:

```bash
python -m ingestion.ingest_outputs --input output/
python -m ingestion.ingest_outputs --input output/daily/散熱
python -m ingestion.ingest_outputs --dry-run
python -m ingestion.ingest_outputs --packet-type event
```

### CLI flags

- `--input`: root folder or subfolder to scan
- `--dry-run`: perform read and mapping only, do not write to Supabase
- `--packet-type`: limit ingestion to a single packet family

### CLI behavior

- Default behavior should scan all supported JSON packets under `output/`
- `--dry-run` should not require a Supabase key
- `--packet-type` should narrow the ingest scope without changing the mapping logic

## Safety design

The ingestion script should follow these rules:

- `SUPABASE_URL` must come from environment variables
- `SUPABASE_SERVICE_ROLE_KEY` must come from environment variables
- no hardcoded keys
- `dry-run` mode does not need Supabase credentials
- the script only maps and writes packets; it does not alter the collector output
- packet validation happens before write attempts

## Relationship to ingestion mapping

This design depends on [ingestion_mapping.md](./ingestion_mapping.md).

The mapping document defines field-by-field staging contracts.
This design document defines how a script should apply those mappings in practice.

## Future scope

This first version is intentionally conservative.
Later versions can add:

- retry policies
- batch writes
- dead-letter handling
- richer error analytics
- optional n8n invocation as an orchestration wrapper

The initial goal is correctness, traceability, and safe staging writes.
