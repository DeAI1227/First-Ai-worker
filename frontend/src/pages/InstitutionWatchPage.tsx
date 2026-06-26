import { useCallback } from "react";
import { RefreshCcw } from "lucide-react";
import { useAsync } from "@/hooks/useAsync";
import { getInstitutionWatchEvents } from "@/lib/queries";
import { buildPageDigest } from "@/lib/presentation";
import { PageFrame } from "@/components/layout/PageFrame";
import { Button } from "@/components/ui/Button";
import { LoadingState } from "@/components/ui/LoadingState";
import { ErrorState } from "@/components/ui/ErrorState";
import { EventItem } from "@/components/domain/EventItem";
import { SectionHeader } from "@/components/ui/SectionHeader";
import { EmptyState } from "@/components/ui/EmptyState";
import { Card } from "@/components/ui/Card";

export function InstitutionWatchPage() {
  const loader = useCallback(() => getInstitutionWatchEvents(), []);
  const { data, loading, error, reload } = useAsync(loader, [loader]);

  return (
    <PageFrame
      title="大行關注"
      subtitle="聚合大行關注股票與供應鏈相關事件，讓你先看重點，不必自己消化一大串雜訊。"
      actions={
        <Button tone="secondary" onClick={reload}>
          <RefreshCcw className="h-4 w-4" />
          重新整理
        </Button>
      }
    >
      {loading ? <LoadingState label="正在整理大行關注事件" /> : null}
      {error ? <ErrorState description={error} onRetry={reload} /> : null}

      {data ? (
        <div className="space-y-4">
          <Card className="space-y-4">
            <SectionHeader title="大行關注摘要" description="先把事件整理成一段摘要，避免你一次看到太多沒有意義的卡片。" />
            <p className="text-sm leading-7 text-white/70">{buildPageDigest("大行關注", data)}</p>
          </Card>

          <SectionHeader title="近期事件" description="只保留近期較有閱讀價值的事件卡片。" />
          {data.length === 0 ? (
            <EmptyState
              title="目前沒有大行關注事件"
              description="如果今天沒有相關事件，前端會顯示空狀態，不會生成假資料。"
            />
          ) : (
            data.slice(0, 8).map((event) => <EventItem key={event.event_id} event={event} showQuality hideScopeLabel />)
          )}
        </div>
      ) : null}
    </PageFrame>
  );
}
