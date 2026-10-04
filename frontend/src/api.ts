import type {
  ChatMessage,
  CoachMode,
  CoachResponse,
  Profile,
  Reflection,
  Step,
  Task,
} from "./types";

const BASE: string = import.meta.env.VITE_API_URL ?? "/api";

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  let response: Response;
  try {
    response = await fetch(BASE + path, {
      headers: { "Content-Type": "application/json" },
      ...init,
    });
  } catch {
    throw new Error("Can't reach the Remi server. Check that it's running.");
  }
  if (!response.ok) {
    throw new Error(`The server returned an error (${response.status}).`);
  }
  return response.status === 204 ? (undefined as T) : response.json();
}

const send = <T>(method: string, path: string, body?: unknown) =>
  request<T>(path, { method, body: body ? JSON.stringify(body) : undefined });

/** The user's wall-clock time without a zone, e.g. 2026-03-04T09:05:00. */
function localTime(): string {
  const now = new Date();
  const local = new Date(now.getTime() - now.getTimezoneOffset() * 60_000);
  return local.toISOString().slice(0, 19);
}

export const api = {
  tasks: () => request<Task[]>("/tasks"),
  profile: () => request<Profile>("/profile"),
  brainDump: (text: string) => send<{ tasks: Task[] }>("POST", "/brain-dump", { text }),
  complete: (id: number) => send<Task>("POST", `/tasks/${id}/complete`),
  skip: (id: number) => send<Task>("POST", `/tasks/${id}/skip`),
  breakDown: (id: number) => send<Task>("POST", `/tasks/${id}/breakdown`),
  remove: (id: number) => send<void>("DELETE", `/tasks/${id}`),
  setStep: (id: number, done: boolean) => send<Step>("PATCH", `/steps/${id}`, { done }),
  focus: (minutes: number, taskId: number | null) =>
    send<{ xp_awarded: number }>("POST", "/focus", { minutes, task_id: taskId }),
  reflection: () => request<Reflection | null>("/reflections/today"),
  saveReflection: (friction: number, note: string) =>
    send<Reflection>("POST", "/reflections", { friction, note }),
  messages: () => request<ChatMessage[]>("/coach/messages"),
  clearMessages: () => send<void>("DELETE", "/coach/messages"),
  coach: (message: string, mode?: CoachMode) =>
    send<CoachResponse>("POST", "/coach", { message, mode, local_time: localTime() }),
};
