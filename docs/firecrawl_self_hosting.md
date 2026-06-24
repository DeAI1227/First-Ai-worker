# Firecrawl Self-Hosting Guide

這份文件只說一件事：**怎麼把 Firecrawl 當成免費的搜尋來源跑起來**。

## 1. Clone Firecrawl

如果你還沒把 Firecrawl 放在本機，可以先 clone：

```bash
gh repo clone firecrawl/firecrawl
```

## 2. 進入 Firecrawl 專案

```bash
cd firecrawl
```

## 3. 建立 `.env`

根據 Firecrawl 的 `SELF_HOST.md`，最少需要這些值：

```env
PORT=3002
HOST=0.0.0.0
USE_DB_AUTHENTICATION=false
BULL_AUTH_KEY=CHANGEME
```

> 如果你只是本機測試 collector 的搜尋流程，先用最小配置即可。  
> `OPENAI_API_KEY` 不是本專案主線必填。

## 4. 啟動 Firecrawl

```bash
docker compose build
docker compose up
```

啟動後，Firecrawl API 預設可從這裡使用：

```text
http://localhost:3002
```

## 5. 回到 collector 專案設定 env

在 `investment_research_collector/.env` 填入：

```env
FIRECRAWL_BASE_URL=http://localhost:3002
FIRECRAWL_API_KEY=
SEARCH_PROVIDER=firecrawl
```

## 6. 驗證方式

先跑這些：

```bash
python main.py --source-mode search --search-provider firecrawl
python -m unittest discover -s tests -p "test_*.py" -v
```

如果 Firecrawl 還沒起來，collector 會 fallback 到 mock；它不會把流程假裝成 Firecrawl 成功。

