# Deployment Wiring Checklist

這份文件的目標很直接：讓你真的把整條 AI 員工接起來，而不是只看架構圖。

正式接線路徑：

```text
n8n Schedule Trigger
→ FastAPI POST /pipeline/run
→ LangGraph Collector
→ ingestion
→ Supabase staging
→ promotion
→ Supabase production/views
→ 前端讀 Supabase
```

## 先講清楚資料責任

- 前端只讀 Supabase production views
- 前端不讀 Python 程式
- 前端不讀 `output/` JSON
- `output/` JSON 是後端中間產物，不是前端資料來源
- `service_role` key 只給後端，不能放前端
- `anon` key 給前端讀 Supabase views 用

## 1. Supabase 必做事項

### 1. 建立 Supabase project

1. 到 [Supabase Console](https://supabase.com/dashboard)。
2. 點 `New project`。
3. 選 Organization。
4. 輸入 Project name。
5. 設定 database password。
6. 選 region。
7. 等 project 建好。

### 2. 找到 Project URL

1. 進入你的 Supabase project。
2. 左側點 `Project Settings`。
3. 進入 `API`。
4. 複製 `Project URL`。

這個值會放進：

- 後端 `.env` 的 `SUPABASE_URL`
- 前端 `.env` 的 `VITE_SUPABASE_URL`

### 3. 找到 anon key

1. 還是在 `Project Settings` → `API`。
2. 找 `Project API keys`。
3. 複製 `anon public` key。

這個值只給前端：

- `VITE_SUPABASE_ANON_KEY`

### 4. 找到 service_role key

1. 一樣在 `Project Settings` → `API`。
2. 找 `service_role` key。
3. 複製它。

這個值只給後端：

- `SUPABASE_SERVICE_ROLE_KEY`

不要把這個 key 放進前端、n8n workflow、或公開文件。

### 5. 打開 SQL Editor

1. 左側點 `SQL Editor`。
2. 點 `New query`。
3. 依序執行 SQL 檔。

### 6. 依序執行 SQL

先執行：

```text
supabase/production_schema.sql
supabase/staging_schema.sql
supabase/seed_reference_data.sql
```

建議順序是：

1. `supabase/production_schema.sql`
2. `supabase/staging_schema.sql`
3. `supabase/seed_reference_data.sql`

### 7. 確認 tables 存在

執行完後，在 SQL Editor 跑：

```sql
select table_name
from information_schema.tables
where table_schema = 'public'
order by table_name;
```

確認至少有這些 tables：

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

### 8. 確認 views 存在

再跑：

```sql
select table_name
from information_schema.views
where table_schema = 'public'
order by table_name;
```

確認至少有：

- `view_dashboard_events`
- `view_industry_cards`
- `view_stock_cards`
- `view_stock_detail_events`
- `view_macro_events`
- `view_institution_watch_events`
- `view_recent_reports`
- `view_unread_counts`

### 9. 確認 stocks reference data

跑：

```sql
select stock_code, stock_name
from stocks
order by stock_code;
```

你應該會看到 45 檔追蹤股票。

### 10. 確認 industries reference data

跑：

```sql
select industry_id, industry_name
from industries
order by industry_id;
```

你應該會看到六大產業：

- 散熱
- 電力
- 自動駕駛
- 機器人
- CPO 光通訊
- 網通

## 2. 後端 `.env` 必填

請在專案根目錄放 `.env`，內容請參考 [../.env.example](../.env.example)。

### 必填

```env
SUPABASE_URL=
SUPABASE_SERVICE_ROLE_KEY=
API_AUTH_TOKEN=
```

### 選填

```env
OPENAI_API_KEY=
OPENAI_MODEL=
GEMINI_API_KEY=
GEMINI_MODEL=
TAVILY_API_KEY=
SERPAPI_API_KEY=
```

### 後端設定方式

1. 打開根目錄 `.env`
2. 貼入 `SUPABASE_URL`
3. 貼入 `SUPABASE_SERVICE_ROLE_KEY`
4. 貼入 `API_AUTH_TOKEN`
5. 存檔

### 後端用途

- `SUPABASE_URL`：後端連 Supabase
- `SUPABASE_SERVICE_ROLE_KEY`：後端寫 staging / production
- `API_AUTH_TOKEN`：保護 FastAPI endpoint

## 3. 前端 `.env` 必填

請在 `frontend/.env` 放入，格式參考 [../frontend/.env.example](../frontend/.env.example)。

### 必填

```env
VITE_SUPABASE_URL=
VITE_SUPABASE_ANON_KEY=
```

### 設定方式

1. 打開 `frontend/.env`
2. 貼入 `VITE_SUPABASE_URL`
3. 貼入 `VITE_SUPABASE_ANON_KEY`
4. 存檔

### 前端限制

- 前端不能使用 `service_role` key
- 前端只能讀 Supabase production views
- 前端不能直接讀 `output/` JSON
- 前端不能直接呼叫 Collector

## 4. n8n 必做事項

請在 n8n 做一個 workflow，照下面步驟設。

### Step 1. 建立 workflow

1. 打開 n8n。
2. 點 `New Workflow`。
3. 命名，例如：
   - `AI Investment Research Daily Pipeline`

### Step 2. 加 Schedule Trigger

1. 新增 `Cron` 或 `Schedule Trigger` node。
2. 設定每日排程。
3. 例如每天 `07:00` 觸發。

### Step 3. 加 HTTP Request node

1. 新增 `HTTP Request` node。
2. Method 設為 `POST`。
3. URL 填你的 FastAPI 位址：

```text
https://<你的後端網址>/pipeline/run
```

如果本機開發，會是：

```text
http://localhost:8000/pipeline/run
```

### Step 4. Header

加上：

```text
Authorization: Bearer <API_AUTH_TOKEN>
Content-Type: application/json
```

如果你想用環境變數，請用：

```text
Authorization: Bearer {{$env.API_AUTH_TOKEN}}
```

不要把真 token 寫死在 node 裡。

### Step 5. Body

Body 使用這份：

```json
{
  "scope": "all",
  "source_mode": "hybrid",
  "summarizer_mode": "auto",
  "ingestion_dry_run": false,
  "promotion_dry_run": false
}
```

### Step 6. 加 IF node

判斷回傳的 `status`：

- `success`
- `partial_success`
- `failed`

### Step 7. 通知邏輯

- `success`：記錄成功即可
- `partial_success`：通知管理者檢查
- `failed`：通知管理者，並停止後續流程

### Step 8. n8n 的角色

- n8n 只負責排程與觸發
- n8n 不負責研究邏輯
- n8n 不負責抓新聞
- 如果 FastAPI 沒部署或沒啟動，n8n 叫不到 AI 員工

## 5. 後端啟動方式

### 本地啟動 FastAPI

```bash
uvicorn api.main:app --reload
```

### 手動跑一次完整流程

```bash
python scripts/run_autonomous_once.py
```

如果你還沒部署 Supabase，這個腳本會誠實回報：

- `wrote_to_supabase: false`
- `autonomous_ready: false`
- 並列出缺少的 env 或 write mode 錯誤

## 6. 實際部署順序

建議照這個順序接：

1. 先把 Supabase project 建起來
2. 執行 production / staging / seed SQL
3. 填後端 `.env`
4. 啟動 FastAPI
5. 用 `python scripts/run_autonomous_once.py` 手動驗證
6. 填前端 `.env`
7. 啟動前端
8. 在 n8n 建 workflow
9. 讓 n8n 呼叫 `/pipeline/run`

## 7. 最後確認清單

- [ ] Supabase project 已建立
- [ ] production_schema.sql 已執行
- [ ] staging_schema.sql 已執行
- [ ] seed_reference_data.sql 已執行
- [ ] 後端 `.env` 已填 `SUPABASE_URL`
- [ ] 後端 `.env` 已填 `SUPABASE_SERVICE_ROLE_KEY`
- [ ] 後端 `.env` 已填 `API_AUTH_TOKEN`
- [ ] 前端 `.env` 已填 `VITE_SUPABASE_URL`
- [ ] 前端 `.env` 已填 `VITE_SUPABASE_ANON_KEY`
- [ ] FastAPI 可以啟動
- [ ] `/health` 可以打通
- [ ] `/pipeline/run` 可以手動打通
- [ ] n8n workflow 已建立
- [ ] n8n 可以呼叫 `/pipeline/run`
- [ ] Supabase production tables 有資料
- [ ] 前端可以讀 Supabase views
- [ ] 前端沒有讀 `output/` JSON
- [ ] 前端沒有讀 Python 程式

