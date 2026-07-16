import json

from app.agents.base import Agent, AgentContext, AgentResult
from app.core.logging import get_logger
from app.services.llm_client import LLMUnavailableError, generate_text

logger = get_logger("planner_agent")

PLANNER_SYSTEM_PROMPT = """You are the Planner agent in a financial advisory multi-agent system.
Given a user's message, decide which specialist agents should run to answer it well.
Available agents:
- portfolio_agent: analyzes the user's current holdings and asset allocation
- risk_agent: compares current allocation against the user's stated risk tolerance
- recommendation_agent: retrieves knowledge-base context and drafts the final advice (should almost always run last)

Respond ONLY with compact JSON, no markdown fences, in this exact shape:
{"agents": ["portfolio_agent", "risk_agent", "recommendation_agent"], "reasoning": "one short sentence"}
Only include agents that are actually relevant. recommendation_agent should be included whenever the user wants advice, not just raw data.
"""

_DEFAULT_PLAN = {
    "agents": ["portfolio_agent", "risk_agent", "recommendation_agent"],
    "reasoning": "Fallback default plan.",
}


class PlannerAgent(Agent):
    name = "planner"

    def run(self, context: AgentContext) -> AgentResult:
        try:
            raw = generate_text(
                prompt=f"User message: {context.user_message!r}",
                system_instruction=PLANNER_SYSTEM_PROMPT,
                temperature=0.0,
            )
            plan = self._parse_plan(raw)
            summary = f"Plan: run {', '.join(plan['agents'])}. Reasoning: {plan['reasoning']}"
        except LLMUnavailableError as exc:
            logger.warning("planner_llm_unavailable", detail=str(exc))
            plan = dict(_DEFAULT_PLAN, reasoning="LLM unavailable - running the full deterministic pipeline.")
            context.scratchpad["llm_unavailable"] = True
            summary = (
                "Planner couldn't reach the LLM (quota/availability issue), so the full "
                "deterministic pipeline is running instead. Numeric analysis below is unaffected."
            )

        context.scratchpad["plan"] = plan
        return AgentResult(agent=self.name, summary=summary, detail=plan)

    @staticmethod
    def _parse_plan(raw: str) -> dict:
        cleaned = raw.strip().removeprefix("```json").removeprefix("```").removesuffix("```").strip()
        try:
            plan = json.loads(cleaned)
            agents = [a for a in plan.get("agents", []) if a in _KNOWN_AGENTS]
            if not agents:
                raise ValueError("empty agent list")
            return {"agents": agents, "reasoning": plan.get("reasoning", "")}
        except Exception:
            logger.warning("planner_parse_fallback", raw=raw[:200])
            # Safe default: run the full pipeline so the user still gets a useful answer.
            return dict(_DEFAULT_PLAN, reasoning="Fallback default plan (planner output could not be parsed).")


_KNOWN_AGENTS = {"portfolio_agent", "risk_agent", "recommendation_agent"}
