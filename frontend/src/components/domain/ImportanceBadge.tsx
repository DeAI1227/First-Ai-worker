import type { Importance } from "@/lib/types";
import { Badge } from "../ui/Badge";
import { importanceZhLabel } from "@/lib/format";

type Props = {
  importance: Importance;
};

export function ImportanceBadge({ importance }: Props) {
  const tone = importance === "critical" ? "critical" : importance === "important" ? "important" : "general";
  return <Badge tone={tone}>{importanceZhLabel(importance)}</Badge>;
}
