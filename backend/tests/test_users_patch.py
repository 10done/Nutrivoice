from tests.conftest import auth_header


def test_patch_goals(client, user_and_token):
    _, token = user_and_token
    r = client.patch(
        "/api/me/goals",
        headers=auth_header(token),
        json={"daily_calorie_goal": 2450, "daily_protein_goal_g": 160},
    )
    assert r.status_code == 200
    assert r.json()["daily_calorie_goal"] == 2450
    assert r.json()["daily_protein_goal_g"] == 160
