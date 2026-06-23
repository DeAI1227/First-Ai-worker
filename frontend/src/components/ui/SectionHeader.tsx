import type { ReactNode } from "react";

type Props = {
  title: string;
  description?: string;
  action?: ReactNode;
};

export function SectionHeader({ title, description, action }: Props) {
  return (
    <div className="flex flex-col gap-3 sm:flex-row sm:items-end sm:justify-between">
      <div>
        <div className="text-lg font-semibold text-white">{title}</div>
        {description ? <p className="mt-1 text-sm leading-6 text-white/50">{description}</p> : null}
      </div>
      {action ? <div>{action}</div> : null}
    </div>
  );
}
