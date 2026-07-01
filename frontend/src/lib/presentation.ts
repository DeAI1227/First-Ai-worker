import type {
  DashboardEvent,
  InstitutionWatchEvent,
  MacroEvent,
  RecentReport,
  StockDetailEvent,
} from "./types";
import { cleanSourceUrls, isPlaceholderContent } from "./referenceData";

type EventLike = DashboardEvent | MacroEvent | InstitutionWatchEvent | StockDetailEvent;

const NOISE_PATTERNS = [
  /English technology coverage/gi,
  /Scammers are becoming ever more sophisticated[\s\S]*/gi,
  /The threat to summer holidays[\s\S]*/gi,
  /本次內容先整理為事件脈絡[^。]{0,120}/gi,
];

function truncate(text: string, maxLength: number): string {
  if (text.length <= maxLength) {
    return text;
  }
  return `${text.slice(0, maxLength).trim()}...`;
}

export function cleanText(value: string | null | undefined): string {
  if (!value) {
    return "";
  }

  let next = value;
  for (const pattern of NOISE_PATTERNS) {
    next = next.replace(pattern, "");
  }

  return next.replace(/\s+/g, " ").trim();
}

export function sanitizeEvent<T extends EventLike>(event: T): T | null {
  const sourceUrls = cleanSourceUrls(event.source_urls);
  const summary = cleanText(event.ai_summary);
  const impact = cleanText(event.possible_impact);
  const risk = cleanText(event.risk_note);

  if (!summary || summary.length < 12) {
    return null;
  }
  if (isPlaceholderContent(summary, event.source_urls ?? [])) {
    return null;
  }

  return {
    ...event,
    ai_summary: truncate(summary, 1500),
    possible_impact: impact || "這則事件可能影響後續研究判讀，但仍需搭配更多來源驗證。",
    risk_note: risk || "單一事件不宜過度延伸，請回到原始來源與後續公告交叉確認。",
    source_urls: sourceUrls,
  };
}

export function sanitizeReport(report: RecentReport): RecentReport | null {
  const title = cleanText(report.report_title);
  const body = cleanText(report.report_body);
  if (!title || !body) {
    return null;
  }
  return {
    ...report,
    report_title: title,
    report_body: truncate(body, 1500),
  };
}

export function buildPageDigest(label: string, events: EventLike[]): string {
  const summaries = Array.from(
    new Set(
      events
        .map((event) => cleanText(event.ai_summary))
        .filter(Boolean)
        .map((item) => truncate(item, 160)),
    ),
  ).slice(0, 6);

  if (summaries.length === 0) {
    return `${label} 目前沒有可讀的研究事件。若今天沒有有效新聞，頁面會維持空狀態，不會用假摘要填滿。`;
  }

  const digest = `${label} 本頁共整理 ${events.length} 則研究事件。重點包括：${summaries.join("；")}`;

  return truncate(digest, 1500);
}
