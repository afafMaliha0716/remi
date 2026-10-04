import { isOverdue, taskFacts } from "../format";
import type { Task } from "../types";
import { CheckIcon, PlayIcon } from "./Icons";

interface Props {
  task: Task;
  onDone: () => void;
  onOpen: () => void;
  /** When given, the row shows a play button that starts a focus timer. */
  onFocus?: () => void;
}

export function TaskRow({ task, onDone, onOpen, onFocus }: Props) {
  const facts = taskFacts(task);
  const stepsDone = task.steps.filter((s) => s.done).length;
  return (
    <li className="task">
      <button className="task-check" aria-label={`Mark "${task.title}" done`} onClick={onDone}>
        <CheckIcon size={16} />
      </button>
      <button className="task-body" onClick={onOpen}>
        <span className="task-title">{task.title}</span>
        {(facts || task.steps.length > 0) && (
          <span
            className={
              task.due_date && isOverdue(task.due_date) ? "task-facts overdue" : "task-facts"
            }
          >
            {facts}
            {task.steps.length > 0 &&
              `${facts ? ", " : ""}${stepsDone} of ${task.steps.length} steps`}
          </span>
        )}
      </button>
      {onFocus && (
        <button className="task-play" aria-label={`Focus on "${task.title}"`} onClick={onFocus}>
          <PlayIcon size={16} />
        </button>
      )}
    </li>
  );
}
