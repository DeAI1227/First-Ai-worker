-- Query views for the production schema.
-- These are read models for the front-end and dashboard layer.

create or replace view view_dashboard_events as
select
  e.event_id,
  e.event_date,
  e.importance,
  e.scope,
  e.scope_name,
  e.title,
  e.ai_summary,
  e.possible_impact,
  e.risk_note,
  e.tags,
  e.quality_summary,
  e.source_urls
from events e
order by e.event_date desc, e.created_at desc;

create or replace view view_industry_cards as
select
  er.relation_value as industry_name,
  count(*) as recent_event_count,
  count(*) filter (where e.importance = 'critical') as critical_count,
  count(*) filter (where e.importance = 'important') as important_count,
  max(e.event_date) as latest_event_date
from event_relations er
join events e on e.event_id = er.event_id
where er.relation_type = 'industry'
group by er.relation_value;

create or replace view view_stock_cards as
select
  er.relation_value as stock_code,
  s.stock_name,
  array_agg(distinct si.industry_name order by si.industry_name) filter (where si.industry_name is not null) as related_industries,
  count(*) as recent_event_count,
  max(e.event_date) as latest_event_date
from event_relations er
join events e on e.event_id = er.event_id
left join stocks s on s.stock_code = er.relation_value
left join stock_industries si on si.stock_code = er.relation_value
where er.relation_type = 'stock'
group by er.relation_value, s.stock_name;

create or replace view view_macro_events as
select
  e.event_id,
  e.event_date,
  e.importance,
  e.scope,
  e.scope_name,
  e.title,
  e.ai_summary,
  e.possible_impact,
  e.risk_note,
  e.tags,
  e.source_urls
from events e
left join event_relations er on er.event_id = e.event_id
where e.scope = 'macro'
   or er.relation_type = 'macro_topic';

create or replace view view_institution_watch_events as
select
  e.event_id,
  e.event_date,
  e.importance,
  e.scope,
  e.scope_name,
  e.title,
  e.ai_summary,
  e.possible_impact,
  e.risk_note,
  e.tags,
  e.source_urls
from events e
left join event_relations er on er.event_id = e.event_id
where e.scope in ('institution', 'institution_watch')
   or er.relation_type = 'institution_watch';

create or replace view view_unread_counts as
select
  urs.user_id,
  urs.item_type,
  count(*) filter (where coalesce(urs.is_read, false) = false) as unread_count
from user_read_status urs
group by urs.user_id, urs.item_type;

create or replace view view_recent_reports as
select
  r.report_id,
  r.report_date,
  r.report_type,
  r.scope,
  r.scope_name,
  r.importance,
  r.report_title,
  r.quality_summary
from reports r
order by r.report_date desc, r.created_at desc;
