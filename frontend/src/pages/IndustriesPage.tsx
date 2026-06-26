import { useCallback } from "react";
import { RefreshCcw } from "lucide-react";
import { useAsync } from "@/hooks/useAsync";
import { getIndustryCards } from "@/lib/queries";
import { PageFrame } from "@/components/layout/PageFrame";
import { Button } from "@/components/ui/Button";
import { LoadingState } from "@/components/ui/LoadingState";
import { ErrorState } from "@/components/ui/ErrorState";
import { SectionHeader } from "@/components/ui/SectionHeader";
import { IndustryCardItem } from "@/components/domain/IndustryCardItem";

export function IndustriesPage() {
  const loader = useCallback(() => getIndustryCards(), []);
  const { data, loading, error, reload } = useAsync(loader, [loader]);

  return (
    <PageFrame
      title="產業追蹤"
      subtitle="先看六大產業的整體狀態，再點進去看該產業的摘要、相關股票與事件內容。"
      actions={
        <Button tone="secondary" onClick={reload}>
          <RefreshCcw className="h-4 w-4" />
          重新整理
        </Button>
      }
    >
      {loading ? <LoadingState label="正在載入六大產業卡片…" /> : null}
      {error ? <ErrorState description={error} onRetry={reload} /> : null}

      {data ? (
        <div className="space-y-5">
          <SectionHeader
            title="六大產業"
            description="點卡片可以進入產業明細頁。這裡只顯示聚合後的卡片，不把原始事件整片攤開。"
          />
          <div className="grid gap-4 xl:grid-cols-2">
            {data.map((industry) => (
              <IndustryCardItem key={industry.industry_name} industry={industry} />
            ))}
          </div>
        </div>
      ) : null}
    </PageFrame>
  );
}
