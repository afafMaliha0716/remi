/** "25 min" or "1 hr 30 min". */
export function formatMinutes(minutes: number): string {
  if (minutes < 60) return `${minutes} min`;
  const hours = Math.floor(minutes / 60);
  const rest = minutes % 60;
  return rest ? `${hours} hr ${rest} min` : `${hours} hr`;
}

/** "today", "tomorrow", "Friday", or "Mar 14", from a YYYY-MM-DD string. */
export function formatDue(isoDate: string): string {
  const [year, month, day] = isoDate.split("-").map(Number);
  const due = new Date(year, month - 1, day);
  const today = new Date();
  today.setHours(0, 0, 0, 0);
  const days = Math.round((due.getTime() - today.getTime()) / 86_400_000);
  if (days < 0) return days === -1 ? "yesterday" : `${-days} days ago`;
  if (days === 0) return "today";
  if (days === 1) return "tomorrow";
  if (days < 7) return due.toLocaleDateString(undefined, { weekday: "long" });
  return due.toLocaleDateString(undefined, { month: "short", day: "numeric" });
}

/** Joins reasons into one sentence: "Due today, quick win and fits your low energy." */
export function formatReasons(reasons: string[]): string {
  if (reasons.length === 0) return "";
  const parts = reasons.map((r, i) => (i === 0 ? r : r[0].toLowerCase() + r.slice(1)));
  const last = parts.pop()!;
  return (parts.length ? `${parts.join(", ")} and ${last}` : last) + ".";
}
