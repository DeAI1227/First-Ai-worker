# n8n Ingestion Workflow 設計

這份文件描述未來 n8n 如何觸發 Collector ingestion、讀取 batch report、判斷執行結果並通知。
它是設計文件，不會直接建立 n8n workflow，也不會連到 LINE 或前端。

## 整體流程

```text
Cron Trigger
↓
Execute Command 或 HTTP Request
↓
執行 ingestion write mode
↓
讀取 output/ingestion_logs 最新 batch report
↓
判斷 status
↓
success：正常結束
partial_success：發出檢查通知
failed：發出警報通知
```

## n8n 執行方式

### 方案 1：Execute Command

適合本機或自架 n8n。

```bash
python -m ingestion.ingest_outputs --input output/
```

這種方式的優點是最直接，n8n 不需要額外 API 層。
它適合早期 MVP 或內網環境。

### 方案 2：HTTP API

未來可以由 FastAPI 包一層 ingestion 入口。

```text
POST /ingestion/run
```

這次只做設計，不實作 API。
HTTP 版的優點是更容易水平擴充，也比較適合雲端部署。

## batch report 判斷規則

n8n 讀到 batch report 後，主要看 `status`：

```text
status = success
status = partial_success
status = failed
```

分流規則如下：

```text
success：
- 不通知，或只記錄執行紀錄

partial_success：
- 通知：有部分 packet 寫入失敗，需要檢查

failed：
- 通知：整批 ingestion 失敗，需要立即檢查
```

## n8n 需要讀取的 batch report 欄位

n8n 只需要讀取摘要欄位，不需要解析完整 packet。

- `batch_id`
- `started_at`
- `finished_at`
- `mode`
- `input_path`
- `files_scanned`
- `packets_loaded`
- `mapped`
- `written`
- `failed`
- `errors`
- `status`

## 通知內容格式

### partial_success

```text
AI 投資研究終端 ingestion 部分成功

Batch ID：
Status：partial_success
Loaded：
Written：
Failed：
Errors：

請檢查 output/ingestion_logs 的 batch report。
```

### failed

```text
AI 投資研究終端 ingestion 失敗

Batch ID：
Status：failed
Loaded：
Written：
Failed：
Errors：

請立即檢查 Supabase key、staging schema、packet 格式或 output JSON。
```

## 安全設計

- 不要把 Supabase service role key 寫進 n8n 節點內容
- 請使用 n8n credentials 或環境變數
- 若使用 HTTP API，必須加 auth token
- webhook 不應公開暴露
- batch report 可以給 n8n 讀，但不要把 service key 寫入 report
- errors 中不要記錄敏感 key

## 未來 n8n workflow 節點草圖

### Execute Command 版

```text
Cron Trigger
↓
Execute Command: run ingestion
↓
Read File: latest batch report
↓
Code Node: parse JSON
↓
IF Node: status == success
├─ success path
├─ partial_success path
└─ failed path
```

### HTTP API 版

```text
Cron Trigger
↓
HTTP Request: POST /ingestion/run
↓
IF Node: response.status
├─ success
├─ partial_success
└─ failed
```

## 與 Supabase README 的關係

這份文件會在 [supabase/README.md](./README.md) 中被引用，作為未來 n8n 自動化排程與通知的設計入口。

