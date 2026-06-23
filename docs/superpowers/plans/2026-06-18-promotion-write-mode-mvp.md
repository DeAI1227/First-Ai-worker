# Promotion Write Mode MVP Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add a safe production write mode to promotion so staging packets can be promoted into production tables without breaking dry-run, API, or pipeline behavior.

**Architecture:** Keep the existing promotion flow as the single source of truth. Extend the current packet promoter and relation builder to support a Supabase-backed write path, then surface that mode through the CLI, API service layer, and `/pipeline/run`. Preserve dry-run behavior, keep rejected sources append-only, and treat relations as normalized child rows rather than duplicated parent packets.

**Tech Stack:** Python 3.14, Supabase Python client, FastAPI, Pydantic, unittest, JSON file IO.

---

### Task 1: Add promotion Supabase write path

**Files:**
- Modify: `promotion/packet_promoter.py`
- Create: `promotion/supabase_client.py`
- Create: `promotion/upsert.py`

- [ ] **Step 1: Write the failing tests**

Add tests that monkeypatch a mock Supabase client and assert:
```python
def test_promotion_write_mode_requires_supabase_env():
    result = run_promotion_sync(input_path="output/", dry_run=False)
    assert result["status"] == "failed"
    assert "SUPABASE_URL" in result["message"]


def test_events_use_event_id_upsert():
    row = map_event_packet({"event_id": "event_001"})
    assert row["event_id"] == "event_001"
```

- [ ] **Step 2: Run the tests to verify they fail**

Run: `python -m unittest tests.test_production_promotion -v`
Expected: failures for missing write mode and missing Supabase client.

- [ ] **Step 3: Implement the minimal promotion write mode**

Implement:
```python
def create_supabase_client() -> SupabaseClient: ...
def upsert_row(client, table_name: str, row: dict, *, conflict_key: str | None = None) -> None: ...
```

Wire `promote_packets(..., dry_run=False)` to:
- load packets
- map event/report/crawl_run/rejected_source rows
- write parent rows to `events`, `reports`, `crawl_runs`, `rejected_sources`
- write relation rows to `event_relations` and `report_relations`
- record write failures in the promotion report

- [ ] **Step 4: Run the tests to verify they pass**

Run: `python -m unittest tests.test_production_promotion -v`
Expected: pass.

- [ ] **Step 5: Commit**

```bash
git add promotion/packet_promoter.py promotion/supabase_client.py promotion/upsert.py tests/test_production_promotion.py
git commit -m "feat: add promotion write mode"
```

### Task 2: Keep relation building strict and normalized

**Files:**
- Modify: `promotion/relation_builder.py`
- Modify: `tests/test_production_promotion.py`

- [ ] **Step 1: Write the failing tests**

Add tests that assert:
```python
def test_event_relations_keep_stock_and_industry_separate():
    relations = build_event_relations({"event_id": "event_001"}, {
        "related_industries": ["散熱"],
        "related_stocks": ["6230"],
    })
    assert any(r["relation_type"] == "industry" and r["relation_value"] == "散熱" for r in relations)
    assert any(r["relation_type"] == "stock" and r["relation_value"] == "6230" for r in relations)
```

- [ ] **Step 2: Run the tests to verify they fail**

Run: `python -m unittest tests.test_production_promotion -v`
Expected: failure only if current relation builder or tests do not enforce this clearly.

- [ ] **Step 3: Tighten relation builder if needed**

Keep `_build_relations()` strictly mapping:
- `related_industries` -> `relation_type="industry"`
- `related_stocks` -> `relation_type="stock"`
- `related_events` -> `relation_type="event"`
- `related_macro_topics` -> `relation_type="macro_topic"`
- `related_institution_watch` -> `relation_type="institution_watch"`

Do not duplicate packets per relation.

- [ ] **Step 4: Run the tests to verify they pass**

Run: `python -m unittest tests.test_production_promotion -v`
Expected: pass.

- [ ] **Step 5: Commit**

```bash
git add promotion/relation_builder.py tests/test_production_promotion.py
git commit -m "test: lock down promotion relations"
```

### Task 3: Surface promotion write mode through CLI, API, and pipeline

**Files:**
- Modify: `promotion/promote_staging.py`
- Modify: `api/services/promotion_service.py`
- Modify: `api/routes/promotion.py`
- Modify: `api/services/pipeline_service.py`
- Modify: `api/routes/pipeline.py`
- Modify: `api/schemas.py`

- [ ] **Step 1: Write the failing tests**

Add API tests that cover:
```python
def test_promotion_run_write_mode_requires_supabase_key(client):
    response = client.post("/promotion/run", json={"input_path": "output/", "packet_type": "all", "dry_run": False}, headers=auth_headers())
    assert response.status_code == 200
    assert response.json()["status"] in {"failed", "partial_success"}


def test_pipeline_run_supports_promotion_write_mode(client):
    payload = {"collect": {...}, "ingestion": {...}, "promotion": {"enabled": True, "dry_run": False}}
    response = client.post("/pipeline/run", json=payload, headers=auth_headers())
    assert response.json()["data"]["promotion_result"]["mode"] == "write"
```

- [ ] **Step 2: Run the tests to verify they fail**

Run: `python -m unittest tests.test_api tests.test_production_promotion -v`
Expected: failures until the route/service wiring is in place.

- [ ] **Step 3: Implement the thin orchestration layer**

Ensure:
- CLI still supports `python -m promotion.promote_staging --input output/ --dry-run`
- CLI also supports `python -m promotion.promote_staging --input output/`
- API route calls the same service function as CLI
- pipeline passes promotion dry_run flag through unchanged

- [ ] **Step 4: Run the tests to verify they pass**

Run: `python -m unittest discover -s tests -p "test_*.py" -v`
Expected: pass.

- [ ] **Step 5: Commit**

```bash
git add promotion/promote_staging.py api/services/promotion_service.py api/routes/promotion.py api/services/pipeline_service.py api/routes/pipeline.py api/schemas.py tests/test_api.py
git commit -m "feat: wire promotion write mode through api"
```

### Task 4: Update docs and verify end-to-end

**Files:**
- Modify: `README.md`
- Modify: `supabase/staging_to_production_mapping.md`
- Modify: `supabase/README.md`

- [ ] **Step 1: Add documentation for write mode**

Document:
- dry-run vs write mode
- required Supabase env vars
- promotion report output path
- relation builder rules
- pipeline promotion dry_run false support

- [ ] **Step 2: Run the full verification suite**

Run:
```bash
python -m unittest discover -s tests -p "test_*.py" -v
python -m compileall .
python main.py --batch industries
python -m ingestion.ingest_outputs --input output/ --dry-run
python -m promotion.promote_staging --input output/ --dry-run
```

Expected: all pass.

- [ ] **Step 3: Commit**

```bash
git add README.md supabase/staging_to_production_mapping.md supabase/README.md
git commit -m "docs: describe promotion write mode"
```

