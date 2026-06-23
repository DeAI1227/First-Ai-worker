import type { ReactNode } from "react";
import { cn } from "@/lib/utils";

type Props = {
  children: ReactNode;
  tone?: "critical" | "important" | "general" | "neutral" | "success";
};

export function Badge({ children, tone = "neutral" }: Props) {
  const toneClasses = {
    critical: "border-critical/30 bg-critical/15 text-red-100",
    important: "border-important/30 bg-important/15 text-amber-100",
    general: "border-general/30 bg-general/12 text-sky-100",
    neutral: "border-white/10 bg-white/6 text-white/72",
    success: "border-emerald-400/30 bg-emerald-400/12 text-emerald-100",
  }[tone];

  return (
    <span
      className={cn(
        "inline-flex items-center rounded-full border px-2.5 py-1 text-[11px] font-medium tracking-wide",
        toneClasses,
      )}
    >
      {children}
    </span>
  );
}
