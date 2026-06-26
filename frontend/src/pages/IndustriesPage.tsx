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
      subtitle="六大產業由 reference data 固定呈現。即使今天沒有事件，產業卡片仍會存在。"
      actions={
        <Button tone="secondary" onClick={reload}>
          <RefreshCcw className="h-4 w-4" />
          重新整理
        </Button>
      }
    >
      {loading ? <LoadingState label="正在讀取產業卡片" /> : null}
      {error ? <ErrorState description={error} onRetry={reload} /> : null}

      {data ? (
        <div className="space-y-5">
          <SectionHeader
            title="六大產業"
            description="點擊任一產業可進入詳情頁，查看整理後摘要、相關股票與近期事件。"
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
