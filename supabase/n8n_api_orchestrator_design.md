# n8n API Orchestrator Design

這份文件說明 n8n 要如何透過 HTTP Request 呼叫 `investment_research_collector` 的 FastAPI Orchestrator。

## 整體流程

```text
Cron Trigger
↓
HTTP Request: POST /collect/run
↓
IF Node: response.status
├─ success
├─ partial_success
└─ failed
```

目前第一版採用同步模式：

```text
execution_mode = "sync"
job_id = null
```

這代表 n8n 呼叫後會直接拿到結果，不需要另外查 job 狀態。

## 共用請求設定

所有受保護 endpoint 都需要帶上：

```http
Authorization: Bearer <API_AUTH_TOKEN>
Content-Type: application/json
```

如果本機開發沒有設定 `API_AUTH_TOKEN`，API 會維持寬鬆模式；但 production 必須設定 token。

## Collect API 範例

### Endpoint

```text
POST http://localhost:8000/collect/run
```

### Batch industries body

```json
{
  "batch": "industries",
  "source_mode": "hybrid",
  "summarizer_mode": "mock",
  "dry_run": false
}
```

### Single task body

```json
{
  "mode": "daily",
  "scope": "industry",
  "scope_name": "散熱",
  "stock_code": "6230",
  "stock_name": "尼得科超眾",
  "source_mode": "hybrid",
  "summarizer_mode": "mock",
  "llm_provider": "auto",
  "search_provider": "mock",
  "batch": null,
  "dry_run": false
}
```

### n8n 分流規則

```text
response.status == success → 正常結束
response.status == partial_success → 通知檢查
response.status == failed → 發出警報
```

## Ingestion API 範例

### Endpoint

```text
POST http://localhost:8000/ingestion/run
```

### Body

```json
{
  "input_path": "output/",
  "packet_type": "all",
  "dry_run": true
}
```

### 說明

- `dry_run=true`：只做讀取、檢測、mapping，不需要 Supabase key
- `dry_run=false`：會執行 Supabase write mode，需要 `SUPABASE_URL` 與 `SUPABASE_SERVICE_ROLE_KEY`

### 分流規則

```text
response.status == success → 正常結束
response.status == partial_success → 通知檢查
response.status == failed → 發出警報
```

## Promotion API 範例

### Endpoint

```text
POST http://localhost:8000/promotion/run
```

### Body

```json
{
  "input_path": "output/",
  "packet_type": "all",
  "dry_run": true
}
```

### 說明

- 第一版只支援 `dry_run=true`
- `dry_run=false` 會回傳未實作訊息：
  `Promotion write mode is not implemented yet. Please use dry_run=true.`

### 分流規則

```text
response.status == success → 正常結束
response.status == partial_success → 通知檢查
response.status == failed → 發出警報
```

## 未來 async job 預留

目前 MVP 使用 sync mode。
未來如果 `batch all` 或其他批次任務變慢，可以升級成 async job 模式。

預留的 endpoint 形狀如下：

```text
POST /collect/jobs
GET /collect/jobs/{job_id}
POST /ingestion/jobs
GET /ingestion/jobs/{job_id}
POST /promotion/jobs
GET /promotion/jobs/{job_id}
```

未來的流程會長這樣：

```text
POST job
↓
取得 job_id
↓
n8n Wait
↓
GET job result
↓
依 status 分流
```

目前這些 async endpoint 都尚未實作，只是預留接口方向。

## 安全注意事項

- 不要把 `SUPABASE_SERVICE_ROLE_KEY` 寫死在 n8n 節點內容中
- 優先使用 n8n credentials 或環境變數
- 若未來改成 HTTP API 版 job flow，請加上 auth token
- webhook 不應公開暴露
- batch report 可供 n8n 讀取，但不應包含任何 service key
- errors 也不應記錄敏感 key

