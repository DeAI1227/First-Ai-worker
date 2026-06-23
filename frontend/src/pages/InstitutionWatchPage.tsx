import { useCallback } from "react";
import { RefreshCcw } from "lucide-react";
import { useAsync } from "@/hooks/useAsync";
import { getInstitutionWatchEvents } from "@/lib/queries";
import { PageFrame } from "@/components/layout/PageFrame";
import { Button } from "@/components/ui/Button";
import { LoadingState } from "@/components/ui/LoadingState";
import { ErrorState } from "@/components/ui/ErrorState";
import { EventItem } from "@/components/domain/EventItem";
import { SectionHeader } from "@/components/ui/SectionHeader";
import { EmptyState } from "@/components/ui/EmptyState";

export function InstitutionWatchPage() {
  const loader = useCallback(() => getInstitutionWatchEvents(), []);
  const { data, loading, error, reload } = useAsync(loader, [loader]);

  return (
    <PageFrame
      title="大行關注"
      subtitle="追蹤 3665 貿聯-KY、2330 台積電、2454 聯發科、2308 台達電等大行關注股。"
      actions={
        <Button tone="secondary" onClick={reload}>
          <RefreshCcw className="h-4 w-4" />
          重新整理
        </Button>
      }
    >
      {loading ? <LoadingState label="正在載入大行關注事件…" /> : null}
      {error ? <ErrorState description={error} onRetry={reload} /> : null}

      {data ? (
        <div className="space-y-4">
          <SectionHeader title="關注事件流" description="這裡只顯示關聯到 institution_watch 的研究事件。" />
          {data.length === 0 ? (
            <EmptyState
              title="目前沒有大行關注事件"
              description="今天沒有大行關注事件，前端會以空狀態呈現。"
            />
          ) : (
            data.map((event) => <EventItem key={event.event_id} event={event} showQuality />)
          )}
        </div>
      ) : null}
    </PageFrame>
  );
}
