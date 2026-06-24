-- Supabase production schema for Investment Research Collector
-- This schema receives curated records after staging validation and promotion.

create extension if not exists pgcrypto;

create table if not exists industries (
  id uuid primary key default gen_random_uuid(),
  industry_id text not null unique,
  industry_name text not null unique,
  enabled boolean not null default true,
  keywords_zh jsonb not null default '[]'::jsonb,
  keywords_en jsonb not null default '[]'::jsonb,
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now()
);

create table if not exists stocks (
  id uuid primary key default gen_random_uuid(),
  stock_code text not null unique,
  stock_name text not null,
  enabled boolean not null default true,
  keywords_zh jsonb not null default '[]'::jsonb,
  keywords_en jsonb not null default '[]'::jsonb,
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now()
);

create table if not exists stock_industries (
  id uuid primary key default gen_random_uuid(),
  stock_code text not null references stocks (stock_code) on delete cascade on update cascade,
  industry_name text not null references industries (industry_name) on delete cascade on update cascade,
  created_at timestamptz not null default now(),
  unique (stock_code, industry_name)
);

create index if not exists idx_stock_industries_stock_code on stock_industries (stock_code);
create index if not exists idx_stock_industries_industry_name on stock_industries (industry_name);

create table if not exists macro_topics (
  id uuid primary key default gen_random_uuid(),
  topic_id text not null unique,
  topic_name text not null unique,
  enabled boolean not null default true,
  keywords_zh jsonb not null default '[]'::jsonb,
  keywords_en jsonb not null default '[]'::jsonb,
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now()
);

create table if not exists institution_watch_stocks (
  id uuid primary key default gen_random_uuid(),
  stock_code text not null unique references stocks (stock_code) on delete cascade on update cascade,
  stock_name text not null,
  enabled boolean not null default true,
  watch_reason text,
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now()
);

create table if not exists crawl_runs (
  id uuid primary key default gen_random_uuid(),
  run_id text not null unique,
  run_date date not null,
  started_at timestamptz not null,
  finished_at timestamptz not null,
  status text not null check (status in ('success', 'partial_success', 'failed')),
  mode text not null check (mode in ('daily', 'three_day')),
  scope text not null,
  scope_name text not null,
  source_mode text not null check (source_mode in ('mock', 'rss', 'http', 'search', 'hybrid')),
  summarizer_mode text not null check (summarizer_mode in ('mock', 'llm', 'auto')),
  llm_provider text not null check (llm_provider in ('mock', 'agnes', 'gemini', 'auto')),
  search_provider text not null check (search_provider in ('mock', 'tavily', 'serpapi', 'firecrawl', 'auto')),
  total_sources_count integer not null default 0 check (total_sources_count >= 0),
  accepted_sources_count integer not null default 0 check (accepted_sources_count >= 0),
  rejected_sources_count integer not null default 0 check (rejected_sources_count >= 0),
  quality_summary jsonb not null default '{}'::jsonb,
  rejected_reasons jsonb not null default '[]'::jsonb,
  output_files jsonb not null default '[]'::jsonb,
  run_errors jsonb not null default '[]'::jsonb,
  raw_packet jsonb not null,
  created_at timestamptz not null default now()
);

create index if not exists idx_crawl_runs_run_date on crawl_runs (run_date);
create index if not exists idx_crawl_runs_status on crawl_runs (status);
create index if not exists idx_crawl_runs_scope on crawl_runs (scope);
create index if not exists idx_crawl_runs_scope_name on crawl_runs (scope_name);
create index if not exists idx_crawl_runs_source_mode on crawl_runs (source_mode);

create table if not exists events (
  id uuid primary key default gen_random_uuid(),
  event_id text not null unique,
  run_id text not null references crawl_runs (run_id) on delete cascade on update cascade,
  event_date date not null,
  scope text not null,
  scope_name text not null,
  event_type text not null check (event_type in ('macro', 'industry', 'global_leader', 'domestic_leader', 'stock', 'institution')),
  importance text not null check (importance in ('general', 'important', 'critical')),
  language text not null,
  title text not null,
  ai_summary text not null,
  possible_impact text not null,
  risk_note text not null,
  tags jsonb not null default '[]'::jsonb,
  source_urls jsonb not null default '[]'::jsonb,
  quality_summary jsonb not null default '{}'::jsonb,
  raw_packet jsonb not null,
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now()
);

create index if not exists idx_events_run_id on events (run_id);
create index if not exists idx_events_event_date on events (event_date);
create index if not exists idx_events_scope on events (scope);
create index if not exists idx_events_scope_name on events (scope_name);
create index if not exists idx_events_importance on events (importance);
create index if not exists idx_events_event_type on events (event_type);

create table if not exists event_relations (
  id uuid primary key default gen_random_uuid(),
  event_id text not null references events (event_id) on delete cascade on update cascade,
  relation_type text not null check (relation_type in ('industry', 'stock', 'macro_topic', 'institution_watch')),
  relation_value text not null,
  created_at timestamptz not null default now(),
  unique (event_id, relation_type, relation_value)
);

create index if not exists idx_event_relations_event_id on event_relations (event_id);
create index if not exists idx_event_relations_relation_type_value on event_relations (relation_type, relation_value);

create table if not exists reports (
  id uuid primary key default gen_random_uuid(),
  report_id text not null unique,
  run_id text not null references crawl_runs (run_id) on delete cascade on update cascade,
  report_date date not null,
  report_type text not null check (report_type in ('full_report', 'urgent_alert', 'industry_report', 'stock_report', 'macro_report', 'institution_report')),
  scope text not null,
  scope_name text not null,
  importance text not null check (importance in ('general', 'important', 'critical')),
  report_title text not null,
  report_body text not null,
  quality_summary jsonb not null default '{}'::jsonb,
  raw_packet jsonb not null,
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now()
);

create index if not exists idx_reports_run_id on reports (run_id);
create index if not exists idx_reports_report_date on reports (report_date);
create index if not exists idx_reports_scope on reports (scope);
create index if not exists idx_reports_scope_name on reports (scope_name);
create index if not exists idx_reports_importance on reports (importance);
create index if not exists idx_reports_report_type on reports (report_type);

create table if not exists report_relations (
  id uuid primary key default gen_random_uuid(),
  report_id text not null references reports (report_id) on delete cascade on update cascade,
  relation_type text not null check (relation_type in ('industry', 'stock', 'event', 'macro_topic', 'institution_watch')),
  relation_value text not null,
  created_at timestamptz not null default now(),
  unique (report_id, relation_type, relation_value)
);

create index if not exists idx_report_relations_report_id on report_relations (report_id);
create index if not exists idx_report_relations_relation_type_value on report_relations (relation_type, relation_value);

create table if not exists rejected_sources (
  id uuid primary key default gen_random_uuid(),
  run_id text not null references crawl_runs (run_id) on delete cascade on update cascade,
  source_url text not null,
  source_name text not null,
  source_type text not null,
  title text not null,
  content text not null,
  quality_score integer not null default 0 check (quality_score >= 0),
  quality_level text not null check (quality_level in ('high', 'medium', 'low', 'rejected')),
  quality_reasons jsonb not null default '[]'::jsonb,
  raw_source jsonb not null,
  created_at timestamptz not null default now()
);

create index if not exists idx_rejected_sources_run_id on rejected_sources (run_id);
create index if not exists idx_rejected_sources_source_url on rejected_sources (source_url);
create index if not exists idx_rejected_sources_source_type on rejected_sources (source_type);
create index if not exists idx_rejected_sources_quality_level on rejected_sources (quality_level);

create table if not exists user_read_status (
  id uuid primary key default gen_random_uuid(),
  user_id text not null,
  item_type text not null check (item_type in ('event', 'report')),
  item_id text not null,
  is_read boolean not null default false,
  read_at timestamptz,
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now(),
  unique (user_id, item_type, item_id)
);

create index if not exists idx_user_read_status_user_id on user_read_status (user_id);
create index if not exists idx_user_read_status_item_type on user_read_status (item_type);
create index if not exists idx_user_read_status_is_read on user_read_status (is_read);

create or replace view view_dashboard_events as
select
  e.event_id,
  e.event_date,
  e.importance,
  e.scope,
  e.scope_name,
  e.ai_summary,
  e.possible_impact,
  e.risk_note,
  e.tags,
  e.quality_summary,
  e.source_urls
from events e
order by e.event_date desc, e.created_at desc;

create or replace view view_industry_cards as
with latest_events as (
  select
    er.relation_value as industry_name,
    count(*) as recent_event_count,
    count(*) filter (where e.importance = 'critical') as critical_count,
    count(*) filter (where e.importance = 'important') as important_count,
    max(e.event_date) as latest_event_date
  from event_relations er
  join events e on e.event_id = er.event_id
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
with latest_events as (
  select
    er.relation_value as stock_code,
    count(*) as recent_event_count,
    max(e.event_date) as latest_event_date
  from event_relations er
  join events e on e.event_id = er.event_id
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
  e.source_urls
from events e
join event_relations er on er.event_id = e.event_id and er.relation_type = 'stock'
left join stocks s on s.stock_code = er.relation_value
order by er.relation_value, e.event_date desc, e.created_at desc;

create or replace view view_macro_events as
select
  e.event_id,
  e.event_date,
  e.importance,
  e.scope,
  e.scope_name,
  e.ai_summary,
  e.possible_impact,
  e.risk_note,
  e.tags,
  e.quality_summary,
  e.source_urls
from events e
where e.event_type = 'macro'
order by e.event_date desc, e.created_at desc;

create or replace view view_institution_watch_events as
select
  e.event_id,
  e.event_date,
  e.importance,
  e.scope,
  e.scope_name,
  e.ai_summary,
  e.possible_impact,
  e.risk_note,
  e.tags,
  e.quality_summary,
  e.source_urls
from events e
where e.event_type = 'institution'
order by e.event_date desc, e.created_at desc;

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
