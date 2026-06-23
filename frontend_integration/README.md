# Frontend Integration Pack

This folder is the reference bundle for integrating the frontend with Supabase production views.

## What this pack is for

- Use the production views as the frontend read model.
- Avoid hand-written joins in the UI.
- Keep `stocks` as reference data and `events` as actual event data.
- Use `user_read_status` for read / unread state.
- Render empty states in the frontend when a stock has no events.
- Do not generate fake "today no major update" events.

## Recommended flow

1. Query the matching Supabase view for the page.
2. Render the row types defined in `types.ts`.
3. Use `user_read_status` for read markers and unread counters.
4. Treat `stocks` as reference data only.

## Files in this pack

- `src/supabaseClient.ts`
- `src/queries.ts`
- `src/readStatus.ts`
- `src/index.ts`
- `supabase_views_contract.md`
- `supabase_query_examples.md`
- `types.ts`

## Wiring rule

Use the query helpers in `src/queries.ts` and the read-status helpers in `src/readStatus.ts` from the page layer.
The UI should stay the same; only the data source changes from mock data to Supabase views.

## Scope of this pack

This folder is the contract and query reference pack for the future Supabase-only frontend.

- It is not a plan to connect the current frontend directly to Python.
- It is not a way to read `output/` JSON from the UI.
- It is a Supabase-first data contract for the new frontend that will be regenerated later.
- The frontend should read production views only.
