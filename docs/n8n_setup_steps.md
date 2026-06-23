# n8n Setup Steps

這份文件專門寫給你在 n8n 裡面實際照著點的步驟。

## 1. 建立 workflow

1. 打開 n8n。
2. 點 `New Workflow`。
3. 命名，例如：
   - `AI Investment Research Daily Pipeline`

## 2. 加 Schedule Trigger

1. 新增 `Schedule Trigger` node。
2. 設定每日觸發時間。
3. 建議：
   - 每天 07:00

## 3. 加 HTTP Request node

1. 新增 `HTTP Request` node。
2. Method 選 `POST`。
3. URL 填：

```text
https://<你的後端網址>/pipeline/run
```

如果是本機開發：

```text
http://localhost:8000/pipeline/run
```

## 4. Header 設定

加這兩個 header：

```text
Authorization: Bearer {{$env.API_AUTH_TOKEN}}
Content-Type: application/json
```

注意：

- 不要把 token 寫死在 workflow JSON
- 不要把 `SUPABASE_SERVICE_ROLE_KEY` 放進 n8n
- n8n 只需要 API token，不需要 Supabase service key

## 5. Body 設定

請把 request body 設成：

```json
{
  "scope": "all",
  "source_mode": "hybrid",
  "summarizer_mode": "auto",
  "ingestion_dry_run": false,
  "promotion_dry_run": false
}
```

這代表：

- 先跑整批追蹤宇宙
- 來源層用 `hybrid`
- 摘要器先用 `auto`
- ingestion 寫 staging
- promotion 寫 production

## 6. 加 IF node

在 HTTP Request 後面加 `IF` node，判斷 `{{$json.status}}`。

### success

```text
status = success
```

處理：

- 正常結束
- 寫 log

### partial_success

```text
status = partial_success
```

處理：

- 通知管理者檢查
- 建議附上 pipeline report 路徑

### failed

```text
status = failed
```

處理：

- 發警報
- 停止後續流程

## 7. n8n 應該讀哪些欄位

從 `/pipeline/run` 回傳內容，n8n 至少要看：

- `status`
- `message`
- `data.pipeline_report`
- `data.collect_result`
- `data.ingestion_result`
- `data.promotion_result`
- `errors`

## 8. 你要知道的角色邊界

- n8n：排程與觸發
- FastAPI：接收命令與包裝後端流程
- LangGraph Collector：研究與收集大腦
- ingestion：把 output packets 寫進 Supabase staging
- promotion：把 staging 推進 production
- Supabase：正式資料中心
- 前端：只讀 production views

## 9. 失敗時先檢查什麼

如果 n8n 收到 `failed` 或 `partial_success`，先看這些：

1. `API_AUTH_TOKEN` 有沒有設
2. FastAPI 有沒有真的啟動
3. 後端 `SUPABASE_URL` 有沒有設
4. 後端 `SUPABASE_SERVICE_ROLE_KEY` 有沒有設
5. `output/` 有沒有寫出檔案
6. `output/logs/` 裡的 pipeline report 有沒有產生

