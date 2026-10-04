"""Remi's conversational coach.

The coach has four modes, matching the product's core prompts:

* ``plan_day``   time-block the next few hours
* ``overwhelm``  shrink everything down to one small step
* ``lost_item``  walk through a calm search for a misplaced thing
* ``chat``       anything else

``GeminiCoach`` writes replies with Gemini. ``ScriptedCoach`` uses fixed,
CBT-informed scripts; it needs no API key and takes over if the model fails.
"""

from __future__ import annotations

import logging
import re
from dataclasses import dataclass, field
from enum import Enum
from typing import Protocol

from ..config import get_settings
from ..models import Task
from .schedule import Block

logger = logging.getLogger(__name__)


class Mode(str, Enum):
    plan_day = "plan_day"
    overwhelm = "overwhelm"
    lost_item = "lost_item"
    chat = "chat"


_MODE_PATTERNS = [
    (Mode.plan_day, re.compile(r"\bplan\b|\bschedule\b|what should i do", re.I)),
    (
        Mode.overwhelm,
        re.compile(
            r"overwhelm|stress|too much|can'?t (?:start|focus|do)|stuck|"
            r"anxious|panic|paralyz|behind on everything",
            re.I,
        ),
    ),
    (Mode.lost_item, re.compile(r"\blost\b|can'?t find|where (?:is|are|did)|misplac", re.I)),
]


def detect_mode(message: str) -> Mode:
    for mode, pattern in _MODE_PATTERNS:
        if pattern.search(message):
            return mode
    return Mode.chat


@dataclass
class Context:
    """What the coach knows when it replies."""

    open_tasks: list[Task] = field(default_factory=list)  # ranked, best first
    plan: list[Block] = field(default_factory=list)
    history: list[tuple[str, str]] = field(default_factory=list)  # (role, text)

    @property
    def smallest_task(self) -> Task | None:
        """The quickest open task: the easiest possible place to start."""
        if not self.open_tasks:
            return None
        return min(self.open_tasks, key=lambda t: t.estimated_minutes or 25)


@dataclass
class Reply:
    text: str
    # A task the app can offer to start a focus timer on.
    suggested_task_id: int | None = None


class Coach(Protocol):
    name: str

    def reply(self, mode: Mode, message: str, context: Context) -> Reply: ...


def _clock(moment) -> str:
    return moment.strftime("%I:%M %p").lstrip("0")


def format_plan(plan: list[Block]) -> str:
    return "\n".join(f"{_clock(b.start)}  {b.title}" for b in plan)


class ScriptedCoach:
    name = "scripted"

    def reply(self, mode: Mode, message: str, context: Context) -> Reply:
        handler = {
            Mode.plan_day: self._plan_day,
            Mode.overwhelm: self._overwhelm,
            Mode.lost_item: self._lost_item,
            Mode.chat: self._chat,
        }[mode]
        return handler(context)

    def _plan_day(self, context: Context) -> Reply:
        if not context.plan:
            return Reply(
                "Your list is empty, so there's nothing to plan yet. "
                "Tell me what's on your mind and I'll turn it into tasks."
            )
        first = next(b for b in context.plan if b.kind == "task")
        return Reply(
            "Here's a plan for the next few hours, most important first, "
            "with breaks built in:\n\n"
            f"{format_plan(context.plan)}\n\n"
            f"Only the first one matters right now: {first.title}.",
            suggested_task_id=first.task_id,
        )

    def _overwhelm(self, context: Context) -> Reply:
        opening = (
            "That's a lot to hold at once, and it makes sense that it feels "
            "heavy. Let's make it smaller.\n\n"
            "1. Breathe out slowly, longer than you breathe in. Three times.\n"
            "2. You don't have to do everything. You only have to do the next thing.\n"
        )
        task = context.smallest_task
        if task is None:
            return Reply(
                opening + "3. Tell me the one thing that's weighing on you most, "
                "and we'll find its first tiny step."
            )
        minutes = task.estimated_minutes or 25
        return Reply(
            opening + f'3. The smallest thing on your list is "{task.title}" '
            f"(about {minutes} min). Do only that. Everything else can wait "
            "until it's done.",
            suggested_task_id=task.id,
        )

    def _lost_item(self, context: Context) -> Reply:
        return Reply(
            "Let's find it. Searching while stressed makes it harder, so "
            "first stand still for a second.\n\n"
            "1. Say out loud what you're looking for. It keeps your attention on it.\n"
            "2. Where did you last use it, not where it should be? Start there.\n"
            "3. Check the usual drop spots: pockets, bag, desk, bed, bathroom "
            "counter, car, by the door.\n"
            "4. Look under and inside things near those spots. Lost items are "
            "usually within arm's reach of where you last had them.\n"
            "5. Retrace your last 30 minutes in order.\n\n"
            "When you find it, pick one home for it so it's there next time."
        )

    def _chat(self, context: Context) -> Reply:
        if not context.open_tasks:
            return Reply(
                "I'm here. Your list is clear right now. If something's on "
                "your mind, tell me and I'll help you turn it into a first step."
            )
        top = context.open_tasks[0]
        return Reply(
            f"I'm here. You have {len(context.open_tasks)} open "
            f"{'task' if len(context.open_tasks) == 1 else 'tasks'}, and the "
            f'one I\'d start with is "{top.title}". I can plan your day, '
            "help when it all feels like too much, or help you find something "
            "you've lost.",
            suggested_task_id=top.id,
        )


_SYSTEM_PROMPT = """\
You are Remi, a warm, calm coach for adults with ADHD. You live inside a task
app and the user is talking to you there.

How you talk:
- Short. At most 120 words. Plain words, no jargon, no emoji.
- Never shame or lecture. Assume the user is doing their best.
- Give one concrete next action, not a list of options to choose from.
- Use ideas from CBT for ADHD: shrink the task, lower the bar to starting,
  separate feelings from facts, plan around energy rather than willpower.
- You are not a therapist or a doctor. If the user describes a crisis or
  wanting to harm themselves, gently tell them to contact a crisis line or
  emergency services, and do not try to handle it yourself.

What this message needs:
{mode_instructions}

The user's open tasks, most important first:
{tasks}
{plan}
Conversation so far:
{history}

User: {message}
Remi:"""

_MODE_INSTRUCTIONS = {
    Mode.plan_day: (
        "The user wants their day planned. A schedule has already been built "
        "and is listed below; present it as it is, do not change the times, "
        "and end by pointing at the first task only."
    ),
    Mode.overwhelm: (
        "The user is overwhelmed. Acknowledge it in one sentence, give one "
        "brief calming action, then pick the single smallest task and say to "
        "do only that."
    ),
    Mode.lost_item: (
        "The user has lost something. Walk them through a calm, ordered "
        "search: last place used, usual drop spots, retrace steps."
    ),
    Mode.chat: "Respond helpfully to what the user said.",
}


class GeminiCoach:
    name = "gemini"

    def __init__(self, api_key: str, model: str, client=None) -> None:
        if client is None:
            from google import genai

            client = genai.Client(api_key=api_key)
        self._client = client
        self._model = model
        self._fallback = ScriptedCoach()

    def reply(self, mode: Mode, message: str, context: Context) -> Reply:
        scripted = self._fallback.reply(mode, message, context)
        tasks = "\n".join(
            f"- {t.title} ({t.estimated_minutes or 25} min, {t.energy.value} effort"
            + (f", due {t.due_date.isoformat()}" if t.due_date else "")
            + ")"
            for t in context.open_tasks[:12]
        )
        plan = (
            f"\nThe schedule:\n{format_plan(context.plan)}\n"
            if mode is Mode.plan_day and context.plan
            else ""
        )
        history = "\n".join(
            f"{'User' if role == 'user' else 'Remi'}: {text}"
            for role, text in context.history[-8:]
        )
        prompt = _SYSTEM_PROMPT.format(
            mode_instructions=_MODE_INSTRUCTIONS[mode],
            tasks=tasks or "(none)",
            plan=plan,
            history=history or "(this is the first message)",
            message=message,
        )
        try:
            response = self._client.models.generate_content(
                model=self._model,
                contents=prompt,
                config={"temperature": 0.6, "max_output_tokens": 400},
            )
            text = (response.text or "").strip()
        except Exception:
            logger.exception("Gemini coach reply failed; using the script")
            return scripted
        if not text:
            return scripted
        # The model writes the words; the suggested task stays rule-based.
        return Reply(text, scripted.suggested_task_id)


def get_coach() -> Coach:
    """FastAPI dependency: Gemini when a key is configured, scripts otherwise."""
    settings = get_settings()
    if settings.gemini_api_key:
        return GeminiCoach(settings.gemini_api_key, settings.gemini_model)
    return ScriptedCoach()
