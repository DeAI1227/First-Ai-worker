# FastAPI Orchestrator Layer Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add a FastAPI orchestrator layer that lets n8n call collector, ingestion, and promotion workflows through HTTP while sharing the same in-process Python services as the CLI.

**Architecture:** Build a thin `api/` package around existing collector, ingestion, and promotion functions. `/collect/run` stays synchronous in v1 but returns `execution_mode` and `job_id` fields so an async job model can be added later without changing response shape. `/ingestion/run` and `/promotion/run` wrap the current ingest/promotion services directly, and `/health` remains unauthenticated. CLI behavior stays intact and reuses the same service functions.

**Tech Stack:** FastAPI, Pydantic, Uvicorn, existing collector/ingestion/promotion Python modules, pytest/unittest-style tests.

---

### Task 1: API app scaffold and auth

**Files:**
- Create: `api/__init__.py`
- Create: `api/main.py`
- Create: `api/config.py`
- Create: `api/auth.py`
- Create: `api/schemas.py`
- Create: `api/routes/__init__.py`
- Create: `api/routes/health.py`
- Create: `api/routes/collect.py`
- Create: `api/routes/ingestion.py`
- Create: `api/routes/promotion.py`
- Create: `api/services/__init__.py`
- Create: `api/services/collector_service.py`
- Create: `api/services/ingestion_service.py`
- Create: `api/services/promotion_service.py`
- Modify: `requirements.txt`
- Modify: `README.md`

- [ ] **Step 1: Write the failing tests**

```python
from fastapi.testclient import TestClient
from api.main import app

def test_health_ok():
    client = TestClient(app)
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {
        "status": "ok",
        "service": "investment_research_collector",
        "version": "mvp",
    }
```

```python
from fastapi.testclient import TestClient
from api.main import app

def test_protected_endpoint_without_token_is_rejected():
    client = TestClient(app)
    response = client.post("/collect/run", json={"mode": "daily"})
    assert response.status_code in (401, 403)
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python -m unittest tests.test_api -v`
Expected: fail because `api.main` does not exist yet.

- [ ] **Step 3: Write minimal implementation**

```python
from fastapi import FastAPI

app = FastAPI(title="investment_research_collector")
```

- [ ] **Step 4: Run test to verify it passes**

Run: `python -m unittest tests.test_api -v`
Expected: health passes, auth gate still rejects unauthenticated protected routes.

- [ ] **Step 5: Commit**

```bash
git add api tests/test_api.py requirements.txt README.md
git commit -m "feat: add FastAPI orchestrator scaffold"
```

### Task 2: Collector service and `/collect/run`

**Files:**
- Modify: `api/schemas.py`
- Modify: `api/services/collector_service.py`
- Modify: `api/routes/collect.py`
- Modify: `main.py`
- Modify: `tests/test_api.py`

- [ ] **Step 1: Write the failing tests**

```python
from fastapi.testclient import TestClient
from api.main import app

def test_collect_run_sync_response_includes_job_id_null(monkeypatch):
    client = TestClient(app)
    client.app.state.api_auth_token = "test-token"
    response = client.post(
        "/collect/run",
        headers={"Authorization": "Bearer test-token"},
        json={"scope": "industry", "scope_name": "散熱", "mode": "daily", "source_mode": "mock", "summarizer_mode": "mock"},
    )
    body = response.json()
    assert body["execution_mode"] == "sync"
    assert body["job_id"] is None
    assert "batch_report" in body
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python -m unittest tests.test_api -v`
Expected: `/collect/run` route missing or response shape wrong.

- [ ] **Step 3: Write minimal implementation**

```python
from collector.graph import run_collector_task, run_three_day_report_task
from collector.batch_runner import run_batch_tasks
from collector.tasks import make_task, generate_batch_tasks

def run_collect_sync(payload: dict) -> dict:
    if payload.get("batch"):
        tasks = generate_batch_tasks(...)
        batch = run_batch_tasks(tasks, batch_type=payload["batch"])
        return {
            "status": batch["status"],
            "execution_mode": "sync",
            "job_id": None,
            "message": "Collector run completed.",
            "output_files": batch.get("output_files", []),
            "run_errors": batch.get("run_errors", []),
            "batch_report": batch,
        }
    task = make_task(...)
    state = run_three_day_report_task(task) if payload.get("mode") == "three_day" else run_collector_task(task)
    return {
        "status": state.get("status", "failed"),
        "execution_mode": "sync",
        "job_id": None,
        "message": "Collector run completed.",
        "output_files": state.get("output_paths", []),
        "run_errors": state.get("run_errors", []),
        "batch_report": state.get("crawl_run_packet", {}),
    }
```

- [ ] **Step 4: Run test to verify it passes**

Run: `python -m unittest tests.test_api -v`
Expected: collector endpoint returns sync response and null job_id.

- [ ] **Step 5: Commit**

```bash
git add api main.py tests/test_api.py
git commit -m "feat: add sync collect run API"
```

### Task 3: Ingestion and promotion services

**Files:**
- Modify: `api/services/ingestion_service.py`
- Modify: `api/routes/ingestion.py`
- Modify: `api/services/promotion_service.py`
- Modify: `api/routes/promotion.py`
- Modify: `tests/test_api.py`
- Modify: `README.md`

- [ ] **Step 1: Write the failing tests**

```python
def test_ingestion_dry_run_and_promotion_dry_run():
    ...
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python -m unittest tests.test_api -v`
Expected: service functions missing.

- [ ] **Step 3: Write minimal implementation**

```python
from ingestion.ingest_outputs import dry_run_ingest, write_ingest
from promotion.packet_promoter import promote_packets

def run_ingestion(input_path: str, packet_type: str, dry_run: bool) -> dict:
    return dry_run_ingest(input_path, packet_type_filter=packet_type) if dry_run else write_ingest(input_path, packet_type_filter=packet_type)

def run_promotion(input_path: str, packet_type: str, dry_run: bool) -> dict:
    if not dry_run:
        return {
            "status": "failed",
            "message": "Promotion write mode is not implemented yet. Please use dry_run=true.",
        }
    return promote_packets(input_path=input_path, packet_type_filter=packet_type, dry_run=True)
```

- [ ] **Step 4: Run test to verify it passes**

Run: `python -m unittest tests.test_api -v`
Expected: ingestion dry-run works, promotion dry-run works, write-mode missing-key behavior returns failed cleanly.

- [ ] **Step 5: Commit**

```bash
git add api tests/test_api.py README.md
git commit -m "feat: add ingestion and promotion API services"
```

### Task 4: Integration cleanup and full verification

**Files:**
- Modify: `README.md`
- Modify: `supabase/README.md`
- Modify: `main.py`
- Modify: `ingestion/ingest_outputs.py`
- Modify: `promotion/promote_staging.py`
- Modify: `tests/test_api.py`

- [ ] **Step 1: Run the full API and CLI regression tests**

Run:
`python main.py`
`python main.py --batch industries`
`python -m ingestion.ingest_outputs --input output/ --dry-run`
`python -m promotion.promote_staging --input output/ --dry-run`
`python -m unittest discover -s tests -p "test_*.py" -v`
`python -m compileall .`

- [ ] **Step 2: Fix any integration mismatches**

If the API response keys, auth checks, or shared service return shapes differ from the CLI paths, align them by updating the shared service functions instead of duplicating logic.

- [ ] **Step 3: Update docs**

Document:
- `GET /health`
- `POST /collect/run`
- `POST /ingestion/run`
- `POST /promotion/run`
- `Authorization: Bearer <API_AUTH_TOKEN>`
- future async endpoints `POST /collect/jobs` and `GET /collect/jobs/{job_id}`

- [ ] **Step 4: Commit**

```bash
git add api ingestion promotion main.py README.md supabase/README.md tests/test_api.py
git commit -m "feat: add FastAPI orchestrator layer"
```

---

### Coverage check

- Health API: Task 1
- Auth token: Task 1 + Task 4
- Sync collect run: Task 2
- Batch support with sync response shape: Task 2
- Ingestion API: Task 3
- Promotion API: Task 3
- CLI compatibility: Task 2 + Task 4
- README updates: Tasks 1, 3, 4
- Full regression + compileall: Task 4

