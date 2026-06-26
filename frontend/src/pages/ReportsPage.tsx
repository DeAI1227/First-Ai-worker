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
      subtitle="這裡顯示經過整理後的研究報告，而不是原始抓取內容。"
      actions={
        <Button tone="secondary" onClick={reload}>
          <RefreshCcw className="h-4 w-4" />
          重新整理
        </Button>
      }
    >
      {loading ? <LoadingState label="正在讀取研究報告" /> : null}
      {error ? <ErrorState description={error} onRetry={reload} /> : null}

      {data ? (
        <div className="space-y-4">
          <SectionHeader title="近期報告" description="只顯示可閱讀的報告內容，讓報告頁回到真正有資訊密度的狀態。" />
          {data.length === 0 ? (
            <EmptyState title="目前沒有研究報告" description="如果今天還沒有產出 report_packet，這裡會維持空白。" />
          ) : (
            data.map((report) => <ReportItem key={report.report_id} report={report} />)
          )}
        </div>
      ) : null}
    </PageFrame>
  );
}
