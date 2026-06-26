import { NavLink } from "react-router-dom";
import { ChevronRight, Database, Radio } from "lucide-react";
import { NAV_ITEMS, NAV_META } from "@/lib/navigation";
import { cn } from "@/lib/utils";

type SidebarProps = {
  onNavigate?: () => void;
};

export function Sidebar({ onNavigate }: SidebarProps) {
  return (
    <div className="flex h-full flex-col gap-6 p-5">
      <div className="rounded-3xl border border-white/8 bg-white/5 p-5 shadow-glow">
        <div className="flex items-center gap-3">
          <div className="flex h-11 w-11 items-center justify-center rounded-2xl bg-gradient-to-br from-accent/25 to-accent-2/25 ring-1 ring-white/10">
            <Radio className="h-5 w-5 text-accent" />
          </div>
          <div>
            <div className="text-sm font-semibold tracking-wide text-white/90">AI 投資研究終端</div>
            <div className="text-xs text-white/45">Supabase production views only</div>
          </div>
        </div>

        <div className="mt-4 grid gap-2">
          {NAV_META.map((item) => (
            <div
              key={item.label}
              className="flex items-center justify-between rounded-2xl border border-white/6 bg-black/20 px-3 py-2 text-xs text-white/75"
            >
              <div className="flex items-center gap-2">
                <item.icon className="h-3.5 w-3.5 text-accent" />
                <span>{item.label}</span>
              </div>
              <span className="text-white/50">{item.value}</span>
            </div>
          ))}
        </div>
      </div>

      <nav className="space-y-1">
        {NAV_ITEMS.map((item) => (
          <NavLink
            key={item.path}
            to={item.path}
            onClick={onNavigate}
            className={({ isActive }) =>
              cn(
                "group flex items-center gap-3 rounded-2xl border px-4 py-3 text-sm transition",
                isActive
                  ? "border-accent/30 bg-accent/10 text-white shadow-[0_0_0_1px_rgba(45,212,191,0.12)]"
                  : "border-transparent bg-transparent text-white/72 hover:border-white/8 hover:bg-white/5 hover:text-white",
              )
            }
          >
            <item.icon className="h-4 w-4 text-current" />
            <span className="flex-1">{item.label}</span>
            <ChevronRight className="h-4 w-4 text-white/30 transition group-hover:text-white/60" />
          </NavLink>
        ))}
      </nav>

      <div className="mt-auto rounded-3xl border border-white/8 bg-white/5 p-4">
        <div className="flex items-center gap-2 text-xs text-white/55">
          <Database className="h-3.5 w-3.5 text-accent" />
          <span>資料中心</span>
        </div>
        <div className="mt-2 text-sm font-medium text-white/90">Supabase production views</div>
        <p className="mt-2 text-xs leading-5 text-white/45">
          這個前端只讀正式 views，不讀 Python、不讀 output JSON，也不自己生成假事件。
        </p>
      </div>
    </div>
  );
}
