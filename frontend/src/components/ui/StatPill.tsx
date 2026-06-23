type Props = {
  label: string;
  value: string | number;
  tone?: "critical" | "important" | "general" | "accent";
};

export function StatPill({ label, value, tone = "accent" }: Props) {
  const toneClasses = {
    critical: "from-red-500/18 to-red-500/7 text-red-100",
    important: "from-amber-500/18 to-amber-500/7 text-amber-100",
    general: "from-sky-500/18 to-sky-500/7 text-sky-100",
    accent: "from-teal-500/18 to-indigo-500/10 text-white",
  }[tone];

  return (
    <div className={`rounded-2xl border border-white/8 bg-gradient-to-br ${toneClasses} px-4 py-3`}>
      <div className="text-xs text-white/48">{label}</div>
      <div className="mt-1 text-xl font-semibold">{value}</div>
    </div>
  );
}
