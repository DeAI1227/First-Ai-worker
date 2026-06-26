import { ArrowUpRight } from "lucide-react";
import { Link } from "react-router-dom";
import type { StockCard } from "@/lib/types";
import { Card } from "../ui/Card";
import { Badge } from "../ui/Badge";
import { formatDate } from "@/lib/format";

type Props = {
  stock: StockCard;
};

export function StockRow({ stock }: Props) {
  return (
    <Link to={`/stocks/${stock.stock_code}`} className="block">
      <Card className="group transition hover:border-accent/20 hover:bg-white/[0.05]">
        <div className="flex items-start justify-between gap-4">
          <div className="space-y-3">
            <div>
              <div className="text-xl font-semibold text-white">{stock.stock_code}</div>
              <div className="mt-1 text-sm text-white/60">{stock.stock_name}</div>
            </div>
            <div className="flex flex-wrap gap-2">
              {stock.related_industries.length ? (
                stock.related_industries.map((industry) => (
                  <Badge key={industry} tone="neutral">
                    {industry}
                  </Badge>
                ))
              ) : (
                <Badge tone="neutral">大行關注</Badge>
              )}
            </div>
          </div>
          <ArrowUpRight className="h-4 w-4 text-white/30 transition group-hover:text-white/70" />
        </div>

        <div className="mt-4 grid grid-cols-2 gap-3 text-sm">
          <div className="rounded-2xl border border-white/8 bg-black/20 p-3">
            <div className="text-[11px] text-white/42">研究事件數</div>
            <div className="mt-1 text-lg font-semibold text-white">{stock.recent_event_count}</div>
          </div>
          <div className="rounded-2xl border border-white/8 bg-black/20 p-3">
            <div className="text-[11px] text-white/42">最近更新</div>
            <div className="mt-1 text-lg font-semibold text-white">{formatDate(stock.latest_event_date)}</div>
          </div>
        </div>
      </Card>
    </Link>
  );
}
