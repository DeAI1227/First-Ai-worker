# Supabase Views Contract

This pack is the data contract for the future frontend that reads Supabase only.

The frontend should read from views instead of assembling page data from raw tables.

## Page to view mapping

- 總覽頁 -> `view_dashboard_events`
- 產業追蹤頁 -> `view_industry_cards`
- 股票清單頁 -> `view_stock_cards`
- 股票詳情頁 -> `view_stock_detail_events`
- 大環境頁 -> `view_macro_events`
- 大行關注頁 -> `view_institution_watch_events`
- 研究報告頁 -> `view_recent_reports`
- 未讀統計 -> `view_unread_counts`

## View details

### `view_dashboard_events`

- Purpose: latest curated event stream for the dashboard.
- Fields: `event_id`, `event_date`, `importance`, `scope`, `scope_name`, `ai_summary`, `possible_impact`, `risk_note`, `tags`, `quality_summary`, `source_urls`
- Frontend display: event cards, summary rows, or a compact feed.
- Empty state: show an empty dashboard feed state if the view returns no rows.

### `view_industry_cards`

- Purpose: industry tracking cards and summary counts.
- Fields: `industry_name`, `recent_event_count`, `critical_count`, `important_count`, `latest_event_date`
- Frontend display: one card per industry with counts and latest date.
- Empty state: the six industries still render because the view is anchored on `industries`; counts can be zero.

### `view_stock_cards`

- Purpose: tracked stock list and industry tags.
- Fields: `stock_code`, `stock_name`, `related_industries`, `recent_event_count`, `latest_event_date`
- Frontend display: stock list rows or cards with industry chips.
- Empty state: all tracked stocks still render because the source is `stocks` reference data.
- Important: stocks without events still appear here.

### `view_stock_detail_events`

- Purpose: event stream for a specific stock.
- Fields: `stock_code`, `stock_name`, `event_id`, `event_date`, `importance`, `ai_summary`, `possible_impact`, `risk_note`, `tags`, `source_urls`
- Frontend display: detail-page timeline or event list filtered by stock.
- Empty state: render a stock-specific empty state when no rows are returned.

### `view_macro_events`

- Purpose: macro event stream.
- Fields: `event_id`, `event_date`, `importance`, `scope`, `scope_name`, `ai_summary`, `possible_impact`, `risk_note`, `tags`, `quality_summary`, `source_urls`
- Frontend display: macro cards or a filtered feed.
- Empty state: show empty state if no macro events exist.

### `view_institution_watch_events`

- Purpose: institution watch event stream.
- Fields: `event_id`, `event_date`, `importance`, `scope`, `scope_name`, `ai_summary`, `possible_impact`, `risk_note`, `tags`, `quality_summary`, `source_urls`
- Frontend display: large-cap / institution watch feed.
- Empty state: show empty state if no rows are returned.

### `view_recent_reports`

- Purpose: latest research reports.
- Fields: `report_id`, `report_date`, `report_type`, `importance`, `scope`, `scope_name`, `report_title`, `report_body`, `quality_summary`
- Frontend display: report cards or knowledge-base style list.
- Empty state: show empty state when no reports are available.

### `view_unread_counts`

- Purpose: unread counters derived from `user_read_status`.
- Fields: `user_id`, `unread_event_count`, `unread_report_count`, `unread_total_count`
- Frontend display: badge counts and top-bar unread indicators.
- Empty state: show zeros when there is no read-status row for a user.

## Core guardrails

- Stocks without events still exist in `stocks`.
- The frontend should render empty states when a stock has no events.
- The backend must not generate fake "today no major update" events.
- Do not generate fake no-news events.
