from app.agents.base import AgentContext
from app.agents.portfolio_agent import PortfolioAgent
from app.agents.risk_agent import RiskAgent
from app.db.models import Holding, Portfolio, RiskProfile, RiskTolerance, User


def _make_context(holdings, tolerance=RiskTolerance.moderate):
    user = User(email="x@example.com", full_name="X", hashed_password="hash")
    user.risk_profile = RiskProfile(tolerance=tolerance, time_horizon_years=10)
    portfolio = Portfolio(owner=user, name="Test")
    portfolio.holdings = [Holding(**h) for h in holdings]
    return AgentContext(db=None, user=user, user_message="How am I doing?", portfolio=portfolio)


def test_portfolio_agent_computes_allocation():
    context = _make_context(
        [
            {"ticker": "GTMX", "asset_class": "equity", "quantity": 10, "avg_cost": 50, "current_price": 100},
            {"ticker": "AGBX", "asset_class": "bond", "quantity": 10, "avg_cost": 50, "current_price": 100},
        ]
    )
    result = PortfolioAgent().run(context)
    assert result.detail["total_value"] == 2000
    assert result.detail["allocation_pct"]["equity"] == 50.0
    assert result.detail["allocation_pct"]["bond"] == 50.0


def test_portfolio_agent_flags_concentration():
    context = _make_context(
        [
            {"ticker": "SOLO", "asset_class": "equity", "quantity": 100, "avg_cost": 10, "current_price": 10},
            {"ticker": "SMALL", "asset_class": "bond", "quantity": 1, "avg_cost": 10, "current_price": 10},
        ]
    )
    result = PortfolioAgent().run(context)
    assert "concentration risk" in result.summary.lower()


def test_portfolio_agent_handles_empty_portfolio():
    user = User(email="empty@example.com", full_name="Empty", hashed_password="hash")
    context = AgentContext(db=None, user=user, user_message="hi", portfolio=None)
    result = PortfolioAgent().run(context)
    assert result.detail["total_value"] == 0


def test_risk_agent_flags_under_allocation_for_aggressive_investor():
    context = _make_context(
        [
            {"ticker": "AGBX", "asset_class": "bond", "quantity": 100, "avg_cost": 10, "current_price": 10},
        ],
        tolerance=RiskTolerance.aggressive,
    )
    PortfolioAgent().run(context)  # populates scratchpad
    result = RiskAgent().run(context)
    assert "under-allocated" in result.detail["verdict"]


def test_risk_agent_flags_alignment_for_conservative_investor():
    context = _make_context(
        [
            {"ticker": "AGBX", "asset_class": "bond", "quantity": 70, "avg_cost": 10, "current_price": 10},
            {"ticker": "GTMX", "asset_class": "equity", "quantity": 30, "avg_cost": 10, "current_price": 10},
        ],
        tolerance=RiskTolerance.conservative,
    )
    PortfolioAgent().run(context)
    result = RiskAgent().run(context)
    assert result.detail["verdict"] == "well aligned with your stated risk tolerance"
