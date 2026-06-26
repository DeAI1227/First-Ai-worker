import { AlertTriangle } from "lucide-react";
import { Button } from "./Button";

type Props = {
  title?: string;
  description: string;
  onRetry?: () => void;
};

export function ErrorState({
  title = "資料讀取失敗",
  description,
  onRetry,
}: Props) {
  return (
    <div className="rounded-[24px] border border-red-400/20 bg-red-500/8 p-6">
      <div className="flex items-start gap-4">
        <div className="flex h-11 w-11 shrink-0 items-center justify-center rounded-2xl border border-red-400/25 bg-red-500/10">
          <AlertTriangle className="h-5 w-5 text-red-200" />
        </div>
        <div className="flex-1">
          <div className="text-base font-semibold text-white">{title}</div>
          <p className="mt-1 text-sm leading-6 text-red-100/80">{description}</p>
          {onRetry ? (
            <div className="mt-4">
              <Button tone="secondary" onClick={onRetry}>
                重新載入
              </Button>
            </div>
          ) : null}
        </div>
      </div>
    </div>
  );
}
