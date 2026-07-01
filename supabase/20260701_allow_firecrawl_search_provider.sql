-- Migration to align existing Supabase tables with the current MVP contract.
-- This file is safe to re-run. It updates legacy check constraints so the
-- autonomous pipeline can persist crawl runs that use search_provider = 'firecrawl'.

alter table if exists public.staging_crawl_runs
  drop constraint if exists staging_crawl_runs_search_provider_check;

alter table if exists public.staging_crawl_runs
  add constraint staging_crawl_runs_search_provider_check
  check (search_provider in ('mock', 'tavily', 'serpapi', 'firecrawl', 'auto'));

alter table if exists public.crawl_runs
  drop constraint if exists crawl_runs_search_provider_check;

alter table if exists public.crawl_runs
  add constraint crawl_runs_search_provider_check
  check (search_provider in ('mock', 'tavily', 'serpapi', 'firecrawl', 'auto'));
