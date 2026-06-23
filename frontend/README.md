# AI 投資研究終端 Frontend

這是一個全新的 Supabase-first 前端專案，用來閱讀研究事件、產業卡片、股票事件流、研究報告與未讀狀態。

## 定位

- 這不是報價 App
- 這不是技術分析工具
- 這不是 Python 專案的視覺外殼
- 前端不讀 Python 程式
- 前端不讀 `output/` JSON
- 這是只讀 Supabase production views 的研究終端

## 技術棧

- React
- TypeScript
- Vite
- Tailwind CSS
- Supabase JS
- React Router
- lucide-react

## 環境變數

請設定：

```text
VITE_SUPABASE_URL
VITE_SUPABASE_ANON_KEY
VITE_DEFAULT_USER_ID
```

`VITE_DEFAULT_USER_ID` 可選，用於本機測試未讀數。

## 開發

```bash
cd frontend
npm install
npm run dev
```

## 打包

```bash
cd frontend
npm run build
```

## 資料來源規則

- 總覽頁 → `view_dashboard_events`
- 產業追蹤頁 → `view_industry_cards`
- 股票清單頁 → `view_stock_cards`
- 股票詳情頁 → `view_stock_detail_events`
- 大環境頁 → `view_macro_events`
- 大行關注頁 → `view_institution_watch_events`
- 研究報告頁 → `view_recent_reports`
- 未讀統計 → `view_unread_counts`

## 已讀 / 未讀

- 使用 `user_read_status`
- 不要把 read / unread 寫進 `events` 或 `reports`
- 不要在前端自己推導假資料

## 空狀態規則

- 股票沒有事件時，前端顯示 empty state
- 不要產生「今日未找到重大更新」假事件
- 股票清單仍然顯示 45 檔 reference data

## 專案結構

- `src/lib/`：Supabase client、types、queries、read status
- `src/components/`：版面與共用 UI
- `src/pages/`：各頁面
- `src/hooks/`：共用資料載入 hooks
