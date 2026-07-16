import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import * as endpoints from "../api/endpoints";
import type { Portfolio, RiskProfile } from "../api/types";
import { StatCard } from "../components/StatCard";
import { AllocationDonut } from "../components/AllocationDonut";

export default function Dashboard() {
  const [portfolio, setPortfolio] = useState<Portfolio | null>(null);
  const [risk, setRisk] = useState<RiskProfile | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    (async () => {
      const [portfolios, riskProfile] = await Promise.all([
        endpoints.listPortfolios(),
        endpoints.getRiskProfile(),
      ]);
      setPortfolio(portfolios[0] ?? null);
      setRisk(riskProfile);
      setLoading(false);
    })();
  }, []);

  if (loading) {
    return <p className="font-mono text-sm text-slate-soft">Loading dashboard…</p>;
  }

  const totalValue =
    portfolio?.holdings.reduce((sum, h) => sum + h.quantity * h.current_price, 0) ?? 0;

  const byAssetClass: Record<string, number> = {};
  (portfolio?.holdings ?? []).forEach((h) => {
    const value = h.quantity * h.current_price;
    byAssetClass[h.asset_class] = (byAssetClass[h.asset_class] ?? 0) + value;
  });
  const allocationPct = Object.fromEntries(
    Object.entries(byAssetClass).map(([k, v]) => [k, totalValue ? (v / totalValue) * 100 : 0])
  );

  return (
    <div>
      <div className="flex items-baseline justify-between">
        <div>
          <h1 className="font-display text-2xl text-ink">Dashboard</h1>
          <p className="mt-1 text-sm text-slate-soft">
            A snapshot of your holdings and risk posture.
          </p>
        </div>
        <Link
          to="/advisor"
          className="rounded-md bg-indigo px-4 py-2 text-sm font-medium text-white hover:bg-indigo-dark"
        >
          Ask the advisor
        </Link>
      </div>

      <div className="mt-8 grid grid-cols-3 gap-4">
        <StatCard
          label="Portfolio value"
          value={`$${totalValue.toLocaleString(undefined, { maximumFractionDigits: 0 })}`}
          sublabel={`${portfolio?.holdings.length ?? 0} holdings`}
        />
        <StatCard
          label="Risk tolerance"
          value={risk ? risk.tolerance[0].toUpperCase() + risk.tolerance.slice(1) : "—"}
          sublabel={risk ? `${risk.time_horizon_years}y time horizon` : undefined}
        />
        <StatCard
          label="Monthly capacity"
          value={risk ? `$${risk.monthly_investment_capacity.toLocaleString()}` : "—"}
          sublabel="Available to invest"
        />
      </div>

      <div className="mt-6 grid grid-cols-2 gap-4">
        <div className="rounded-lg border border-slate-line bg-white p-5 shadow-card">
          <p className="font-mono text-[11px] uppercase tracking-widest text-slate-soft">
            Allocation by asset class
          </p>
          <AllocationDonut allocation={allocationPct} />
        </div>

        <div className="rounded-lg border border-slate-line bg-white p-5 shadow-card">
          <p className="font-mono text-[11px] uppercase tracking-widest text-slate-soft">
            Holdings
          </p>
          <div className="mt-3 space-y-2">
            {portfolio?.holdings.length ? (
              portfolio.holdings.map((h) => (
                <div key={h.id} className="flex items-center justify-between text-sm">
                  <span className="font-mono text-ink">{h.ticker}</span>
                  <span className="text-slate-soft">{h.asset_class}</span>
                  <span className="font-mono text-ink">
                    ${(h.quantity * h.current_price).toLocaleString()}
                  </span>
                </div>
              ))
            ) : (
              <p className="text-sm text-slate-soft">
                No holdings yet.{" "}
                <Link to="/portfolio" className="text-indigo-dark hover:underline">
                  Add your first holding
                </Link>
                .
              </p>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}
