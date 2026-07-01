import { useCallback } from "react";
import { RefreshCcw } from "lucide-react";
import { useAsync } from "@/hooks/useAsync";
import { getSystemSnapshot } from "@/lib/queries";
import { getStoredUserId } from "@/lib/user";
import { buildPageDigest } from "@/lib/presentation";
import { PageFrame } from "@/components/layout/PageFrame";
import { Card } from "@/components/ui/Card";
import { LoadingState } from "@/components/ui/LoadingState";
import { ErrorState } from "@/components/ui/ErrorState";
import { Button } from "@/components/ui/Button";
import { StatPill } from "@/components/ui/StatPill";
import { SectionHeader } from "@/components/ui/SectionHeader";
import { EventItem } from "@/components/domain/EventItem";
import { QualitySummaryMini } from "@/components/ui/QualitySummaryMini";
import { SystemSummaryCard } from "@/components/domain/SystemSummaryCard";

export function DashboardPage() {
  const userId = getStoredUserId();
  const loader = useCallback(() => getSystemSnapshot(userId), [userId]);
  const { data, loading, error, reload } = useAsync(loader, [loader]);

  return (
    <PageFrame
      title="AI 投資研究終端"
      subtitle="這不是報價 App。這裡只顯示整理過的研究事件、研究報告與資料品質摘要。"
      actions={
        <Button tone="secondary" onClick={reload}>
          <RefreshCcw className="h-4 w-4" />
          重新整理
        </Button>
      }
    >
      {loading ? <LoadingState label="正在讀取 Supabase 研究資料" /> : null}
      {error ? <ErrorState description={error} onRetry={reload} /> : null}

      {data ? (
        <div className="grid gap-5 xl:grid-cols-[1.8fr_0.9fr]">
          <div className="space-y-5">
            <div className="grid gap-3 sm:grid-cols-3">
              <StatPill label="重大事件" value={data.dashboardEvents.filter((item) => item.importance === "critical").length} tone="critical" />
              <StatPill label="重要事件" value={data.dashboardEvents.filter((item) => item.importance === "important").length} tone="important" />
              <StatPill label="一般事件" value={data.dashboardEvents.filter((item) => item.importance === "general").length} tone="general" />
            </div>

            <div className="grid gap-4 lg:grid-cols-[1.2fr_0.8fr]">
              <QualitySummaryMini summary={data.latestCrawlRun?.quality_summary ?? data.dashboardEvents[0]?.quality_summary} />
              <Card className="space-y-4">
                <SectionHeader
                  title="未讀狀態"
                  description="已讀狀態來自 user_read_status，不寫回事件本體。"
                  action={
                    <div className="rounded-full border border-white/8 bg-white/5 px-3 py-1 text-xs text-white/60">
                      {data.unreadCounts.unread_total_count} 筆未讀
                    </div>
                  }
                />
                <div className="grid grid-cols-3 gap-3">
                  <Metric label="事件" value={data.unreadCounts.unread_event_count} />
                  <Metric label="報告" value={data.unreadCounts.unread_report_count} />
                  <Metric label="總計" value={data.unreadCounts.unread_total_count} accent />
                </div>
              </Card>
            </div>

            <Card className="space-y-4">
              <SectionHeader title="今日研究摘要" description="先看聚合後的研究摘要，而不是先讀一堆碎片新聞。" />
              <p className="text-sm leading-7 text-white/70">{buildPageDigest("總覽", data.dashboardEvents)}</p>
            </Card>

            <Card className="space-y-4">
              <SectionHeader title="最新研究事件" description="先看摘要，再展開原始事件。" />
              {data.dashboardEvents.length === 0 ? (
                <div className="rounded-[24px] border border-dashed border-white/10 bg-white/[0.02] p-6 text-center text-sm text-white/46">
                  目前沒有可顯示的研究事件。請確認後端 pipeline 是否已寫入 Supabase production views。
                </div>
              ) : (
                <details className="rounded-[24px] border border-white/8 bg-black/20 p-4">
                  <summary className="cursor-pointer list-none text-sm font-medium text-white/80">
                    展開原始事件（{data.dashboardEvents.length} 則）
                  </summary>
                  <div className="mt-4 space-y-4">
                    {data.dashboardEvents.slice(0, 6).map((event) => <EventItem key={event.event_id} event={event} showQuality />)}
                  </div>
                </details>
              )}
            </Card>
          </div>

          <div className="space-y-5">
            <SystemSummaryCard
              userId={data.unreadCounts.user_id}
              unreadEventCount={data.unreadCounts.unread_event_count}
              unreadReportCount={data.unreadCounts.unread_report_count}
              unreadTotalCount={data.unreadCounts.unread_total_count}
            />

            <Card className="space-y-4">
              <SectionHeader title="近期研究報告" description="報告來自 report_packet 與 Supabase production views。" />
              <div className="space-y-3">
                {data.reports.length === 0 ? (
                  <div className="rounded-2xl border border-dashed border-white/10 bg-white/[0.02] p-4 text-sm text-white/46">
                    目前沒有研究報告。
                  </div>
                ) : (
                  data.reports.slice(0, 3).map((report) => (
                    <div key={report.report_id} className="rounded-2xl border border-white/8 bg-black/20 p-4">
                      <div className="text-xs text-white/45">{report.report_type}</div>
                      <div className="mt-1 text-sm font-medium text-white">{report.report_title}</div>
                      <div className="mt-2 line-clamp-4 text-xs leading-5 text-white/52">{report.report_body}</div>
                    </div>
                  ))
                )}
              </div>
            </Card>

            <Card className="space-y-4">
              <SectionHeader title="系統邊界" description="前端只讀 Supabase production views。" />
              <div className="space-y-3 text-sm leading-6 text-white/55">
                <p>不讀 Python 程式。</p>
                <p>不讀 output JSON。</p>
                <p>不直接呼叫 Collector。</p>
                <p>沒有新聞時顯示 empty state，不產生假事件。</p>
              </div>
            </Card>
          </div>
        </div>
      ) : null}
    </PageFrame>
  );
}

function Metric({ label, value, accent = false }: { label: string; value: number; accent?: boolean }) {
  return (
    <div className={`rounded-2xl border p-3 ${accent ? "border-accent/15 bg-accent/10" : "border-white/8 bg-black/20"}`}>
      <div className="text-[11px] text-white/42">{label}</div>
      <div className="mt-1 text-xl font-semibold text-white">{value}</div>
    </div>
  );
}
