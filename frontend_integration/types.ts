export type JsonValue =
  | string
  | number
  | boolean
  | null
  | JsonValue[]
  | { [key: string]: JsonValue };

export type Importance = "general" | "important" | "critical";

export type RelationType = "industry" | "stock" | "macro_topic" | "institution_watch";

export type ReadStatus = {
  id?: string;
  user_id: string;
  item_type: "event" | "report";
  item_id: string;
  is_read: boolean;
  read_at: string | null;
  created_at?: string;
  updated_at?: string;
};

export type QualitySummary = {
  total_sources?: number;
  high?: number;
  medium?: number;
  low?: number;
  rejected?: number;
};

export type DashboardEvent = {
  event_id: string;
  event_date: string;
  importance: Importance;
  scope: "macro" | "industry" | "stock" | "institution_watch" | string;
  scope_name: string;
  ai_summary: string;
  possible_impact: string;
  risk_note: string;
  tags: JsonValue[];
  quality_summary: QualitySummary;
  source_urls: string[];
};

export type IndustryCard = {
  industry_name: string;
  recent_event_count: number;
  critical_count: number;
  important_count: number;
  latest_event_date: string | null;
};

export type StockCard = {
  stock_code: string;
  stock_name: string;
  related_industries: string[];
  recent_event_count: number;
  latest_event_date: string | null;
};

export type StockDetailEvent = {
  stock_code: string;
  stock_name: string | null;
  event_id: string;
  event_date: string;
  importance: Importance;
  ai_summary: string;
  possible_impact: string;
  risk_note: string;
  tags: JsonValue[];
  source_urls: string[];
};

export type MacroEvent = {
  event_id: string;
  event_date: string;
  importance: Importance;
  scope: "macro" | string;
  scope_name: string;
  ai_summary: string;
  possible_impact: string;
  risk_note: string;
  tags: JsonValue[];
  quality_summary: QualitySummary;
  source_urls: string[];
};

export type InstitutionWatchEvent = {
  event_id: string;
  event_date: string;
  importance: Importance;
  scope: "institution_watch" | "institution" | string;
  scope_name: string;
  ai_summary: string;
  possible_impact: string;
  risk_note: string;
  tags: JsonValue[];
  quality_summary: QualitySummary;
  source_urls: string[];
};

export type RecentReport = {
  report_id: string;
  report_date: string;
  report_type:
    | "full_report"
    | "urgent_alert"
    | "industry_report"
    | "stock_report"
    | "macro_report"
    | "institution_report"
    | string;
  importance: Importance;
  scope: "macro" | "industry" | "stock" | "institution_watch" | string;
  scope_name: string;
  report_title: string;
  report_body: string;
  quality_summary: QualitySummary;
};

export type UnreadCount = {
  user_id: string;
  unread_event_count: number;
  unread_report_count: number;
  unread_total_count: number;
};

export type LatestCrawlRun = {
  run_id: string;
  run_date: string;
  started_at: string;
  finished_at: string;
  status: "success" | "partial_success" | "failed" | string;
  mode: "daily" | "three_day" | string;
  scope: "macro" | "industry" | "stock" | "institution_watch" | string;
  scope_name: string;
  source_mode: "mock" | "rss" | "http" | "search" | "hybrid" | string;
  summarizer_mode: "mock" | "llm" | "auto" | string;
  llm_provider: "mock" | "agnes" | "gemini" | "auto" | string;
  search_provider: "mock" | "tavily" | "serpapi" | "firecrawl" | "auto" | string;
  total_sources_count: number;
  accepted_sources_count: number;
  rejected_sources_count: number;
  quality_summary: QualitySummary;
  rejected_reasons: JsonValue[];
  output_files: JsonValue[];
  run_errors: JsonValue[];
  raw_packet: JsonValue;
  created_at: string;
};
