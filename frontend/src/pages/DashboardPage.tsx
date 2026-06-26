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
      title="總覽"
      subtitle="這是 AI 投資研究終端，不是報價 App。這裡只顯示整理過的研究事件、報告與資料品質摘要。"
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
              <StatPill
                label="重大事件"
                value={data.dashboardEvents.filter((item) => item.importance === "critical").length}
                tone="critical"
              />
              <StatPill
                label="重要事件"
                value={data.dashboardEvents.filter((item) => item.importance === "important").length}
                tone="important"
              />
              <StatPill
                label="一般事件"
                value={data.dashboardEvents.filter((item) => item.importance === "general").length}
                tone="general"
              />
            </div>

            <div className="grid gap-4 lg:grid-cols-[1.2fr_0.8fr]">
              <QualitySummaryMini summary={data.dashboardEvents[0]?.quality_summary} />

              <Card className="space-y-4">
                <SectionHeader
                  title="未讀統計"
                  description="未讀狀態來自 user_read_status。"
                  action={
                    <div className="rounded-full border border-white/8 bg-white/5 px-3 py-1 text-xs text-white/60">
                      {data.unreadCounts.unread_total_count} 筆未讀
                    </div>
                  }
                />

                <div className="grid grid-cols-3 gap-3">
                  <div className="rounded-2xl border border-white/8 bg-black/20 p-3">
                    <div className="text-[11px] text-white/42">事件</div>
                    <div className="mt-1 text-xl font-semibold text-white">{data.unreadCounts.unread_event_count}</div>
                  </div>
                  <div className="rounded-2xl border border-white/8 bg-black/20 p-3">
                    <div className="text-[11px] text-white/42">報告</div>
                    <div className="mt-1 text-xl font-semibold text-white">{data.unreadCounts.unread_report_count}</div>
                  </div>
                  <div className="rounded-2xl border border-accent/15 bg-accent/10 p-3">
                    <div className="text-[11px] text-white/42">使用者 ID</div>
                    <div className="mt-1 text-sm font-medium break-all text-white/90">{data.unreadCounts.user_id}</div>
                  </div>
                </div>
              </Card>
            </div>

            <Card className="space-y-4">
              <SectionHeader title="今日研究摘要" description="先看一段人能讀的摘要，而不是先丟一堆碎片事件給你。" />
              <p className="text-sm leading-7 text-white/70">{buildPageDigest("總覽", data.dashboardEvents)}</p>
            </Card>

            <Card className="space-y-4">
              <SectionHeader title="最新事件" description="只保留近期重點事件卡片，避免畫面被重複訊息淹沒。" />
              <div className="space-y-4">
                {data.dashboardEvents.length === 0 ? (
                  <div className="rounded-[24px] border border-dashed border-white/10 bg-white/[0.02] p-6 text-center text-sm text-white/46">
                    目前沒有可顯示的事件。請稍後重新整理，或先檢查後端資料是否已寫入 Supabase。
                  </div>
                ) : (
                  data.dashboardEvents.slice(0, 6).map((event) => <EventItem key={event.event_id} event={event} showQuality />)
                )}
              </div>
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
              <SectionHeader title="近期報告" description="顯示最近產出的研究報告摘要。" />
              <div className="space-y-3">
                {data.reports.length === 0 ? (
                  <div className="rounded-2xl border border-dashed border-white/10 bg-white/[0.02] p-4 text-sm text-white/46">
                    目前還沒有研究報告。
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
              <SectionHeader title="系統邊界" description="這個終端的資料來源與限制。" />
              <div className="space-y-3 text-sm leading-6 text-white/55">
                <p>前端只讀 Supabase views。</p>
                <p>前端不讀 Python 程式。</p>
                <p>前端不讀 output JSON。</p>
                <p>沒有事件時使用空狀態，不產生假事件。</p>
              </div>
            </Card>
          </div>
        </div>
      ) : null}
    </PageFrame>
  );
}
