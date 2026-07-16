from app.agents.base import Agent, AgentContext, AgentResult
from app.db.models import RiskTolerance

# Model target equity allocation ranges per risk tolerance bucket (rule-based,
# mirrors the guidance in sample_docs/market_notes.md).
TARGET_EQUITY_RANGE = {
    RiskTolerance.conservative: (25, 35),
    RiskTolerance.moderate: (55, 65),
    RiskTolerance.aggressive: (80, 95),
}

EQUITY_LIKE_CLASSES = {"equity", "crypto", "real_estate"}


class RiskAgent(Agent):
    """Deterministic agent: flags mismatches between actual and target risk exposure."""

    name = "risk_agent"

    def run(self, context: AgentContext) -> AgentResult:
        profile = context.user.risk_profile
        allocation_pct = context.scratchpad.get("portfolio_analysis", {}).get("allocation_pct", {})

        current_equity_pct = round(
            sum(pct for cls, pct in allocation_pct.items() if cls in EQUITY_LIKE_CLASSES), 2
        )
        target_low, target_high = TARGET_EQUITY_RANGE[profile.tolerance]

        if current_equity_pct < target_low:
            verdict = "under-allocated to growth assets relative to your risk tolerance"
        elif current_equity_pct > target_high:
            verdict = "over-allocated to growth assets relative to your risk tolerance"
        else:
            verdict = "well aligned with your stated risk tolerance"

        detail = {
            "tolerance": profile.tolerance.value,
            "time_horizon_years": profile.time_horizon_years,
            "current_equity_like_pct": current_equity_pct,
            "target_equity_range_pct": [target_low, target_high],
            "verdict": verdict,
        }
        context.scratchpad["risk_analysis"] = detail

        summary = (
            f"Risk tolerance: {profile.tolerance.value} (time horizon {profile.time_horizon_years}y). "
            f"Current growth-asset exposure is {current_equity_pct}% vs a target range of "
            f"{target_low}-{target_high}%. Portfolio is {verdict}."
        )
        return AgentResult(agent=self.name, summary=summary, detail=detail)
