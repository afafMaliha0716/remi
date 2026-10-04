import { useCallback, useEffect, useState } from "react";
import { api } from "./api";
import { TabBar } from "./components/TabBar";
import { TaskSheet } from "./components/TaskSheet";
import { Coach } from "./screens/Coach";
import { Focus, type FocusResult } from "./screens/Focus";
import { Me } from "./screens/Me";
import { Today } from "./screens/Today";
import type { Profile, Tab, Task } from "./types";

type Theme = "dark" | "light";

function savedTheme(): Theme {
  try {
    return localStorage.getItem("remi-theme") === "light" ? "light" : "dark";
  } catch {
    return "dark";
  }
}

export default function App() {
  const [tab, setTab] = useState<Tab>("today");
  const [tasks, setTasks] = useState<Task[]>([]);
  const [profile, setProfile] = useState<Profile | null>(null);
  const [openId, setOpenId] = useState<number | null>(null);
  const [focusId, setFocusId] = useState<number | null>(null);
  const [busy, setBusy] = useState(false);
  const [toast, setToast] = useState<{ id: number; text: string; kind: "xp" | "error" } | null>(
    null,
  );
  const [theme, setTheme] = useState<Theme>(savedTheme);

  useEffect(() => {
    document.documentElement.dataset.theme = theme;
    try {
      localStorage.setItem("remi-theme", theme);
    } catch {
      // Private browsing: the choice just won't be remembered.
    }
  }, [theme]);

  useEffect(() => {
    if (!toast) return;
    const timer = setTimeout(() => setToast(null), toast.kind === "error" ? 5000 : 2200);
    return () => clearTimeout(timer);
  }, [toast]);

  const showError = useCallback((text: string) => {
    setToast({ id: Date.now(), text, kind: "error" });
  }, []);

  /** Celebrates earned XP, and a level-up when the new profile shows one. */
  const celebrate = useCallback((xp: number, before: Profile | null, after: Profile) => {
    if (xp <= 0) return;
    const leveledUp = before !== null && after.level > before.level;
    setToast({
      id: Date.now(),
      kind: "xp",
      text: leveledUp ? `Level ${after.level}: ${after.level_title}` : `+${xp} XP`,
    });
  }, []);

  const refresh = useCallback(async () => {
    const [nextTasks, nextProfile] = await Promise.all([api.tasks(), api.profile()]);
    setTasks(nextTasks);
    setProfile(nextProfile);
    return nextProfile;
  }, []);

  /** Runs an API call, reloads, and shows any XP it earned. */
  const run = useCallback(
    async (action?: () => Promise<{ xp_awarded?: number } | unknown>) => {
      setBusy(true);
      try {
        const result = await action?.();
        const before = profile;
        const after = await refresh();
        const xp = (result as { xp_awarded?: number } | undefined)?.xp_awarded ?? 0;
        celebrate(xp, before, after);
      } catch (cause) {
        showError(cause instanceof Error ? cause.message : "Something went wrong.");
      } finally {
        setBusy(false);
      }
    },
    [profile, refresh, celebrate, showError],
  );

  useEffect(() => {
    refresh().catch((cause: Error) => showError(cause.message));
  }, [refresh, showError]);

  const openTask = tasks.find((task) => task.id === openId) ?? null;
  const focusTask = tasks.find((task) => task.id === focusId) ?? null;

  function startFocus(task: Task) {
    setFocusId(task.id);
    setOpenId(null);
    setTab("focus");
  }

  /** Checks a step off immediately, then saves it. */
  function toggleStep(stepId: number, done: boolean) {
    setTasks((current) =>
      current.map((task) => ({
        ...task,
        steps: task.steps.map((s) => (s.id === stepId ? { ...s, done } : s)),
      })),
    );
    void run(() => api.setStep(stepId, done));
  }

  async function finishFocus({ minutes, task, taskDone }: FocusResult) {
    await run(async () => {
      let xp = 0;
      if (minutes > 0) xp += (await api.focus(minutes, task?.id ?? null)).xp_awarded;
      if (task && taskDone) xp += (await api.complete(task.id)).xp_awarded;
      return { xp_awarded: xp };
    });
    if (taskDone) setFocusId(null);
  }

  return (
    <div className="app">
      <main>
        {tab === "today" && (
          <Today
            tasks={tasks}
            profile={profile}
            busy={busy}
            onAdd={(text) => run(() => api.brainDump(text))}
            onDone={(task) => run(() => api.complete(task.id))}
            onOpen={(task) => setOpenId(task.id)}
            onFocus={startFocus}
          />
        )}
        {tab === "coach" && <Coach tasks={tasks} onFocus={startFocus} onError={showError} />}
        {/* Focus stays mounted so a running timer survives switching tabs. */}
        <div hidden={tab !== "focus"}>
          <Focus
            key={focusId ?? "none"}
            tasks={tasks}
            task={focusTask}
            onPick={(task) => setFocusId(task?.id ?? null)}
            onFinish={finishFocus}
          />
        </div>
        {tab === "me" && (
          <Me
            profile={profile}
            theme={theme}
            onTheme={setTheme}
            onCheckIn={(friction, note) => run(() => api.saveReflection(friction, note))}
          />
        )}
      </main>

      {toast && (
        <p key={toast.id} className={`toast ${toast.kind}`} role="status">
          {toast.text}
        </p>
      )}

      {openTask && (
        <TaskSheet
          task={openTask}
          busy={busy}
          onClose={() => setOpenId(null)}
          onFocus={() => startFocus(openTask)}
          onBreakDown={() => run(() => api.breakDown(openTask.id))}
          onSkip={() => {
            setOpenId(null);
            void run(() => api.skip(openTask.id));
          }}
          onRemove={() => {
            setOpenId(null);
            void run(() => api.remove(openTask.id));
          }}
          onToggleStep={toggleStep}
        />
      )}

      <TabBar tab={tab} onChange={setTab} />
    </div>
  );
}
