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
          <div className="text-lg font-semibold text-white">系統狀態</div>
          <div className="text-xs text-white/42">使用者：{userId}</div>
        </div>
      </div>

      <div className="grid gap-3">
        <div className="rounded-2xl border border-white/8 bg-black/20 p-3">
          <div className="text-[11px] text-white/42">未讀事件</div>
          <div className="mt-1 text-xl font-semibold text-white">{unreadEventCount}</div>
        </div>
        <div className="rounded-2xl border border-white/8 bg-black/20 p-3">
          <div className="text-[11px] text-white/42">未讀報告</div>
          <div className="mt-1 text-xl font-semibold text-white">{unreadReportCount}</div>
        </div>
        <div className="rounded-2xl border border-accent/15 bg-accent/10 p-3">
          <div className="text-[11px] text-white/42">總未讀</div>
          <div className="mt-1 text-xl font-semibold text-white">{unreadTotalCount}</div>
        </div>
      </div>

      <div className="grid gap-2 text-xs text-white/45">
        <div className="flex items-center gap-2">
          <Clock3 className="h-3.5 w-3.5 text-accent" />
          <span>前端只讀 Supabase production views</span>
        </div>
        <div className="flex items-center gap-2">
          <ShieldAlert className="h-3.5 w-3.5 text-amber-300" />
          <span>未讀狀態寫入 user_read_status</span>
        </div>
        <div className="flex items-center gap-2">
          <FileBarChart2 className="h-3.5 w-3.5 text-sky-300" />
          <span>資料品質摘要會顯示在事件與報告</span>
        </div>
      </div>
    </Card>
  );
}
