# Staging to Production Mapping

This document defines how staging tables are promoted into production tables.
It is the bridge between Collector output, ingestion, and the production read models.

## Overall flow

```text
Collector output JSON
→ ingestion script or n8n
→ Supabase staging tables
→ manual or automated review
→ production tables
```

## Design principles

- staging is temporary and conservative
- production is normalized and query-friendly
- `raw_packet` and `raw_source` are always preserved
- relationship data is normalized into relation tables
- `staging_daily_digests` is kept in staging for now

## `staging_events` -> `events` + `event_relations`

### Main row mapping

| Staging column | Production column | Notes |
| --- | --- | --- |
| `event_id` | `event_id` | Stable event key |
| `run_id` | `run_id` | Links back to execution |
| `event_date` | `event_date` | Event date |
| `scope` | `scope` | Execution scope |
| `scope_name` | `scope_name` | Human-readable scope |
| `event_type` | `event_type` | `macro`, `industry`, `global_leader`, `domestic_leader`, `stock`, `institution` |
| `importance` | `importance` | `general`, `important`, `critical` |
| `language` | `language` | Usually `zh-TW` |
| `title` | `title` | Event title |
| `ai_summary` | `ai_summary` | Summary text |
| `possible_impact` | `possible_impact` | Objective impact |
| `risk_note` | `risk_note` | Risk reminder |
| `tags` | `tags` | jsonb |
| `source_urls` | `source_urls` | jsonb |
| `quality_summary` | `quality_summary` | jsonb |
| `raw_packet` | `raw_packet` | Preserve original packet |

### Relation mapping

- `related_industries` -> `event_relations(relation_type='industry')`
- `related_stocks` -> `event_relations(relation_type='stock')`
- `related_macro_topics` -> `event_relations(relation_type='macro_topic')`
- `related_institution_watch` -> `event_relations(relation_type='institution_watch')`

## `staging_reports` -> `reports` + `report_relations`

### Main row mapping

| Staging column | Production column | Notes |
| --- | --- | --- |
| `report_id` | `report_id` | Stable report key |
| `run_id` | `run_id` | Links back to execution |
| `report_date` | `report_date` | Report date |
| `report_type` | `report_type` | `full_report`, `urgent_alert`, `industry_report`, `stock_report`, `macro_report`, `institution_report` |
| `scope` | `scope` | Execution scope |
| `scope_name` | `scope_name` | Human-readable scope |
| `importance` | `importance` | `general`, `important`, `critical` |
| `report_title` | `report_title` | Report title |
| `report_body` | `report_body` | Full report body |
| `quality_summary` | `quality_summary` | jsonb |
| `raw_packet` | `raw_packet` | Preserve original packet |

### Relation mapping

- `related_industries` -> `report_relations(relation_type='industry')`
- `related_stocks` -> `report_relations(relation_type='stock')`
- `related_events` -> `report_relations(relation_type='event')`
- `related_macro_topics` -> `report_relations(relation_type='macro_topic')`
- `related_institution_watch` -> `report_relations(relation_type='institution_watch')`

## `staging_crawl_runs` -> `crawl_runs`

| Staging column | Production column | Notes |
| --- | --- | --- |
| `run_id` | `run_id` | Stable execution key |
| `run_date` | `run_date` | Run date |
| `started_at` | `started_at` | Start timestamp |
| `finished_at` | `finished_at` | Finish timestamp |
| `status` | `status` | `success`, `partial_success`, `failed` |
| `mode` | `mode` | `daily`, `three_day` |
| `scope` | `scope` | Scope |
| `scope_name` | `scope_name` | Scope display name |
| `source_mode` | `source_mode` | `mock`, `rss`, `http`, `search`, `hybrid` |
| `summarizer_mode` | `summarizer_mode` | `mock`, `llm` |
| `llm_provider` | `llm_provider` | `mock`, `agnes`, `gemini`, `auto` |
| `search_provider` | `search_provider` | `mock`, `tavily`, `serpapi`, `firecrawl`, `auto` |
| `total_sources_count` | `total_sources_count` | Total sources |
| `accepted_sources_count` | `accepted_sources_count` | Accepted sources |
| `rejected_sources_count` | `rejected_sources_count` | Rejected sources |
| `quality_summary` | `quality_summary` | jsonb |
| `rejected_reasons` | `rejected_reasons` | jsonb |
| `output_files` | `output_files` | jsonb |
| `run_errors` | `run_errors` | jsonb |
| `raw_packet` | `raw_packet` | Preserve original packet |

## `staging_rejected_sources` -> `rejected_sources`

| Staging column | Production column | Notes |
| --- | --- | --- |
| `run_id` | `run_id` | Links to execution |
| `source_url` | `source_url` | Canonical URL |
| `source_name` | `source_name` | Publication name |
| `source_type` | `source_type` | `mock`, `rss`, `http`, `search` |
| `title` | `title` | Source title |
| `content` | `content` | Source content |
| `quality_score` | `quality_score` | 0-100 |
| `quality_level` | `quality_level` | `high`, `medium`, `low`, `rejected` |
| `quality_reasons` | `quality_reasons` | jsonb |
| `raw_source` | `raw_source` | Preserve original source |

## Upsert rules

- `events` upsert by `event_id`
- `reports` upsert by `report_id`
- `crawl_runs` upsert by `run_id`
- relation tables can be rebuilt from packet relations
- `rejected_sources` may remain append-only at first

## Write order

1. `crawl_runs`
2. `events`
3. `event_relations`
4. `reports`
5. `report_relations`
6. `rejected_sources`

## Why daily digests are not promoted yet

`daily_digest` is useful operationally, but it is not yet part of the production read model.
We keep it in staging until we have a clear use case for a production summary table or a richer reporting model.
