# Deployment Wiring Checklist

這份文件是「實際去設定」的 checklist。正式排程已改為 **GitHub Actions**，不是 n8n / Umbrella。

```text
GitHub Actions Schedule
→ FastAPI POST /pipeline/run
→ LangGraph Collector
→ ingestion
→ Supabase staging
→ promotion
→ Supabase production/views
→ frontend reads Supabase only
```

## 你要先知道的邊界

- 前端只讀 Supabase production views
- 前端不讀 Python 程式
- 前端不讀 `output/` JSON
- `output/` JSON 只是後端中間產物
- `service_role` key 只能給後端，不給前端
- `anon` key 給前端使用

## 1. Supabase 必做事項

### 1) 建立 Supabase project

1. 到 [Supabase Console](https://supabase.com/dashboard)
2. 建立 `New project`
3. 選 organization
4. 輸入 project name
5. 設定 database password
6. 選 region
7. 等待 project 建立完成

### 2) 找到 Project URL

1. 打開你的 Supabase project
2. 進入 `Project Settings`
3. 點 `API`
4. 複製 `Project URL`

填入：

- 後端 `.env` 的 `SUPABASE_URL`
- 前端 `.env` 的 `VITE_SUPABASE_URL`

### 3) 找到 anon key

1. 在 `Project Settings` → `API`
2. 找 `Project API keys`
3. 複製 `anon public` key

填入：

- 前端 `.env` 的 `VITE_SUPABASE_ANON_KEY`

### 4) 找到 service_role key

1. 在 `Project Settings` → `API`
2. 找 `service_role` key
3. 複製這把 key

填入：

- 後端 `.env` 的 `SUPABASE_SERVICE_ROLE_KEY`

注意：這把 key 只能放後端，不能放前端，也不要寫進 workflow JSON。

### 5) 打開 SQL Editor

1. 進入 `SQL Editor`
2. 點 `New query`
3. 準備執行 SQL

### 6) 依序執行 SQL

依序執行：

1. `supabase/production_schema.sql`
2. `supabase/staging_schema.sql`
3. `supabase/seed_reference_data.sql`

### 7) 確認 tables 存在

在 SQL Editor 執行：

```sql
select table_name
from information_schema.tables
where table_schema = 'public'
order by table_name;
```

應該要看到至少這些 tables：

- `industries`
- `stocks`
- `stock_industries`
- `macro_topics`
- `institution_watch_stocks`
- `events`
- `event_relations`
- `reports`
- `report_relations`
- `crawl_runs`
- `rejected_sources`
- `user_read_status`
- `staging_events`
- `staging_daily_digests`
- `staging_reports`
- `staging_crawl_runs`
- `staging_rejected_sources`
- `ingestion_errors`

### 8) 確認 views 存在

執行：

```sql
select table_name
from information_schema.views
where table_schema = 'public'
order by table_name;
```

應該要看到：

- `view_dashboard_events`
- `view_industry_cards`
- `view_stock_cards`
- `view_stock_detail_events`
- `view_macro_events`
- `view_institution_watch_events`
- `view_recent_reports`
- `view_unread_counts`

### 9) 確認 stocks reference data

執行：

```sql
select stock_code, stock_name
from stocks
order by stock_code;
```

應該會看到追蹤股票 reference data。

### 10) 確認 industries reference data

執行：

```sql
select industry_id, industry_name
from industries
order by industry_id;
```

應該會看到六大產業：

- 散熱
- 電力
- 自動駕駛
- 機器人
- CPO 光通訊
- 網通

## 2. 後端 `.env` 必填

把 `.env.example` 複製成 `.env`，再填真實值。

### 正式寫入 Supabase 必填

```env
SUPABASE_URL=
SUPABASE_SERVICE_ROLE_KEY=
API_AUTH_TOKEN=
```

### 可選但建議先準備

```env
ENVIRONMENT=development
ALLOW_INSECURE_SSL=false
GEMINI_API_KEY=
GEMINI_MODEL=
AGNES_API_KEY=
AGNES_API_URL=
AGNES_BASE_URL=
AGNES_MODEL=agnes-2.0-flash
FIRECRAWL_BASE_URL=http://localhost:3002
FIRECRAWL_API_KEY=
SEARCH_PROVIDER=firecrawl
TAVILY_API_KEY=
SERPAPI_API_KEY=
```

### 後端 `.env` 重點

- `SUPABASE_URL`：Supabase project URL
- `SUPABASE_SERVICE_ROLE_KEY`：只給後端
- `API_AUTH_TOKEN`：保護 FastAPI endpoint
- `ALLOW_INSECURE_SSL`：正式環境必須維持 `false`

## 3. 前端 `.env` 必填

前端只需要讀 Supabase views，所以只放 public 權限的 key。

### `frontend/.env.example`

```env
VITE_SUPABASE_URL=
VITE_SUPABASE_ANON_KEY=
```

### 前端重點

- 不能使用 `service_role` key
- 只能讀 Supabase production views
- 不能讀 `output/` JSON
- 不能直接呼叫 Collector

## 4. GitHub Actions 必做事項

GitHub Actions 是正式的免費雲端排程器；n8n / Umbrella 只保留歷史參考，不是主線。

### 1) 確認 workflow 檔案

請確認存在：

- `.github/workflows/daily-pipeline.yml`

### 2) 設定 Schedule

- 設定每天早上 07:00
- 時區使用 `Asia/Taipei`

### 3) 設定 Secrets

在 GitHub repository settings 內設定：

- `FASTAPI_BASE_URL`
- `API_AUTH_TOKEN`

### 4) Workflow 會做的事

- `POST /pipeline/run`
- 檢查 `status`
- `success` 正常結束
- `partial_success` 發出提醒
- `failed` 直接失敗

### 5) 失敗時檢查

如果失敗，先檢查：

- GitHub Actions secrets 是否存在
- FastAPI 是否有啟動
- `SUPABASE_URL`
- `SUPABASE_SERVICE_ROLE_KEY`
- `pipeline_report` 和 `batch_report`

## 5. 後端啟動方式

### 本地啟動 FastAPI

```bash
uvicorn api.main:app --reload
```

### 手動跑一次完整流程

```bash
python scripts/run_autonomous_once.py
```

## 6. 最後確認清單

```text
[ ] Supabase project 已建立
[ ] production_schema.sql 已執行
[ ] staging_schema.sql 已執行
[ ] seed_reference_data.sql 已執行
[ ] 後端 .env 已填 SUPABASE_URL
[ ] 後端 .env 已填 SUPABASE_SERVICE_ROLE_KEY
[ ] 後端 .env 已填 API_AUTH_TOKEN
[ ] 前端 .env 已填 VITE_SUPABASE_URL
[ ] 前端 .env 已填 VITE_SUPABASE_ANON_KEY
[ ] FastAPI 可以啟動
[ ] /health 可以打通
[ ] /pipeline/run 可以手動打通
[ ] GitHub Actions workflow 已建立
[ ] GitHub Actions 可以呼叫 /pipeline/run
[ ] Supabase production tables 有資料
[ ] 前端可以讀 Supabase views

## 5. n8n / Umbrella 狀態

- `n8n` / `Umbrella` 不再是正式排程路線
- 舊 workflow 文件僅作歷史參考
- 正式的自動排程請使用 GitHub Actions
```
