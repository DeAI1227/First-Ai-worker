export function LoadingState({ label = "資料載入中" }: { label?: string }) {
  return (
    <div className="space-y-3 rounded-[24px] border border-white/8 bg-white/[0.03] p-5">
      <div className="h-4 w-32 animate-pulse rounded-full bg-white/10" />
      <div className="grid gap-3">
        <div className="h-24 animate-pulse rounded-2xl bg-white/8" />
        <div className="h-24 animate-pulse rounded-2xl bg-white/8" />
        <div className="h-24 animate-pulse rounded-2xl bg-white/8" />
      </div>
      <div className="text-sm text-white/45">{label}</div>
    </div>
  );
}
