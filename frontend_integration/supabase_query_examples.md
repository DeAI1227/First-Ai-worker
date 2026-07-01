# Supabase Query Examples

These examples use the Supabase JS client.

## Query dashboard events

```ts
const { data, error } = await supabase
  .from("view_dashboard_events")
  .select("*")
  .order("event_date", { ascending: false })
  .limit(20);
```

## Query industry cards

```ts
const { data, error } = await supabase
  .from("view_industry_cards")
  .select("*")
  .order("industry_name", { ascending: true });
```

## Query stock cards

```ts
const { data, error } = await supabase
  .from("view_stock_cards")
  .select("*")
  .order("stock_code", { ascending: true });
```

## Query a single stock event stream

```ts
const { data, error } = await supabase
  .from("view_stock_detail_events")
  .select("*")
  .eq("stock_code", "6230")
  .order("event_date", { ascending: false });
```

## Query macro events

```ts
const { data, error } = await supabase
  .from("view_macro_events")
  .select("*")
  .order("event_date", { ascending: false });
```

## Query institution watch events

```ts
const { data, error } = await supabase
  .from("view_institution_watch_events")
  .select("*")
  .order("event_date", { ascending: false });
```

## Query recent reports

```ts
const { data, error } = await supabase
  .from("view_recent_reports")
  .select("*")
  .order("report_date", { ascending: false })
  .limit(20);
```

## Query unread counts

```ts
const { data, error } = await supabase
  .from("view_unread_counts")
  .select("*")
  .eq("user_id", userId)
  .maybeSingle();
```

## Query latest crawl run

```ts
const { data, error } = await supabase
  .from("view_latest_crawl_run")
  .select("*")
  .maybeSingle();
```

## Mark an event as read

```ts
const { error } = await supabase.from("user_read_status").upsert({
  user_id: userId,
  item_type: "event",
  item_id: eventId,
  is_read: true,
  read_at: new Date().toISOString(),
});
```

## Mark a report as read

```ts
const { error } = await supabase.from("user_read_status").upsert({
  user_id: userId,
  item_type: "report",
  item_id: reportId,
  is_read: true,
  read_at: new Date().toISOString(),
});
```

## Notes

- `stocks` is reference data.
- `events` contains real events only.
- Stocks with no events still appear in `view_stock_cards`.
- The dashboard source-quality card should read the latest crawl run summary, not a random event row.
- Do not create fake "no news" events in the backend.
