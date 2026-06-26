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
      subtitle="這裡聚合利率、通膨、就業、美元、殖利率、AI 資本支出與資料中心需求等總體事件。"
      actions={
        <Button tone="secondary" onClick={reload}>
          <RefreshCcw className="h-4 w-4" />
          重新整理
        </Button>
      }
    >
      {loading ? <LoadingState label="正在整理大環境事件" /> : null}
      {error ? <ErrorState description={error} onRetry={reload} /> : null}

      {data ? (
        <div className="space-y-4">
          <Card className="space-y-4">
            <SectionHeader title="大環境摘要" description="先看整理後摘要，再往下看事件細節。" />
            <p className="text-sm leading-7 text-white/70">{buildPageDigest("大環境", data)}</p>
          </Card>

          <SectionHeader title="大環境事件" description="顯示近期最值得先看的事件，避免同頁塞進太多重複卡片。" />
          {data.length === 0 ? (
            <EmptyState
              title="目前沒有大環境事件"
              description="如果今天沒有新的總體事件，這裡會保持空白，不會生成假事件。"
            />
          ) : (
            data.slice(0, 8).map((event) => <EventItem key={event.event_id} event={event} showQuality hideScopeLabel />)
          )}
        </div>
      ) : null}
    </PageFrame>
  );
}
