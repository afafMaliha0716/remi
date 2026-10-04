import { useEffect, useState } from "react";
import { api } from "../api";
import { Mascot } from "../components/Mascot";
import { formatMinutes } from "../format";
import type { Profile } from "../types";

const FRICTION = ["Easy", "Fine", "Some effort", "Hard", "Very hard"];

interface Props {
  profile: Profile | null;
  theme: "dark" | "light";
  onTheme: (theme: "dark" | "light") => void;
  onCheckIn: (friction: number, note: string) => Promise<void>;
}

export function Me({ profile, theme, onTheme, onCheckIn }: Props) {
  const [friction, setFriction] = useState<number | null>(null);
  const [note, setNote] = useState("");
  const [saved, setSaved] = useState(false);

  useEffect(() => {
    api
      .reflection()
      .then((reflection) => {
        if (reflection) {
          setFriction(reflection.friction);
          setNote(reflection.note);
          setSaved(true);
        }
      })
      .catch(() => undefined);
  }, []);

  if (!profile) return <div className="screen" />;

  const toNext = profile.xp_for_next - profile.xp_into_level;

  return (
    <div className="screen">
      <header className="screen-head">
        <h1>Me</h1>
      </header>

      <section className="card level">
        <Mascot size={64} mood={profile.completed_today >= profile.daily_goal ? "happy" : "calm"} />
        <div className="level-body">
          <p className="muted">Level {profile.level}</p>
          <h2>{profile.level_title}</h2>
          <div
            className="bar"
            role="progressbar"
            aria-valuemin={0}
            aria-valuemax={profile.xp_for_next}
            aria-valuenow={profile.xp_into_level}
            aria-label="Progress to next level"
          >
            <span style={{ width: `${(profile.xp_into_level / profile.xp_for_next) * 100}%` }} />
          </div>
          <p className="muted">
            {profile.xp} XP, {toNext} to level {profile.level + 1}
          </p>
        </div>
      </section>

      <dl className="stats">
        <div>
          <dt>Day streak</dt>
          <dd>{profile.streak_days}</dd>
        </div>
        <div>
          <dt>Done today</dt>
          <dd>{profile.completed_today}</dd>
        </div>
        <div>
          <dt>Focused</dt>
          <dd>{formatMinutes(profile.focus_minutes)}</dd>
        </div>
      </dl>

      <section aria-labelledby="checkin">
        <h2 id="checkin" className="section-title">
          End-of-day check-in
        </h2>
        <div className="card">
          <p>How hard was it to get started today?</p>
          <div className="scale">
            {FRICTION.map((label, index) => (
              <button
                key={label}
                aria-pressed={friction === index + 1}
                onClick={() => {
                  setFriction(index + 1);
                  setSaved(false);
                }}
              >
                <strong>{index + 1}</strong>
                <span>{label}</span>
              </button>
            ))}
          </div>
          <textarea
            rows={2}
            value={note}
            placeholder="Anything that helped or got in the way? (optional)"
            aria-label="Note"
            onChange={(event) => {
              setNote(event.target.value);
              setSaved(false);
            }}
          />
          <button
            className="button primary"
            disabled={friction === null || saved}
            onClick={async () => {
              await onCheckIn(friction!, note);
              setSaved(true);
            }}
          >
            {saved ? "Saved" : "Save check-in"}
          </button>
        </div>
      </section>

      <section aria-labelledby="badges">
        <h2 id="badges" className="section-title">
          Badges
        </h2>
        <ul className="badges">
          {profile.badges.map((badge) => (
            <li key={badge.id} className={badge.earned ? "earned" : undefined}>
              <strong>{badge.name}</strong>
              <span>{badge.description}</span>
            </li>
          ))}
        </ul>
      </section>

      <section aria-labelledby="appearance">
        <h2 id="appearance" className="section-title">
          Appearance
        </h2>
        <div className="segments">
          {(["dark", "light"] as const).map((option) => (
            <button key={option} aria-pressed={theme === option} onClick={() => onTheme(option)}>
              {option === "dark" ? "Dark" : "Light"}
            </button>
          ))}
        </div>
      </section>
    </div>
  );
}
