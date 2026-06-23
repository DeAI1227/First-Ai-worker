import { useCallback } from "react";
import { useParams } from "react-router-dom";
import { RefreshCcw, ShieldAlert } from "lucide-react";
import { useAsync } from "@/hooks/useAsync";
import { getStockCards, getStockDetailEvents } from "@/lib/queries";
import { PageFrame } from "@/components/layout/PageFrame";
import { Button } from "@/components/ui/Button";
import { LoadingState } from "@/components/ui/LoadingState";
import { ErrorState } from "@/components/ui/ErrorState";
import { SectionHeader } from "@/components/ui/SectionHeader";
import { Card } from "@/components/ui/Card";
import { EventItem } from "@/components/domain/EventItem";
import { EmptyState } from "@/components/ui/EmptyState";
import { Badge } from "@/components/ui/Badge";

export function StockDetailPage() {
  const params = useParams<{ stockCode: string }>();
  const stockCode = params.stockCode ?? "";

  const stockLoader = useCallback(async () => {
    const cards = await getStockCards();
    return cards.find((item) => item.stock_code === stockCode) ?? null;
  }, [stockCode]);

  const eventsLoader = useCallback(() => getStockDetailEvents(stockCode), [stockCode]);

  const stockState = useAsync(stockLoader, [stockLoader]);
  const eventState = useAsync(eventsLoader, [eventsLoader]);

  const stock = stockState.data;
  const events = eventState.data ?? [];

  return (
    <PageFrame
      title={stock ? `${stock.stock_code} ${stock.stock_name}` : `股票詳情 ${stockCode}`}
      subtitle="股票詳情頁只顯示與該股票關聯的事件流。沒有事件時，前端會顯示乾淨的 empty state。"
      actions={
        <Button tone="secondary" onClick={() => {
          stockState.reload();
          eventState.reload();
        }}>
          <RefreshCcw className="h-4 w-4" />
          重新整理
        </Button>
      }
    >
      {stockState.loading || eventState.loading ? <LoadingState label="正在載入股票事件流…" /> : null}
      {stockState.error ? <ErrorState description={stockState.error} onRetry={stockState.reload} /> : null}
      {eventState.error ? <ErrorState description={eventState.error} onRetry={eventState.reload} /> : null}

      {stock ? (
        <div className="grid gap-5 xl:grid-cols-[1.1fr_0.9fr]">
          <Card className="space-y-4">
            <SectionHeader
              title="股票資訊"
              description="股票資料來自 stocks reference data + stock_industries 關聯。"
            />
            <div className="flex flex-wrap gap-2">
              {stock.related_industries.map((industry) => (
                <Badge key={industry} tone="neutral">
                  {industry}
                </Badge>
              ))}
            </div>
            <div className="grid grid-cols-2 gap-3">
              <div className="rounded-2xl border border-white/8 bg-black/20 p-4">
                <div className="text-[11px] text-white/42">事件數</div>
                <div className="mt-1 text-xl font-semibold text-white">{stock.recent_event_count}</div>
              </div>
              <div className="rounded-2xl border border-white/8 bg-black/20 p-4">
                <div className="text-[11px] text-white/42">最近更新</div>
                <div className="mt-1 text-xl font-semibold text-white">{stock.latest_event_date ?? "—"}</div>
              </div>
            </div>
            <div className="rounded-2xl border border-white/8 bg-accent/10 p-4 text-sm leading-6 text-white/70">
              如果沒有事件，這個頁面不會製造假資料；前端會自然顯示 empty state。
            </div>
          </Card>

          <Card className="space-y-4">
            <SectionHeader
              title="注意事項"
              description="不要把沒有事件的股票硬生成成「無重大更新」JSON。"
            />
            <div className="flex items-start gap-3 rounded-2xl border border-amber-400/15 bg-amber-400/10 p-4 text-sm leading-6 text-amber-50">
              <ShieldAlert className="mt-0.5 h-4 w-4 shrink-0" />
              <div>
                <div className="font-medium">無事件時的處理方式</div>
                <p className="mt-1 text-amber-50/80">
                  後端保持沉默，前端顯示 empty state。這樣才能維持事件資料的真實性。
                </p>
              </div>
            </div>
          </Card>
        </div>
      ) : null}

      <div className="mt-5">
        <SectionHeader title="事件流" description="一則事件可關聯多檔股票，這裡只顯示該股票相關事件。" />
      </div>

      {events.length === 0 && !eventState.loading ? (
        <div className="mt-4">
          <EmptyState
            title="目前沒有可顯示的事件"
            description="這支股票今天沒有事件，不代表系統失效，只代表沒有偵測到有效事件。"
          />
        </div>
      ) : null}

      <div className="mt-4 space-y-4">
        {events.map((event) => (
          <EventItem key={event.event_id} event={event} />
        ))}
      </div>
    </PageFrame>
  );
}
