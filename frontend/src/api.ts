import type { Moment, Stats, Step, Task } from "./types";

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

const post = <T>(path: string, body?: unknown) =>
  request<T>(path, { method: "POST", body: body ? JSON.stringify(body) : undefined });

function momentQuery(moment: Moment): string {
  const params = new URLSearchParams();
  if (moment.energy) params.set("energy", moment.energy);
  if (moment.minutes) params.set("minutes", String(moment.minutes));
  const query = params.toString();
  return query ? `?${query}` : "";
}

export const api = {
  tasks: (moment: Moment) => request<Task[]>(`/tasks${momentQuery(moment)}`),
  stats: () => request<Stats>("/stats"),
  brainDump: (text: string) =>
    post<{ planner: string; tasks: Task[] }>("/brain-dump", { text }),
  complete: (id: number) => post<Task>(`/tasks/${id}/complete`),
  reopen: (id: number) => post<Task>(`/tasks/${id}/reopen`),
  skip: (id: number) => post<Task>(`/tasks/${id}/skip`),
  breakDown: (id: number) => post<Task>(`/tasks/${id}/breakdown`),
  remove: (id: number) => request<void>(`/tasks/${id}`, { method: "DELETE" }),
  setStep: (id: number, done: boolean) =>
    request<Step>(`/steps/${id}`, { method: "PATCH", body: JSON.stringify({ done }) }),
};
