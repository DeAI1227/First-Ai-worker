-- Dedupe historical duplicate research packets so the newest row survives.
-- Safe to re-run.

with ranked_events as (
  select id,
         row_number() over (
           partition by coalesce(raw_packet->>'source_url', source_urls->>0, event_id)
           order by created_at desc, event_id desc
         ) as rn
  from public.events
  where coalesce(raw_packet->>'source_url', source_urls->>0, event_id) is not null
    and coalesce(raw_packet->>'source_url', source_urls->>0, event_id) <> ''
)
delete from public.events e
using ranked_events r
where e.id = r.id
  and r.rn > 1;

with ranked_staging_events as (
  select id,
         row_number() over (
           partition by coalesce(raw_packet->>'source_url', source_urls->>0, event_id)
           order by created_at desc, event_id desc
         ) as rn
  from public.staging_events
  where coalesce(raw_packet->>'source_url', source_urls->>0, event_id) is not null
    and coalesce(raw_packet->>'source_url', source_urls->>0, event_id) <> ''
)
delete from public.staging_events e
using ranked_staging_events r
where e.id = r.id
  and r.rn > 1;
