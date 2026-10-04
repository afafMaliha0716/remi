import type { Tab } from "../types";
import { CoachIcon, FocusIcon, MeIcon, TodayIcon } from "./Icons";

const TABS: { id: Tab; label: string; icon: typeof TodayIcon }[] = [
  { id: "today", label: "Today", icon: TodayIcon },
  { id: "coach", label: "Coach", icon: CoachIcon },
  { id: "focus", label: "Focus", icon: FocusIcon },
  { id: "me", label: "Me", icon: MeIcon },
];

interface Props {
  tab: Tab;
  onChange: (tab: Tab) => void;
}

export function TabBar({ tab, onChange }: Props) {
  return (
    <nav className="tabbar" aria-label="Main">
      {TABS.map(({ id, label, icon: TabIcon }) => (
        <button
          key={id}
          aria-current={tab === id ? "page" : undefined}
          onClick={() => onChange(id)}
        >
          <TabIcon />
          <span>{label}</span>
        </button>
      ))}
    </nav>
  );
}
