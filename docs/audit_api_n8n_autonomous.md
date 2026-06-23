# API、n8n、自動執行能力全面巡檢

## 1. 整體結論：warning

目前後端與 n8n 接線結構是正確的，而且 `collect → ingestion → promotion` 的同步主流程已經存在；`/pipeline/run` 也不是假成功，會真的往下呼叫各階段。

但這一版在我這個工作區的實際執行結果仍是 **failed**，主因是：

- `SUPABASE_URL` 缺失
- `SUPABASE_SERVICE_ROLE_KEY` 缺失
- 來源端 RSS / HTTP 設定仍不完整，且有外部 RSS 站點回 `401`

所以目前屬於「架構已通、實跑未完全接線」的狀態，還不能算 autonomous ready。

---

## 2. FastAPI endpoints 是否完整

目前可確認的 endpoint 如下：

- `GET /health`
- `POST /collect/run`
- `POST /ingestion/run`
- `POST /promotion/run`
- `POST /pipeline/run`

文件裡另外有保留未來 async job 的位置，但目前沒有真的實作 job queue 或 `/pipeline/status`。

### 目前狀態

- `/health`：存在，且不需要 token
- 其餘 protected endpoints：存在，且需要 `Authorization: Bearer <API_AUTH_TOKEN>`
- `/pipeline/status`：未實作，僅作 future 預留

---

## 3. /pipeline/run 是否真的跑 collect → ingestion → promotion

是，**真的有依序跑**。

我實際執行 `python scripts/run_autonomous_once.py`，結果顯示：

- `collect_ran: true`
- `ingestion_ran: true`
- `promotion_ran: true`

但最後整體狀態是：

- `status: failed`
- `autonomous_ready: false`
- `wrote_to_supabase: false`

### 失敗原因

執行輸出中可見：

- `rss fetch failed for https://www.reuters.com/business/rss: HTTP Error 401`
- `rss feeds are not configured`
- `http urls are not configured`
- `Missing required environment variables: SUPABASE_URL, SUPABASE_SERVICE_ROLE_KEY`

這代表流程有跑完，但沒有真的成功寫進 Supabase。

---

## 4. auth 是否安全

目前 auth 設計是合理的：

- `/health` 可不帶 token
- `/collect/run`、`/ingestion/run`、`/promotion/run`、`/pipeline/run` 都需要 `Authorization: Bearer <API_AUTH_TOKEN>`
- `.env.example` 有 `API_AUTH_TOKEN=`
- token 沒有硬寫進程式

### 結論

auth 基本上是安全的，至少在結構上沒有看到把 token 寫死在 repo 的問題。

---

## 5. n8n workflow 是否存在

有，已經存在：

- `n8n_workflows/autonomous_daily_pipeline.json`

它的內容是最小可用版本：

- Schedule Trigger
- HTTP Request `POST /pipeline/run`
- IF node 根據 `status` 分流

### 角色定位

n8n 目前是 **觸發器與分流器**，不是研究邏輯執行者。

---

## 6. n8n 是否能呼叫 /pipeline/run

可以，但前提是：

- FastAPI 有啟動
- `API_AUTH_TOKEN` 有設定
- HTTP Request 使用 Bearer token

文件與 workflow 都已經把這件事設計好，n8n 只需要發出請求與看回應狀態，不需要自己做研究判斷。

---

## 7. run_autonomous_once.py 是否可用

有這支腳本，而且它**可以手動啟動完整 pipeline**。

實際執行後，腳本沒有假裝成功，而是誠實回傳 pipeline 結果：

- `collect_ran: true`
- `ingestion_ran: true`
- `promotion_ran: true`
- `wrote_to_supabase: false`
- `status: failed`
- `autonomous_ready: false`

### 判讀

這支腳本是可用的，但在目前環境下還不能算成功寫入 Supabase。

---

## 8. 是否能真的寫 Supabase

這次實跑結果顯示：**不能**。

原因是缺少：

- `SUPABASE_URL`
- `SUPABASE_SERVICE_ROLE_KEY`

這不是假成功，pipeline 有誠實失敗。

---

## 9. 缺哪些 env

從這次實際輸出確認缺少：

- `SUPABASE_URL`
- `SUPABASE_SERVICE_ROLE_KEY`

`API_AUTH_TOKEN` 沒有在這次 pipeline 輸出中被列為缺失項目。

---

## 10. 目前是否 autonomous ready

**不是。**

理由很直接：

- collect / ingestion / promotion 雖然都有跑
- 但 Supabase 寫入沒有完成
- 來源配置還不完整
- 外部 RSS 有 401

### 所以現在的狀態是

- 架構 ready
- 流程 ready
- 實際部署接線還沒完成

---

## 11. 測試結果

我已確認測試通過：

- `python -m unittest discover -s tests -p "test_*.py" -v`

結果：

- `213` tests passed
- `OK`

---

## 12. compileall 結果

我已確認：

- `python -m compileall .`

結果：

- 成功
- exit code `0`

---

## 13. 必須人工處理的事項

1. 補上正式環境變數：
   - `SUPABASE_URL`
   - `SUPABASE_SERVICE_ROLE_KEY`

2. 確認 collector 的真實來源配置：
   - RSS feeds
   - HTTP URLs
   - 必要時調整 fallback 策略

3. 檢查 RSS 來源是否可穩定讀取
   - 這次有看到 Reuters RSS 回 `401`
   - 這表示來源端或抓取方式需要重新配置

4. 觀察 ingestion 掃描範圍
   - 這次 run 中出現大量 `Unknown packet type` 警告
   - 代表 ingestion 目前可能掃到一些非 packet JSON
   - 這不一定是致命錯誤，但會增加噪音，後續應收斂 input 範圍或改善 detector

5. 確認 production / staging / promotion 的實際寫入權限

6. 確認 n8n workflow 使用的 `API_AUTH_TOKEN` 與後端一致

---

## 14. 建議下一步

1. 先把 Supabase env 補齊
2. 把可用的 RSS / HTTP 來源補進設定
3. 再跑一次 `python scripts/run_autonomous_once.py`
4. 若要讓 n8n 正式接管，直接用 `n8n_workflows/autonomous_daily_pipeline.json`
5. 寫入成功後，再檢查 Supabase production views 是否能被新前端直接讀到

---

## 補充觀察

- 從結構來看，後端主線是正確的：
  `LangGraph Collector → output packets → ingestion → Supabase staging → promotion → Supabase production/views`
- 前端仍應維持只讀 Supabase views
- 前端不應直接讀 Python output JSON
- 不應產生「今日未找到重大更新」假 event
