# Production Schema

This file documents the production schema for the Investment Research Collector.

## Purpose

The production schema is the curated destination layer. It receives data after staging validation and promotion.
It is separate from staging so we can preserve the original collector payloads while keeping production tables query-friendly.

## What is promoted

- `staging_events` -> `events` + `event_relations`
- `staging_reports` -> `reports` + `report_relations`
- `staging_crawl_runs` -> `crawl_runs`
- `staging_rejected_sources` -> `rejected_sources`

## What stays in staging

- `staging_daily_digests` stays in staging for now

## Why relation tables exist

`event_relations` and `report_relations` keep the many-to-many relationships clean:

- industry
- stock
- macro_topic
- institution_watch

That means `related_industries` and `related_stocks` in packets become normalized rows, instead of being embedded forever inside one JSON blob.

## Why `user_read_status` is separate

Read state depends on the user, not the event itself.
Keeping it in `user_read_status` prevents read/unread from being duplicated into the event or report tables.

## Query strategy

Front-end cards and dashboards should read from SQL views built on top of the production tables.
This gives us stable read models without compromising the raw schema.

The page-to-view contract is documented in [frontend_query_contract.md](./frontend_query_contract.md).
