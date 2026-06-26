import {
  Activity,
  Building2,
  Brain,
  Database,
  Globe2,
  LayoutDashboard,
  Layers3,
  NotebookText,
  Settings2,
  ShieldAlert,
} from "lucide-react";

export type NavItem = {
  label: string;
  path: string;
  icon: typeof LayoutDashboard;
};

export const NAV_ITEMS: NavItem[] = [
  { label: "總覽", path: "/", icon: LayoutDashboard },
  { label: "產業追蹤", path: "/industries", icon: Layers3 },
  { label: "股票清單", path: "/stocks", icon: Building2 },
  { label: "大環境", path: "/macro", icon: Globe2 },
  { label: "大行關注", path: "/institution-watch", icon: ShieldAlert },
  { label: "研究報告", path: "/reports", icon: NotebookText },
  { label: "系統設定", path: "/settings", icon: Settings2 },
];

export const NAV_META = [
  { label: "資料流", value: "Supabase only", icon: Database },
  { label: "更新狀態", value: "即時查詢", icon: Activity },
  { label: "摘要模式", value: "AI 摘要 + 人工判讀", icon: Brain },
];
