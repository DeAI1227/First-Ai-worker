# Backend and Supabase Audit

1. 整體結論：warning
2. 後端主線是否正確
   - Pass. 現在的正式資料流是 Collector / LangGraph -> output packets -> ingestion -> Supabase staging -> promotion -> Supabase production / views。
   - Frontend only reads Supabase production views.
   - `output/` JSON is a backend intermediate artifact, not a frontend data source.
3. Supabase schema 是否完整
   - Pass.
   - Production schema includes: `industries`, `stocks`, `stock_industries`, `macro_topics`, `institution_watch_stocks`, `events`, `event_relations`, `reports`, `report_relations`, `crawl_runs`, `rejected_sources`, `user_read_status`.
   - Staging schema includes: `staging_events`, `staging_daily_digests`, `staging_reports`, `staging_crawl_runs`, `staging_rejected_sources`, `ingestion_errors`.
   - Production views include: `view_dashboard_events`, `view_industry_cards`, `view_stock_cards`, `view_stock_detail_events`, `view_macro_events`, `view_institution_watch_events`, `view_recent_reports`, `view_unread_counts`.
4. seed_reference_data 是否完整
   - Pass with a note.
   - Seed has the six industries, macro topics, institution watch stocks, and the tracked stock universe.
   - Actual runtime snapshot from `collector.config.tracking_universe`:
     - industries: 6
     - tracked stock codes (unique across tracked + institution watch): 45
     - tracked stock rows in `TRACKED_STOCKS`: 41
     - institution watch stocks: 4
     - macro topics: 10
     - stock-industry relations: 42
   - The seed and generator currently produce the expected production reference set.
5. tracking universe 實際股票數量
   - 45 unique stock codes in the combined reference universe.
   - 41 rows in `TRACKED_STOCKS` plus 4 institution-watch rows.
   - 3227 原相 appears once in `stocks` and has multiple industry relations.
6. ingestion 狀態
   - Pass.
   - Ingestion supports dry-run and write mode.
   - It can map `event_packet`, `daily_digest_packet`, `report_packet`, `crawl_run_packet`, and `rejected_source` into staging rows.
   - It records packet-level failures into `ingestion_errors`.
7. promotion 狀態
   - Pass.
   - Promotion supports dry-run and write mode.
   - It writes into production tables and relation tables, with upsert rules for parent rows.
   - It keeps `rejected_sources` append-only.
8. 是否發現假 no-news event 風險
   - No active risk found in current pipeline logic.
   - Coverage reports record stocks without events, but the backend does not synthesize fake "today no major update" event packets.
   - Frontend is expected to render empty states for stocks with no rows in `view_stock_detail_events`.
9. 是否發現前端讀 Python / output JSON 風險
   - No active risk found.
   - Frontend docs, integration docs, and query files point to Supabase views.
   - The audit scan did find direct frontend references only to Supabase views and environment variables, not to Python output JSON as a data source.
10. 測試結果
   - Pass.
   - Fresh verification run completed successfully:
     - `python -m unittest discover -s tests -p "test_*.py" -v`
     - Result: `OK` with 213 tests passing.
11. compileall 結果
   - Pass.
   - Fresh verification run completed successfully:
     - `python -m compileall .`
     - Result: exit code 0.
12. 必須人工處理的事項
   - Supabase write mode still requires real environment values in deployment:
     - `SUPABASE_URL`
     - `SUPABASE_SERVICE_ROLE_KEY`
     - `API_AUTH_TOKEN`
   - Frontend deployment still needs its own env values:
     - `VITE_SUPABASE_URL`
     - `VITE_SUPABASE_ANON_KEY`
   - If the frontend repo is regenerated separately, it must remain read-only against Supabase production views.
   - The seed generator currently reflects 45 unique stock codes in the full reference universe, but the tracked-stock subsection itself is 41 rows; this is intentional in the current registry model and should remain documented so future edits do not accidentally duplicate 3227 or move institution-watch entries into event data.
13. 建議下一步
   - Keep the current backend path frozen unless a real schema change is required.
   - Use this audit as the baseline for deployment wiring.
   - If you want to harden one thing next, focus on end-to-end deployment steps rather than feature expansion.

## Fresh bootstrap verification

- `scripts/bootstrap_supabase.py` now runs directly from the project root because it prepends the repo root to `sys.path` before importing `project_env`.
- Fresh bootstrap result:
  - project ref: `shkjhtzsbeggsjrjliva`
  - `industries`: 6
  - `stocks`: 45
  - `stock_industries`: 42
  - `macro_topics`: 10
  - `institution_watch_stocks`: 4
  - staging tables: present
  - production views: present
- This confirms the live Supabase schema / seed / view wiring is actually present in the current project environment.

## Supporting evidence

- Production schema file: `supabase/production_schema.sql`
- Staging schema file: `supabase/staging_schema.sql`
- Seed file: `supabase/seed_reference_data.sql`
- Frontend query contract: `supabase/frontend_query_contract.md`
- System data flow: `docs/system_data_flow.md`
- Backend final audit reference: `docs/backend_final_audit.md`
- Latest verification commands passed in this workspace:
  - `python -m unittest discover -s tests -p "test_*.py" -v`
  - `python -m compileall .`
