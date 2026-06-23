import { ArrowUpRight, FileText } from "lucide-react";
import type { DashboardEvent, InstitutionWatchEvent, MacroEvent, StockDetailEvent } from "@/lib/types";
import { formatDateTime, summaryTotal } from "@/lib/format";
import { Card } from "../ui/Card";
import { ImportanceBadge } from "./ImportanceBadge";
import { QualitySummaryMini } from "../ui/QualitySummaryMini";
import { Badge } from "../ui/Badge";

type EventLike = DashboardEvent | MacroEvent | InstitutionWatchEvent | StockDetailEvent;

type Props = {
  event: EventLike;
  showQuality?: boolean;
};

export function EventItem({ event, showQuality = false }: Props) {
  return (
    <Card className="space-y-4">
      <div className="flex items-start justify-between gap-4">
        <div className="space-y-2">
          <div className="flex flex-wrap items-center gap-2">
            <ImportanceBadge importance={event.importance} />
            {"scope_name" in event ? <Badge tone="neutral">{event.scope_name}</Badge> : null}
            <span className="text-xs text-white/42">{formatDateTime(event.event_date)}</span>
          </div>
          <div className="text-base font-semibold leading-7 text-white">
            {"ai_summary" in event ? event.ai_summary : ""}
          </div>
          <div className="text-sm leading-6 text-white/56">{event.possible_impact}</div>
        </div>
        <div className="flex shrink-0 items-center gap-2 text-white/30">
          <FileText className="h-4 w-4" />
          <ArrowUpRight className="h-4 w-4" />
        </div>
      </div>

      <div className="grid gap-3 md:grid-cols-2">
        <div className="rounded-2xl border border-white/8 bg-black/20 p-4">
          <div className="text-[11px] uppercase tracking-[0.24em] text-white/35">風險提醒</div>
          <p className="mt-2 text-sm leading-6 text-white/60">{event.risk_note}</p>
        </div>
        <div className="rounded-2xl border border-white/8 bg-black/20 p-4">
          <div className="text-[11px] uppercase tracking-[0.24em] text-white/35">來源連結</div>
          <div className="mt-2 flex flex-wrap gap-2">
            {event.source_urls?.slice(0, 3).map((url) => (
              <span key={url} className="truncate rounded-full border border-white/8 bg-white/5 px-3 py-1 text-xs text-white/58">
                {url}
              </span>
            ))}
          </div>
        </div>
      </div>

      {showQuality && "quality_summary" in event ? (
        <QualitySummaryMini summary={event.quality_summary} />
      ) : null}
    </Card>
  );
}
