import { useCallback } from "react";
import { RefreshCcw } from "lucide-react";
import { useAsync } from "@/hooks/useAsync";
import { getStockCards } from "@/lib/queries";
import { PageFrame } from "@/components/layout/PageFrame";
import { Button } from "@/components/ui/Button";
import { LoadingState } from "@/components/ui/LoadingState";
import { ErrorState } from "@/components/ui/ErrorState";
import { SectionHeader } from "@/components/ui/SectionHeader";
import { StockRow } from "@/components/domain/StockRow";

export function StocksPage() {
  const loader = useCallback(() => getStockCards(), []);
  const { data, loading, error, reload } = useAsync(loader, [loader]);

  return (
    <PageFrame
      title="股票清單"
      subtitle="這裡的股票來自 reference data。即使今天沒有事件，股票仍然會出現在清單裡。"
      actions={
        <Button tone="secondary" onClick={reload}>
          <RefreshCcw className="h-4 w-4" />
          重新整理
        </Button>
      }
    >
      {loading ? <LoadingState label="正在載入追蹤股票清單…" /> : null}
      {error ? <ErrorState description={error} onRetry={reload} /> : null}

      {data ? (
        <div className="space-y-5">
          <SectionHeader title="Tracking Universe" description="點任一股票可進入詳情頁；沒有事件時，詳情頁會顯示 empty state。" />
          <div className="grid gap-4 md:grid-cols-2 xl:grid-cols-3">
            {data.map((stock) => (
              <StockRow key={stock.stock_code} stock={stock} />
            ))}
          </div>
        </div>
      ) : null}
    </PageFrame>
  );
}
