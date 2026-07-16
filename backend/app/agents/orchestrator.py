from sqlalchemy.orm import Session

from app.agents.base import AgentContext
from app.agents.planner import PlannerAgent
from app.agents.portfolio_agent import PortfolioAgent
from app.agents.recommendation_agent import RecommendationAgent
from app.agents.risk_agent import RiskAgent
from app.core.logging import get_logger
from app.core.telemetry import get_tracer
from app.db import models

logger = get_logger("orchestrator")
tracer = get_tracer("orchestrator")

_AGENT_REGISTRY = {
    "portfolio_agent": PortfolioAgent(),
    "risk_agent": RiskAgent(),
    "recommendation_agent": RecommendationAgent(),
}


def run_advisory_pipeline(db: Session, user: models.User, user_message: str) -> dict:
    """
    Runs the full agentic pipeline for one user turn:
      1. Planner decides which specialist agents are relevant
      2. Specialist agents run in a fixed dependency-safe order, writing
         findings into a shared scratchpad
      3. Returns the final reply plus a step-by-step trace for the UI

    Every step is wrapped in an OpenTelemetry span so the whole pipeline is
    visible end-to-end in a tracing backend (Jaeger/Tempo/etc).
    """
    portfolio = user.portfolios[0] if user.portfolios else None
    context = AgentContext(db=db, user=user, user_message=user_message, portfolio=portfolio)
    trace_steps = []

    with tracer.start_as_current_span("advisory_pipeline"):
        planner = PlannerAgent()
        with tracer.start_as_current_span(f"agent.{planner.name}"):
            plan_result = planner.run(context)
        trace_steps.append(plan_result)
        logger.info("agent_step", agent=plan_result.agent, summary=plan_result.summary)

        planned_agents = context.scratchpad["plan"]["agents"]
        # Enforce a safe execution order regardless of what the planner returned,
        # since recommendation_agent depends on the outputs of the other two.
        ordered_agents = [a for a in ["portfolio_agent", "risk_agent"] if a in planned_agents]
        if "recommendation_agent" in planned_agents:
            ordered_agents.append("recommendation_agent")

        for agent_name in ordered_agents:
            agent = _AGENT_REGISTRY[agent_name]
            with tracer.start_as_current_span(f"agent.{agent_name}"):
                result = agent.run(context)
            trace_steps.append(result)
            logger.info("agent_step", agent=result.agent, summary=result.summary)

    final_reply = context.scratchpad.get(
        "final_reply",
        "Here's what I found: " + " ".join(step.summary for step in trace_steps),
    )
    citations = context.scratchpad.get("citations", [])

    return {
        "reply": final_reply,
        "trace": [{"agent": s.agent, "summary": s.summary, "detail": s.detail} for s in trace_steps],
        "citations": citations,
    }
