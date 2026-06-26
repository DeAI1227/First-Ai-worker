-- Query views for the production schema.
-- These are read models for the frontend. They intentionally filter mock
-- sources and dedupe noisy runs so the UI shows research summaries, not every
-- raw article as a separate card.

create or replace view view_dashboard_events as
with clean_events as (
  select
    e.*,
    row_number() over (
      partition by e.scope, e.scope_name, e.event_date
      order by e.created_at desc, e.event_id desc
    ) as row_rank
  from events e
  where coalesce(e.source_urls::text, '') not like '%example.com%'
    and coalesce(e.source_urls::text, '') not like '%/mock/%'
)
select
  event_id,
  event_date,
  importance,
  scope,
  scope_name,
  ai_summary,
  possible_impact,
  risk_note,
  tags,
  quality_summary,
  source_urls
from clean_events
where row_rank = 1
order by event_date desc, created_at desc;

create or replace view view_industry_cards as
with clean_events as (
  select
    e.*,
    row_number() over (
      partition by e.scope, e.scope_name, e.event_date
      order by e.created_at desc, e.event_id desc
    ) as row_rank
  from events e
  where coalesce(e.source_urls::text, '') not like '%example.com%'
    and coalesce(e.source_urls::text, '') not like '%/mock/%'
),
latest_events as (
  select
    er.relation_value as industry_name,
    count(*) as recent_event_count,
    count(*) filter (where e.importance = 'critical') as critical_count,
    count(*) filter (where e.importance = 'important') as important_count,
    max(e.event_date) as latest_event_date
  from event_relations er
  join clean_events e on e.event_id = er.event_id and e.row_rank = 1
  where er.relation_type = 'industry'
  group by er.relation_value
)
select
  i.industry_name,
  coalesce(le.recent_event_count, 0) as recent_event_count,
  coalesce(le.critical_count, 0) as critical_count,
  coalesce(le.important_count, 0) as important_count,
  le.latest_event_date
from industries i
left join latest_events le on le.industry_name = i.industry_name
order by i.industry_name;

create or replace view view_stock_cards as
with clean_events as (
  select
    e.*,
    row_number() over (
      partition by er.relation_value, e.event_date
      order by e.created_at desc, e.event_id desc
    ) as row_rank
  from events e
  join event_relations er on er.event_id = e.event_id and er.relation_type = 'stock'
  where coalesce(e.source_urls::text, '') not like '%example.com%'
    and coalesce(e.source_urls::text, '') not like '%/mock/%'
),
latest_events as (
  select
    er.relation_value as stock_code,
    count(*) as recent_event_count,
    max(e.event_date) as latest_event_date
  from event_relations er
  join clean_events e on e.event_id = er.event_id and e.row_rank = 1
  where er.relation_type = 'stock'
  group by er.relation_value
)
select
  s.stock_code,
  s.stock_name,
  coalesce(
    (
      select jsonb_agg(si.industry_name order by si.industry_name)
      from stock_industries si
      where si.stock_code = s.stock_code
    ),
    '[]'::jsonb
  ) as related_industries,
  coalesce(le.recent_event_count, 0) as recent_event_count,
  le.latest_event_date
from stocks s
left join latest_events le on le.stock_code = s.stock_code
order by s.stock_code;

create or replace view view_stock_detail_events as
with clean_stock_events as (
  select
    er.relation_value as stock_code,
    s.stock_name,
    e.event_id,
    e.event_date,
    e.importance,
    e.ai_summary,
    e.possible_impact,
    e.risk_note,
    e.tags,
    e.source_urls,
    e.created_at,
    row_number() over (
      partition by er.relation_value, e.event_date
      order by e.created_at desc, e.event_id desc
    ) as row_rank
  from events e
  join event_relations er on er.event_id = e.event_id and er.relation_type = 'stock'
  left join stocks s on s.stock_code = er.relation_value
  where coalesce(e.source_urls::text, '') not like '%example.com%'
    and coalesce(e.source_urls::text, '') not like '%/mock/%'
)
select
  stock_code,
  stock_name,
  event_id,
  event_date,
  importance,
  ai_summary,
  possible_impact,
  risk_note,
  tags,
  source_urls
from clean_stock_events
where row_rank = 1
order by stock_code, event_date desc, created_at desc;

create or replace view view_macro_events as
with clean_macro_events as (
  select
    e.*,
    row_number() over (
      partition by e.scope_name, e.event_date
      order by e.created_at desc, e.event_id desc
    ) as row_rank
  from events e
  where e.event_type = 'macro'
    and coalesce(e.source_urls::text, '') not like '%example.com%'
    and coalesce(e.source_urls::text, '') not like '%/mock/%'
)
select
  event_id,
  event_date,
  importance,
  scope,
  scope_name,
  ai_summary,
  possible_impact,
  risk_note,
  tags,
  quality_summary,
  source_urls
from clean_macro_events
where row_rank = 1
order by event_date desc, created_at desc;

create or replace view view_institution_watch_events as
with clean_institution_events as (
  select
    e.*,
    row_number() over (
      partition by e.scope_name, e.event_date
      order by e.created_at desc, e.event_id desc
    ) as row_rank
  from events e
  where e.event_type = 'institution'
    and coalesce(e.source_urls::text, '') not like '%example.com%'
    and coalesce(e.source_urls::text, '') not like '%/mock/%'
)
select
  event_id,
  event_date,
  importance,
  scope,
  scope_name,
  ai_summary,
  possible_impact,
  risk_note,
  tags,
  quality_summary,
  source_urls
from clean_institution_events
where row_rank = 1
order by event_date desc, created_at desc;

create or replace view view_recent_reports as
select
  r.report_id,
  r.report_date,
  r.report_type,
  r.importance,
  r.scope,
  r.scope_name,
  r.report_title,
  r.report_body,
  r.quality_summary
from reports r
order by r.report_date desc, r.created_at desc;

create or replace view view_unread_counts as
select
  user_id,
  sum(case when item_type = 'event' and not is_read then 1 else 0 end) as unread_event_count,
  sum(case when item_type = 'report' and not is_read then 1 else 0 end) as unread_report_count,
  sum(case when not is_read then 1 else 0 end) as unread_total_count
from user_read_status
group by user_id;
