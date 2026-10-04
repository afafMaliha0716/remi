from datetime import datetime
from types import SimpleNamespace

from app.models import Task
from app.services.coach import (
    Context,
    GeminiCoach,
    Mode,
    ScriptedCoach,
    detect_mode,
)
from app.services.schedule import build_plan


def test_detects_mode_from_the_message():
    assert detect_mode("can you plan my day") is Mode.plan_day
    assert detect_mode("I'm so overwhelmed right now") is Mode.overwhelm
    assert detect_mode("I can't start anything") is Mode.overwhelm
    assert detect_mode("I lost my keys") is Mode.lost_item
    assert detect_mode("where are my headphones") is Mode.lost_item
    assert detect_mode("hey") is Mode.chat


def context():
    tasks = [
        Task(id=1, title="Write essay", estimated_minutes=60),
        Task(id=2, title="Reply to Sam", estimated_minutes=5),
    ]
    return Context(open_tasks=tasks, plan=build_plan(tasks, datetime(2026, 3, 4, 9, 0)))


def scripted(mode, ctx=None):
    return ScriptedCoach().reply(mode, "", ctx if ctx is not None else context())


def test_plan_lists_the_schedule_and_points_at_the_first_task():
    reply = scripted(Mode.plan_day)
    assert "9:00 AM  Write essay" in reply.text
    assert "10:05 AM  Reply to Sam" in reply.text
    assert reply.suggested_task_id == 1


def test_plan_with_no_tasks_asks_for_some():
    reply = scripted(Mode.plan_day, Context())
    assert "nothing to plan" in reply.text
    assert reply.suggested_task_id is None


def test_overwhelm_points_at_the_smallest_task():
    reply = scripted(Mode.overwhelm)
    assert '"Reply to Sam"' in reply.text
    assert reply.suggested_task_id == 2


def test_overwhelm_with_no_tasks_still_helps():
    reply = scripted(Mode.overwhelm, Context())
    assert "Breathe out" in reply.text
    assert reply.suggested_task_id is None


def test_lost_item_gives_search_steps():
    assert "last use it" in scripted(Mode.lost_item).text


def test_chat_suggests_the_top_task():
    reply = scripted(Mode.chat)
    assert "2 open tasks" in reply.text
    assert reply.suggested_task_id == 1


class FakeClient:
    def __init__(self, text=None, error=None):
        self.text, self.error, self.calls = text, error, []
        self.models = SimpleNamespace(generate_content=self._generate)

    def _generate(self, **kwargs):
        self.calls.append(kwargs)
        if self.error:
            raise self.error
        return SimpleNamespace(text=self.text)


def test_gemini_reply_is_used_and_keeps_the_rule_based_suggestion():
    client = FakeClient("Start with the reply to Sam. It's five minutes.")
    coach = GeminiCoach("key", "test-model", client=client)
    ctx = context()
    ctx.history = [("user", "hi"), ("remi", "hello")]

    reply = coach.reply(Mode.overwhelm, "too much going on", ctx)

    assert reply.text == "Start with the reply to Sam. It's five minutes."
    assert reply.suggested_task_id == 2
    prompt = client.calls[0]["contents"]
    assert "- Write essay (60 min" in prompt
    assert "User: hi" in prompt and "too much going on" in prompt


def test_gemini_plan_prompt_includes_the_schedule():
    client = FakeClient("Here you go.")
    GeminiCoach("key", "m", client=client).reply(Mode.plan_day, "plan my day", context())
    assert "9:00 AM  Write essay" in client.calls[0]["contents"]


def test_gemini_failure_or_empty_reply_falls_back_to_the_script():
    for client in (FakeClient(error=RuntimeError("down")), FakeClient(text="  ")):
        reply = GeminiCoach("key", "m", client=client).reply(Mode.lost_item, "", context())
        assert "last use it" in reply.text
