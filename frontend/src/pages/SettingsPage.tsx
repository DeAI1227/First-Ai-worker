import { useCallback } from "react";
import { RefreshCcw, Database, Settings2 } from "lucide-react";
import { useAsync } from "@/hooks/useAsync";
import { getUnreadCounts } from "@/lib/queries";
import { getStoredUserId } from "@/lib/user";
import { PageFrame } from "@/components/layout/PageFrame";
import { Button } from "@/components/ui/Button";
import { LoadingState } from "@/components/ui/LoadingState";
import { ErrorState } from "@/components/ui/ErrorState";
import { Card } from "@/components/ui/Card";
import { SectionHeader } from "@/components/ui/SectionHeader";
import { UserIdEditor } from "@/components/domain/UserIdEditor";
import { SystemSummaryCard } from "@/components/domain/SystemSummaryCard";
import { useState } from "react";

export function SettingsPage() {
  const [userId, setUserId] = useState(getStoredUserId());
  const loader = useCallback(() => getUnreadCounts(userId), [userId]);
  const { data, loading, error, reload } = useAsync(loader, [loader]);

  return (
    <PageFrame
      title="系統設定"
      subtitle="顯示資料來源狀態、read status、環境設定與系統說明。"
      actions={
        <Button tone="secondary" onClick={reload}>
          <RefreshCcw className="h-4 w-4" />
          重新整理
        </Button>
      }
    >
      {loading ? <LoadingState label="正在載入系統資料…" /> : null}
      {error ? <ErrorState description={error} onRetry={reload} /> : null}

      <div className="grid gap-5 xl:grid-cols-[0.95fr_1.05fr]">
        <div className="space-y-5">
          <UserIdEditor
            userId={userId}
            onChange={(next) => {
              setUserId(next);
            }}
          />

          <Card className="space-y-4">
            <SectionHeader title="資料來源規則" description="這個前端只讀 Supabase production views。" />
            <div className="space-y-2 text-sm leading-6 text-white/56">
              <p>• 前端不讀 Python 程式。</p>
              <p>• 前端不讀 output JSON。</p>
              <p>• 前端不直接呼叫 Collector。</p>
              <p>• read / unread 只寫入 user_read_status。</p>
            </div>
          </Card>
        </div>

        <div className="space-y-5">
          {data ? (
            <SystemSummaryCard
              userId={data.user_id}
              unreadEventCount={data.unread_event_count}
              unreadReportCount={data.unread_report_count}
              unreadTotalCount={data.unread_total_count}
            />
          ) : null}

          <Card className="space-y-4">
            <SectionHeader title="Supabase 連線狀態" description="使用 VITE_SUPABASE_URL 與 VITE_SUPABASE_ANON_KEY。" />
            <div className="flex items-start gap-3 rounded-2xl border border-white/8 bg-black/20 p-4 text-sm leading-6 text-white/55">
              <Database className="mt-0.5 h-4 w-4 shrink-0 text-accent" />
              <div>
                <div className="font-medium text-white">正式資料中心</div>
                <p className="mt-1">
                  新前端只讀 Supabase production views；如果沒有設定環境變數，頁面會回報清楚的連線錯誤。
                </p>
              </div>
            </div>
            <div className="flex items-start gap-3 rounded-2xl border border-white/8 bg-black/20 p-4 text-sm leading-6 text-white/55">
              <Settings2 className="mt-0.5 h-4 w-4 shrink-0 text-white/55" />
              <div>
                <div className="font-medium text-white">前端定位</div>
                <p className="mt-1">
                  這不是行情工具，也不是 Python 的視覺外殼，而是新的 Supabase-only 研究終端。
                </p>
              </div>
            </div>
          </Card>
        </div>
      </div>
    </PageFrame>
  );
}
