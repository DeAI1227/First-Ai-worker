import { ArrowUpRight, FileText } from "lucide-react";
import type { DashboardEvent, InstitutionWatchEvent, MacroEvent, StockDetailEvent } from "@/lib/types";
import { formatDateTime } from "@/lib/format";
import { Card } from "../ui/Card";
import { ImportanceBadge } from "./ImportanceBadge";
import { QualitySummaryMini } from "../ui/QualitySummaryMini";
import { Badge } from "../ui/Badge";

type EventLike = DashboardEvent | MacroEvent | InstitutionWatchEvent | StockDetailEvent;

type Props = {
  event: EventLike;
  showQuality?: boolean;
  hideScopeLabel?: boolean;
};

export function EventItem({ event, showQuality = false, hideScopeLabel = false }: Props) {
  const primarySourceUrl = event.source_urls?.[0];

  return (
    <Card className="space-y-4">
      <div className="flex items-start justify-between gap-4">
        <div className="space-y-2">
          <div className="flex flex-wrap items-center gap-2">
            <ImportanceBadge importance={event.importance} />
            {"scope_name" in event && !hideScopeLabel ? <Badge tone="neutral">{event.scope_name}</Badge> : null}
            <span className="text-xs text-white/42">{formatDateTime(event.event_date)}</span>
          </div>
          <div className="text-base font-semibold leading-7 text-white">{event.ai_summary}</div>
          <div className="text-sm leading-6 text-white/56">{event.possible_impact}</div>
        </div>
        {primarySourceUrl ? (
          <a
            href={primarySourceUrl}
            target="_blank"
            rel="noreferrer"
            className="inline-flex shrink-0 items-center gap-2 rounded-full border border-white/8 bg-white/5 px-3 py-2 text-xs text-white/68 transition hover:bg-white/10 hover:text-white"
          >
            <FileText className="h-3.5 w-3.5" />
            <span>原始來源</span>
            <ArrowUpRight className="h-3.5 w-3.5" />
          </a>
        ) : null}
      </div>

      <div className="grid gap-3 md:grid-cols-2">
        <div className="rounded-2xl border border-white/8 bg-black/20 p-4">
          <div className="text-[11px] uppercase tracking-[0.24em] text-white/35">風險提醒</div>
          <p className="mt-2 text-sm leading-6 text-white/60">{event.risk_note}</p>
        </div>
        <div className="rounded-2xl border border-white/8 bg-black/20 p-4">
          <div className="text-[11px] uppercase tracking-[0.24em] text-white/35">來源連結</div>
          {event.source_urls?.length ? (
            <div className="mt-2 flex flex-wrap gap-2">
              {event.source_urls.slice(0, 3).map((url) => (
                <a
                  key={url}
                  href={url}
                  target="_blank"
                  rel="noreferrer"
                  className="truncate rounded-full border border-white/8 bg-white/5 px-3 py-1 text-xs text-white/58 transition hover:bg-white/10 hover:text-white"
                >
                  {url}
                </a>
              ))}
            </div>
          ) : (
            <p className="mt-2 text-sm leading-6 text-white/50">目前沒有可公開顯示的來源連結。</p>
          )}
        </div>
      </div>

      {showQuality && "quality_summary" in event ? <QualitySummaryMini summary={event.quality_summary} /> : null}
    </Card>
  );
}
