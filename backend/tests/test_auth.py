from tests.conftest import auth_header


def test_register_and_login(client):
    r = client.post("/api/auth/register", json={"email": "u@example.com", "password": "secretpass1"})
    assert r.status_code == 200
    data = r.json()
    assert "access_token" in data
    assert data["token_type"] == "bearer"

    r2 = client.post("/api/auth/login", json={"email": "u@example.com", "password": "secretpass1"})
    assert r2.status_code == 200
    assert r2.json()["access_token"]


def test_register_duplicate(client):
    client.post("/api/auth/register", json={"email": "dup@example.com", "password": "password123"})
    r = client.post("/api/auth/register", json={"email": "dup@example.com", "password": "password123"})
    assert r.status_code == 400


def test_me_requires_auth(client):
    r = client.get("/api/me")
    assert r.status_code == 401


def test_me_with_token(client, user_and_token):
    _, token = user_and_token
    r = client.get("/api/me", headers=auth_header(token))
    assert r.status_code == 200
    body = r.json()
    assert body["email"] == "test@example.com"
    assert "daily_calorie_goal" in body
