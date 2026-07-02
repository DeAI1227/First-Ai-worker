# Yahoo Stock News Filter and Cnyes Removal Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Remove Cnyes from the stock-news pipeline and relax Yahoo filtering so any article mentioning a tracked stock code or Chinese stock name can flow into summarization as one combined stock brief.

**Architecture:** Keep the existing collector graph and source fetchers, but simplify the stock/institution source routing to Yahoo-only URLs. Adjust quality scoring so stock-news articles are accepted when their正文 mentions the target stock identity, while still rejecting obvious quote-bulletin or prohibited-content noise. Update summarizers to emit a single combined brief per task with a longer cap for stock news.

**Tech Stack:** Python 3.13, collector pipeline, pytest/unittest-style tests, existing Yahoo HTTP fetcher, existing mock/LLM summarizers.

---

### Task 1: Lock the new behavior with tests

**Files:**
- Modify: `tests/test_http_fetcher.py`
- Modify: `tests/test_search_provider.py` (only if needed to keep hybrid-order expectations aligned)

- [ ] **Step 1: Write the failing test**

```python
from collector.tasks import make_task
from collector.graph import load_task
from collector.nodes.planner import generate_search_plan
from collector.nodes.fetcher import fetch_sources
from collector.nodes.filter import filter_sources


def test_yahoo_stock_page_keeps_articles_that_mention_target_stock():
    state = load_task(make_task(
        scope="stock",
        scope_name="台積電",
        stock_code="2330",
        stock_name="台積電",
        source_mode="http",
        summarizer_mode="mock",
        search_provider="mock",
    ))
    state = generate_search_plan(state)
    state = fetch_sources(state)
    state = filter_sources(state)
    assert state["filtered_sources"], "Yahoo stock page articles should survive filtering"
    assert state["quality_summary"]["rejected"] < state["quality_summary"]["total_sources"]
```

```python
def test_hybrid_stock_task_does_not_use_cnyes_sources_anymore():
    task = make_task(
        scope="stock",
        scope_name="台積電",
        stock_code="2330",
        stock_name="台積電",
        source_mode="hybrid",
        summarizer_mode="mock",
        search_provider="mock",
    )
    assert all("cnyes" not in rule.get("url", "").lower() for rule in task.get("source_rules", []))
```

- [ ] **Step 2: Run the test to verify it fails**

Run: `python -m unittest tests.test_http_fetcher -v`
Expected: fail because Cnyes still appears and Yahoo rows are over-rejected.

- [ ] **Step 3: Write minimal implementation**

Add Yahoo-only source routing in `collector/sources/entrypoints.py`, remove Cnyes category rules from stock/institution tasks in `collector/tasks.py` and `collector/task_batches.py`, and relax the scorer so Yahoo articles mentioning the target stock code or Chinese name are accepted instead of rejected as quote bulletin noise.

- [ ] **Step 4: Run the test to verify it passes**

Run: `python -m unittest tests.test_http_fetcher -v`
Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add tests/test_http_fetcher.py collector/sources/entrypoints.py collector/tasks.py collector/task_batches.py collector/quality/source_scorer.py collector/summarizers/mock_summarizer.py collector/summarizers/llm_summarizer.py collector/sources/config.py docs/superpowers/plans/2026-07-02-yahoo-filter-cnyes-removal.md
git commit -m "fix: prioritize yahoo stock news and drop cnyes routing"
```

### Task 2: Clean up source routing and provider defaults

**Files:**
- Modify: `collector/sources/config.py`
- Modify: `collector/sources/registry.py`
- Modify: `collector/sources/__init__.py`
- Modify: `collector/sources/entrypoints.py`
- Modify: `collector/tasks.py`
- Modify: `collector/task_batches.py`

- [ ] **Step 1: Write the failing test**

```python
def test_stock_source_rules_are_yahoo_only():
    rules = build_stock_source_rules("2330", "台積電")
    assert len(rules) == 1
    assert "yahoo" in rules[0]["url"].lower()
    assert "cnyes" not in rules[0]["url"].lower()
```

- [ ] **Step 2: Run the test to verify it fails**

Run: `python -m unittest tests.test_stock_entrypoints -v`
Expected: FAIL until Cnyes references are removed.

- [ ] **Step 3: Write minimal implementation**

Return Yahoo stock-news URL rules only for stock and watchlist routes. Remove Cnyes feed/config entries for stock/institution scopes and keep macro/category routing out of the stock pipeline.

- [ ] **Step 4: Run the test to verify it passes**

Run: `python -m unittest tests.test_stock_entrypoints -v`
Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add collector/sources/config.py collector/sources/registry.py collector/sources/__init__.py collector/sources/entrypoints.py collector/tasks.py collector/task_batches.py
git commit -m "refactor: remove cnyes from stock news routing"
```

### Task 3: Make summaries stock-task centric and longer

**Files:**
- Modify: `collector/summarizers/mock_summarizer.py`
- Modify: `collector/summarizers/llm_summarizer.py`
- Modify: `collector/schemas/event_packet.py`
- Modify: `collector/schemas/report_packet.py`

- [ ] **Step 1: Write the failing test**

```python
def test_stock_summarizer_combines_multiple_articles_into_one_brief_under_1500_chars():
    state = {
        "scope": "stock",
        "scope_name": "台積電",
        "target_stock_code": "2330",
        "target_stock_name": "台積電",
        "filtered_sources": [
            {"title": "A", "content": "...", "source_name": "Yahoo", "source_url": "https://..."},
            {"title": "B", "content": "...", "source_name": "Yahoo", "source_url": "https://..."},
        ],
        "search_keywords": ["2330", "台積電"],
    }
    result = summarize_with_mock(state, state["filtered_sources"])
    assert len(result["ai_summary"]) <= 1500
```

- [ ] **Step 2: Run the test to verify it fails**

Run: `python -m unittest tests.test_summarizer -v`
Expected: FAIL until cap and grouping are updated.

- [ ] **Step 3: Write minimal implementation**

Increase the mock/LLM summary cap for stock-mode briefs, keep one summary per task, and frame the prompt around "combine the included news into one stock brief" rather than per-article output.

- [ ] **Step 4: Run the test to verify it passes**

Run: `python -m unittest tests.test_summarizer -v`
Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add collector/summarizers/mock_summarizer.py collector/summarizers/llm_summarizer.py collector/schemas/event_packet.py collector/schemas/report_packet.py
git commit -m "feat: make stock summaries combine multiple yahoo articles"
```

### Task 4: Verify end-to-end collector output

**Files:**
- No code changes unless a final small fix is needed

- [ ] **Step 1: Run the targeted collector task**

Run:
```bash
python - <<'PY'
from collector.tasks import make_task
from collector.graph import run_collector_task
state = run_collector_task(make_task(scope='stock', scope_name='台積電', stock_code='2330', stock_name='台積電', source_mode='http', summarizer_mode='mock', search_provider='mock'))
print(state['status'])
print(len(state.get('filtered_sources', [])))
print(state.get('event_packet', {}).get('source_count'))
PY
```
Expected: `status` is success/partial_success, filtered sources > 0, and `event_packet.source_count` reflects multiple sources.

- [ ] **Step 2: Run the full test suite**

Run: `python -m unittest discover -s tests -p "test_*.py" -v`
Expected: PASS.

- [ ] **Step 3: Commit**

```bash
git add -A
git commit -m "fix: align yahoo stock news filtering and aggregation"
```