import { supabase } from "./supabaseClient";

export async function getDashboardEvents() {
  return supabase
    .from("view_dashboard_events")
    .select("*")
    .order("event_date", { ascending: false })
    .limit(20);
}

export async function getIndustryCards() {
  return supabase
    .from("view_industry_cards")
    .select("*")
    .order("industry_name", { ascending: true });
}

export async function getStockCards() {
  return supabase
    .from("view_stock_cards")
    .select("*")
    .order("stock_code", { ascending: true });
}

export async function getStockDetailEvents(stockCode: string) {
  return supabase
    .from("view_stock_detail_events")
    .select("*")
    .eq("stock_code", stockCode)
    .order("event_date", { ascending: false });
}

export async function getMacroEvents() {
  return supabase
    .from("view_macro_events")
    .select("*")
    .order("event_date", { ascending: false });
}

export async function getInstitutionWatchEvents() {
  return supabase
    .from("view_institution_watch_events")
    .select("*")
    .order("event_date", { ascending: false });
}

export async function getRecentReports() {
  return supabase
    .from("view_recent_reports")
    .select("*")
    .order("report_date", { ascending: false })
    .limit(20);
}

export async function getUnreadCounts(userId: string) {
  return supabase
    .from("view_unread_counts")
    .select("*")
    .eq("user_id", userId)
    .maybeSingle();
}

export async function getLatestCrawlRun() {
  return supabase
    .from("view_latest_crawl_run")
    .select("*")
    .maybeSingle();
}
