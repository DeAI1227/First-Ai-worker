# Production Reference Data Seed

This seed keeps the production reference layer aligned with the MVP tracking universe.

## What it seeds

- `industries`
- `stocks`
- `stock_industries`
- `macro_topics`
- `institution_watch_stocks`

## Source of truth

The SQL is generated from `collector/config/tracking_universe.py`.
Run `python scripts/generate_reference_data_seed.py` whenever the tracking universe changes.

## Important rules

- `stocks` contains the 45 unique reference stocks used by the MVP universe.
- `3227` appears only once in `stocks`.
- `3227` maps to both `自動駕駛` and `機器人` in `stock_industries`.
- `CPO 光通訊` exists as an industry even though it currently has no tracked stocks.
- `institution_watch_stocks` includes `3665`, `2330`, `2454`, and `2308`.
- This file does not create or seed any events.

## Idempotency

The SQL uses `insert ... on conflict ... do update` or `do nothing`, so the seed can be run repeatedly without duplicating rows.

## Frontend data alignment

- Stock list pages should read from `stocks` joined with `stock_industries`.
- Event streams should read from `events` joined with `event_relations`.
- Stocks without events still exist in `stocks`; the frontend handles empty state.
- The backend does not generate fake "today no major update" events.

## Load order

1. `industries`
2. `stocks`
3. `stock_industries`
4. `macro_topics`
5. `institution_watch_stocks`

## Why this matters

These tables are the production reference layer for the research terminal.
They let the collector, promotion service, and frontend all agree on the same tracking universe before any event data is promoted.

