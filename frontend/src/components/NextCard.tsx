import { formatDue, formatMinutes, formatReasons } from "../format";
import type { Task } from "../types";

interface Props {
  task: Task;
  busy: boolean;
  onDone: () => void;
  onSkip: () => void;
  onBreakDown: () => void;
  onToggleStep: (stepId: number, done: boolean) => void;
}

/** The one task Remi suggests doing now. Everything else stays out of the way. */
export function NextCard({ task, busy, onDone, onSkip, onBreakDown, onToggleStep }: Props) {
  const facts = [
    task.estimated_minutes ? formatMinutes(task.estimated_minutes) : null,
    task.due_date ? `due ${formatDue(task.due_date)}` : null,
    `${task.energy} effort`,
  ].filter(Boolean);
  const nextStep = task.steps.find((step) => !step.done);

  return (
    <section className="next" aria-labelledby="next-title">
      <p className="next-kicker">Do this next</p>
      <h2 id="next-title">{task.title}</h2>
      <p className="next-facts">{facts.join(", ")}</p>
      {task.reasons.length > 0 && (
        <p className="next-why">Why this one: {formatReasons(task.reasons)}</p>
      )}

      {task.steps.length > 0 && (
        <ol className="steps">
          {task.steps.map((step) => (
            <li key={step.id} className={step === nextStep ? "current" : undefined}>
              <label>
                <input
                  type="checkbox"
                  checked={step.done}
                  onChange={(event) => onToggleStep(step.id, event.target.checked)}
                />
                <span>{step.title}</span>
              </label>
            </li>
          ))}
        </ol>
      )}

      <div className="next-actions">
        <button className="button primary" onClick={onDone} disabled={busy}>
          Done
        </button>
        <button className="button" onClick={onBreakDown} disabled={busy}>
          {task.steps.length > 0 ? "Break it down again" : "Break it down"}
        </button>
        <button className="button quiet" onClick={onSkip} disabled={busy}>
          Not now
        </button>
      </div>
    </section>
  );
}
