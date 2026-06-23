import type { Importance, QualitySummary } from "./types";

const zhDateTime = new Intl.DateTimeFormat("zh-TW", {
  dateStyle: "medium",
  timeStyle: "short",
});

const zhDate = new Intl.DateTimeFormat("zh-TW", {
  dateStyle: "medium",
});

export function formatDateTime(value: string | null | undefined): string {
  if (!value) {
    return "—";
  }

  const parsed = new Date(value);
  if (Number.isNaN(parsed.getTime())) {
    return value;
  }

  return zhDateTime.format(parsed);
}

export function formatDate(value: string | null | undefined): string {
  if (!value) {
    return "—";
  }

  const parsed = new Date(value);
  if (Number.isNaN(parsed.getTime())) {
    return value;
  }

  return zhDate.format(parsed);
}

export function importanceLabel(value: Importance): string {
  if (value === "critical") {
    return "Critical";
  }
  if (value === "important") {
    return "Important";
  }
  return "General";
}

export function importanceZhLabel(value: Importance): string {
  if (value === "critical") {
    return "重大";
  }
  if (value === "important") {
    return "重要";
  }
  return "一般";
}

export function qualityLevelLabel(summary: QualitySummary | null | undefined, key: keyof QualitySummary): string {
  return String(summary?.[key] ?? 0);
}

export function summaryTotal(summary: QualitySummary | null | undefined): number {
  return Number(summary?.total_sources ?? 0);
}
