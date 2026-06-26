import { useCallback } from "react";
import { Link, useParams } from "react-router-dom";
import { RefreshCcw } from "lucide-react";
import { useAsync } from "@/hooks/useAsync";
import { getDashboardEvents, getStockCards } from "@/lib/queries";
import { buildPageDigest } from "@/lib/presentation";
import { getIndustryNameByKey } from "@/lib/referenceData";
import { PageFrame } from "@/components/layout/PageFrame";
import { Button } from "@/components/ui/Button";
import { LoadingState } from "@/components/ui/LoadingState";
import { ErrorState } from "@/components/ui/ErrorState";
import { SectionHeader } from "@/components/ui/SectionHeader";
import { Card } from "@/components/ui/Card";
import { EmptyState } from "@/components/ui/EmptyState";
import { EventItem } from "@/components/domain/EventItem";
import { Badge } from "@/components/ui/Badge";

export function IndustryDetailPage() {
  const params = useParams<{ industryKey: string }>();
  const industryName = getIndustryNameByKey(params.industryKey ?? "");

  const loader = useCallback(async () => {
    const [events, stocks] = await Promise.all([getDashboardEvents(), getStockCards()]);

    return {
      events: events.filter((item) => item.scope === "industry" && item.scope_name === industryName),
      stocks: stocks.filter((item) => item.related_industries.includes(industryName)),
    };
  }, [industryName]);

  const { data, loading, error, reload } = useAsync(loader, [loader]);
  const events = data?.events ?? [];
  const stocks = data?.stocks ?? [];

  return (
    <PageFrame
      title={`${industryName} 產業頁`}
      subtitle="這裡顯示單一產業的事件摘要、相關追蹤股票與近期事件。沒有事件時，只顯示乾淨的空狀態，不會用假資料填滿。"
      actions={
        <Button tone="secondary" onClick={reload}>
          <RefreshCcw className="h-4 w-4" />
          重新整理
        </Button>
      }
    >
      {loading ? <LoadingState label={`正在整理 ${industryName} 產業資料`} /> : null}
      {error ? <ErrorState description={error} onRetry={reload} /> : null}

      {data ? (
        <div className="space-y-5">
          <Card className="space-y-4">
            <SectionHeader title={`${industryName} 研究摘要`} description="先把事件整理成一段能讀的摘要，而不是讓你自己看一整排零碎卡片。" />
            <p className="text-sm leading-7 text-white/70">{buildPageDigest(industryName, events)}</p>
          </Card>

          <Card className="space-y-4">
            <SectionHeader title="相關追蹤股票" description="股票名單來自 reference data。就算今天沒有事件，股票仍然存在於清單中。" />
            <div className="flex flex-wrap gap-2">
              {stocks.map((stock) => (
                <Link key={stock.stock_code} to={`/stocks/${stock.stock_code}`}>
                  <Badge tone="neutral">
                    {stock.stock_code} {stock.stock_name}
                  </Badge>
                </Link>
              ))}
              {stocks.length === 0 ? <div className="text-sm text-white/46">目前沒有對應股票資料。</div> : null}
            </div>
          </Card>

          <div className="space-y-4">
            <SectionHeader title="近期事件" description="只顯示整理後仍然有價值的事件，不再把一大堆雜訊原樣堆到畫面上。" />
            {events.length === 0 ? (
              <EmptyState
                title={`${industryName} 目前沒有事件`}
                description="今天這個產業沒有可用事件時，前端會直接顯示空狀態，不會生成『今日未找到重大更新』之類的假內容。"
              />
            ) : (
              events.slice(0, 8).map((event) => <EventItem key={event.event_id} event={event} hideScopeLabel />)
            )}
          </div>
        </div>
      ) : null}
    </PageFrame>
  );
}
