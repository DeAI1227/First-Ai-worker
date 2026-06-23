# Autonomous Run MVP Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Make `/pipeline/run` run the real backend sequence for n8n and local one-shot execution, while clearly reporting whether Supabase write mode actually happened.

**Architecture:** Keep the existing sync-first FastAPI orchestrator and extend its pipeline response so it reports autonomous readiness, stage execution, and real write-state truthfully. Add one minimal n8n workflow template and one local runner script that both reuse the same pipeline entrypoint. Do not add queues, workers, or async job storage.

**Tech Stack:** Python, FastAPI, Pydantic, n8n workflow JSON, existing collector/ingestion/promotion services.

---

### Task 1: Tighten pipeline request and response contract

**Files:**
- Modify: `investment_research_collector/api/schemas.py`
- Modify: `investment_research_collector/api/services/pipeline_service.py`
- Modify: `investment_research_collector/api/routes/pipeline.py`
- Test: `investment_research_collector/tests/test_api.py`
- Test: `investment_research_collector/tests/test_api_contract_pack.py`

- [ ] **Step 1: Write the failing test**

```python
def test_pipeline_run_returns_autonomous_flags(self):
    response = self.client.post(
        "/pipeline/run",
        headers={"Authorization": "Bearer test-token"},
        json={
            "scope": "all",
            "source_mode": "hybrid",
            "summarizer_mode": "auto",
            "ingestion_dry_run": False,
            "promotion_dry_run": False,
        },
    )
    body = response.json()
    assert body["execution_mode"] == "sync"
    assert body["job_id"] is None
    assert body["data"]["autonomous_ready"] in {True, False}
    assert body["data"]["collect_ran"] is True
    assert body["data"]["ingestion_ran"] is True
    assert body["data"]["promotion_ran"] is True
    assert body["data"]["wrote_to_supabase"] in {True, False}
```

- [ ] **Step 2: Run test to verify it fails**

Run:
```bash
python -m unittest tests.test_api.ApiTests.test_pipeline_run_returns_autonomous_flags -v
```
Expected: FAIL because the current response body does not expose the autonomous flags yet.

- [ ] **Step 3: Write minimal implementation**

Update the pipeline request schema to accept the simpler autonomous call shape while keeping the existing nested shape for backward compatibility:

```python
class PipelineRunRequest(BaseModel):
    scope: str = "all"
    source_mode: SourceMode = "hybrid"
    summarizer_mode: SummarizerMode = "auto"
    ingestion_dry_run: bool = True
    promotion_dry_run: bool = True
    collect: PipelineCollectRequest | None = None
    ingestion: PipelineIngestionRequest | None = None
    promotion: PipelinePromotionRequest | None = None
```

Return a response `data` payload that includes:

```python
{
    "autonomous_ready": True,
    "collect_ran": True,
    "ingestion_ran": True,
    "promotion_ran": True,
    "wrote_to_supabase": bool(...),
    "collect_result": {...},
    "ingestion_result": {...},
    "promotion_result": {...},
    "pipeline_report": {...},
}
```

When Supabase env vars are missing, `wrote_to_supabase` must be `False`.

- [ ] **Step 4: Run test to verify it passes**

Run:
```bash
python -m unittest tests.test_api.ApiTests.test_pipeline_run_returns_autonomous_flags -v
```
Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add investment_research_collector/api/schemas.py investment_research_collector/api/services/pipeline_service.py investment_research_collector/api/routes/pipeline.py investment_research_collector/tests/test_api.py
git commit -m "feat: tighten autonomous pipeline contract"
```

### Task 2: Make pipeline write truth explicit

**Files:**
- Modify: `investment_research_collector/api/services/pipeline_service.py`
- Modify: `investment_research_collector/api/services/ingestion_service.py`
- Modify: `investment_research_collector/api/services/promotion_service.py`
- Test: `investment_research_collector/tests/test_api.py`
- Test: `investment_research_collector/tests/test_promotion_write_mode.py`
- Test: `investment_research_collector/tests/test_ingestion_package.py`

- [ ] **Step 1: Write the failing test**

```python
def test_pipeline_run_marks_wrote_to_supabase_false_without_env(self):
    with patch.dict(os.environ, {}, clear=True):
        response = self.client.post(
            "/pipeline/run",
            headers={"Authorization": "Bearer test-token"},
            json={
                "scope": "all",
                "source_mode": "hybrid",
                "summarizer_mode": "auto",
                "ingestion_dry_run": False,
                "promotion_dry_run": False,
            },
        )
    body = response.json()
    assert body["data"]["wrote_to_supabase"] is False
    assert body["status"] in {"partial_success", "failed"}
    assert body["data"]["promotion_result"]["status"] in {"failed", "partial_success"}
```

- [ ] **Step 2: Run test to verify it fails**

Run:
```bash
python -m unittest tests.test_api.ApiTests.test_pipeline_run_marks_wrote_to_supabase_false_without_env -v
```
Expected: FAIL until the pipeline response is wired to inspect Supabase env truthfully.

- [ ] **Step 3: Write minimal implementation**

Surface a helper in `pipeline_service.py` that checks:

```python
def has_supabase_write_env() -> bool:
    return bool(os.getenv("SUPABASE_URL") and os.getenv("SUPABASE_SERVICE_ROLE_KEY"))
```

Use it to set `wrote_to_supabase`, and keep write-mode stage results honest when env vars are missing.

- [ ] **Step 4: Run test to verify it passes**

Run:
```bash
python -m unittest tests.test_api.ApiTests.test_pipeline_run_marks_wrote_to_supabase_false_without_env -v
```
Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add investment_research_collector/api/services/pipeline_service.py investment_research_collector/api/services/ingestion_service.py investment_research_collector/api/services/promotion_service.py investment_research_collector/tests/test_api.py investment_research_collector/tests/test_promotion_write_mode.py investment_research_collector/tests/test_ingestion_package.py
git commit -m "fix: report real write mode status"
```

### Task 3: Add local autonomous runner

**Files:**
- Create: `investment_research_collector/scripts/run_autonomous_once.py`
- Test: `investment_research_collector/tests/test_autonomous_run.py`

- [ ] **Step 1: Write the failing test**

```python
def test_run_autonomous_once_script_exists(self):
    self.assertTrue((self.project_root / "scripts" / "run_autonomous_once.py").exists())
```

```python
def test_run_autonomous_once_outputs_status_fields(self):
    result = subprocess.run(
        ["python", "scripts/run_autonomous_once.py"],
        cwd=self.project_root,
        capture_output=True,
        text=True,
    )
    assert "collect_ran" in result.stdout
    assert "ingestion_ran" in result.stdout
    assert "promotion_ran" in result.stdout
    assert "wrote_to_supabase" in result.stdout
```

- [ ] **Step 2: Run test to verify it fails**

Run:
```bash
python -m unittest tests.test_autonomous_run -v
```
Expected: FAIL because the script does not exist yet.

- [ ] **Step 3: Write minimal implementation**

Implement the script as a thin wrapper around the same pipeline service:

```python
from api.schemas import PipelineRunRequest
from api.services.pipeline_service import run_pipeline_sync

result = run_pipeline_sync(PipelineRunRequest(
    scope="all",
    source_mode="hybrid",
    summarizer_mode="auto",
    ingestion_dry_run=False,
    promotion_dry_run=False,
))
print(result["data"]["collect_ran"])
print(result["data"]["ingestion_ran"])
print(result["data"]["promotion_ran"])
print(result["data"]["wrote_to_supabase"])
print(result["status"])
print(result["errors"])
```

- [ ] **Step 4: Run test to verify it passes**

Run:
```bash
python -m unittest tests.test_autonomous_run -v
```
Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add investment_research_collector/scripts/run_autonomous_once.py investment_research_collector/tests/test_autonomous_run.py
git commit -m "feat: add autonomous one-shot runner"
```

### Task 4: Add minimal n8n workflow template

**Files:**
- Create: `investment_research_collector/n8n_workflows/autonomous_daily_pipeline.json`
- Test: `investment_research_collector/tests/test_n8n_workflows.py`

- [ ] **Step 1: Write the failing test**

```python
def test_autonomous_daily_pipeline_workflow_exists(self):
    self.assertTrue((self.project_root / "n8n_workflows" / "autonomous_daily_pipeline.json").exists())
```

- [ ] **Step 2: Run test to verify it fails**

Run:
```bash
python -m unittest tests.test_n8n_workflows -v
```
Expected: FAIL until the workflow file exists.

- [ ] **Step 3: Write minimal implementation**

Create a tiny n8n workflow JSON with:

```json
{
  "nodes": [
    { "name": "Schedule Trigger", "type": "n8n-nodes-base.cron" },
    { "name": "HTTP Request", "type": "n8n-nodes-base.httpRequest" },
    { "name": "IF", "type": "n8n-nodes-base.if" }
  ]
}
```

The HTTP node should call `POST /pipeline/run` with:

```json
{
  "scope": "all",
  "source_mode": "hybrid",
  "summarizer_mode": "auto",
  "ingestion_dry_run": false,
  "promotion_dry_run": false
}
```

The auth header should be:

```text
Authorization: Bearer {{$env.API_AUTH_TOKEN}}
```

- [ ] **Step 4: Run test to verify it passes**

Run:
```bash
python -m unittest tests.test_n8n_workflows -v
```
Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add investment_research_collector/n8n_workflows/autonomous_daily_pipeline.json investment_research_collector/tests/test_n8n_workflows.py
git commit -m "feat: add autonomous n8n workflow template"
```

### Task 5: Final verification and README note

**Files:**
- Modify: `investment_research_collector/README.md`
- Modify: `investment_research_collector/docs/api_contract.md` if needed

- [ ] **Step 1: Write the final smoke assertions**

```python
def test_pipeline_response_reports_autonomous_state(self):
    response = self.client.post(
        "/pipeline/run",
        headers={"Authorization": "Bearer test-token"},
        json={
            "scope": "all",
            "source_mode": "hybrid",
            "summarizer_mode": "auto",
            "ingestion_dry_run": False,
            "promotion_dry_run": False,
        },
    )
    body = response.json()
    assert "autonomous_ready" in body["data"]
    assert "collect_ran" in body["data"]
    assert "ingestion_ran" in body["data"]
    assert "promotion_ran" in body["data"]
    assert "wrote_to_supabase" in body["data"]
```

- [ ] **Step 2: Run full test suite**

Run:
```bash
python -m unittest discover -s tests -p "test_*.py" -v
```
Expected: PASS.

- [ ] **Step 3: Run compileall**

Run:
```bash
python -m compileall .
```
Expected: PASS.

- [ ] **Step 4: Update README with autonomous run note**

Add a short note explaining:

- `/pipeline/run` is the n8n trigger point
- autonomous mode is sync-first
- `autonomous_ready` and `wrote_to_supabase` must be truthful
- missing Supabase env means write mode is not real

- [ ] **Step 5: Commit**

```bash
git add investment_research_collector/README.md investment_research_collector/docs/api_contract.md
git commit -m "docs: finalize autonomous run contract"
```

