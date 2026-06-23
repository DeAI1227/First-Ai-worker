# Backend Final Audit

## Audit summary

The backend MVP is organized around one official data path:

```text
LangGraph Collector
→ Output Packets
→ Ingestion
→ Supabase Staging
→ Promotion
→ Supabase Production / Views
→ Frontend reads Supabase
```

## Checkpoints

- LangGraph Collector is the core research engine.
- Output packets are complete and remain the backend handoff format.
- Ingestion writes packets into Supabase staging tables.
- Promotion writes curated data into Supabase production tables and relations.
- Production views are the frontend read model.
- 45 tracked stocks are reference data, not event data.
- Stocks with no events do not generate fake packets.
- GitHub Actions is the official scheduler and only triggers `POST /pipeline/run` through the workflow; legacy n8n docs are historical only.
- The frontend reads Supabase views only.
- The frontend does not read Python code or `output/` JSON files.

## Operational note

This file is the final backend audit summary for the MVP. If any of the commands listed in `docs/pipeline_runbook.md` fail locally, record the failure there instead of silently assuming success.
