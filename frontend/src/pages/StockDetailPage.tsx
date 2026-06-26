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
      title={stock ? `${stock.stock_code} ${stock.stock_name}` : `股票 ${stockCode}`}
      subtitle="這裡顯示該股票的研究事件流。沒有事件時，只顯示 empty state。"
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
      {stockState.loading || eventState.loading ? <LoadingState label="正在讀取股票研究事件" /> : null}
      {stockState.error ? <ErrorState description={stockState.error} onRetry={stockState.reload} /> : null}
      {eventState.error ? <ErrorState description={eventState.error} onRetry={eventState.reload} /> : null}

      {stock ? (
        <div className="grid gap-5 xl:grid-cols-[1.1fr_0.9fr]">
          <Card className="space-y-4">
            <SectionHeader title="股票基本資料" description="股票來自 Supabase reference data，不依賴事件是否存在。" />
            <div className="flex flex-wrap gap-2">
              {stock.related_industries.length ? (
                stock.related_industries.map((industry) => (
                  <Badge key={industry} tone="neutral">
                    {industry}
                  </Badge>
                ))
              ) : (
                <Badge tone="neutral">大行關注</Badge>
              )}
            </div>
            <div className="grid grid-cols-2 gap-3">
              <Metric label="研究事件數" value={stock.recent_event_count} />
              <Metric label="最近更新" value={stock.latest_event_date ?? "無事件"} />
            </div>
          </Card>

          <Card className="space-y-4">
            <SectionHeader title="閱讀提醒" description="AI 只整理事件脈絡，不做價格方向判斷。" />
            <div className="flex items-start gap-3 rounded-2xl border border-amber-400/15 bg-amber-400/10 p-4 text-sm leading-6 text-amber-50">
              <ShieldAlert className="mt-0.5 h-4 w-4 shrink-0" />
              <div>
                <div className="font-medium">請回到來源交叉確認</div>
                <p className="mt-1 text-amber-50/80">
                  一檔股票有多則新聞時，系統會先統整成研究摘要，再保留來源供你回查。
                </p>
              </div>
            </div>
          </Card>
        </div>
      ) : null}

      <Card className="mt-5 space-y-4">
        <SectionHeader title="本頁研究摘要" description="這裡把該股票近期事件收斂成一段文字。" />
        <p className="text-sm leading-7 text-white/70">
          {buildPageDigest(stock ? `${stock.stock_code} ${stock.stock_name}` : stockCode, events)}
        </p>
      </Card>

      <div className="mt-5">
        <SectionHeader title="近期事件" description="只列出通過品質篩選的研究事件，避免大量雜訊卡片。" />
      </div>

      {events.length === 0 && !eventState.loading ? (
        <div className="mt-4">
          <EmptyState
            title="目前沒有可讀事件"
            description="如果今天沒有有效新聞，這裡會保持空白，不會塞入『無重大更新』假資料。"
          />
        </div>
      ) : null}

      <div className="mt-4 space-y-4">
        {events.slice(0, 6).map((event) => (
          <EventItem key={event.event_id} event={event} />
        ))}
      </div>
    </PageFrame>
  );
}

function Metric({ label, value }: { label: string; value: string | number }) {
  return (
    <div className="rounded-2xl border border-white/8 bg-black/20 p-4">
      <div className="text-[11px] text-white/42">{label}</div>
      <div className="mt-1 text-xl font-semibold text-white">{value}</div>
    </div>
  );
}
