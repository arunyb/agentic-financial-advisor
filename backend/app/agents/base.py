"""
Minimal, dependency-light multi-agent framework.

Rather than pulling in a heavy orchestration library, each agent is a plain
Python class with a `run(context) -> AgentResult` method. The Orchestrator
(see orchestrator.py) wires them together. This keeps the architecture easy
to read end-to-end for a demo, while still cleanly separating concerns:

    Planner -> decides which specialist agents are relevant
    PortfolioAgent -> computes portfolio composition & performance metrics
    RiskAgent -> compares current allocation against the user's risk profile
    RecommendationAgent -> retrieves RAG context + synthesizes final advice
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Optional

from sqlalchemy.orm import Session

from app.db import models


@dataclass
class AgentContext:
    db: Session
    user: models.User
    user_message: str
    portfolio: Optional[models.Portfolio] = None
    scratchpad: dict[str, Any] = field(default_factory=dict)  # agents read/write shared findings here


@dataclass
class AgentResult:
    agent: str
    summary: str
    detail: dict[str, Any] = field(default_factory=dict)


class Agent:
    name: str = "agent"

    def run(self, context: AgentContext) -> AgentResult:
        raise NotImplementedError
