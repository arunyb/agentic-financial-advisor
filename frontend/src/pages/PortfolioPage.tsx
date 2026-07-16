import { useEffect, useState, type FormEvent } from "react";
import * as endpoints from "../api/endpoints";
import type { Portfolio } from "../api/types";

const ASSET_CLASSES = ["equity", "bond", "cash", "commodity", "crypto", "real_estate"];

export default function PortfolioPage() {
  const [portfolio, setPortfolio] = useState<Portfolio | null>(null);
  const [loading, setLoading] = useState(true);
  const [form, setForm] = useState({
    ticker: "",
    asset_class: "equity",
    quantity: "",
    avg_cost: "",
    current_price: "",
  });
  const [submitting, setSubmitting] = useState(false);

  async function refresh() {
    const portfolios = await endpoints.listPortfolios();
    setPortfolio(portfolios[0] ?? null);
    setLoading(false);
  }

  useEffect(() => {
    refresh();
  }, []);

  async function handleAddHolding(e: FormEvent) {
    e.preventDefault();
    setSubmitting(true);
    try {
      const newHolding = {
        ticker: form.ticker.toUpperCase(),
        asset_class: form.asset_class,
        quantity: parseFloat(form.quantity),
        avg_cost: parseFloat(form.avg_cost),
        current_price: parseFloat(form.current_price),
      };
      const existingHoldings = (portfolio?.holdings ?? []).map((h) => ({
        ticker: h.ticker,
        asset_class: h.asset_class,
        quantity: h.quantity,
        avg_cost: h.avg_cost,
        current_price: h.current_price,
      }));

      if (portfolio) {
        await endpoints.deletePortfolio(portfolio.id);
      }
      await endpoints.createPortfolio({
        name: portfolio?.name ?? "My Portfolio",
        holdings: [...existingHoldings, newHolding],
      });
      setForm({ ticker: "", asset_class: "equity", quantity: "", avg_cost: "", current_price: "" });
      await refresh();
    } finally {
      setSubmitting(false);
    }
  }

  if (loading) return <p className="font-mono text-sm text-slate-soft">Loading portfolio…</p>;

  return (
    <div>
      <h1 className="font-display text-2xl text-ink">Portfolio</h1>
      <p className="mt-1 text-sm text-slate-soft">
        Manage the holdings the agents use to ground their analysis.
      </p>

      <div className="mt-8 grid grid-cols-5 gap-6">
        <div className="col-span-3 rounded-lg border border-slate-line bg-white shadow-card">
          <div className="border-b border-slate-line px-4 py-3">
            <p className="font-mono text-[11px] uppercase tracking-widest text-slate-soft">
              Current holdings
            </p>
          </div>
          <table className="w-full text-sm">
            <thead>
              <tr className="text-left text-xs uppercase tracking-wide text-slate-soft">
                <th className="px-4 py-2 font-medium">Ticker</th>
                <th className="px-4 py-2 font-medium">Class</th>
                <th className="px-4 py-2 font-medium">Qty</th>
                <th className="px-4 py-2 font-medium">Price</th>
                <th className="px-4 py-2 font-medium">Value</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-line">
              {(portfolio?.holdings ?? []).map((h) => (
                <tr key={h.id}>
                  <td className="px-4 py-2 font-mono text-ink">{h.ticker}</td>
                  <td className="px-4 py-2 text-slate-soft">{h.asset_class}</td>
                  <td className="px-4 py-2 font-mono">{h.quantity}</td>
                  <td className="px-4 py-2 font-mono">${h.current_price}</td>
                  <td className="px-4 py-2 font-mono">
                    ${(h.quantity * h.current_price).toLocaleString()}
                  </td>
                </tr>
              ))}
              {!portfolio?.holdings.length && (
                <tr>
                  <td colSpan={5} className="px-4 py-6 text-center text-sm text-slate-soft">
                    No holdings yet — add your first one.
                  </td>
                </tr>
              )}
            </tbody>
          </table>
        </div>

        <form
          onSubmit={handleAddHolding}
          className="col-span-2 h-fit space-y-3 rounded-lg border border-slate-line bg-white p-5 shadow-card"
        >
          <p className="font-mono text-[11px] uppercase tracking-widest text-slate-soft">
            Add a holding
          </p>
          <input
            required
            placeholder="Ticker (e.g. GTMX)"
            value={form.ticker}
            onChange={(e) => setForm({ ...form, ticker: e.target.value })}
            className="w-full rounded-md border border-slate-line px-3 py-2 text-sm focus:border-indigo"
          />
          <select
            value={form.asset_class}
            onChange={(e) => setForm({ ...form, asset_class: e.target.value })}
            className="w-full rounded-md border border-slate-line px-3 py-2 text-sm focus:border-indigo"
          >
            {ASSET_CLASSES.map((c) => (
              <option key={c} value={c}>
                {c}
              </option>
            ))}
          </select>
          <input
            required
            type="number"
            step="any"
            placeholder="Quantity"
            value={form.quantity}
            onChange={(e) => setForm({ ...form, quantity: e.target.value })}
            className="w-full rounded-md border border-slate-line px-3 py-2 text-sm focus:border-indigo"
          />
          <input
            required
            type="number"
            step="any"
            placeholder="Average cost"
            value={form.avg_cost}
            onChange={(e) => setForm({ ...form, avg_cost: e.target.value })}
            className="w-full rounded-md border border-slate-line px-3 py-2 text-sm focus:border-indigo"
          />
          <input
            required
            type="number"
            step="any"
            placeholder="Current price"
            value={form.current_price}
            onChange={(e) => setForm({ ...form, current_price: e.target.value })}
            className="w-full rounded-md border border-slate-line px-3 py-2 text-sm focus:border-indigo"
          />
          <button
            type="submit"
            disabled={submitting}
            className="w-full rounded-md bg-indigo px-3 py-2.5 text-sm font-medium text-white hover:bg-indigo-dark disabled:opacity-60"
          >
            {submitting ? "Adding…" : "Add holding"}
          </button>
        </form>
      </div>
    </div>
  );
}
