# Frontend Query Contract

This document defines which Supabase production views the future frontend should query.

The future frontend reads Supabase only.
It does not read Python code or `output/` JSON directly.

## Page to view mapping

- 總覽頁 -> `view_dashboard_events`
- 產業追蹤頁 -> `view_industry_cards`
- 股票清單頁 -> `view_stock_cards`
- 股票詳情頁 -> `view_stock_detail_events`
- 大環境頁 -> `view_macro_events`
- 大行關注頁 -> `view_institution_watch_events`
- 研究報告頁 -> `view_recent_reports`
- 未讀統計 -> `view_unread_counts`

## Core data rules

- `stocks` is reference data.
- `events` is actual event data.
- Stocks without events still exist in `stocks`.
- The frontend should render empty states when a stock has no events.
- The backend must not generate fake "today no major update" events.

## Query intent by page

### 總覽頁

Read from `view_dashboard_events` for the latest curated event stream.

### 產業追蹤頁

Read from `view_industry_cards` for industry cards and summary counts.

### 股票清單頁

Read from `view_stock_cards` to show all 45 tracked stocks and their industry tags.

### 股票詳情頁

Read from `view_stock_detail_events` for the event stream of a specific stock.

### 大環境頁

Read from `view_macro_events` for macro-related events.

### 大行關注頁

Read from `view_institution_watch_events` for institution watch events.

### 研究報告頁

Read from `view_recent_reports` for the latest research reports.

### 未讀統計

Read from `view_unread_counts` and derive read state from `user_read_status`.

## Why this contract exists

The frontend should not infer page-level structure directly from raw tables.
These views provide stable read models that are easier to query, index, and evolve without changing the UI contract.
