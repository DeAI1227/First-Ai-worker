import { Database, FileBarChart2, ShieldAlert, Clock3 } from "lucide-react";
import { Card } from "../ui/Card";

type Props = {
  userId: string;
  unreadEventCount: number;
  unreadReportCount: number;
  unreadTotalCount: number;
};

export function SystemSummaryCard({ userId, unreadEventCount, unreadReportCount, unreadTotalCount }: Props) {
  return (
    <Card className="space-y-4">
      <div className="flex items-center gap-3">
        <div className="flex h-11 w-11 items-center justify-center rounded-2xl border border-white/8 bg-white/5">
          <Database className="h-4 w-4 text-accent" />
        </div>
        <div>
          <div className="text-lg font-semibold text-white">系統總覽</div>
          <div className="text-xs text-white/42">使用者 ID：{userId}</div>
        </div>
      </div>

      <div className="grid gap-3">
        <div className="rounded-2xl border border-white/8 bg-black/20 p-4">
          <div className="flex items-center gap-2 text-xs text-white/48">
            <Clock3 className="h-3.5 w-3.5 text-white/35" />
            <span>未讀總數</span>
          </div>
          <div className="mt-2 text-2xl font-semibold text-white">{unreadTotalCount}</div>
        </div>

        <div className="grid grid-cols-2 gap-3">
          <div className="rounded-2xl border border-white/8 bg-black/20 p-4">
            <div className="flex items-center gap-2 text-xs text-white/48">
              <Database className="h-3.5 w-3.5 text-accent" />
              <span>事件未讀</span>
            </div>
            <div className="mt-2 text-xl font-semibold text-white">{unreadEventCount}</div>
          </div>

          <div className="rounded-2xl border border-white/8 bg-black/20 p-4">
            <div className="flex items-center gap-2 text-xs text-white/48">
              <FileBarChart2 className="h-3.5 w-3.5 text-white/55" />
              <span>報告未讀</span>
            </div>
            <div className="mt-2 text-xl font-semibold text-white">{unreadReportCount}</div>
          </div>
        </div>

        <div className="rounded-2xl border border-amber-400/15 bg-amber-400/10 p-4">
          <div className="flex items-center gap-2 text-xs text-amber-50/70">
            <ShieldAlert className="h-3.5 w-3.5" />
            <span>狀態說明 / user_read_status</span>
          </div>
          <p className="mt-2 text-sm leading-6 text-amber-50/85">
            已讀狀態獨立儲存在 `user_read_status`，不會直接寫回事件或報告本體。
          </p>
        </div>
      </div>
    </Card>
  );
}
