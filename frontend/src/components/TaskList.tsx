import { formatDue, formatMinutes } from "../format";
import type { Task } from "../types";

interface Props {
  tasks: Task[];
  onDone: (id: number) => void;
  onRemove: (id: number) => void;
}

/** Everything that isn't the next task, kept deliberately quiet. */
export function TaskList({ tasks, onDone, onRemove }: Props) {
  return (
    <section className="later" aria-labelledby="later-title">
      <h2 id="later-title">After that</h2>
      <ul>
        {tasks.map((task) => (
          <li key={task.id}>
            <button
              className="check"
              aria-label={`Mark "${task.title}" done`}
              onClick={() => onDone(task.id)}
            />
            <div className="later-body">
              <span className="later-title">{task.title}</span>
              <span className="later-facts">
                {[
                  task.estimated_minutes ? formatMinutes(task.estimated_minutes) : null,
                  task.due_date ? `due ${formatDue(task.due_date)}` : null,
                ]
                  .filter(Boolean)
                  .join(", ")}
              </span>
            </div>
            <button
              className="remove"
              aria-label={`Delete "${task.title}"`}
              onClick={() => onRemove(task.id)}
            >
              ×
            </button>
          </li>
        ))}
      </ul>
    </section>
  );
}
