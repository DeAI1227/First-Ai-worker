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
      title={`${industryName} 產業`}
      subtitle="先看整理後摘要，再看相關股票與近期事件。沒有事件時不會產生假資料。"
      actions={
        <Button tone="secondary" onClick={reload}>
          <RefreshCcw className="h-4 w-4" />
          重新整理
        </Button>
      }
    >
      {loading ? <LoadingState label={`正在讀取 ${industryName} 產業資料`} /> : null}
      {error ? <ErrorState description={error} onRetry={reload} /> : null}

      {data ? (
        <div className="space-y-5">
          <Card className="space-y-4">
            <SectionHeader title={`${industryName} 研究摘要`} description="這裡聚合本產業近期事件，不逐篇堆疊新聞。" />
            <p className="text-sm leading-7 text-white/70">{buildPageDigest(industryName, events)}</p>
          </Card>

          <Card className="space-y-4">
            <SectionHeader title="相關追蹤股票" description="股票來自 reference data，不依賴事件是否存在。" />
            <div className="flex flex-wrap gap-2">
              {stocks.map((stock) => (
                <Link key={stock.stock_code} to={`/stocks/${stock.stock_code}`}>
                  <Badge tone="neutral">
                    {stock.stock_code} {stock.stock_name}
                  </Badge>
                </Link>
              ))}
              {stocks.length === 0 ? <div className="text-sm text-white/46">目前沒有設定相關股票。</div> : null}
            </div>
          </Card>

          <div className="space-y-4">
            <SectionHeader title="近期事件" description="先看摘要，再展開原始事件。" />
            {events.length === 0 ? (
              <EmptyState
                title={`${industryName} 目前沒有可讀事件`}
                description="如果今天沒有有效新聞，這裡會保持空白，由前端顯示 empty state。"
              />
            ) : (
              <details className="rounded-[24px] border border-white/8 bg-black/20 p-4">
                <summary className="cursor-pointer list-none text-sm font-medium text-white/80">
                  展開原始事件（{events.length} 則）
                </summary>
                <div className="mt-4 space-y-4">
                  {events.slice(0, 6).map((event) => <EventItem key={event.event_id} event={event} hideScopeLabel />)}
                </div>
              </details>
            )}
          </div>
        </div>
      ) : null}
    </PageFrame>
  );
}
