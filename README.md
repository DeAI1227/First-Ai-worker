# LangGraph Research Collector Agent MVP

This repository builds the backend of an AI investment research terminal, not a stock quote app.

## System boundary

## Official system direction

The official system direction is documented in [`docs/system_data_flow.md`](docs/system_data_flow.md).

The core data flow is:

```text
LangGraph Collector
→ output packets
→ ingestion
→ Supabase staging
→ promotion
→ Supabase Production / Views
→ Frontend reads Supabase
```

The frontend reads only Supabase production views.
The frontend reads only Supabase production views.
Frontend reads Supabase views only.

The frontend does not read Python code.
The frontend does not read `output/` JSON.
The frontend does not call the collector directly.

## What this project tracks

- 6 industries
- 45 tracked stocks in the reference universe
- 4 institution watch stocks
- macro topics
- event packets
- daily digest packets
- three-day reports
- quality summaries

## What this project does not do

- real-time stock quotes
- daily price changes
- percentage change screens
- K-line charts
- technical analysis
- buy/sell suggestions
- target price predictions
- return forecasts
- fake "no major update" events

## Main modules

- `collector/` - LangGraph Collector, source layer, summarizer, quality scoring
- `ingestion/` - packet loading, dry-run, Supabase write mode
- `promotion/` - staging to production promotion
- `supabase/` - staging schema, production schema, reference seed, views contract
- `api/` - FastAPI orchestrator for `n8n`
- `frontend_integration/` - future Supabase-only frontend contract

## Running the backend

Start the API:

```bash
uvicorn api.main:app --reload
```

Run the collector and pipeline locally:

```bash
python main.py --batch all
python scripts/run_autonomous_once.py
```

Dry-run ingestion:

```bash
python -m ingestion.ingest_outputs --input output/ --dry-run
```

Dry-run promotion:

```bash
python -m promotion.promote_staging --input output/ --dry-run
```

## Supabase contract

Production tables and views are the source of truth for the frontend.
Reference data is seeded into Supabase before any event data is promoted.

The stock list comes from `stocks` plus `stock_industries`.
The event streams come from `events` plus `event_relations`.
Empty state for stocks with no events is handled by the frontend.

## Tracking universe

The MVP universe contains:

- `散熱`
- `電力`
- `自動駕駛`
- `機器人`
- `CPO 光通訊`
- `網通`

It also includes 45 tracked stocks in the reference universe, plus 4 institution watch stocks.

## Smoke and audit

- `python scripts/e2e_mvp_smoke.py`
- `python -m unittest discover -s tests -p "test_*.py" -v`
- `python -m compileall .`

## Notes

- The collector can run in `mock`, `rss`, `http`, `search`, or `hybrid` source mode.
- `n8n` only triggers `POST /pipeline/run`; it does not contain research logic.
- `Supabase` is the formal data center for the new frontend.
