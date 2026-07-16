import uuid

import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.services.llm_client import LLMUnavailableError


@pytest.fixture(autouse=True)
def mock_llm(monkeypatch):
    """
    Every test runs against the real Postgres test database but with LLM
    calls mocked, so the test suite never needs a real GROQ_API_KEY and
    never makes network calls (fast + deterministic + free to run in CI).
    """
    def fake_generate_text(prompt: str, system_instruction: str | None = None, temperature: float = 0.4) -> str:
        if system_instruction and "Planner" in system_instruction:
            return '{"agents": ["portfolio_agent", "risk_agent", "recommendation_agent"], "reasoning": "test plan"}'
        return "This is a mocked recommendation reply grounded in the provided analysis. Educational only, not individualized advice."

    def fake_embed_query(text: str) -> list[float]:
        # Deterministic pseudo-embedding so pgvector similarity search still works in tests.
        return [(hash(text) % 1000) / 1000.0] * 768

    monkeypatch.setattr("app.services.llm_client.generate_text", fake_generate_text)
    monkeypatch.setattr("app.services.llm_client.embed_query", fake_embed_query)
    monkeypatch.setattr("app.agents.planner.generate_text", fake_generate_text)
    monkeypatch.setattr("app.agents.recommendation_agent.generate_text", fake_generate_text)
    monkeypatch.setattr("app.rag.retriever.embed_query", fake_embed_query)


@pytest.fixture
def mock_llm_quota_exhausted(monkeypatch):
    """Simulate Groq returning a rate-limit error, for testing graceful degradation."""

    def raise_rate_limited(*args, **kwargs):
        raise LLMUnavailableError("Groq's free-tier rate limit was hit for this key.")

    monkeypatch.setattr("app.agents.planner.generate_text", raise_rate_limited)
    monkeypatch.setattr("app.agents.recommendation_agent.generate_text", raise_rate_limited)


@pytest.fixture
def client():
    return TestClient(app)


@pytest.fixture
def registered_user_token(client):
    email = f"test_{uuid.uuid4().hex[:8]}@example.com"
    client.post(
        "/api/v1/auth/register",
        json={"email": email, "full_name": "Test User", "password": "TestPass123"},
    )
    resp = client.post("/api/v1/auth/login", json={"email": email, "password": "TestPass123"})
    return resp.json()["access_token"], email
