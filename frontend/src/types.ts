export type Energy = "low" | "medium" | "high";

export interface Step {
  id: number;
  title: string;
  done: boolean;
  position: number;
}

export interface Task {
  id: number;
  title: string;
  notes: string;
  status: "todo" | "done";
  energy: Energy;
  importance: number;
  estimated_minutes: number | null;
  due_date: string | null;
  skip_count: number;
  created_at: string;
  completed_at: string | null;
  steps: Step[];
  score: number;
  reasons: string[];
  suggest_breakdown: boolean;
}

export interface Stats {
  open_count: number;
  completed_today: number;
  streak_days: number;
}

/** What the user tells Remi about this moment. */
export interface Moment {
  energy: Energy | null;
  minutes: number | null;
}
