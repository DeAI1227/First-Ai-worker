import type { HTMLAttributes, ReactNode } from "react";
import { cn } from "@/lib/utils";

type Props = HTMLAttributes<HTMLDivElement> & {
  children: ReactNode;
};

export function Card({ className, children, ...props }: Props) {
  return (
    <div
      className={cn(
        "rounded-[24px] border border-white/8 bg-white/[0.035] p-5 shadow-[0_0_0_1px_rgba(255,255,255,0.02)] backdrop-blur-xl",
        className,
      )}
      {...props}
    >
      {children}
    </div>
  );
}
