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
  steps: Step[];
  score: number;
  reasons: string[];
  suggest_breakdown: boolean;
  xp_awarded: number;
}

export interface Badge {
  id: string;
  name: string;
  description: string;
  earned: boolean;
}

export interface Profile {
  xp: number;
  level: number;
  level_title: string;
  xp_into_level: number;
  xp_for_next: number;
  streak_days: number;
  completed_today: number;
  daily_goal: number;
  open_count: number;
  focus_minutes: number;
  reflected_today: boolean;
  badges: Badge[];
}

export interface Reflection {
  day: string;
  friction: number;
  note: string;
  xp_awarded: number;
}

export interface ChatMessage {
  id: number;
  role: "user" | "remi";
  content: string;
  created_at: string;
}

export interface CoachResponse {
  coach: string;
  mode: string;
  reply: ChatMessage;
  suggested_task_id: number | null;
}

export type CoachMode = "plan_day" | "overwhelm" | "lost_item";

export type Tab = "today" | "coach" | "focus" | "me";
