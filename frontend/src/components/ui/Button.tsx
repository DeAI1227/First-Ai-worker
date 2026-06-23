import type { ButtonHTMLAttributes, ReactNode } from "react";
import { cn } from "@/lib/utils";

type Props = ButtonHTMLAttributes<HTMLButtonElement> & {
  children: ReactNode;
  tone?: "primary" | "secondary" | "ghost";
};

export function Button({ className, children, tone = "secondary", ...props }: Props) {
  const toneClasses = {
    primary:
      "border-accent/35 bg-accent/15 text-white shadow-[0_0_0_1px_rgba(45,212,191,0.12)] hover:bg-accent/20",
    secondary: "border-white/8 bg-white/5 text-white/82 hover:bg-white/8",
    ghost: "border-transparent bg-transparent text-white/70 hover:bg-white/5 hover:text-white",
  }[tone];

  return (
    <button
      className={cn(
        "inline-flex items-center justify-center gap-2 rounded-2xl border px-4 py-2.5 text-sm font-medium transition focus:outline-none focus:ring-2 focus:ring-accent/40",
        toneClasses,
        className,
      )}
      {...props}
    >
      {children}
    </button>
  );
}
