import { useCallback, useEffect, useState } from "react";
import { api } from "./api";
import { BrainDump } from "./components/BrainDump";
import { MomentPicker } from "./components/MomentPicker";
import { NextCard } from "./components/NextCard";
import { TaskList } from "./components/TaskList";
import type { Moment, Stats, Task } from "./types";

export default function App() {
  const [tasks, setTasks] = useState<Task[] | null>(null);
  const [stats, setStats] = useState<Stats | null>(null);
  const [moment, setMoment] = useState<Moment>({ energy: null, minutes: null });
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const refresh = useCallback(async () => {
    const [nextTasks, nextStats] = await Promise.all([api.tasks(moment), api.stats()]);
    setTasks(nextTasks);
    setStats(nextStats);
  }, [moment]);

  /** Runs an API call, then reloads the list so the ranking stays current. */
  const run = useCallback(
    async (action?: () => Promise<unknown>) => {
      setBusy(true);
      try {
        await action?.();
        await refresh();
        setError(null);
      } catch (cause) {
        setError(cause instanceof Error ? cause.message : "Something went wrong.");
      } finally {
        setBusy(false);
      }
    },
    [refresh],
  );

  useEffect(() => {
    void run();
  }, [run]);

  /** Checks a step off immediately, then saves it. */
  function toggleStep(stepId: number, done: boolean) {
    setTasks(
      (current) =>
        current?.map((task) => ({
          ...task,
          steps: task.steps.map((s) => (s.id === stepId ? { ...s, done } : s)),
        })) ?? null,
    );
    void run(() => api.setStep(stepId, done));
  }

  const [next, ...later] = tasks ?? [];

  return (
    <main>
      <header className="masthead">
        <img src="/shell.svg" alt="" width="36" height="36" />
        <h1>Remi</h1>
        {stats && stats.completed_today > 0 && (
          <p className="tally">
            {stats.completed_today} done today
            {stats.streak_days > 1 && `, ${stats.streak_days}-day streak`}
          </p>
        )}
      </header>

      <BrainDump busy={busy} onSubmit={(text) => run(() => api.brainDump(text))} />

      {error && (
        <p className="error" role="alert">
          {error}
        </p>
      )}

      {tasks !== null && tasks.length === 0 && !error && (
        <p className="empty">
          Nothing on your list. Write down whatever's in your head and Remi will turn it
          into tasks.
        </p>
      )}

      {next && (
        <>
          <MomentPicker moment={moment} onChange={setMoment} />
          <NextCard
            task={next}
            busy={busy}
            onDone={() => run(() => api.complete(next.id))}
            onSkip={() => run(() => api.skip(next.id))}
            onBreakDown={() => run(() => api.breakDown(next.id))}
            onToggleStep={toggleStep}
          />
        </>
      )}

      {later.length > 0 && (
        <TaskList
          tasks={later}
          onDone={(id) => run(() => api.complete(id))}
          onRemove={(id) => run(() => api.remove(id))}
        />
      )}
    </main>
  );
}
