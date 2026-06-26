import { useCallback } from "react";
import { useParams } from "react-router-dom";
import { RefreshCcw, ShieldAlert } from "lucide-react";
import { useAsync } from "@/hooks/useAsync";
import { getStockCards, getStockDetailEvents } from "@/lib/queries";
import { buildPageDigest } from "@/lib/presentation";
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
      subtitle="股票是 reference data，事件才是研究內容。沒有事件時，這頁會顯示空狀態，不會硬塞假新聞。"
      actions={
        <Button
          tone="secondary"
          onClick={() => {
            stockState.reload();
            eventState.reload();
          }}
        >
          <RefreshCcw className="h-4 w-4" />
          重新整理
        </Button>
      }
    >
      {stockState.loading || eventState.loading ? <LoadingState label="正在整理股票事件" /> : null}
      {stockState.error ? <ErrorState description={stockState.error} onRetry={stockState.reload} /> : null}
      {eventState.error ? <ErrorState description={eventState.error} onRetry={eventState.reload} /> : null}

      {stock ? (
        <div className="grid gap-5 xl:grid-cols-[1.1fr_0.9fr]">
          <Card className="space-y-4">
            <SectionHeader title="股票基本資訊" description="這些資訊來自 stocks 與 stock_industries，不依賴事件是否存在。" />
            <div className="flex flex-wrap gap-2">
              {stock.related_industries.map((industry) => (
                <Badge key={industry} tone="neutral">
                  {industry}
                </Badge>
              ))}
            </div>
            <div className="grid grid-cols-2 gap-3">
              <div className="rounded-2xl border border-white/8 bg-black/20 p-4">
                <div className="text-[11px] text-white/42">資料庫事件數</div>
                <div className="mt-1 text-xl font-semibold text-white">{stock.recent_event_count}</div>
              </div>
              <div className="rounded-2xl border border-white/8 bg-black/20 p-4">
                <div className="text-[11px] text-white/42">最近更新</div>
                <div className="mt-1 text-xl font-semibold text-white">{stock.latest_event_date ?? "—"}</div>
              </div>
            </div>
            <div className="rounded-2xl border border-white/8 bg-accent/10 p-4 text-sm leading-6 text-white/70">
              就算這支股票今天沒有事件，它仍然應該出現在股票清單中；只有事件流會是空的。
            </div>
          </Card>

          <Card className="space-y-4">
            <SectionHeader title="使用提醒" description="這裡顯示的是研究事件，不是股價系統，也不是投資建議工具。" />
            <div className="flex items-start gap-3 rounded-2xl border border-amber-400/15 bg-amber-400/10 p-4 text-sm leading-6 text-amber-50">
              <ShieldAlert className="mt-0.5 h-4 w-4 shrink-0" />
              <div>
                <div className="font-medium">請把這裡當成研究終端</div>
                <p className="mt-1 text-amber-50/80">
                  這些內容用來看事件脈絡、供應鏈關聯與後續追蹤方向，不直接提供買賣建議。
                </p>
              </div>
            </div>
          </Card>
        </div>
      ) : null}

      {events.length > 0 ? (
        <Card className="mt-5 space-y-4">
          <SectionHeader title="股票摘要" description="先看一段摘要，再決定要不要往下讀完整事件卡。" />
          <p className="text-sm leading-7 text-white/70">
            {buildPageDigest(stock ? `${stock.stock_code} ${stock.stock_name}` : stockCode, events)}
          </p>
        </Card>
      ) : null}

      <div className="mt-5">
        <SectionHeader title="事件流" description="只顯示與這支股票真的有關的事件。" />
      </div>

      {events.length === 0 && !eventState.loading ? (
        <div className="mt-4">
          <EmptyState
            title="目前沒有這支股票的事件"
            description="如果今天沒有找到可用事件，這一頁會保持乾淨，不會塞入『無重大更新』之類的假內容。"
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
