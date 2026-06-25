# Firecrawl Hosted API Guide

本專案現在使用 **Firecrawl Hosted API**，不再自架 Firecrawl。

## 為什麼改成 hosted API

- 不再依賴本機 `localhost:3002`
- 不再維護 Firecrawl 的 Docker / Redis / RabbitMQ / Playwright / Postgres
- 更符合目前主線：GitHub Actions / Render / Supabase 的雲端執行方式

## 必填環境變數

在後端 `.env` 填入：

```env
FIRECRAWL_BASE_URL=https://api.firecrawl.dev
FIRECRAWL_API_KEY=
SEARCH_PROVIDER=firecrawl
```

說明：

- `FIRECRAWL_BASE_URL` 指向 Firecrawl hosted API base URL
- `FIRECRAWL_API_KEY` 建議提供正式 API key
- `SEARCH_PROVIDER=firecrawl` 代表搜尋層優先走 Firecrawl

## 後端如何使用

搜尋 provider 會對 Firecrawl 發送：

```text
POST https://api.firecrawl.dev/v2/search
```

Header 會使用：

```text
Authorization: Bearer <FIRECRAWL_API_KEY>
```

如果 Firecrawl 暫時不可用，系統會 fallback 到 mock search，不會讓整條 collector pipeline 直接崩潰。

## 目前主線

```text
Collector
→ Firecrawl Hosted API
→ raw sources
→ quality scoring
→ summarizer
→ output packets
→ ingestion
→ Supabase staging
→ promotion
→ Supabase production / views
```

## 不再使用的路線

以下不再是正式主線：

- 本機 `docker compose up`
- `http://localhost:3002`
- Firecrawl self-host
- Firecrawl on Render 多服務自架

如果未來真的要回頭自架，請視為新的基礎設施專案，不要再把它混進目前 MVP 主線。
