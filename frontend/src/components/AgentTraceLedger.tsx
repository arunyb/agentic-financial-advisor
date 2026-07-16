import type { AgentStep } from "../api/types";

const AGENT_META: Record<string, { label: string; accent: string; dot: string }> = {
  planner: { label: "PLANNER", accent: "text-indigo-dark", dot: "bg-indigo" },
  portfolio_agent: { label: "PORTFOLIO AGENT", accent: "text-ink", dot: "bg-ink" },
  risk_agent: { label: "RISK AGENT", accent: "text-amber", dot: "bg-amber" },
  recommendation_agent: { label: "RECOMMENDATION AGENT", accent: "text-sage", dot: "bg-sage" },
};

function metaFor(agent: string) {
  return AGENT_META[agent] ?? { label: agent.toUpperCase(), accent: "text-ink", dot: "bg-ink" };
}

export function AgentTraceLedger({ steps }: { steps: AgentStep[] }) {
  if (!steps.length) return null;

  return (
    <div className="rounded-lg border border-slate-line bg-white shadow-card">
      <div className="flex items-center justify-between border-b border-slate-line px-4 py-2.5">
        <p className="font-mono text-[11px] uppercase tracking-widest text-slate-soft">
          Agent execution trace
        </p>
        <p className="font-mono text-[11px] text-slate-soft">{steps.length} steps</p>
      </div>

      <ol className="divide-y divide-slate-line">
        {steps.map((step, i) => {
          const meta = metaFor(step.agent);
          return (
            <li key={`${step.agent}-${i}`} className="flex gap-3 px-4 py-3">
              <div className="flex flex-col items-center pt-0.5">
                <span className={`h-2 w-2 rounded-full ${meta.dot}`} />
                {i < steps.length - 1 && <span className="mt-1 h-full w-px flex-1 bg-slate-line" />}
              </div>
              <div className="flex-1 pb-1">
                <div className="flex items-baseline justify-between gap-2">
                  <span className={`font-mono text-[11px] font-medium tracking-wide ${meta.accent}`}>
                    {String(i + 1).padStart(2, "0")} · {meta.label}
                  </span>
                </div>
                <p className="mt-1 text-sm leading-snug text-ink/80">{step.summary}</p>
              </div>
            </li>
          );
        })}
      </ol>
    </div>
  );
}
