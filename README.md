# AI 投資研究終端

這個專案是 **AI 投資研究終端**，不是股票報價 App。

## Official system direction

The frontend reads only Supabase production views.

## 正式系統主線

```text
LangGraph / Collector
→ output packets
→ ingestion
→ Supabase staging
→ promotion
→ Supabase production tables / views
→ frontend reads Supabase only
```

## 資料邊界

- 前端只讀 Supabase production views
- 前端不讀 Python 程式
- 前端不讀 `output/` JSON
- 前端不直接呼叫 Collector
- `output/` JSON 只是後端中間產物
- 不做即時股價、K 線、技術分析、買賣建議、目標價、報酬率預測
- 不產生「今日未找到重大更新」假 event
- 股票是 reference data，沒有事件也會存在於 `stocks` 與 `view_stock_cards`

## 目前主模組

- `collector/` - LangGraph Collector、source layer、summarizer、quality scoring
- `ingestion/` - packet loading、dry-run、Supabase write mode
- `promotion/` - staging to production promotion
- `supabase/` - staging schema、production schema、reference seed、views contract
- `api/` - FastAPI orchestrator for GitHub Actions / manual trigger
- `frontend_integration/` - future Supabase-only frontend contract and query reference
- `docs/` - deployment, audit, and runbook documents
- `n8n_workflows/` - legacy workflow templates kept for reference

## 搜尋來源

目前搜尋層的正式主線是 **Firecrawl Hosted API**。

- 預設可使用 `SEARCH_PROVIDER=firecrawl`
- 後端透過 `FIRECRAWL_BASE_URL` 連到 Firecrawl 的 hosted `/v2/search`
- 建議提供 `FIRECRAWL_API_KEY`；若未提供，是否能使用取決於 Firecrawl 當下提供的 keyless/free tier 能力
- Firecrawl 不可用時，搜尋層會安全 fallback 到 mock，不會讓主流程假成功

### Firecrawl Hosted API 建議設定

```env
FIRECRAWL_BASE_URL=https://api.firecrawl.dev
FIRECRAWL_API_KEY=
SEARCH_PROVIDER=firecrawl
```

### Firecrawl 使用說明

- [Firecrawl hosted API guide](docs/firecrawl_hosted_api.md)

> Firecrawl 現在被視為外部搜尋/抓取供應商，不再是本專案需要自架與維護的核心基礎設施。

## 跟蹤宇宙

MVP 追蹤宇宙包含：

- 六大產業：散熱、電力、自動駕駛、機器人、CPO 光通訊、網通
- 45 檔追蹤股票 reference data
- 4 檔大行關注股票
- macro topics
- event packets
- daily digest packets
- three-day reports
- quality summaries

## 快速啟動

### 1. 本地啟動 FastAPI

```bash
uvicorn api.main:app --reload
```

### 1.5 前端部署成真正網址

前端已經是 Supabase-only 的靜態站，可以直接部署到 GitHub Pages。

部署 workflow：

- [`.github/workflows/frontend-pages.yml`](.github/workflows/frontend-pages.yml)

部署後的網址通常會像：

```text
https://<your-github-username>.github.io/First-Ai-worker/
```

> GitHub Pages 只負責前端靜態站，不承載 Python 後端。

### 2. 跑一次完整流程

```bash
python scripts/run_autonomous_once.py
```

### 3. 官方排程

GitHub Actions 是目前正式使用的免費雲端排程器。每天早上 07:00 Taipei time 會觸發後端 pipeline。

這個每日 workflow 現在會把 **daily** 和 **three-day** 兩段流程一起跑完，但會拆成多個較小的 `/pipeline/run` 請求，避免單一長請求在 Render 冷啟動時更容易撞到 502。

相關設定請看：

- [`docs/github_actions_schedule.md`](docs/github_actions_schedule.md)
- [`.github/workflows/daily-pipeline.yml`](.github/workflows/daily-pipeline.yml)

### 4. 跑 batch all

```bash
python main.py --batch all
```

### 5. ingestion dry-run

```bash
python -m ingestion.ingest_outputs --input output/ --dry-run
```

### 6. promotion dry-run

```bash
python -m promotion.promote_staging --input output/ --dry-run
```

### 7. 自動流程 smoke test

```bash
python scripts/e2e_mvp_smoke.py
```

## Supabase 角色

Supabase 是正式資料中心。

- `staging` tables 接收 ingestion 寫入
- `production` tables 接收 promotion 寫入
- `views` 是新前端唯一應讀來源

## 前端資料來源

前端頁面對應的 view：

- 總覽頁 → `view_dashboard_events`
- 產業追蹤頁 → `view_industry_cards`
- 股票清單頁 → `view_stock_cards`
- 股票詳情頁 → `view_stock_detail_events`
- 大環境頁 → `view_macro_events`
- 大行關注頁 → `view_institution_watch_events`
- 研究報告頁 → `view_recent_reports`
- 未讀統計 → `view_unread_counts`

## 重要文件

- [`docs/system_data_flow.md`](docs/system_data_flow.md)
- [`docs/deployment_wiring_checklist.md`](docs/deployment_wiring_checklist.md)
- [`docs/github_actions_schedule.md`](docs/github_actions_schedule.md)
- [`docs/pipeline_runbook.md`](docs/pipeline_runbook.md)
- [`docs/api_contract.md`](docs/api_contract.md)
- [`docs/github_pages_frontend.md`](docs/github_pages_frontend.md) - frontend deployment note
- [`docs/n8n_api_usage.md`](docs/n8n_api_usage.md) - legacy reference only
- [`docs/n8n_setup_steps.md`](docs/n8n_setup_steps.md) - legacy reference only
- [`docs/mvp_release_checklist.md`](docs/mvp_release_checklist.md)
- [`docs/backend_final_audit.md`](docs/backend_final_audit.md)
- [`docs/audit_backend_supabase.md`](docs/audit_backend_supabase.md)
- [`docs/audit_api_n8n_autonomous.md`](docs/audit_api_n8n_autonomous.md)
- [`docs/audit_frontend_full_system.md`](docs/audit_frontend_full_system.md)
- [`docs/time_health_audit.md`](docs/time_health_audit.md)

## 測試與驗證

```bash
python -m unittest discover -s tests -p "test_*.py" -v
python -m compileall .
```

## 環境變數

後端正式寫入 Supabase 必填：

- `SUPABASE_URL`
- `SUPABASE_SERVICE_ROLE_KEY`
- `API_AUTH_TOKEN`

前端必填：

- `VITE_SUPABASE_URL`
- `VITE_SUPABASE_ANON_KEY`

LLM / Search providers 可先選填，沒有就 fallback mock。

- `FIRECRAWL_BASE_URL`
- `FIRECRAWL_API_KEY`
- `SEARCH_PROVIDER=firecrawl`

### 排程器

- 官方正式排程器：GitHub Actions
- `n8n` / Umbrella：保留舊文件參考，不再是主線
