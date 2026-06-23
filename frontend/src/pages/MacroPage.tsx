import { useCallback } from "react";
import { RefreshCcw } from "lucide-react";
import { useAsync } from "@/hooks/useAsync";
import { getMacroEvents } from "@/lib/queries";
import { PageFrame } from "@/components/layout/PageFrame";
import { Button } from "@/components/ui/Button";
import { LoadingState } from "@/components/ui/LoadingState";
import { ErrorState } from "@/components/ui/ErrorState";
import { EventItem } from "@/components/domain/EventItem";
import { SectionHeader } from "@/components/ui/SectionHeader";
import { EmptyState } from "@/components/ui/EmptyState";

export function MacroPage() {
  const loader = useCallback(() => getMacroEvents(), []);
  const { data, loading, error, reload } = useAsync(loader, [loader]);

  return (
    <PageFrame
      title="大環境"
      subtitle="聚焦 FED、CPI、PPI、就業、十年期美債殖利率、美元指數、AI 資本支出、資料中心需求。"
      actions={
        <Button tone="secondary" onClick={reload}>
          <RefreshCcw className="h-4 w-4" />
          重新整理
        </Button>
      }
    >
      {loading ? <LoadingState label="正在載入大環境事件…" /> : null}
      {error ? <ErrorState description={error} onRetry={reload} /> : null}

      {data ? (
        <div className="space-y-4">
          <SectionHeader title="宏觀事件流" description="每則事件都會保留摘要、可能影響、風險提醒與品質摘要。" />
          {data.length === 0 ? (
            <EmptyState
              title="目前沒有大環境事件"
              description="今天沒有觀察到可寫入的宏觀事件，請稍後再查看。"
            />
          ) : (
            data.map((event) => <EventItem key={event.event_id} event={event} showQuality />)
          )}
        </div>
      ) : null}
    </PageFrame>
  );
}
