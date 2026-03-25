def test_serves_login_page(client):
    r = client.get("/login.html")
    assert r.status_code == 200
    assert "NutriVoice" in r.text


def test_serves_js(client):
    r = client.get("/js/config.js")
    assert r.status_code == 200
    assert "NUTRIVOICE_API" in r.text


def test_root_serves_index(client):
    r = client.get("/")
    assert r.status_code == 200
    assert "Daily summary" in r.text or "NutriVoice" in r.text
