# MVP Release Checklist

## Reference data

- Reference seed has been executed.
- 45 tracked stocks exist in `stocks`.
- 6 industries exist in `industries`.
- 4 institution watch stocks exist.
- Macro topics exist.

## Pipeline

- Ingestion write mode works.
- Promotion write mode works.
- Production views are queryable.
- FastAPI `POST /pipeline/run` works.
- GitHub Actions can call `POST /pipeline/run`.

## Frontend

- Frontend reads Supabase views only.
- Frontend does not read Python code.
- Frontend does not read `output/` JSON files.
- Frontend renders empty states when a stock has no events.

## Research guardrails

- No fake "today no major update" events.
- No investment advice.
- No target price.
- No return forecast.
- No technical analysis or price action framing.

## Remaining checks

- Verify write mode on a real Supabase project.
- Verify production views against the live frontend.
- Verify GitHub Actions status branching against the live endpoint.
