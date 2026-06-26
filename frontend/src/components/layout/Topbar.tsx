import { Menu, Search, Bell, Settings2, X } from "lucide-react";
import { NavLink, useLocation } from "react-router-dom";
import { NAV_ITEMS } from "@/lib/navigation";
import { cn } from "@/lib/utils";

type TopbarProps = {
  mobileMenuOpen: boolean;
  onMenuToggle: () => void;
};

export function Topbar({ mobileMenuOpen, onMenuToggle }: TopbarProps) {
  const location = useLocation();
  const current = NAV_ITEMS.find((item) => item.path === location.pathname)?.label ?? "總覽";

  return (
    <header className="sticky top-0 z-30 border-b border-white/5 bg-[#07111f]/90 backdrop-blur-xl">
      <div className="flex items-center gap-3 px-4 py-3 sm:px-6 lg:px-8">
        <button
          type="button"
          onClick={onMenuToggle}
          className="inline-flex h-10 w-10 items-center justify-center rounded-2xl border border-white/8 bg-white/5 text-white/80 transition hover:bg-white/8 lg:hidden"
          aria-label="切換選單"
        >
          {mobileMenuOpen ? <X className="h-4 w-4" /> : <Menu className="h-4 w-4" />}
        </button>

        <div className="flex flex-1 flex-col">
          <div className="text-xs uppercase tracking-[0.32em] text-white/35">Research Terminal</div>
          <div className="text-lg font-semibold text-white">{current}</div>
        </div>

        <div className="hidden min-w-[320px] items-center gap-3 rounded-2xl border border-white/8 bg-white/5 px-4 py-3 lg:flex">
          <Search className="h-4 w-4 text-white/35" />
          <span className="text-sm text-white/40">搜尋事件、產業、股票或報告</span>
        </div>

        <div className="flex items-center gap-2">
          <div className="rounded-2xl border border-white/8 bg-white/5 px-3 py-2 text-xs text-white/70">
            只讀 Supabase
          </div>
          <div className="flex h-10 w-10 items-center justify-center rounded-2xl border border-white/8 bg-white/5">
            <Bell className="h-4 w-4 text-white/70" />
          </div>
          <NavLink to="/settings" className="flex h-10 w-10 items-center justify-center rounded-2xl border border-white/8 bg-white/5">
            <Settings2 className="h-4 w-4 text-white/70" />
          </NavLink>
        </div>
      </div>

      <div className="border-t border-white/5 bg-white/[0.02] px-4 py-3 sm:px-6 lg:hidden">
        <div className="flex gap-2 overflow-x-auto">
          {NAV_ITEMS.map((item) => (
            <NavLink
              key={item.path}
              to={item.path}
              className={cn(
                "whitespace-nowrap rounded-full border px-3 py-1.5 text-xs transition",
                location.pathname === item.path
                  ? "border-accent/30 bg-accent/10 text-white"
                  : "border-white/8 bg-white/5 text-white/60",
              )}
            >
              {item.label}
            </NavLink>
          ))}
        </div>
      </div>
    </header>
  );
}
