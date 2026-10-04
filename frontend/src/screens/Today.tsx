import { useState } from "react";
import { FlameIcon, PlusIcon } from "../components/Icons";
import { TaskRow } from "../components/TaskRow";
import type { Profile, Task } from "../types";

interface Props {
  tasks: Task[];
  profile: Profile | null;
  busy: boolean;
  onAdd: (text: string) => Promise<void>;
  onDone: (task: Task) => void;
  onOpen: (task: Task) => void;
  onFocus: (task: Task) => void;
}

const UP_NEXT = 3;

export function Today({ tasks, profile, busy, onAdd, onDone, onOpen, onFocus }: Props) {
  const [text, setText] = useState("");
  const upNext = tasks.slice(0, UP_NEXT);
  const later = tasks.slice(UP_NEXT);
  const date = new Date().toLocaleDateString(undefined, {
    weekday: "long",
    month: "long",
    day: "numeric",
  });

  async function submit() {
    const trimmed = text.trim();
    if (!trimmed || busy) return;
    await onAdd(trimmed);
    setText("");
  }

  return (
    <div className="screen">
      <header className="screen-head">
        <div>
          <p className="muted">{date}</p>
          <h1>Today</h1>
        </div>
        {profile && (
          <span
            className={profile.streak_days > 0 ? "streak lit" : "streak"}
            aria-label={`${profile.streak_days}-day streak`}
          >
            <FlameIcon size={18} />
            {profile.streak_days}
          </span>
        )}
      </header>

      {profile && <DailyGoal done={profile.completed_today} goal={profile.daily_goal} />}

      {tasks.length === 0 ? (
        <p className="empty">
          Nothing on your list. Add a task below, or type out everything on your mind and Remi
          will sort it into tasks.
        </p>
      ) : (
        <>
          <section className="card" aria-labelledby="up-next">
            <h2 id="up-next">Up next</h2>
            <ul className="tasks">
              {upNext.map((task) => (
                <TaskRow
                  key={task.id}
                  task={task}
                  onDone={() => onDone(task)}
                  onOpen={() => onOpen(task)}
                  onFocus={() => onFocus(task)}
                />
              ))}
            </ul>
          </section>

          {later.length > 0 && (
            <section aria-labelledby="later">
              <h2 id="later" className="section-title">
                Later
              </h2>
              <ul className="tasks plain">
                {later.map((task) => (
                  <TaskRow
                    key={task.id}
                    task={task}
                    onDone={() => onDone(task)}
                    onOpen={() => onOpen(task)}
                  />
                ))}
              </ul>
            </section>
          )}
        </>
      )}

      <form
        className="composer"
        onSubmit={(event) => {
          event.preventDefault();
          void submit();
        }}
      >
        <input
          value={text}
          onChange={(event) => setText(event.target.value)}
          placeholder="Add a task, or dump everything"
          aria-label="Add a task"
        />
        <button className="round" type="submit" disabled={busy || !text.trim()} aria-label="Add">
          <PlusIcon size={20} />
        </button>
      </form>
    </div>
  );
}

function DailyGoal({ done, goal }: { done: number; goal: number }) {
  const reached = done >= goal;
  return (
    <div className="goal">
      <div className="goal-pips" aria-hidden="true">
        {Array.from({ length: goal }, (_, i) => (
          <span key={i} className={i < done ? "pip filled" : "pip"} />
        ))}
      </div>
      <p>
        {reached
          ? `Daily goal reached. ${done} done today.`
          : `${done} of ${goal} done today`}
      </p>
    </div>
  );
}
