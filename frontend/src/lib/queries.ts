import { getSupabaseClient } from "./supabase";
import type {
  DashboardEvent,
  IndustryCard,
  InstitutionWatchEvent,
  LatestCrawlRun,
  MacroEvent,
  RecentReport,
  StockCard,
  StockDetailEvent,
  UnreadCount,
} from "./types";
import {
  getReferenceIndustriesByStockCode,
  normalizeIndustryName,
  normalizeScopeName,
  normalizeStockName,
} from "./referenceData";
import { sanitizeEvent, sanitizeReport } from "./presentation";

function notNull<T>(value: T | null): value is T {
  return value !== null;
}

export async function getDashboardEvents(): Promise<DashboardEvent[]> {
  const supabase = getSupabaseClient();
  const { data, error } = await supabase
    .from("view_dashboard_events")
    .select("*")
    .order("event_date", { ascending: false })
    .limit(30);

  if (error) {
    throw error;
  }

  return ((data ?? []) as DashboardEvent[])
    .map((item) => ({
      ...item,
      scope_name: normalizeScopeName(item.scope_name, item.scope),
    }))
    .map((item) => sanitizeEvent(item))
    .filter(notNull);
}

export async function getIndustryCards(): Promise<IndustryCard[]> {
  const supabase = getSupabaseClient();
  const { data, error } = await supabase
    .from("view_industry_cards")
    .select("*")
    .order("industry_name", { ascending: true });

  if (error) {
    throw error;
  }

  return ((data ?? []) as IndustryCard[]).map((item) => ({
    ...item,
    industry_name: normalizeIndustryName(item.industry_name),
  }));
}

export async function getStockCards(): Promise<StockCard[]> {
  const supabase = getSupabaseClient();
  const { data, error } = await supabase
    .from("view_stock_cards")
    .select("*")
    .order("stock_code", { ascending: true });

  if (error) {
    throw error;
  }

  return ((data ?? []) as StockCard[]).map((item) => ({
    ...item,
    stock_name: normalizeStockName(item.stock_code, item.stock_name),
    related_industries:
      item.related_industries?.length
        ? item.related_industries.map((industry) => normalizeIndustryName(industry))
        : getReferenceIndustriesByStockCode(item.stock_code),
  }));
}

export async function getStockDetailEvents(stockCode: string): Promise<StockDetailEvent[]> {
  const supabase = getSupabaseClient();
  const { data, error } = await supabase
    .from("view_stock_detail_events")
    .select("*")
    .eq("stock_code", stockCode)
    .order("event_date", { ascending: false });

  if (error) {
    throw error;
  }

  return ((data ?? []) as StockDetailEvent[])
    .map((item) => ({
      ...item,
      stock_name: normalizeStockName(item.stock_code, item.stock_name),
    }))
    .map((item) => sanitizeEvent(item))
    .filter(notNull);
}

export async function getMacroEvents(): Promise<MacroEvent[]> {
  const supabase = getSupabaseClient();
  const { data, error } = await supabase
    .from("view_macro_events")
    .select("*")
    .order("event_date", { ascending: false });

  if (error) {
    throw error;
  }

  return ((data ?? []) as MacroEvent[])
    .map((item) => ({
      ...item,
      scope_name: normalizeScopeName(item.scope_name, item.scope),
    }))
    .map((item) => sanitizeEvent(item))
    .filter(notNull);
}

export async function getInstitutionWatchEvents(): Promise<InstitutionWatchEvent[]> {
  const supabase = getSupabaseClient();
  const { data, error } = await supabase
    .from("view_institution_watch_events")
    .select("*")
    .order("event_date", { ascending: false });

  if (error) {
    throw error;
  }

  return ((data ?? []) as InstitutionWatchEvent[])
    .map((item) => ({
      ...item,
      scope_name: normalizeScopeName(item.scope_name, item.scope),
    }))
    .map((item) => sanitizeEvent(item))
    .filter(notNull);
}

export async function getRecentReports(): Promise<RecentReport[]> {
  const supabase = getSupabaseClient();
  const { data, error } = await supabase
    .from("view_recent_reports")
    .select("*")
    .order("report_date", { ascending: false })
    .limit(20);

  if (error) {
    throw error;
  }

  return ((data ?? []) as RecentReport[])
    .map((item) => ({
      ...item,
      scope_name: normalizeScopeName(item.scope_name, item.scope),
    }))
    .map((item) => sanitizeReport(item))
    .filter(notNull);
}

export async function getUnreadCounts(userId: string): Promise<UnreadCount> {
  const supabase = getSupabaseClient();
  const { data, error } = await supabase
    .from("view_unread_counts")
    .select("*")
    .eq("user_id", userId)
    .maybeSingle();

  if (error) {
    throw error;
  }

  return (
    data ?? {
      user_id: userId,
      unread_event_count: 0,
      unread_report_count: 0,
      unread_total_count: 0,
    }
  ) as UnreadCount;
}

export async function getLatestCrawlRun(): Promise<LatestCrawlRun | null> {
  const supabase = getSupabaseClient();
  const { data, error } = await supabase.from("view_latest_crawl_run").select("*").maybeSingle();

  if (error) {
    throw error;
  }

  return (data ?? null) as LatestCrawlRun | null;
}

export async function getSystemSnapshot(userId: string) {
  const [dashboardEvents, industryCards, stockCards, macroEvents, institutionEvents, reports, unreadCounts, latestCrawlRun] =
    await Promise.all([
      getDashboardEvents(),
      getIndustryCards(),
      getStockCards(),
      getMacroEvents(),
      getInstitutionWatchEvents(),
      getRecentReports(),
      getUnreadCounts(userId),
      getLatestCrawlRun(),
    ]);

  return {
    dashboardEvents,
    industryCards,
    stockCards,
    macroEvents,
    institutionEvents,
    reports,
    unreadCounts,
    latestCrawlRun,
  };
}
