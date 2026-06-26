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
      subtitle="聚合 3665、2330、2454、2308 等大行關注股票的研究事件。"
      actions={
        <Button tone="secondary" onClick={reload}>
          <RefreshCcw className="h-4 w-4" />
          重新整理
        </Button>
      }
    >
      {loading ? <LoadingState label="正在讀取大行關注事件" /> : null}
      {error ? <ErrorState description={error} onRetry={reload} /> : null}

      {data ? (
        <div className="space-y-4">
          <Card className="space-y-4">
            <SectionHeader title="大行關注摘要" description="先把事件收斂成摘要，避免一次看到太多雜訊卡片。" />
            <p className="text-sm leading-7 text-white/70">{buildPageDigest("大行關注", data)}</p>
          </Card>

          <SectionHeader title="近期事件" description="只保留通過品質篩選的研究事件。" />
          {data.length === 0 ? (
            <EmptyState title="目前沒有大行關注事件" description="沒有有效事件時不會生成假資料。" />
          ) : (
            data.slice(0, 6).map((event) => <EventItem key={event.event_id} event={event} showQuality hideScopeLabel />)
          )}
        </div>
      ) : null}
    </PageFrame>
  );
}
