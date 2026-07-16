import { useEffect, useState, type FormEvent } from "react";
import * as endpoints from "../api/endpoints";
import type { RiskProfile, RiskTolerance } from "../api/types";

export default function RiskProfilePage() {
  const [profile, setProfile] = useState<RiskProfile | null>(null);
  const [saved, setSaved] = useState(false);
  const [submitting, setSubmitting] = useState(false);

  useEffect(() => {
    endpoints.getRiskProfile().then(setProfile);
  }, []);

  async function handleSubmit(e: FormEvent) {
    e.preventDefault();
    if (!profile) return;
    setSubmitting(true);
    setSaved(false);
    try {
      const updated = await endpoints.updateRiskProfile({
        tolerance: profile.tolerance,
        time_horizon_years: profile.time_horizon_years,
        monthly_investment_capacity: profile.monthly_investment_capacity,
        questionnaire_score: profile.questionnaire_score,
      });
      setProfile(updated);
      setSaved(true);
    } finally {
      setSubmitting(false);
    }
  }

  if (!profile) return <p className="font-mono text-sm text-slate-soft">Loading…</p>;

  return (
    <div className="max-w-lg">
      <h1 className="font-display text-2xl text-ink">Risk profile</h1>
      <p className="mt-1 text-sm text-slate-soft">
        The Risk Agent compares your holdings against these preferences.
      </p>

      <form
        onSubmit={handleSubmit}
        className="mt-8 space-y-5 rounded-lg border border-slate-line bg-white p-6 shadow-card"
      >
        <div>
          <label className="block text-xs font-medium uppercase tracking-wide text-slate-soft">
            Risk tolerance
          </label>
          <div className="mt-2 grid grid-cols-3 gap-2">
            {(["conservative", "moderate", "aggressive"] as RiskTolerance[]).map((t) => (
              <button
                type="button"
                key={t}
                onClick={() => setProfile({ ...profile, tolerance: t })}
                className={`rounded-md border px-3 py-2 text-sm capitalize transition ${
                  profile.tolerance === t
                    ? "border-indigo bg-indigo-light text-indigo-dark"
                    : "border-slate-line text-ink/70 hover:border-ink/30"
                }`}
              >
                {t}
              </button>
            ))}
          </div>
        </div>

        <div>
          <label className="block text-xs font-medium uppercase tracking-wide text-slate-soft">
            Time horizon: {profile.time_horizon_years} years
          </label>
          <input
            type="range"
            min={1}
            max={40}
            value={profile.time_horizon_years}
            onChange={(e) => setProfile({ ...profile, time_horizon_years: Number(e.target.value) })}
            className="mt-2 w-full accent-indigo"
          />
        </div>

        <div>
          <label className="block text-xs font-medium uppercase tracking-wide text-slate-soft">
            Monthly investment capacity ($)
          </label>
          <input
            type="number"
            min={0}
            value={profile.monthly_investment_capacity}
            onChange={(e) =>
              setProfile({ ...profile, monthly_investment_capacity: Number(e.target.value) })
            }
            className="mt-1 w-full rounded-md border border-slate-line px-3 py-2 text-sm focus:border-indigo"
          />
        </div>

        <div>
          <label className="block text-xs font-medium uppercase tracking-wide text-slate-soft">
            Comfort with volatility: {profile.questionnaire_score}/100
          </label>
          <input
            type="range"
            min={0}
            max={100}
            value={profile.questionnaire_score}
            onChange={(e) => setProfile({ ...profile, questionnaire_score: Number(e.target.value) })}
            className="mt-2 w-full accent-indigo"
          />
        </div>

        <button
          type="submit"
          disabled={submitting}
          className="w-full rounded-md bg-indigo px-3 py-2.5 text-sm font-medium text-white hover:bg-indigo-dark disabled:opacity-60"
        >
          {submitting ? "Saving…" : "Save risk profile"}
        </button>
        {saved && <p className="text-center text-sm text-sage">Saved.</p>}
      </form>
    </div>
  );
}
