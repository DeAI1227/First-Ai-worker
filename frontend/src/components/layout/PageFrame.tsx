import type { ReactNode } from "react";

type PageFrameProps = {
  title: string;
  subtitle?: string;
  actions?: ReactNode;
  children: ReactNode;
};

export function PageFrame({ title, subtitle, actions, children }: PageFrameProps) {
  return (
    <section className="space-y-5">
      <div className="flex flex-col gap-4 rounded-[28px] border border-white/8 bg-white/[0.04] p-5 shadow-glow backdrop-blur-xl sm:p-6">
        <div className="flex flex-col gap-4 lg:flex-row lg:items-end lg:justify-between">
          <div className="max-w-3xl">
            <div className="text-xs uppercase tracking-[0.28em] text-white/35">AI 投資研究終端</div>
            <h1 className="mt-2 text-3xl font-semibold tracking-tight text-white sm:text-4xl">{title}</h1>
            {subtitle ? <p className="mt-3 max-w-3xl text-sm leading-6 text-white/55">{subtitle}</p> : null}
          </div>
          {actions ? <div className="flex flex-wrap items-center gap-2">{actions}</div> : null}
        </div>
      </div>
      {children}
    </section>
  );
}
