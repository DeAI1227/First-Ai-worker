# Supabase Write Path Checklist

## Official write path

```text
Collector output JSON
→ ingestion write mode
→ staging tables
→ promotion write mode
→ production tables
→ frontend views
```

## Environment variables to verify

- `SUPABASE_URL`
- `SUPABASE_SERVICE_ROLE_KEY`
- `VITE_SUPABASE_URL`
- `VITE_SUPABASE_ANON_KEY`

## What to confirm

- Ingestion can write to staging without crashing on packet-level failures.
- Promotion can move staging rows into production tables and relation tables.
- Production views are available for the future frontend.
- The frontend reads only production views.
- No fake "no news" event is generated for empty stock coverage.

