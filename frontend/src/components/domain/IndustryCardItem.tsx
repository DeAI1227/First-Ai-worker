import { ArrowUpRight, Layers3 } from "lucide-react";
import { Link } from "react-router-dom";
import type { IndustryCard } from "@/lib/types";
import { formatDate } from "@/lib/format";
import { Card } from "../ui/Card";
import { getIndustryKeyByName } from "@/lib/referenceData";

type Props = {
  industry: IndustryCard;
};

export function IndustryCardItem({ industry }: Props) {
  return (
    <Link to={`/industries/${getIndustryKeyByName(industry.industry_name)}`} className="block">
      <Card className="group transition hover:border-accent/20 hover:bg-white/[0.05]">
        <div className="flex items-start justify-between gap-3">
          <div>
            <div className="flex items-center gap-2">
              <div className="flex h-10 w-10 items-center justify-center rounded-2xl border border-white/8 bg-white/5">
                <Layers3 className="h-4 w-4 text-accent" />
              </div>
              <div>
                <div className="text-lg font-semibold text-white">{industry.industry_name}</div>
                <div className="text-xs text-white/42">最近更新 {formatDate(industry.latest_event_date)}</div>
              </div>
            </div>
          </div>
          <ArrowUpRight className="h-4 w-4 text-white/30 transition group-hover:text-white/70" />
        </div>

        <div className="mt-4 grid grid-cols-3 gap-3">
          <div className="rounded-2xl border border-white/8 bg-black/20 p-3">
            <div className="text-[11px] text-white/42">事件數</div>
            <div className="mt-1 text-xl font-semibold text-white">{industry.recent_event_count}</div>
          </div>
          <div className="rounded-2xl border border-red-400/15 bg-red-400/10 p-3">
            <div className="text-[11px] text-red-100/70">重大</div>
            <div className="mt-1 text-xl font-semibold text-red-50">{industry.critical_count}</div>
          </div>
          <div className="rounded-2xl border border-amber-400/15 bg-amber-400/10 p-3">
            <div className="text-[11px] text-amber-100/70">重要</div>
            <div className="mt-1 text-xl font-semibold text-amber-50">{industry.important_count}</div>
          </div>
        </div>
      </Card>
    </Link>
  );
}
