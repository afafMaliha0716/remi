from datetime import date, timedelta

from app.models import Task, utcnow


def create(client, **body):
    body.setdefault("title", "Task")
    response = client.post("/api/tasks", json=body)
    assert response.status_code == 201
    return response.json()


def test_health_reports_the_active_planner(client):
    assert client.get("/api/health").json() == {"status": "ok", "planner": "rules"}


def test_create_and_list(client):
    create(client, title="Read chapter 4", estimated_minutes=30)
    tasks = client.get("/api/tasks").json()
    assert [t["title"] for t in tasks] == ["Read chapter 4"]
    assert tasks[0]["status"] == "todo"


def test_create_validates_input(client):
    assert client.post("/api/tasks", json={"title": ""}).status_code == 422
    assert client.post("/api/tasks", json={"title": "x", "importance": 7}).status_code == 422


def test_list_is_ranked_by_priority(client):
    create(client, title="someday")
    create(client, title="due today", due_date=date.today().isoformat())
    create(client, title="important", importance=3)
    titles = [t["title"] for t in client.get("/api/tasks").json()]
    assert titles == ["due today", "important", "someday"]


def test_list_ranking_uses_energy_and_time(client):
    create(client, title="deep work", energy="high", estimated_minutes=90)
    create(client, title="quick email", energy="low", estimated_minutes=5)
    tasks = client.get("/api/tasks", params={"energy": "low", "minutes": 15}).json()
    assert tasks[0]["title"] == "quick email"
    assert "Fits your low energy" in tasks[0]["reasons"]


def test_update_changes_only_the_given_fields(client):
    task = create(client, title="Old", importance=3)
    updated = client.patch(f"/api/tasks/{task['id']}", json={"title": "New"}).json()
    assert (updated["title"], updated["importance"]) == ("New", 3)


def test_unknown_task_is_404(client):
    assert client.patch("/api/tasks/999", json={"title": "x"}).status_code == 404
    assert client.post("/api/tasks/999/complete").status_code == 404
    assert client.delete("/api/tasks/999").status_code == 404


def test_delete(client):
    task = create(client)
    assert client.delete(f"/api/tasks/{task['id']}").status_code == 204
    assert client.get("/api/tasks").json() == []


def test_complete_and_reopen(client):
    task = create(client)
    done = client.post(f"/api/tasks/{task['id']}/complete").json()
    assert done["status"] == "done" and done["completed_at"]
    assert client.get("/api/tasks").json() == []
    assert len(client.get("/api/tasks", params={"status": "done"}).json()) == 1

    reopened = client.post(f"/api/tasks/{task['id']}/reopen").json()
    assert reopened["status"] == "todo" and reopened["completed_at"] is None


def test_next_returns_the_top_task_or_null(client):
    assert client.get("/api/tasks/next").json() is None
    create(client, title="later")
    create(client, title="now", due_date=date.today().isoformat())
    assert client.get("/api/tasks/next").json()["title"] == "now"


def test_skipping_three_times_suggests_a_breakdown(client):
    task = create(client, title="Start thesis")
    for _ in range(3):
        skipped = client.post(f"/api/tasks/{task['id']}/skip").json()
    assert skipped["skip_count"] == 3
    assert skipped["suggest_breakdown"] is True


def test_skipping_moves_on_to_another_task(client):
    first = create(client, title="first", importance=3)
    create(client, title="second")
    assert client.get("/api/tasks/next").json()["title"] == "first"
    client.post(f"/api/tasks/{first['id']}/skip")
    assert client.get("/api/tasks/next").json()["title"] == "second"


def test_breakdown_creates_ordered_steps_that_can_be_checked_off(client):
    task = create(client, title="Write history essay")
    broken = client.post(f"/api/tasks/{task['id']}/breakdown").json()
    steps = broken["steps"]
    assert len(steps) >= 3
    assert [s["position"] for s in steps] == list(range(len(steps)))
    assert broken["suggest_breakdown"] is False

    checked = client.patch(f"/api/steps/{steps[0]['id']}", json={"done": True}).json()
    assert checked["done"] is True


def test_breakdown_replaces_existing_steps(client):
    task = create(client, title="Clean room")
    first = client.post(f"/api/tasks/{task['id']}/breakdown").json()["steps"]
    second = client.post(f"/api/tasks/{task['id']}/breakdown").json()["steps"]
    assert len(second) == len(first)
    assert {s["id"] for s in first}.isdisjoint({s["id"] for s in second})


def test_completing_a_task_checks_off_its_steps(client):
    task = create(client)
    client.post(f"/api/tasks/{task['id']}/breakdown")
    done = client.post(f"/api/tasks/{task['id']}/complete").json()
    assert all(s["done"] for s in done["steps"])


def test_brain_dump_creates_structured_tasks(client):
    response = client.post(
        "/api/brain-dump",
        json={"text": "I need to email my advisor tomorrow. write lab report for 2 hours"},
    )
    assert response.status_code == 201
    body = response.json()
    assert body["planner"] == "rules"
    assert [t["title"] for t in body["tasks"]] == ["Email my advisor", "Write lab report"]
    assert body["tasks"][0]["due_date"] == (date.today() + timedelta(days=1)).isoformat()
    assert body["tasks"][1]["estimated_minutes"] == 120
    assert len(client.get("/api/tasks").json()) == 2


def test_brain_dump_rejects_empty_text(client):
    assert client.post("/api/brain-dump", json={"text": ""}).status_code == 422


def test_stats_counts_and_streak(client, session):
    create(client, title="open")
    today_task = create(client, title="done today")
    client.post(f"/api/tasks/{today_task['id']}/complete")
    # Completed yesterday and the day before, which makes a three-day streak.
    for days_ago in (1, 2):
        session.add(
            Task(
                title=f"done {days_ago}d ago",
                status="done",
                completed_at=utcnow() - timedelta(days=days_ago),
            )
        )
    session.commit()

    assert client.get("/api/stats").json() == {
        "open_count": 1,
        "completed_today": 1,
        "streak_days": 3,
    }


def test_streak_survives_until_the_end_of_the_next_day(client, session):
    session.add(
        Task(title="yesterday", status="done", completed_at=utcnow() - timedelta(days=1))
    )
    session.commit()
    assert client.get("/api/stats").json()["streak_days"] == 1
