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
      subtitle="六大產業卡片以事件覆蓋與最新更新時間呈現，沒有事件時仍會保留產業卡片。"
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
            description="散熱、電力、自動駕駛、機器人、CPO 光通訊、網通。"
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
