# Remi

**An ADHD coach that turns a messy brain dump into one clear next step.**

Most to-do apps hand you a long list and leave the hard part to you: deciding
where to start. Remi takes whatever is in your head, turns it into structured
tasks, and then shows you one thing to do next, with the reason it picked it.

![Remi showing one next task with its steps, and the rest of the list below](docs/screenshot.png)

## What it does

- **Brain dump.** Type everything out in any order. Remi splits it into
  tasks and works out due dates, time estimates, effort, and urgency.
- **One next task.** Open tasks are ranked and only the top one is shown
  prominently, along with why: "Due tomorrow and quick win."
- **Matches the moment.** Tell Remi your energy level and how much time you
  have, and the ranking adjusts. Low energy and 15 minutes gets you a quick
  admin task, not the essay.
- **Break it down.** Any task can be split into small steps, starting with one
  that takes under two minutes so getting started is easy.
- **Not now is fine.** Skipping a task moves it aside for a couple of hours
  with no guilt. A task skipped three times gets a suggestion to break it
  down, since it is probably too big or too vague.
- **Progress.** A count of what you finished today and a day streak.

## How the prioritization works

Ranking is a sum of small, explainable signals rather than a black box
(`backend/app/services/prioritize.py`):

| Signal | Effect |
|--------|--------|
| Deadline | Overdue, due today, tomorrow, or this week, in that order |
| Importance | Urgent tasks rank higher |
| Quick win | Tasks of 10 minutes or less get a boost to build momentum |
| Energy fit | Tasks that need more focus than you have right now drop |
| Time fit | Tasks longer than your available time drop |
| Age | Older tasks drift upward slowly so nothing is buried |
| Just skipped | Steps aside for two hours |

Every signal that fires adds a plain-language reason, which the app shows next
to the task.

## How the AI works

Remi has two planners behind one interface
(`backend/app/services/planner.py`):

- **Gemini planner.** Sends the brain dump to Gemini with a prompt written for
  ADHD planning and asks for structured JSON. Every field that comes back is
  validated and clamped before it is saved.
- **Rule-based planner.** Parses due dates ("by Friday"), durations
  ("for 2 hours"), urgency, and effort with plain rules. It needs no API key,
  so the app runs and the tests pass offline, and it takes over automatically
  if the model call fails.

## Tech stack

| Layer    | Tools |
|----------|-------|
| Frontend | React 19, TypeScript, Vite |
| Backend  | Python, FastAPI, SQLModel, Pydantic |
| Database | PostgreSQL (SQLite for zero-setup local development) |
| AI       | Gemini API with structured output |
| Testing  | pytest (47 tests), GitHub Actions |

## Running locally

You need Python 3.11+ and Node 18+.

### Backend

```bash
cd backend
python -m venv venv
source venv/bin/activate          # Windows: venv\Scripts\activate
pip install -r requirements-dev.txt
uvicorn app.main:app --reload     # http://localhost:8000
```

This uses a local SQLite file and the rule-based planner, so there is nothing
else to set up. Interactive API docs are at `http://localhost:8000/docs`.

To use PostgreSQL or Gemini, copy `backend/.env.example` to `backend/.env`
and fill it in. `docker compose up -d` starts a local PostgreSQL.

### Frontend

```bash
cd frontend
npm install
npm run dev                       # http://localhost:5173
```

### Tests

```bash
cd backend
pytest
```

## API

| Endpoint | Description |
|----------|-------------|
| `POST /api/brain-dump` | Turn free-form text into saved tasks |
| `GET /api/tasks` | Open tasks ranked by priority; accepts `energy` and `minutes` |
| `GET /api/tasks/next` | The single best task for right now |
| `POST /api/tasks` | Create a task |
| `PATCH /api/tasks/{id}` | Edit a task |
| `DELETE /api/tasks/{id}` | Delete a task |
| `POST /api/tasks/{id}/complete` | Mark done |
| `POST /api/tasks/{id}/skip` | Not now |
| `POST /api/tasks/{id}/breakdown` | Split into small steps |
| `PATCH /api/steps/{id}` | Check a step off |
| `GET /api/stats` | Open count, completed today, streak |

## Project structure

```
backend/
  app/
    main.py               FastAPI app
    models.py             Task and Step tables
    routers/tasks.py      API endpoints
    services/planner.py   Gemini and rule-based planners
    services/prioritize.py   Ranking engine
  tests/                  pytest suite
frontend/
  src/
    App.tsx               Page layout and data loading
    components/           Brain dump, energy picker, next task, task list
    api.ts                Typed API client
mobile/                   Early Expo app shell for a future native client
```

## Roadmap

- Accounts and sign-in (Remi is single-user today)
- Reminders and scheduling
- Learn from each user's history: adjust time estimates and rankings from what
  actually gets finished and what gets skipped
- Native mobile app on the same API

## Credits

Built by [Afaf Maliha](https://github.com/afafMaliha0716). Thanks to Saurav
Kandel for the early mobile app shell and database setup.
