# GitHub Actions 排程說明

GitHub Actions 是本專案目前正式使用的免費雲端排程器。

## 為什麼不再只用一條 workflow

原本把 `daily + stocks + three_day + ingestion + promotion` 全塞進同一條 job，會讓單次 GitHub Actions 執行時間過長，容易出現：

- 看起來像卡住
- 單次排程太久
- 排程觀察困難
- 一段變慢時整包都延後

因此現在改成 **三條較小的正式排程**。

## 目前正式 workflow

### 1. Daily Core Pipeline

- 檔案：`.github/workflows/daily-core.yml`
- 時間：07:00 Asia/Taipei
- 內容：
  - `macro`
  - `industries`
  - `institution_watch`
  - `ingestion write`
  - `promotion write`

這條是主線，優先確保每天早上有核心研究資料進 Supabase。

### 2. Stock Pipeline

- 檔案：`.github/workflows/stock-pipeline.yml`
- 時間：07:20 Asia/Taipei
- 內容：
  - `stocks`
  - `ingestion write`
  - `promotion write`

股票批次最重，所以獨立成單獨 workflow，避免拖慢主線。

### 3. Three-Day Refresh

- 檔案：`.github/workflows/three-day-refresh.yml`
- 時間：07:40 Asia/Taipei
- 內容：
  - `three_day` 產業報告
  - `three_day` macro 報告
  - `ingestion write`
  - `promotion write`

三日報告仍然每天刷新，但不再壓在 daily core 裡面。

## 執行方式

這三條 workflow 都：

1. checkout repository
2. setup Python
3. install dependencies
4. validate secrets
5. 直接在 GitHub runner 執行本地 Python pipeline script

也就是說，**GitHub Actions 排程主線不再依賴 Render 去接同步長請求**。

## 與 Render 的關係

Render 上的 FastAPI 仍然保留，適合：

- 手動觸發 `/collect/run`
- 手動觸發 `/pipeline/run`
- 管理者測試或 smoke check

但正式的每日排程主線，現在由 GitHub Actions 直接跑本地 pipeline script。

## 與 Supabase 的關係

這次 workflow 拆分：

- **不需要改 Supabase schema**
- staging / production / views 都維持原狀
- 只是把「哪一批資料何時寫入 Supabase」切成三段

## 需要的 GitHub Secrets

### Daily Core / Stock Pipeline

需要：

- `SUPABASE_URL`
- `SUPABASE_SERVICE_ROLE_KEY`
- `GEMINI_API_KEY`
- `GEMINI_MODEL`
- `AGNES_API_KEY`
- `AGNES_API_URL` 或 `AGNES_BASE_URL`
- `AGNES_MODEL`
- `FIRECRAWL_BASE_URL`
- `FIRECRAWL_API_KEY`

### Three-Day Refresh

需要：

- `SUPABASE_URL`
- `SUPABASE_SERVICE_ROLE_KEY`

三日報告是基於既有 daily digest 聚合，所以不依賴 Firecrawl 搜尋抓文。

## 搜尋 provider 空位

目前正式支援的搜尋 provider：

- `firecrawl`
- `tavily`
- `serpapi`
- `mock`
- `auto`

`.env.example` 已預留未來空位：

- `BRAVE_SEARCH_API_KEY`
- `EXA_API_KEY`

但目前 workflow 與程式主線還沒有正式切到這兩個 provider。

## 時區說明

GitHub Actions 的 cron 仍以 UTC 表示，因此：

- 07:00 Asia/Taipei = `0 23 * * *`
- 07:20 Asia/Taipei = `20 23 * * *`
- 07:40 Asia/Taipei = `40 23 * * *`

## 如果某條 workflow 失敗

- `daily-core` 失敗：先看核心資料是否缺失
- `stock-pipeline` 失敗：股票事件更新會延後，但主線大環境與產業仍可存在
- `three-day-refresh` 失敗：報告更新延後，但 daily 事件流不會因此完全中斷

這就是拆開後最大的好處：**某一段慢，不會拖死整包。**
