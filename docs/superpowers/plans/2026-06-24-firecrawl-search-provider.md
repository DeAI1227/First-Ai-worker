# Firecrawl Search Provider Implementation Plan

> Historical note: this plan was written for a self-hosted Firecrawl rollout. The current project direction uses Firecrawl Hosted API instead of local/self-host deployment.

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Replace the search layer's default fallback with a Firecrawl-backed provider while keeping the collector pipeline stable and fully backward-compatible.

**Architecture:** Add a dedicated Firecrawl provider. The current production direction is to call the hosted Firecrawl API rather than a locally self-hosted instance. Wire it into the existing search-provider registry so `auto` prefers Firecrawl when configured, and falls back safely to mock when not available. Keep the rest of the collector, ingestion, and promotion pipeline untouched.

**Tech Stack:** Python, `requests`, existing collector search provider registry, `unittest`, `mock`.

---

### Task 1: Add Firecrawl provider implementation

**Files:**
- Create: `collector/sources/search/firecrawl_provider.py`
- Modify: `collector/sources/search/__init__.py`

- [ ] **Step 1: Write the failing test**

```python
def test_firecrawl_provider_parses_search_response():
    ...
```

- [ ] **Step 2: Run the test to verify it fails**

Run: `python -m unittest tests.test_firecrawl_search_provider -v`
Expected: fail because `FirecrawlProvider` does not exist yet.

- [ ] **Step 3: Write minimal implementation**

```python
class FirecrawlProvider(BaseSearchProvider):
    provider_name = "firecrawl"
    base_url_env = "FIRECRAWL_BASE_URL"
    api_key_env = "FIRECRAWL_API_KEY"
```

- [ ] **Step 4: Run the test to verify it passes**

Run: `python -m unittest tests.test_firecrawl_search_provider -v`
Expected: pass.

---

### Task 2: Wire Firecrawl into provider selection

**Files:**
- Modify: `collector/sources/search/registry.py`
- Modify: `collector/sources/search_fetcher.py`
- Modify: `collector/sources/search/__init__.py`

- [ ] **Step 1: Write the failing test**

```python
def test_auto_prefers_firecrawl_when_configured():
    ...
```

- [ ] **Step 2: Run the test to verify it fails**

Run: `python -m unittest tests.test_firecrawl_search_provider -v`
Expected: fail until `auto` chooses Firecrawl first.

- [ ] **Step 3: Write minimal implementation**

```python
def select_search_provider(...):
    if provider_name == "auto":
        if FirecrawlProvider().is_available():
            return "firecrawl", FirecrawlProvider()
        ...
```

- [ ] **Step 4: Run the test to verify it passes**

Run: `python -m unittest tests.test_firecrawl_search_provider -v`
Expected: pass.

---

### Task 3: Update env docs and Firecrawl usage instructions

**Files:**
- Modify: `.env.example`
- Modify: `README.md`
- Modify: `docs/deployment_wiring_checklist.md`
- Create: `docs/firecrawl_hosted_api.md`

- [ ] **Step 1: Write the failing doc checks**

```python
def test_env_example_has_firecrawl_vars():
    ...
```

- [ ] **Step 2: Run the test to verify it fails**

Run: `python -m unittest tests.test_firecrawl_search_provider -v`
Expected: fail until env vars/docs exist.

- [ ] **Step 3: Write minimal documentation**

```env
FIRECRAWL_BASE_URL=https://api.firecrawl.dev
FIRECRAWL_API_KEY=
SEARCH_PROVIDER=firecrawl
```

- [ ] **Step 4: Run the test to verify it passes**

Run: `python -m unittest tests.test_firecrawl_search_provider -v`
Expected: pass.

---

### Task 4: Verify the full suite

**Files:**
- Modify: none beyond the above if tests reveal issues

- [ ] **Step 1: Run unit tests**

Run: `python -m unittest discover -s tests -p "test_*.py" -v`

- [ ] **Step 2: Run compile check**

Run: `python -m compileall .`

- [ ] **Step 3: Commit**

```bash
git add collector/sources/search/firecrawl_provider.py collector/sources/search/__init__.py collector/sources/search/registry.py collector/sources/search_fetcher.py .env.example README.md docs/deployment_wiring_checklist.md docs/firecrawl_hosted_api.md tests/test_firecrawl_search_provider.py docs/superpowers/plans/2026-06-24-firecrawl-search-provider.md
git commit -m "feat: add firecrawl search provider"
```
