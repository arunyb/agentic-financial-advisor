import uuid


def _unique_email(prefix: str) -> str:
    return f"{prefix}_{uuid.uuid4().hex[:8]}@example.com"


def test_register_and_login(client):
    email = _unique_email("auth_test")
    resp = client.post(
        "/api/v1/auth/register",
        json={"email": email, "full_name": "Auth Test", "password": "TestPass123"},
    )
    assert resp.status_code == 201
    body = resp.json()
    assert body["email"] == email

    login_resp = client.post("/api/v1/auth/login", json={"email": email, "password": "TestPass123"})
    assert login_resp.status_code == 200
    assert "access_token" in login_resp.json()


def test_login_wrong_password(client):
    email = _unique_email("wrongpw")
    client.post(
        "/api/v1/auth/register",
        json={"email": email, "full_name": "Wrong PW", "password": "TestPass123"},
    )
    resp = client.post("/api/v1/auth/login", json={"email": email, "password": "WrongPass"})
    assert resp.status_code == 401


def test_protected_route_requires_token(client):
    resp = client.get("/api/v1/users/me")
    assert resp.status_code == 401


def test_protected_route_with_token(client, registered_user_token):
    token, email = registered_user_token
    resp = client.get("/api/v1/users/me", headers={"Authorization": f"Bearer {token}"})
    assert resp.status_code == 200
    assert resp.json()["email"] == email


def test_duplicate_registration_rejected(client):
    payload = {"email": _unique_email("dup"), "full_name": "Dup", "password": "TestPass123"}
    client.post("/api/v1/auth/register", json=payload)
    resp = client.post("/api/v1/auth/register", json=payload)
    assert resp.status_code == 400
