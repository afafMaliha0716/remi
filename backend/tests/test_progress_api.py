def create(client, **body):
    body.setdefault("title", "Task")
    return client.post("/api/tasks", json=body).json()


def profile(client):
    return client.get("/api/profile").json()


def test_new_profile_starts_at_level_one(client):
    p = profile(client)
    assert (p["xp"], p["level"], p["level_title"]) == (0, 1, "Sand Grain")
    assert (p["completed_today"], p["daily_goal"], p["streak_days"]) == (0, 3, 0)
    assert not any(b["earned"] for b in p["badges"])


def test_completing_a_task_awards_xp_by_effort(client):
    easy = create(client, energy="low")
    hard = create(client, energy="high")
    assert client.post(f"/api/tasks/{easy['id']}/complete").json()["xp_awarded"] == 10
    assert client.post(f"/api/tasks/{hard['id']}/complete").json()["xp_awarded"] == 30

    p = profile(client)
    assert (p["xp"], p["completed_today"], p["streak_days"]) == (40, 2, 1)
    assert "first_wave" in {b["id"] for b in p["badges"] if b["earned"]}


def test_completing_twice_does_not_award_twice(client):
    task = create(client)
    client.post(f"/api/tasks/{task['id']}/complete")
    assert client.post(f"/api/tasks/{task['id']}/complete").json()["xp_awarded"] == 0
    assert profile(client)["xp"] == 20


def test_reopening_takes_the_xp_back(client):
    task = create(client)
    client.post(f"/api/tasks/{task['id']}/complete")
    client.post(f"/api/tasks/{task['id']}/reopen")
    assert profile(client)["xp"] == 0


def test_enough_xp_levels_up(client):
    for _ in range(4):
        task = create(client, energy="high")
        client.post(f"/api/tasks/{task['id']}/complete")
    p = profile(client)
    assert (p["xp"], p["level"], p["level_title"], p["xp_into_level"]) == (
        120,
        2,
        "Periwinkle",
        20,
    )


def test_focus_session_awards_xp_and_counts_minutes(client):
    response = client.post("/api/focus", json={"minutes": 25})
    assert response.status_code == 201
    assert response.json() == {"xp_awarded": 25}
    client.post("/api/focus", json={"minutes": 35})

    p = profile(client)
    assert (p["focus_minutes"], p["xp"]) == (60, 60)
    assert "deep_dive" in {b["id"] for b in p["badges"] if b["earned"]}


def test_focus_rejects_bad_minutes(client):
    assert client.post("/api/focus", json={"minutes": 0}).status_code == 422


def test_breakdown_earns_the_small_steps_badge(client):
    task = create(client)
    client.post(f"/api/tasks/{task['id']}/breakdown")
    assert "small_steps" in {b["id"] for b in profile(client)["badges"] if b["earned"]}


def test_reflection_is_saved_once_a_day_and_can_be_updated(client):
    assert client.get("/api/reflections/today").json() is None

    first = client.post("/api/reflections", json={"friction": 4, "note": "slow start"})
    assert first.status_code == 201
    assert first.json()["xp_awarded"] == 15

    second = client.post("/api/reflections", json={"friction": 2}).json()
    assert (second["friction"], second["xp_awarded"]) == (2, 0)

    assert client.get("/api/reflections/today").json()["friction"] == 2
    p = profile(client)
    assert (p["xp"], p["reflected_today"]) == (15, True)


def test_reflection_validates_friction(client):
    assert client.post("/api/reflections", json={"friction": 9}).status_code == 422


def test_plan_endpoint_orders_by_priority_from_the_given_time(client):
    create(client, title="someday", estimated_minutes=20)
    create(client, title="urgent", importance=3, estimated_minutes=30)
    plan = client.get("/api/plan", params={"start": "2026-03-04T14:00:00"}).json()
    assert [(b["kind"], b["title"]) for b in plan] == [
        ("task", "urgent"),
        ("break", "Break"),
        ("task", "someday"),
    ]
    assert plan[0]["start"] == "2026-03-04T14:00:00"


def test_coach_replies_and_saves_the_conversation(client):
    create(client, title="Reply to Sam", estimated_minutes=5)
    response = client.post("/api/coach", json={"message": "I'm overwhelmed"}).json()

    assert (response["coach"], response["mode"]) == ("scripted", "overwhelm")
    assert "Reply to Sam" in response["reply"]["content"]
    assert response["suggested_task_id"] is not None

    history = client.get("/api/coach/messages").json()
    assert [m["role"] for m in history] == ["user", "remi"]
    assert history[0]["content"] == "I'm overwhelmed"


def test_coach_plan_mode_returns_the_plan_blocks(client):
    create(client, title="Write essay", estimated_minutes=40)
    response = client.post(
        "/api/coach",
        json={"message": "go", "mode": "plan_day", "local_time": "2026-03-04T09:00:00"},
    ).json()
    assert response["mode"] == "plan_day"
    assert [b["title"] for b in response["plan"]] == ["Write essay"]
    assert "9:00 AM  Write essay" in response["reply"]["content"]


def test_unknown_mode_falls_back_to_detection(client):
    response = client.post("/api/coach", json={"message": "I lost my keys", "mode": "nope"})
    assert response.json()["mode"] == "lost_item"


def test_clearing_the_conversation(client):
    client.post("/api/coach", json={"message": "hi"})
    assert client.delete("/api/coach/messages").status_code == 204
    assert client.get("/api/coach/messages").json() == []
