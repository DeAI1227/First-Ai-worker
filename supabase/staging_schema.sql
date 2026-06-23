-- Supabase staging schema for Investment Research Collector
-- This schema stores raw collector output before any production-level curation.

create extension if not exists pgcrypto;

create table if not exists staging_crawl_runs (
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
  llm_provider text not null check (llm_provider in ('mock', 'openai', 'gemini', 'auto')),
  search_provider text not null check (search_provider in ('mock', 'tavily', 'serpapi', 'auto')),
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

create index if not exists idx_staging_crawl_runs_run_date on staging_crawl_runs (run_date);
create index if not exists idx_staging_crawl_runs_status on staging_crawl_runs (status);
create index if not exists idx_staging_crawl_runs_scope on staging_crawl_runs (scope);
create index if not exists idx_staging_crawl_runs_scope_name on staging_crawl_runs (scope_name);
create index if not exists idx_staging_crawl_runs_source_mode on staging_crawl_runs (source_mode);

create table if not exists staging_events (
  id uuid primary key default gen_random_uuid(),
  event_id text not null unique,
  run_id text not null,
  event_date date not null,
  scope text not null,
  scope_name text not null,
  event_type text not null,
  importance text not null,
  language text not null,
  ai_summary text not null,
  possible_impact text not null,
  risk_note text not null,
  tags jsonb not null default '[]'::jsonb,
  related_industries jsonb not null default '[]'::jsonb,
  related_stocks jsonb not null default '[]'::jsonb,
  source_urls jsonb not null default '[]'::jsonb,
  raw_packet jsonb not null,
  created_at timestamptz not null default now()
);

create index if not exists idx_staging_events_run_id on staging_events (run_id);
create index if not exists idx_staging_events_event_date on staging_events (event_date);
create index if not exists idx_staging_events_scope on staging_events (scope);
create index if not exists idx_staging_events_scope_name on staging_events (scope_name);
create index if not exists idx_staging_events_importance on staging_events (importance);

create table if not exists staging_daily_digests (
  id uuid primary key default gen_random_uuid(),
  digest_id text not null unique,
  run_id text not null,
  digest_date date not null,
  scope text not null,
  scope_name text not null,
  summary text not null,
  important_events jsonb not null default '[]'::jsonb,
  quality_summary jsonb not null default '{}'::jsonb,
  rejected_reasons jsonb not null default '[]'::jsonb,
  raw_packet jsonb not null,
  created_at timestamptz not null default now()
);

create index if not exists idx_staging_daily_digests_run_id on staging_daily_digests (run_id);
create index if not exists idx_staging_daily_digests_digest_date on staging_daily_digests (digest_date);
create index if not exists idx_staging_daily_digests_scope on staging_daily_digests (scope);
create index if not exists idx_staging_daily_digests_scope_name on staging_daily_digests (scope_name);

create table if not exists staging_reports (
  id uuid primary key default gen_random_uuid(),
  report_id text not null unique,
  run_id text not null,
  report_date date not null,
  report_type text not null,
  scope text not null,
  scope_name text not null,
  importance text not null,
  report_title text not null,
  report_body text not null,
  quality_summary jsonb not null default '{}'::jsonb,
  raw_packet jsonb not null,
  created_at timestamptz not null default now()
);

create index if not exists idx_staging_reports_run_id on staging_reports (run_id);
create index if not exists idx_staging_reports_report_date on staging_reports (report_date);
create index if not exists idx_staging_reports_scope on staging_reports (scope);
create index if not exists idx_staging_reports_scope_name on staging_reports (scope_name);
create index if not exists idx_staging_reports_importance on staging_reports (importance);

create table if not exists staging_rejected_sources (
  id uuid primary key default gen_random_uuid(),
  run_id text not null,
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

create index if not exists idx_staging_rejected_sources_run_id on staging_rejected_sources (run_id);
create index if not exists idx_staging_rejected_sources_source_url on staging_rejected_sources (source_url);
create index if not exists idx_staging_rejected_sources_source_type on staging_rejected_sources (source_type);
create index if not exists idx_staging_rejected_sources_quality_level on staging_rejected_sources (quality_level);

create table if not exists ingestion_errors (
  id uuid primary key default gen_random_uuid(),
  packet_type text not null,
  packet_id text not null,
  target_table text not null,
  error_message text not null,
  raw_packet jsonb not null,
  created_at timestamptz not null default now()
);

create index if not exists idx_ingestion_errors_packet_type on ingestion_errors (packet_type);
create index if not exists idx_ingestion_errors_target_table on ingestion_errors (target_table);
create index if not exists idx_ingestion_errors_created_at on ingestion_errors (created_at);
