import type { ReactNode } from "react";

export function AuthLayout({
  title,
  subtitle,
  children,
}: {
  title: string;
  subtitle: string;
  children: ReactNode;
}) {
  return (
    <div className="flex min-h-screen">
      <div className="hidden w-1/2 flex-col justify-between bg-ink px-12 py-12 text-white lg:flex">
        <div>
          <p className="font-display text-xl">Ledger</p>
          <p className="font-mono text-[11px] uppercase tracking-widest text-white/50">
            Agentic Advisor
          </p>
        </div>
        <div>
          <p className="font-display text-3xl leading-snug">
            Every recommendation,
            <br />
            traced agent by agent.
          </p>
          <p className="mt-4 max-w-sm text-sm text-white/60">
            Planner, Portfolio, Risk, and Recommendation agents work in sequence,
            grounded in your holdings and a live knowledge base — with a full
            audit trail for every answer.
          </p>
        </div>
        <p className="font-mono text-[11px] text-white/30">
          Reference architecture · educational demo, not real financial advice
        </p>
      </div>

      <div className="flex w-full flex-col justify-center px-8 py-12 lg:w-1/2">
        <div className="mx-auto w-full max-w-sm">
          <h1 className="font-display text-2xl text-ink">{title}</h1>
          <p className="mt-1 text-sm text-slate-soft">{subtitle}</p>
          <div className="mt-8">{children}</div>
        </div>
      </div>
    </div>
  );
}
