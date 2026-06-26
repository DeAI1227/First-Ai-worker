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
          <div className="text-xs uppercase tracking-[0.18em] text-white/38">Source Quality</div>
          <div className="mt-1 text-lg font-semibold text-white">資料品質摘要</div>
        </div>
        <div className="rounded-2xl border border-white/8 bg-white/5 px-3 py-2 text-right">
          <div className="text-[11px] text-white/45">總來源</div>
          <div className="text-lg font-semibold text-white">{total}</div>
        </div>
      </div>

      <div className="mt-4 grid grid-cols-2 gap-3 sm:grid-cols-4">
        <Metric label="High" value={high} className="border-emerald-400/15 bg-emerald-400/10 text-emerald-50" />
        <Metric label="Medium" value={medium} className="border-sky-400/15 bg-sky-400/10 text-sky-50" />
        <Metric label="Low" value={low} className="border-amber-400/15 bg-amber-400/10 text-amber-50" />
        <Metric label="Rejected" value={rejected} className="border-red-400/15 bg-red-400/10 text-red-50" />
      </div>
    </div>
  );
}

function Metric({ label, value, className }: { label: string; value: number; className: string }) {
  return (
    <div className={`rounded-2xl border p-3 ${className}`}>
      <div className="text-[11px] opacity-75">{label}</div>
      <div className="mt-1 text-xl font-semibold">{value}</div>
    </div>
  );
}
