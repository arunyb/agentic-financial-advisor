def _setup_portfolio(client, headers):
    client.post(
        "/api/v1/portfolios",
        headers=headers,
        json={
            "name": "Test Portfolio",
            "holdings": [
                {"ticker": "GTMX", "asset_class": "equity", "quantity": 10, "avg_cost": 50, "current_price": 55},
                {"ticker": "AGBX", "asset_class": "bond", "quantity": 20, "avg_cost": 20, "current_price": 20},
            ],
        },
    )


def test_chat_happy_path(client, registered_user_token):
    token, _ = registered_user_token
    headers = {"Authorization": f"Bearer {token}"}
    _setup_portfolio(client, headers)

    resp = client.post("/api/v1/chat", headers=headers, json={"message": "How is my portfolio allocated?"})
    assert resp.status_code == 200
    body = resp.json()
    assert body["reply"]
    assert len(body["agent_trace"]) >= 1
    agent_names = [step["agent"] for step in body["agent_trace"]]
    assert "planner" in agent_names
    assert "portfolio_agent" in agent_names


def test_chat_degrades_gracefully_when_llm_unavailable(client, registered_user_token, mock_llm_quota_exhausted):
    """
    When Gemini is unavailable (e.g. quota exhausted), the endpoint should
    still return 200 with the deterministic portfolio/risk analysis, not a
    500 - this is the graceful-degradation path the agents implement.
    """
    token, _ = registered_user_token
    headers = {"Authorization": f"Bearer {token}"}
    _setup_portfolio(client, headers)

    resp = client.post("/api/v1/chat", headers=headers, json={"message": "Am I taking too much risk?"})
    assert resp.status_code == 200
    body = resp.json()
    assert "couldn't reach the AI model" in body["reply"]
    assert "Portfolio value" in body["reply"]


def test_chat_requires_auth(client):
    resp = client.post("/api/v1/chat", json={"message": "hello"})
    assert resp.status_code == 401


def test_chat_session_not_found_for_other_user(client, registered_user_token):
    token, _ = registered_user_token
    headers = {"Authorization": f"Bearer {token}"}
    resp = client.get(
        "/api/v1/chat/sessions/00000000-0000-0000-0000-000000000000/messages", headers=headers
    )
    assert resp.status_code == 404
