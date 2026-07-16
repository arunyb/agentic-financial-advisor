from app.agents.base import Agent, AgentContext, AgentResult


class PortfolioAgent(Agent):
    """Deterministic (non-LLM) agent: computes portfolio composition & concentration.

    Keeping this agent rule-based (rather than LLM-based) is intentional -
    numeric portfolio math should be exact and auditable, not left to a
    language model to "calculate".
    """

    name = "portfolio_agent"

    def run(self, context: AgentContext) -> AgentResult:
        portfolio = context.portfolio
        if not portfolio or not portfolio.holdings:
            result = AgentResult(
                agent=self.name,
                summary="No holdings found for this user; treating as a new investor with no existing portfolio.",
                detail={"total_value": 0, "by_asset_class": {}, "concentration": []},
            )
            context.scratchpad["portfolio_analysis"] = result.detail
            return result

        holdings = portfolio.holdings
        total_value = sum(h.quantity * h.current_price for h in holdings)

        by_asset_class: dict[str, float] = {}
        for h in holdings:
            value = h.quantity * h.current_price
            by_asset_class[h.asset_class] = by_asset_class.get(h.asset_class, 0.0) + value

        allocation_pct = {
            k: round((v / total_value) * 100, 2) if total_value else 0
            for k, v in by_asset_class.items()
        }

        concentration = sorted(
            (
                {
                    "ticker": h.ticker,
                    "value": round(h.quantity * h.current_price, 2),
                    "pct_of_portfolio": round((h.quantity * h.current_price / total_value) * 100, 2)
                    if total_value
                    else 0,
                }
                for h in holdings
            ),
            key=lambda x: x["pct_of_portfolio"],
            reverse=True,
        )

        detail = {
            "total_value": round(total_value, 2),
            "by_asset_class": by_asset_class,
            "allocation_pct": allocation_pct,
            "concentration": concentration[:5],
        }
        context.scratchpad["portfolio_analysis"] = detail

        top = concentration[0] if concentration else None
        summary = (
            f"Portfolio total value ${total_value:,.2f} across {len(holdings)} holdings. "
            f"Allocation by asset class: {allocation_pct}."
        )
        if top and top["pct_of_portfolio"] > 25:
            summary += f" Note: {top['ticker']} alone makes up {top['pct_of_portfolio']}% of the portfolio (concentration risk)."

        return AgentResult(agent=self.name, summary=summary, detail=detail)
