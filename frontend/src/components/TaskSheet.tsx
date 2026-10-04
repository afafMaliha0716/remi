import { useEffect } from "react";
import { formatReasons, taskFacts } from "../format";
import type { Task } from "../types";

interface Props {
  task: Task;
  busy: boolean;
  onClose: () => void;
  onFocus: () => void;
  onBreakDown: () => void;
  onSkip: () => void;
  onRemove: () => void;
  onToggleStep: (stepId: number, done: boolean) => void;
}

/** Bottom sheet with a task's details and actions. */
export function TaskSheet(props: Props) {
  const { task, busy, onClose } = props;
  const facts = [taskFacts(task), `${task.energy} effort`].filter(Boolean).join(", ");

  useEffect(() => {
    const onKey = (event: KeyboardEvent) => event.key === "Escape" && onClose();
    window.addEventListener("keydown", onKey);
    return () => window.removeEventListener("keydown", onKey);
  }, [onClose]);

  return (
    <div className="sheet-backdrop" onClick={onClose}>
      <div
        className="sheet"
        role="dialog"
        aria-modal="true"
        aria-labelledby="sheet-title"
        onClick={(event) => event.stopPropagation()}
      >
        <div className="sheet-grabber" />
        <h2 id="sheet-title">{task.title}</h2>
        <p className="muted">{facts}</p>
        {task.reasons.length > 0 && (
          <p className="muted">Why it's here: {formatReasons(task.reasons)}</p>
        )}

        {task.steps.length > 0 && (
          <ol className="steps">
            {task.steps.map((step) => (
              <li key={step.id}>
                <label>
                  <input
                    type="checkbox"
                    checked={step.done}
                    onChange={(event) => props.onToggleStep(step.id, event.target.checked)}
                  />
                  <span>{step.title}</span>
                </label>
              </li>
            ))}
          </ol>
        )}

        <div className="sheet-actions">
          <button className="button primary" onClick={props.onFocus}>
            Start focus
          </button>
          <button className="button" onClick={props.onBreakDown} disabled={busy}>
            {task.steps.length > 0 ? "Redo steps" : "Break it down"}
          </button>
          <button className="button" onClick={props.onSkip} disabled={busy}>
            Not now
          </button>
          <button className="button danger" onClick={props.onRemove} disabled={busy}>
            Delete
          </button>
        </div>
      </div>
    </div>
  );
}
