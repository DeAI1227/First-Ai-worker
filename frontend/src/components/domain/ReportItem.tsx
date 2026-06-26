import { BookOpenText } from "lucide-react";
import type { RecentReport } from "@/lib/types";
import { formatDate } from "@/lib/format";
import { Card } from "../ui/Card";
import { ImportanceBadge } from "./ImportanceBadge";
import { QualitySummaryMini } from "../ui/QualitySummaryMini";
import { Badge } from "../ui/Badge";

type Props = {
  report: RecentReport;
};

export function ReportItem({ report }: Props) {
  return (
    <Card className="space-y-4">
      <div className="flex items-start justify-between gap-4">
        <div className="space-y-2">
          <div className="flex flex-wrap items-center gap-2">
            <ImportanceBadge importance={report.importance} />
            <Badge tone="neutral">{report.report_type}</Badge>
            <span className="text-xs text-white/42">{formatDate(report.report_date)}</span>
          </div>
          <div className="text-lg font-semibold leading-7 text-white">{report.report_title}</div>
          <p className="text-sm leading-6 text-white/56 whitespace-pre-line">{report.report_body}</p>
        </div>
        <div className="flex shrink-0 items-center gap-2 text-white/30">
          <BookOpenText className="h-4 w-4" />
        </div>
      </div>
      <QualitySummaryMini summary={report.quality_summary} />
    </Card>
  );
}
