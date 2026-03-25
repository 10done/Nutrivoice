from tests.conftest import auth_header


def test_analytics_today_empty(client, user_and_token):
    _, token = user_and_token
    r = client.get("/api/analytics/today", headers=auth_header(token))
    assert r.status_code == 200
    body = r.json()
    assert body["consumed_calories"] == 0
    assert body["goal_calories"] == 2000
    assert body["kcal_remaining"] == 2000


def test_analytics_today_after_meal(client, user_and_token):
    _, token = user_and_token
    client.post(
        "/api/meals/text",
        headers=auth_header(token),
        json={"text": "two eggs and coffee"},
    )
    r = client.get("/api/analytics/today", headers=auth_header(token))
    assert r.status_code == 200
    body = r.json()
    assert body["consumed_calories"] > 0
    assert body["protein_g"] > 0


def test_analytics_summary(client, user_and_token):
    _, token = user_and_token
    client.post(
        "/api/meals/text",
        headers=auth_header(token),
        json={"text": "protein shake"},
    )
    r = client.get("/api/analytics/summary", headers=auth_header(token), params={"period": "7d"})
    assert r.status_code == 200
    body = r.json()
    assert body["period"] == "7d"
    assert len(body["days"]) == 7
    assert body["average_daily_calories"] >= 0
