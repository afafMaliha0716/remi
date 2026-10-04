"""Turns free-form text into structured tasks, and tasks into small steps.

Two planners share one interface:

* ``GeminiPlanner`` asks Gemini for structured JSON.
* ``HeuristicPlanner`` uses plain rules. It needs no API key, so the app and
  the test suite work offline, and it is the fallback if the model call fails.
"""

from __future__ import annotations

import json
import logging
import re
from dataclasses import dataclass
from datetime import date, timedelta
from typing import Protocol

from ..config import get_settings
from ..models import Energy

logger = logging.getLogger(__name__)

MAX_TASKS = 20
MAX_STEPS = 6


@dataclass
class PlannedTask:
    title: str
    energy: Energy = Energy.medium
    importance: int = 2
    estimated_minutes: int | None = None
    due_date: date | None = None


class Planner(Protocol):
    name: str

    def parse_brain_dump(self, text: str, today: date) -> list[PlannedTask]: ...

    def break_down(self, title: str, notes: str = "") -> list[str]: ...


# --------------------------------------------------------------------------
# Rule-based planner
# --------------------------------------------------------------------------

_SPLIT = re.compile(r"[\n;]+|(?<=[.!?])\s+|\s+(?:and then|then|and also|also)\s+", re.I)
_BULLET = re.compile(r"^\s*(?:[-*•]|\d+[.)])\s*")
_LEAD_IN = re.compile(r"^(?:(?:and|so|oh|ok|okay|um|also|plus)\b[,\s]*)+", re.I)
_FILLER = re.compile(
    r"^(?:i\s+)?(?:really\s+|still\s+)?"
    r"(?:need to|have to|has to|gotta|got to|should|must|want to|wanna|"
    r"remember to|don'?t forget to|make sure to|make sure i)\s+",
    re.I,
)
_DURATION = re.compile(
    r"\(?\b(?:for\s+|takes?\s+|about\s+|~\s*)?(\d+(?:\.\d+)?)\s*"
    r"(minutes?|mins?|m|hours?|hrs?|h)\b\)?",
    re.I,
)
_WEEKDAYS = ["monday", "tuesday", "wednesday", "thursday", "friday", "saturday", "sunday"]
_DUE = re.compile(
    r"\b(?:(?:due|by|before|on|this)\s+)?"
    r"(today|tonight|tomorrow|next week|" + "|".join(_WEEKDAYS) + r")\b",
    re.I,
)
_URGENT = re.compile(
    r"(?:[,\s]*\b(?:and\s+)?(?:it'?s|it is|this is|that'?s|is|very|really|super)\b)*\s*"
    r"\b(?:urgent(?:ly)?|asap|important|critical|high priority|priority)\b|!{2,}",
    re.I,
)
_LOW_ENERGY = re.compile(
    r"\b(email|text|call|reply|respond|pay|book|schedule|order|buy|pick up|"
    r"drop off|return|renew|print|submit|upload|sign|water|laundry|dishes|trash)\b",
    re.I,
)
_HIGH_ENERGY = re.compile(
    r"\b(write|essay|paper|study|exam|midterm|final|project|code|debug|design|"
    r"research|report|presentation|taxes|plan|prepare|apply|application|resume)\b",
    re.I,
)
_DEFAULT_MINUTES = {Energy.low: 10, Energy.medium: 25, Energy.high: 45}


def _parse_due(match: re.Match[str], today: date) -> date:
    word = match.group(1).lower()
    if word in ("today", "tonight"):
        return today
    if word == "tomorrow":
        return today + timedelta(days=1)
    if word == "next week":
        return today + timedelta(days=7)
    # A weekday name means its next occurrence, never today.
    ahead = (_WEEKDAYS.index(word) - today.weekday()) % 7 or 7
    return today + timedelta(days=ahead)


def _parse_minutes(match: re.Match[str]) -> int:
    value = float(match.group(1))
    if match.group(2).lower().startswith("h"):
        value *= 60
    return max(1, round(value))


class HeuristicPlanner:
    name = "rules"

    def parse_brain_dump(self, text: str, today: date) -> list[PlannedTask]:
        tasks: list[PlannedTask] = []
        for chunk in _SPLIT.split(text):
            task = self._parse_chunk(chunk or "", today)
            if task is not None:
                tasks.append(task)
        return tasks[:MAX_TASKS]

    def _parse_chunk(self, chunk: str, today: date) -> PlannedTask | None:
        chunk = _BULLET.sub("", chunk).strip()
        if not chunk:
            return None

        importance = 3 if _URGENT.search(chunk) else 2
        due = minutes = None

        if m := _DUE.search(chunk):
            due = _parse_due(m, today)
            chunk = chunk[: m.start()] + chunk[m.end():]
        if m := _DURATION.search(chunk):
            minutes = _parse_minutes(m)
            chunk = chunk[: m.start()] + chunk[m.end():]

        if _HIGH_ENERGY.search(chunk):
            energy = Energy.high
        elif _LOW_ENERGY.search(chunk):
            energy = Energy.low
        else:
            energy = Energy.medium

        title = _URGENT.sub("", chunk)
        title = _LEAD_IN.sub("", title.strip())
        title = _FILLER.sub("", title)
        title = re.sub(r"\s+", " ", title).strip(" .,!?:-")
        if len(title) < 2:
            return None

        return PlannedTask(
            title=title[0].upper() + title[1:200],
            energy=energy,
            importance=importance,
            estimated_minutes=minutes or _DEFAULT_MINUTES[energy],
            due_date=due,
        )

    def break_down(self, title: str, notes: str = "") -> list[str]:
        subject = title[0].lower() + title[1:] if title else "this"
        return [
            f"Open or gather what you need to {subject}",
            "Set a 10-minute timer and do only the very first part",
            "Keep going until the main part is done",
            "Do a quick check, then mark it finished",
        ]


# --------------------------------------------------------------------------
# Gemini planner
# --------------------------------------------------------------------------

_PARSE_PROMPT = """\
You are Remi, a planning assistant for people with ADHD. The user has written
an unstructured "brain dump". Extract every distinct thing they need to do.

Rules:
- One task per action. Split compound sentences into separate tasks.
- Titles start with a verb, are specific, and are at most 8 words.
- energy is the focus the task takes: "low" for quick admin, "medium" for
  routine work, "high" for deep or dreaded work.
- importance is 1 (nice to have), 2 (normal), or 3 (urgent or high stakes).
- estimated_minutes is a realistic guess. People with ADHD tend to
  underestimate, so round up.
- due_date is YYYY-MM-DD only when the text states or clearly implies one.
  Today is {today} ({weekday}). Otherwise use null.
- Ignore feelings and commentary that are not tasks.

Brain dump:
\"\"\"{text}\"\"\"
"""

_BREAKDOWN_PROMPT = """\
You are Remi, a planning assistant for people with ADHD. Break the task below
into 3 to {max_steps} small, concrete steps.

Rules:
- The first step must take under two minutes and need no decisions, so
  starting is easy.
- Each step starts with a verb and names a visible action.
- No step should take more than about 15 minutes.

Task: {title}
Notes: {notes}
"""

_TASKS_SCHEMA = {
    "type": "array",
    "items": {
        "type": "object",
        "properties": {
            "title": {"type": "string"},
            "energy": {"type": "string", "enum": ["low", "medium", "high"]},
            "importance": {"type": "integer"},
            "estimated_minutes": {"type": "integer"},
            "due_date": {"type": "string", "nullable": True},
        },
        "required": ["title", "energy", "importance", "estimated_minutes"],
    },
}
_STEPS_SCHEMA = {"type": "array", "items": {"type": "string"}}


def _clamp(value: object, low: int, high: int, default: int) -> int:
    try:
        return max(low, min(high, int(value)))  # type: ignore[arg-type]
    except (TypeError, ValueError):
        return default


def _coerce_task(raw: dict) -> PlannedTask | None:
    """Validate one model-produced task; return None if it is unusable."""
    title = str(raw.get("title") or "").strip()
    if not title:
        return None
    try:
        energy = Energy(str(raw.get("energy", "medium")).lower())
    except ValueError:
        energy = Energy.medium
    due = None
    if raw.get("due_date"):
        try:
            due = date.fromisoformat(str(raw["due_date"])[:10])
        except ValueError:
            due = None
    return PlannedTask(
        title=title[:200],
        energy=energy,
        importance=_clamp(raw.get("importance"), 1, 3, 2),
        estimated_minutes=_clamp(raw.get("estimated_minutes"), 1, 480, 25),
        due_date=due,
    )


class GeminiPlanner:
    name = "gemini"

    def __init__(self, api_key: str, model: str, client=None) -> None:
        if client is None:
            from google import genai

            client = genai.Client(api_key=api_key)
        self._client = client
        self._model = model
        self._fallback = HeuristicPlanner()

    def _generate_json(self, prompt: str, schema: dict):
        response = self._client.models.generate_content(
            model=self._model,
            contents=prompt,
            config={
                "response_mime_type": "application/json",
                "response_schema": schema,
                "temperature": 0.2,
            },
        )
        return json.loads(response.text)

    def parse_brain_dump(self, text: str, today: date) -> list[PlannedTask]:
        prompt = _PARSE_PROMPT.format(
            today=today.isoformat(), weekday=today.strftime("%A"), text=text
        )
        try:
            raw_tasks = self._generate_json(prompt, _TASKS_SCHEMA)
            tasks = [t for t in map(_coerce_task, raw_tasks) if t is not None]
        except Exception:
            logger.exception("Gemini brain-dump parse failed; using rules")
            return self._fallback.parse_brain_dump(text, today)
        return tasks[:MAX_TASKS] or self._fallback.parse_brain_dump(text, today)

    def break_down(self, title: str, notes: str = "") -> list[str]:
        prompt = _BREAKDOWN_PROMPT.format(
            max_steps=MAX_STEPS, title=title, notes=notes or "(none)"
        )
        try:
            raw_steps = self._generate_json(prompt, _STEPS_SCHEMA)
            steps = [str(s).strip()[:200] for s in raw_steps if str(s).strip()]
        except Exception:
            logger.exception("Gemini breakdown failed; using rules")
            return self._fallback.break_down(title, notes)
        return steps[:MAX_STEPS] or self._fallback.break_down(title, notes)


def get_planner() -> Planner:
    """FastAPI dependency: Gemini when a key is configured, rules otherwise."""
    settings = get_settings()
    if settings.gemini_api_key:
        return GeminiPlanner(settings.gemini_api_key, settings.gemini_model)
    return HeuristicPlanner()
