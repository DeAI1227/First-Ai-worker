import { useState } from "react";
import { Button } from "../ui/Button";
import { setStoredUserId } from "@/lib/user";

type Props = {
  userId: string;
  onChange: (next: string) => void;
};

export function UserIdEditor({ userId, onChange }: Props) {
  const [value, setValue] = useState(userId);

  return (
    <div className="rounded-[24px] border border-white/8 bg-white/[0.03] p-5">
      <div className="text-lg font-semibold text-white">使用者識別</div>
      <p className="mt-1 text-sm leading-6 text-white/48">
        未讀數來自 `view_unread_counts` 與 `user_read_status`。你可以先在本機輸入一組使用者 ID 做測試。
      </p>

      <div className="mt-4 flex flex-col gap-3 sm:flex-row">
        <input
          value={value}
          onChange={(event) => setValue(event.target.value)}
          className="h-11 flex-1 rounded-2xl border border-white/10 bg-black/25 px-4 text-sm text-white outline-none ring-0 placeholder:text-white/30 focus:border-accent/30"
          placeholder="例如：local-dev"
        />
        <Button
          tone="primary"
          onClick={() => {
            setStoredUserId(value);
            onChange(value);
          }}
        >
          儲存
        </Button>
      </div>
    </div>
  );
}
