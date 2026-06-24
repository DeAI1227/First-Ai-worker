# Collector Output to Supabase Staging Ingestion Mapping

This document defines how Collector output JSON is mapped into Supabase staging tables.
It is a contract for future ingestion scripts or n8n workflows.
It does not connect to Supabase by itself.

## Overall flow

```text
Collector output JSON
↓
ingestion script or n8n
↓
Supabase staging tables
↓
manual or automated checks
↓
production tables
```

## Design principles

- Staging is a temporary landing layer, not the final production schema.
- The full original packet must always be preserved in `raw_packet jsonb`.
- Common query fields are split into columns so they can be filtered, indexed, and audited easily.
- The ingestion layer may generate or normalize IDs such as `event_id`, `digest_id`, and `report_id` when the collector packet does not already provide them.

## `event_packet` -> `staging_events`

Use this mapping when writing event packets into `staging_events`.

| Collector output field | Staging column | Notes |
| --- | --- | --- |
| `event_id` | `event_id` | Required unique event identifier. If absent, ingestion should generate it. |
| `run_id` | `run_id` | Links the event back to the crawl run. |
| `event_date` | `event_date` | Event date in `YYYY-MM-DD`. |
| `scope` | `scope` | For example `macro`, `industry`, `stock`, `institution_watch`. |
| `scope_name` | `scope_name` | Human-readable scope name. |
| `event_type` | `event_type` | For example `macro`, `industry`, `stock`. |
| `importance` | `importance` | For example `general`, `important`, `critical`. |
| `language` | `language` | Usually `zh-TW`. |
| `ai_summary` | `ai_summary` | AI-generated summary. |
| `possible_impact` | `possible_impact` | Objective impact description. |
| `risk_note` | `risk_note` | Risk reminder or uncertainty note. |
| `tags` | `tags` jsonb | Array of keywords or tags. |
| `related_industries` | `related_industries` jsonb | Industry names only. |
| `related_stocks` | `related_stocks` jsonb | Stock codes only. |
| `source_urls` | `source_urls` jsonb | One or more source links. |
| full `event_packet` | `raw_packet` jsonb | Preserve the original packet. |

### Notes

- `related_industries` must contain industry names only, not stock codes.
- `related_stocks` must contain stock codes only, not industry names.
- If the collector packet contains extra fields, they remain inside `raw_packet`.

## `daily_digest_packet` -> `staging_daily_digests`

Use this mapping when writing digest packets into `staging_daily_digests`.

| Collector output field | Staging column | Notes |
| --- | --- | --- |
| `digest_id` | `digest_id` | Required unique digest identifier. If absent, ingestion should generate it. |
| `run_id` | `run_id` | Links the digest back to the crawl run. |
| `digest_date` | `digest_date` | Digest date in `YYYY-MM-DD`. |
| `scope` | `scope` | For example `macro` or `industry`. |
| `scope_name` | `scope_name` | Human-readable scope name. |
| `summary` | `summary` | Digest summary text. If the collector does not expose a standalone summary field, ingestion can derive or assemble it from the packet content. |
| `important_events` | `important_events` jsonb | Important event list or references. |
| `quality_summary` | `quality_summary` jsonb | Source quality summary for the run or day. |
| `rejected_reasons` | `rejected_reasons` jsonb | Main rejected reasons. |
| full `daily_digest_packet` | `raw_packet` jsonb | Preserve the original packet. |

### Notes

- The digest row should remain small and query-friendly.
- Detailed event content stays in `raw_packet` or the related event table.

## `report_packet` -> `staging_reports`

Use this mapping when writing report packets into `staging_reports`.

| Collector output field | Staging column | Notes |
| --- | --- | --- |
| `report_id` | `report_id` | Required unique report identifier. If absent, ingestion should generate it. |
| `run_id` | `run_id` | Links the report back to the crawl run. |
| `report_date` | `report_date` | Report date in `YYYY-MM-DD`. |
| `report_type` | `report_type` | For example `full_report`, `industry_report`, `macro_report`. |
| `scope` | `scope` | For example `macro`, `industry`. |
| `scope_name` | `scope_name` | Human-readable scope name. |
| `importance` | `importance` | For example `general`, `important`, `critical`. |
| `report_title` | `report_title` | Report title. |
| `report_body` | `report_body` | Full report body. |
| `quality_summary` | `quality_summary` jsonb | Quality summary used to inform the report. |
| full `report_packet` | `raw_packet` jsonb | Preserve the original packet. |

### Notes

- Reports should be stored with enough structure to support filters and preview cards.
- Long-form content belongs in `report_body` and `raw_packet`.

## `crawl_run_packet` -> `staging_crawl_runs`

Use this mapping when writing crawl run packets into `staging_crawl_runs`.

| Collector output field | Staging column | Notes |
| --- | --- | --- |
| `run_id` | `run_id` | Unique execution identifier. |
| `run_date` | `run_date` | Run date in `YYYY-MM-DD`. |
| `started_at` | `started_at` | Run start timestamp. |
| `finished_at` | `finished_at` | Run finish timestamp. |
| `status` | `status` | `success`, `partial_success`, or `failed`. |
| `mode` | `mode` | `daily` or `three_day`. |
| `scope` | `scope` | Execution scope. |
| `scope_name` | `scope_name` | Human-readable scope name. |
| `source_mode` | `source_mode` | `mock`, `rss`, `http`, `search`, or `hybrid`. |
| `summarizer_mode` | `summarizer_mode` | `mock` or `llm`. |
| `llm_provider` | `llm_provider` | `mock`, `agnes`, `gemini`, or `auto`. |
| `search_provider` | `search_provider` | `mock`, `tavily`, `serpapi`, `firecrawl`, or `auto`. |
| `total_sources_count` | `total_sources_count` | Total collected sources. |
| `accepted_sources_count` | `accepted_sources_count` | Sources that passed quality filtering. |
| `rejected_sources_count` | `rejected_sources_count` | Sources that were rejected. |
| `quality_summary` | `quality_summary` jsonb | High / medium / low / rejected counts. |
| `rejected_reasons` | `rejected_reasons` jsonb | Main rejection reasons. |
| `output_files` | `output_files` jsonb | Files written during the run. |
| `run_errors` | `run_errors` jsonb | Standardized run errors and warnings. |
| full `crawl_run_packet` | `raw_packet` jsonb | Preserve the original packet. |

### Notes

- `staging_crawl_runs` is the main audit record for each execution.
- The row should be upserted by `run_id`.

## `rejected_sources` -> `staging_rejected_sources`

Use this mapping when writing rejected sources into `staging_rejected_sources`.

| Collector output field | Staging column | Notes |
| --- | --- | --- |
| `run_id` | `run_id` | Links the rejected source to the crawl run. |
| `source_url` | `source_url` | Canonical URL for the source. |
| `source_name` | `source_name` | Source or publication name. |
| `source_type` | `source_type` | For example `mock`, `rss`, `http`, `search`. |
| `title` | `title` | Source title. |
| `content` | `content` | Source content or summary. |
| `quality_score` | `quality_score` | Numeric score from 0 to 100. |
| `quality_level` | `quality_level` | `high`, `medium`, `low`, or `rejected`. |
| `quality_reasons` | `quality_reasons` jsonb | Reasons for the score or rejection. |
| full raw source | `raw_source` jsonb | Preserve the original raw source. |

### Notes

- Rejected sources can start as append-only rows so quality history is preserved.
- A future implementation may also dedupe by `run_id + source_url`.

## Recommended write order

The suggested ingestion order is:

1. `staging_crawl_runs`
2. `staging_events`
3. `staging_daily_digests`
4. `staging_reports`
5. `staging_rejected_sources`

### Why this order

- `staging_crawl_runs` is the primary record for the execution.
- `event`, `digest`, and `report` rows can all be traced back through `run_id`.
- `staging_rejected_sources` is most useful after the rest of the run has been validated, because it is a quality inspection artifact rather than a primary content artifact.

## Upsert rules

Use these upsert keys when the staging layer is written:

- `staging_events`: `event_id`
- `staging_daily_digests`: `digest_id`
- `staging_reports`: `report_id`
- `staging_crawl_runs`: `run_id`
- `staging_rejected_sources`: append-only initially, or `run_id + source_url` if deduplication is needed later

### Notes

- `staging_crawl_runs` should always be upserted by `run_id`.
- Event, digest, and report rows should use their own stable IDs.
- Rejected sources are often more valuable as a history trail than as a single overwritten record.

## Error handling

If ingestion fails, record the failure in an ingestion error log. The planned fields are:

| Field | Purpose |
| --- | --- |
| `packet_type` | Which packet failed. |
| `packet_id` | The packet identifier, such as `event_id`, `digest_id`, `report_id`, or `run_id`. |
| `target_table` | The staging table that was being written. |
| `error_message` | Human-readable error message. |
| `raw_packet` | The original packet payload. |
| `created_at` | Timestamp of the failure. |

This error log can later become an `ingestion_errors` table.

## Relationship to production tables

These staging tables are not the final production schema.
They are intentionally conservative and easy to inspect.

The longer-term flow is:

```text
Collector output JSON
↓
ingestion script or n8n
↓
Supabase staging tables
↓
manual or automated checks
↓
production tables
```

The staging layer gives us a safe place to validate structure, quality, and lineage before any production migration.
