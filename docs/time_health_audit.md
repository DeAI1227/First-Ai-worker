# Time Health Audit

## 1. Overall conclusion

**warning**

The main timing rules are now explicit and mostly safe. The remaining risks are mostly about clarity and operations, not core logic.

## 2. What I checked

I reviewed the timing-related parts of the repository, especially:

- `collector/utils/time_utils.py`
- `collector/batch_runner.py`
- `ingestion/batch_report.py`
- `promotion/promotion_report.py`
- `api/services/pipeline_service.py`
- `scripts/run_autonomous_once.py`
- `.github/workflows/daily-core.yml`
- `.github/workflows/stock-pipeline.yml`
- `.github/workflows/three-day-refresh.yml`
- `n8n_workflows/autonomous_daily_pipeline.json`
- `docs/pipeline_runbook.md`
- `docs/deployment_wiring_checklist.md`
- `docs/n8n_setup_steps.md`

## 3. Timing rules that are now correct

### Daily run target

The intended daily trigger is **07:00 Asia/Taipei**.

### GitHub Actions

GitHub Actions now uses explicit UTC cron values that map to Taipei time:

- `0 23 * * *` → 07:00 Asia/Taipei
- `20 23 * * *` → 07:20 Asia/Taipei
- `40 23 * * *` → 07:40 Asia/Taipei

This is documented in:

- `.github/workflows/daily-core.yml`
- `.github/workflows/stock-pipeline.yml`
- `.github/workflows/three-day-refresh.yml`
- `docs/pipeline_runbook.md`

### n8n workflow template

The `n8n_workflows/autonomous_daily_pipeline.json` template now explicitly sets:

- workflow timezone: `Asia/Taipei`
- cron expression: `0 7 * * *`

That means the template reads naturally as every day at 07:00 Taipei time.

### Local time helpers

The project now uses an explicit Taipei clock in the main timing helper:

- `collector/utils/time_utils.py`

Key behavior:

- `now_iso()` uses `Asia/Taipei`
- `today_date()` uses `Asia/Taipei`
- `run_id()` uses `Asia/Taipei`

This reduces hidden timezone drift in filenames, run IDs, and log timestamps.

## 4. Remaining timing-sensitive areas

### Ambiguous docs

Some older docs still say `07:00` without repeating the timezone in the same sentence. The actual schedule logic is now explicit, but those docs can still confuse someone who imports them without reading carefully.

### Long-running autonomous CLI

`python scripts/run_autonomous_once.py` is working, but it can take a while because it runs the real pipeline path.

During validation, the CLI smoke test completed successfully, but one run took a long time:

- `test_autonomous_runner_output_json_is_valid` completed successfully
- total run time was about **124 seconds**

That is not a correctness bug by itself, but it is a time-related operational risk:

- if you run it repeatedly or in parallel, it can feel stuck
- if you schedule it too tightly, overlapping runs may happen

### Mock search timestamps

`collector/sources/search/mock_search_provider.py` still uses UTC timestamps for mock search results. That is intentional and not a scheduling bug, but it is worth remembering that:

- scheduling/log timestamps are Taipei-based
- mock search source timestamps may be UTC

## 5. Verification results

### Compile check

- `python -m compileall .`
- Result: **passed**

### Test suite

- `python -m unittest discover -s tests -p "test_*.py" -v`
- Result: **passed**
- Total: **221 tests OK**

### Specific autonomous run check

- `python scripts/run_autonomous_once.py`
- Result: **successful**
- It returns:
  - `collect_ran`
  - `ingestion_ran`
  - `promotion_ran`
  - `wrote_to_supabase`
  - `status`
  - `errors`

## 6. Practical recommendation

If the goal is "run every morning at 07:00 even if my computer is off," the safe setup is:

- use a server-side scheduler, not a laptop-local trigger
- keep the schedule timezone explicit
- treat `Asia/Taipei` as the source of truth in docs and workflow settings

## 7. Bottom line

The main timing path is now in good shape:

- Taipei 07:00 scheduling is explicit
- GitHub Actions uses a timezone-aware schedule
- n8n workflow timezone is explicit
- run IDs and log timestamps are Taipei-based

The remaining risk is mostly operational clarity, not core logic:

- document timezone carefully
- avoid running multiple autonomous runs at the same time unless that is intentional
