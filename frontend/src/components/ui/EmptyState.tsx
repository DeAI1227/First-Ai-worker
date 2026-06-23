import { SearchX } from "lucide-react";
import { Button } from "./Button";

type Props = {
  title: string;
  description: string;
  actionLabel?: string;
  onAction?: () => void;
};

export function EmptyState({ title, description, actionLabel, onAction }: Props) {
  return (
    <div className="rounded-[24px] border border-dashed border-white/10 bg-white/[0.025] p-8 text-center">
      <div className="mx-auto flex h-12 w-12 items-center justify-center rounded-2xl border border-white/10 bg-white/5">
        <SearchX className="h-5 w-5 text-white/50" />
      </div>
      <div className="mt-4 text-lg font-semibold text-white">{title}</div>
      <p className="mx-auto mt-2 max-w-xl text-sm leading-6 text-white/52">{description}</p>
      {actionLabel && onAction ? (
        <div className="mt-5">
          <Button onClick={onAction} tone="secondary">
            {actionLabel}
          </Button>
        </div>
      ) : null}
    </div>
  );
}
