from app.agents.base import Agent, AgentContext, AgentResult
from app.rag.retriever import format_context, retrieve
from app.services.llm_client import LLMUnavailableError, generate_text

RECOMMENDATION_SYSTEM_PROMPT = """You are the Recommendation agent in a financial advisory multi-agent system.
You produce clear, friendly, and specific investment guidance for a retail investor.

Rules:
- Ground your advice in the provided portfolio analysis, risk analysis, and knowledge-base context.
- Be concrete: mention actual numbers/percentages from the analyses when relevant.
- Never guarantee returns or claim certainty about future performance.
- Add one short sentence reminding the user this is educational, not individualized financial advice.
- Keep the response to 3-5 short paragraphs or a short list, no filler.
"""


class RecommendationAgent(Agent):
    name = "recommendation_agent"

    def run(self, context: AgentContext) -> AgentResult:
        portfolio_analysis = context.scratchpad.get("portfolio_analysis", {})
        risk_analysis = context.scratchpad.get("risk_analysis", {})

        if context.scratchpad.get("llm_unavailable"):
            return self._degraded_result(context, portfolio_analysis, risk_analysis, reason="the AI model is currently unavailable")

        try:
            chunks = retrieve(context.db, context.user_message)
            rag_context = format_context(chunks)

            prompt = f"""User question: {context.user_message}

Portfolio analysis: {portfolio_analysis}
Risk analysis: {risk_analysis}

Relevant knowledge-base context:
{rag_context}

Write the final advice for the user now."""

            reply = generate_text(prompt=prompt, system_instruction=RECOMMENDATION_SYSTEM_PROMPT, temperature=0.5)
            citations = sorted({c.source for c in chunks})

            context.scratchpad["final_reply"] = reply
            context.scratchpad["citations"] = citations

            return AgentResult(
                agent=self.name,
                summary="Drafted final recommendation grounded in portfolio, risk, and knowledge-base context.",
                detail={"citations": citations},
            )
        except LLMUnavailableError as exc:
            return self._degraded_result(context, portfolio_analysis, risk_analysis, reason=str(exc))

    def _degraded_result(
        self, context: AgentContext, portfolio_analysis: dict, risk_analysis: dict, reason: str
    ) -> AgentResult:
        """
        Build a reply from the deterministic Portfolio/Risk agent output alone,
        since those don't depend on the LLM. The user still gets real,
        grounded numbers even when the LLM is unreachable, instead of a 500.
        """
        lines = [
            "I couldn't reach the AI model to write personalized commentary right now, "
            f"but here's what the numbers show ({reason}):"
        ]
        if portfolio_analysis.get("total_value") is not None:
            lines.append(
                f"- Portfolio value: ${portfolio_analysis.get('total_value', 0):,.2f}, "
                f"allocated as {portfolio_analysis.get('allocation_pct', {})}."
            )
        if risk_analysis:
            lines.append(
                f"- Risk check: {risk_analysis.get('tolerance', 'unknown')} tolerance, "
                f"{risk_analysis.get('current_equity_like_pct', 0)}% in growth assets vs a target range of "
                f"{risk_analysis.get('target_equity_range_pct', [])}% - portfolio is "
                f"{risk_analysis.get('verdict', 'not yet evaluated')}."
            )
        lines.append("Try again shortly for AI-written commentary once the model is available.")
        reply = "\n".join(lines)

        context.scratchpad["final_reply"] = reply
        context.scratchpad["citations"] = []

        return AgentResult(
            agent=self.name,
            summary="LLM unavailable - returned deterministic portfolio/risk analysis without AI commentary.",
            detail={"citations": [], "degraded": True, "reason": reason},
        )
