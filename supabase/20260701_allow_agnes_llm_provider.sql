-- Migration to align existing Supabase tables with the current MVP contract.
-- This file is safe to re-run. It updates legacy check constraints so the
-- autonomous pipeline can persist crawl runs that use llm_provider = 'agnes'.

alter table if exists public.staging_crawl_runs
  drop constraint if exists staging_crawl_runs_llm_provider_check;

alter table if exists public.staging_crawl_runs
  add constraint staging_crawl_runs_llm_provider_check
  check (llm_provider in ('mock', 'agnes', 'gemini', 'auto'));

alter table if exists public.crawl_runs
  drop constraint if exists crawl_runs_llm_provider_check;

alter table if exists public.crawl_runs
  add constraint crawl_runs_llm_provider_check
  check (llm_provider in ('mock', 'agnes', 'gemini', 'auto'));
