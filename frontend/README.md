# AI 投資研究終端前端

這是一個 **Supabase-first**、**Supabase-only** 的靜態前端，目標是把研究情報用乾淨、現代、深色的介面呈現出來。

## 前端邊界

- 前端只讀 Supabase production views
- 前端不讀 Python 程式
- 前端不讀 `output/` JSON
- 前端不直接呼叫 Collector
- 沒有事件的股票由前端顯示 empty state
- 不產生「今日未找到重大更新」假事件
- �e�ݤ�Ū Python �{��
- �Ѳ��M�歶

## Supabase 資料來源

頁面對應的 views：

- 總覽頁 → `view_dashboard_events`
- 產業追蹤頁 → `view_industry_cards`
- 股票清單頁 → `view_stock_cards`
- 股票詳情頁 → `view_stock_detail_events`
- 大環境頁 → `view_macro_events`
- 大行關注頁 → `view_institution_watch_events`
- 研究報告頁 → `view_recent_reports`
- 未讀統計 → `view_unread_counts`

## 環境變數

```env
VITE_SUPABASE_URL=
VITE_SUPABASE_ANON_KEY=
VITE_DEFAULT_USER_ID=
```

- `VITE_SUPABASE_URL` 和 `VITE_SUPABASE_ANON_KEY` 是前端唯一需要的 Supabase 憑證
- 不可使用 `SUPABASE_SERVICE_ROLE_KEY`

## 本地開發

```bash
cd frontend
npm install
npm run dev
```

## 建置

```bash
cd frontend
npm run build
```

## GitHub Pages

這個前端可以部署到 GitHub Pages。部署 workflow 位於：

- [`.github/workflows/frontend-pages.yml`](../.github/workflows/frontend-pages.yml)

部署後，前端會以靜態站方式提供，並且只透過 Supabase 讀資料。

## 目錄說明

- `src/pages/`：頁面
- `src/components/`：共用 UI 元件
- `src/lib/`：Supabase client、query functions、types
- `src/hooks/`：共用 hooks
