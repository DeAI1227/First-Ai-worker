import { useCallback } from "react";
import { RefreshCcw } from "lucide-react";
import { useAsync } from "@/hooks/useAsync";
import { getMacroEvents } from "@/lib/queries";
import { buildPageDigest } from "@/lib/presentation";
import { PageFrame } from "@/components/layout/PageFrame";
import { Button } from "@/components/ui/Button";
import { LoadingState } from "@/components/ui/LoadingState";
import { ErrorState } from "@/components/ui/ErrorState";
import { EventItem } from "@/components/domain/EventItem";
import { SectionHeader } from "@/components/ui/SectionHeader";
import { EmptyState } from "@/components/ui/EmptyState";
import { Card } from "@/components/ui/Card";

export function MacroPage() {
  const loader = useCallback(() => getMacroEvents(), []);
  const { data, loading, error, reload } = useAsync(loader, [loader]);

  return (
    <PageFrame
      title="大環境"
      subtitle="追蹤 FED、CPI、PPI、就業、美債殖利率、美元指數、AI 資本支出與資料中心需求。"
      actions={
        <Button tone="secondary" onClick={reload}>
          <RefreshCcw className="h-4 w-4" />
          重新整理
        </Button>
      }
    >
      {loading ? <LoadingState label="正在讀取大環境事件" /> : null}
      {error ? <ErrorState description={error} onRetry={reload} /> : null}

      {data ? (
        <div className="space-y-4">
          <Card className="space-y-4">
            <SectionHeader title="大環境摘要" description="先看聚合摘要，再看事件細節。" />
            <p className="text-sm leading-7 text-white/70">{buildPageDigest("大環境", data)}</p>
          </Card>

          <SectionHeader title="近期事件" description="只顯示已通過資料品質篩選的大環境事件。" />
          {data.length === 0 ? (
            <EmptyState title="目前沒有大環境事件" description="沒有有效事件時不會生成假事件。" />
          ) : (
            data.slice(0, 6).map((event) => <EventItem key={event.event_id} event={event} showQuality hideScopeLabel />)
          )}
        </div>
      ) : null}
    </PageFrame>
  );
}
