import io

from tests.conftest import auth_header


def test_meal_text_creates_log(client, user_and_token):
    _, token = user_and_token
    r = client.post(
        "/api/meals/text",
        headers=auth_header(token),
        json={"text": "I had two boiled eggs and black coffee for breakfast"},
    )
    assert r.status_code == 200, r.text
    body = r.json()
    assert body["meal_id"]
    assert body["transcript"]
    assert body["title"]
    assert body["totals"]["calories"] > 0
    assert body["review_status"] == "verified"


def test_list_meals(client, user_and_token):
    _, token = user_and_token
    client.post(
        "/api/meals/text",
        headers=auth_header(token),
        json={"text": "banana and coffee"},
    )
    r = client.get("/api/meals", headers=auth_header(token))
    assert r.status_code == 200
    items = r.json()["items"]
    assert len(items) >= 1
    assert items[0]["calories"] >= 0


def test_meal_search(client, user_and_token):
    _, token = user_and_token
    client.post(
        "/api/meals/text",
        headers=auth_header(token),
        json={"text": "I had eggs only"},
    )
    r = client.get("/api/meals", headers=auth_header(token), params={"q": "egg"})
    assert r.status_code == 200
    assert len(r.json()["items"]) >= 1


def test_voice_mock_whisper(client, user_and_token):
    _, token = user_and_token
    files = {"file": ("test.webm", io.BytesIO(b"fake-audio-bytes"), "audio/webm")}
    r = client.post("/api/meals/voice", headers=auth_header(token), files=files)
    assert r.status_code == 200, r.text
    body = r.json()
    assert "egg" in (body.get("transcript") or "").lower() or body["totals"]["calories"] > 0


def test_delete_meal(client, user_and_token):
    _, token = user_and_token
    create = client.post(
        "/api/meals/text",
        headers=auth_header(token),
        json={"text": "one banana"},
    )
    assert create.status_code == 200
    meal_id = create.json()["meal_id"]
    d = client.delete(f"/api/meals/{meal_id}", headers=auth_header(token))
    assert d.status_code == 204
    lst = client.get("/api/meals", headers=auth_header(token))
    ids = [x["id"] for x in lst.json()["items"]]
    assert meal_id not in ids


def test_delete_meal_not_found(client, user_and_token):
    _, token = user_and_token
    r = client.delete("/api/meals/00000000-0000-0000-0000-000000000000", headers=auth_header(token))
    assert r.status_code == 404
