import { useEffect, useState } from "react";
import { Mascot } from "../components/Mascot";
import { formatClock, taskFacts } from "../format";
import type { Task } from "../types";

const PRESETS = [5, 15, 25, 45];
const RADIUS = 110;
const CIRCUMFERENCE = 2 * Math.PI * RADIUS;

export interface FocusResult {
  minutes: number;
  task: Task | null;
  /** Whether the user says the task itself is finished. */
  taskDone: boolean;
}

interface Props {
  tasks: Task[];
  task: Task | null;
  onPick: (task: Task | null) => void;
  onFinish: (result: FocusResult) => void;
}

type Phase = "setup" | "running" | "finished";

export function Focus({ tasks, task, onPick, onFinish }: Props) {
  const [phase, setPhase] = useState<Phase>("setup");
  const [minutes, setMinutes] = useState(() =>
    PRESETS.includes(task?.estimated_minutes ?? 0) ? task!.estimated_minutes! : 25,
  );
  // Counting toward a fixed end time keeps the timer right when the tab sleeps.
  const [endsAt, setEndsAt] = useState(0);
  const [pausedLeft, setPausedLeft] = useState<number | null>(null);
  const [now, setNow] = useState(() => Date.now());

  const total = minutes * 60;
  const left = pausedLeft ?? Math.max(0, (endsAt - now) / 1000);

  useEffect(() => {
    if (phase !== "running" || pausedLeft !== null) return;
    const timer = setInterval(() => setNow(Date.now()), 250);
    return () => clearInterval(timer);
  }, [phase, pausedLeft]);

  useEffect(() => {
    if (phase === "running" && pausedLeft === null && left <= 0) setPhase("finished");
  }, [phase, pausedLeft, left]);

  function start() {
    setNow(Date.now());
    setEndsAt(Date.now() + total * 1000);
    setPausedLeft(null);
    setPhase("running");
  }

  function togglePause() {
    if (pausedLeft === null) {
      setPausedLeft(left);
    } else {
      setNow(Date.now());
      setEndsAt(Date.now() + pausedLeft * 1000);
      setPausedLeft(null);
    }
  }

  function finish(taskDone: boolean) {
    const worked = Math.floor((total - left) / 60);
    onFinish({ minutes: worked, task, taskDone });
    setPhase("setup");
  }

  if (phase === "setup") {
    return (
      <div className="screen">
        <header className="screen-head">
          <h1>Focus</h1>
        </header>

        <section aria-labelledby="focus-on">
          <h2 id="focus-on" className="section-title">
            Focus on
          </h2>
          <ul className="picker">
            {tasks.slice(0, 3).map((option) => (
              <li key={option.id}>
                <button aria-pressed={task?.id === option.id} onClick={() => onPick(option)}>
                  <span className="task-title">{option.title}</span>
                  <span className="task-facts">{taskFacts(option)}</span>
                </button>
              </li>
            ))}
            <li>
              <button aria-pressed={task === null} onClick={() => onPick(null)}>
                <span className="task-title">Nothing in particular</span>
              </button>
            </li>
          </ul>
        </section>

        <section aria-labelledby="focus-for">
          <h2 id="focus-for" className="section-title">
            For
          </h2>
          <div className="segments">
            {PRESETS.map((preset) => (
              <button
                key={preset}
                aria-pressed={minutes === preset}
                onClick={() => setMinutes(preset)}
              >
                {preset} min
              </button>
            ))}
          </div>
        </section>

        <button className="button primary wide" onClick={start}>
          Start focus
        </button>
      </div>
    );
  }

  const done = phase === "finished";
  return (
    <div className="screen timer">
      <p className="timer-task">{task ? task.title : "Focus time"}</p>

      <div className="ring">
        <svg viewBox="0 0 240 240" aria-hidden="true">
          <circle className="ring-track" cx="120" cy="120" r={RADIUS} />
          <circle
            className="ring-progress"
            cx="120"
            cy="120"
            r={RADIUS}
            strokeDasharray={CIRCUMFERENCE}
            strokeDashoffset={CIRCUMFERENCE * (left / total)}
          />
        </svg>
        <div className="ring-center">
          <Mascot size={56} mood={done ? "happy" : "calm"} />
          <p className="clock" role="timer">
            {done ? "Done" : formatClock(left)}
          </p>
        </div>
      </div>

      <p className="muted timer-note">
        {done
          ? `${minutes} minutes of focus. Nice work.`
          : pausedLeft !== null
            ? "Paused"
            : "Remi's here with you. Just this one thing."}
      </p>

      {done ? (
        <div className="timer-actions">
          {task && (
            <button className="button primary wide" onClick={() => finish(true)}>
              I finished it
            </button>
          )}
          <button className={task ? "button wide" : "button primary wide"} onClick={() => finish(false)}>
            {task ? "Not finished yet" : "Done"}
          </button>
        </div>
      ) : (
        <div className="timer-actions">
          <button className="button wide" onClick={togglePause}>
            {pausedLeft !== null ? "Resume" : "Pause"}
          </button>
          <button className="button quiet wide" onClick={() => finish(false)}>
            End early
          </button>
        </div>
      )}
    </div>
  );
}
