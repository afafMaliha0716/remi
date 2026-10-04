import json
from datetime import date
from types import SimpleNamespace

from app.models import Energy
from app.services.planner import GeminiPlanner, HeuristicPlanner

# A Wednesday.
TODAY = date(2026, 3, 4)


def parse(text):
    return HeuristicPlanner().parse_brain_dump(text, TODAY)


def test_splits_lines_sentences_and_connectors():
    tasks = parse("email my professor. buy groceries\ncall mom and then do laundry")
    assert [t.title for t in tasks] == [
        "Email my professor",
        "Buy groceries",
        "Call mom",
        "Do laundry",
    ]


def test_strips_bullets_and_filler_phrases():
    tasks = parse("- I need to renew my passport\n2. don't forget to water the plants")
    assert [t.title for t in tasks] == ["Renew my passport", "Water the plants"]


def test_strips_lead_in_words():
    tasks = parse("also do laundry\nOh, and I still need to call the dentist")
    assert [t.title for t in tasks] == ["Do laundry", "Call the dentist"]


def test_reads_relative_due_dates():
    assert parse("submit the form today")[0].due_date == TODAY
    assert parse("pay rent tomorrow")[0].due_date == date(2026, 3, 5)
    assert parse("finish lab report by friday")[0].due_date == date(2026, 3, 6)
    assert parse("book flights next week")[0].due_date == date(2026, 3, 11)


def test_weekday_matching_today_means_next_week():
    assert parse("team meeting wednesday")[0].due_date == date(2026, 3, 11)


def test_due_phrase_is_removed_from_the_title():
    assert parse("finish lab report by friday")[0].title == "Finish lab report"


def test_reads_durations():
    assert parse("study for 2 hours")[0].estimated_minutes == 120
    assert parse("stretch 15 min")[0].estimated_minutes == 15
    assert parse("review notes (1.5 hrs)")[0].estimated_minutes == 90


def test_guesses_energy_and_a_default_estimate():
    easy = parse("email the landlord")[0]
    hard = parse("write history essay")[0]
    assert (easy.energy, easy.estimated_minutes) == (Energy.low, 10)
    assert (hard.energy, hard.estimated_minutes) == (Energy.high, 45)


def test_urgent_words_raise_importance_and_leave_the_title():
    task = parse("URGENT pay tuition")[0]
    assert task.importance == 3
    assert task.title == "Pay tuition"

    task = parse("finish the lab report by friday, it's really urgent")[0]
    assert task.importance == 3
    assert task.title == "Finish the lab report"


def test_ignores_empty_input():
    assert parse("   \n\n ...  ") == []


def test_breakdown_starts_with_an_easy_first_step():
    steps = HeuristicPlanner().break_down("Write history essay")
    assert 3 <= len(steps) <= 6
    assert "write history essay" in steps[0]


class FakeClient:
    """Stands in for the Gemini client and returns a canned response."""

    def __init__(self, payload=None, error=None):
        self.payload, self.error, self.calls = payload, error, []
        self.models = SimpleNamespace(generate_content=self._generate)

    def _generate(self, **kwargs):
        self.calls.append(kwargs)
        if self.error:
            raise self.error
        return SimpleNamespace(text=json.dumps(self.payload))


def gemini(payload=None, error=None):
    client = FakeClient(payload, error)
    return GeminiPlanner("key", "test-model", client=client), client


def test_gemini_tasks_are_validated_and_clamped():
    planner, client = gemini(
        [
            {
                "title": "Draft essay outline",
                "energy": "high",
                "importance": 9,
                "estimated_minutes": 40,
                "due_date": "2026-03-06",
            },
            {"title": "  ", "energy": "low", "importance": 1, "estimated_minutes": 5},
            {"title": "Call bank", "energy": "weird", "due_date": "soon"},
        ]
    )
    tasks = planner.parse_brain_dump("essay and bank stuff", TODAY)

    assert [t.title for t in tasks] == ["Draft essay outline", "Call bank"]
    assert tasks[0].importance == 3
    assert tasks[0].due_date == date(2026, 3, 6)
    assert tasks[1].energy is Energy.medium
    assert tasks[1].due_date is None
    assert "2026-03-04" in client.calls[0]["contents"]
    assert client.calls[0]["model"] == "test-model"


def test_gemini_failure_falls_back_to_rules():
    planner, _ = gemini(error=RuntimeError("quota exceeded"))
    tasks = planner.parse_brain_dump("call mom tomorrow", TODAY)
    assert [t.title for t in tasks] == ["Call mom"]
    assert planner.break_down("Write essay")


def test_gemini_empty_result_falls_back_to_rules():
    planner, _ = gemini([])
    assert [t.title for t in planner.parse_brain_dump("call mom", TODAY)] == ["Call mom"]


def test_gemini_breakdown_is_capped():
    planner, _ = gemini([f"Step {i}" for i in range(12)])
    assert len(planner.break_down("Clean the apartment")) == 6
