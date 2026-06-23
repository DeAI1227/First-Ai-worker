import type { QualitySummary } from "@/lib/types";

type Props = {
  summary: QualitySummary | undefined;
  className?: string;
};

export function QualitySummaryMini({ summary, className = "" }: Props) {
  const total = summary?.total_sources ?? 0;
  const high = summary?.high ?? 0;
  const medium = summary?.medium ?? 0;
  const low = summary?.low ?? 0;
  const rejected = summary?.rejected ?? 0;

  return (
    <div className={`rounded-[24px] border border-white/8 bg-white/[0.03] p-5 ${className}`}>
      <div className="flex items-center justify-between">
        <div>
          <div className="text-xs uppercase tracking-[0.22em] text-white/38">資料品質摘要</div>
          <div className="mt-1 text-lg font-semibold text-white">來源品質健康度</div>
        </div>
        <div className="rounded-2xl border border-white/8 bg-white/5 px-3 py-2 text-right">
          <div className="text-[11px] text-white/45">總來源</div>
          <div className="text-lg font-semibold text-white">{total}</div>
        </div>
      </div>

      <div className="mt-4 grid grid-cols-2 gap-3 sm:grid-cols-4">
        <div className="rounded-2xl border border-emerald-400/15 bg-emerald-400/10 p-3">
          <div className="text-[11px] text-emerald-100/70">High</div>
          <div className="mt-1 text-xl font-semibold text-emerald-50">{high}</div>
        </div>
        <div className="rounded-2xl border border-sky-400/15 bg-sky-400/10 p-3">
          <div className="text-[11px] text-sky-100/70">Medium</div>
          <div className="mt-1 text-xl font-semibold text-sky-50">{medium}</div>
        </div>
        <div className="rounded-2xl border border-amber-400/15 bg-amber-400/10 p-3">
          <div className="text-[11px] text-amber-100/70">Low</div>
          <div className="mt-1 text-xl font-semibold text-amber-50">{low}</div>
        </div>
        <div className="rounded-2xl border border-red-400/15 bg-red-400/10 p-3">
          <div className="text-[11px] text-red-100/70">Rejected</div>
          <div className="mt-1 text-xl font-semibold text-red-50">{rejected}</div>
        </div>
      </div>
    </div>
  );
}
