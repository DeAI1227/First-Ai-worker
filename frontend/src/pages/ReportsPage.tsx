import { useCallback } from "react";
import { RefreshCcw } from "lucide-react";
import { useAsync } from "@/hooks/useAsync";
import { getRecentReports } from "@/lib/queries";
import { PageFrame } from "@/components/layout/PageFrame";
import { Button } from "@/components/ui/Button";
import { LoadingState } from "@/components/ui/LoadingState";
import { ErrorState } from "@/components/ui/ErrorState";
import { SectionHeader } from "@/components/ui/SectionHeader";
import { ReportItem } from "@/components/domain/ReportItem";
import { EmptyState } from "@/components/ui/EmptyState";

export function ReportsPage() {
  const loader = useCallback(() => getRecentReports(), []);
  const { data, loading, error, reload } = useAsync(loader, [loader]);

  return (
    <PageFrame
      title="研究報告"
      subtitle="三日完整研究報告、重大事件偵測報告與各類 scope 報告都會在這裡出現。"
      actions={
        <Button tone="secondary" onClick={reload}>
          <RefreshCcw className="h-4 w-4" />
          重新整理
        </Button>
      }
    >
      {loading ? <LoadingState label="正在載入研究報告…" /> : null}
      {error ? <ErrorState description={error} onRetry={reload} /> : null}

      {data ? (
        <div className="space-y-4">
          <SectionHeader title="近期報告" description="報告頁像知識庫，不是新聞列表。" />
          {data.length === 0 ? (
            <EmptyState
              title="目前沒有研究報告"
              description="暫時還沒有可閱讀的研究報告。"
            />
          ) : (
            data.map((report) => <ReportItem key={report.report_id} report={report} />)
          )}
        </div>
      ) : null}
    </PageFrame>
  );
}
