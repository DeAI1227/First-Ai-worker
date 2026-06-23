# Deployment Wiring Checklist

這份文件是「實際去設定」的 checklist。目標是把流程真正接起來：

```text
n8n Schedule Trigger
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

注意：這把 key 只能放後端，不能放前端，也不要寫進 n8n workflow JSON。

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
OPENAI_API_KEY=
OPENAI_MODEL=
GEMINI_API_KEY=
GEMINI_MODEL=
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

## 4. n8n 必做事項

n8n 只負責排程與觸發，不負責研究邏輯。

### 1) 建立 workflow

建立一個新的 workflow，例如：

- `AI Investment Research Daily Pipeline`

### 2) 加 Schedule Trigger

- 設定每天早上 07:00
- 時區使用 `Asia/Taipei`

### 3) 加 HTTP Request node

- Method: `POST`
- URL: `https://<你的後端網址>/pipeline/run`
- Header：

```text
Authorization: Bearer <API_AUTH_TOKEN>
Content-Type: application/json
```

### 4) Body 範例

```json
{
  "scope": "all",
  "source_mode": "hybrid",
  "summarizer_mode": "auto",
  "ingestion_dry_run": false,
  "promotion_dry_run": false
}
```

### 5) 加 IF node 判斷

- `status = success` → 正常結束
- `status = partial_success` → 通知人工檢查
- `status = failed` → 發警報

### 6) 失敗時檢查

如果失敗，先檢查：

- API token 是否正確
- FastAPI 是否有啟動
- Supabase env 是否設定
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
[ ] n8n workflow 已建立
[ ] n8n 可以呼叫 /pipeline/run
[ ] Supabase production tables 有資料
[ ] 前端可以讀 Supabase views
```
