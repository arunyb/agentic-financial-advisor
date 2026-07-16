export function StatCard({
  label,
  value,
  sublabel,
}: {
  label: string;
  value: string;
  sublabel?: string;
}) {
  return (
    <div className="rounded-lg border border-slate-line bg-white p-4 shadow-card">
      <p className="font-mono text-[11px] uppercase tracking-widest text-slate-soft">{label}</p>
      <p className="mt-1.5 font-display text-2xl text-ink">{value}</p>
      {sublabel && <p className="mt-0.5 text-xs text-slate-soft">{sublabel}</p>}
    </div>
  );
}
