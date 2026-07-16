def test_create_and_list_portfolio(client, registered_user_token):
    token, _ = registered_user_token
    headers = {"Authorization": f"Bearer {token}"}

    resp = client.post(
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
    assert resp.status_code == 201
    portfolio = resp.json()
    assert len(portfolio["holdings"]) == 2

    list_resp = client.get("/api/v1/portfolios", headers=headers)
    assert list_resp.status_code == 200
    assert len(list_resp.json()) == 1


def test_risk_profile_update(client, registered_user_token):
    token, _ = registered_user_token
    headers = {"Authorization": f"Bearer {token}"}

    resp = client.put(
        "/api/v1/users/me/risk-profile",
        headers=headers,
        json={
            "tolerance": "aggressive",
            "time_horizon_years": 25,
            "monthly_investment_capacity": 1000,
            "questionnaire_score": 90,
        },
    )
    assert resp.status_code == 200
    assert resp.json()["tolerance"] == "aggressive"


def test_portfolio_not_found_for_other_user(client, registered_user_token):
    token, _ = registered_user_token
    headers = {"Authorization": f"Bearer {token}"}
    resp = client.get("/api/v1/portfolios/00000000-0000-0000-0000-000000000000", headers=headers)
    assert resp.status_code == 404
