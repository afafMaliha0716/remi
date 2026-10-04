import type { Energy, Moment } from "../types";

const ENERGY: { value: Energy; label: string }[] = [
  { value: "low", label: "Low" },
  { value: "medium", label: "Okay" },
  { value: "high", label: "High" },
];
const MINUTES = [15, 30, 60];

interface Props {
  moment: Moment;
  onChange: (moment: Moment) => void;
}

/** Lets the user say how much energy and time they have right now. */
export function MomentPicker({ moment, onChange }: Props) {
  return (
    <div className="moment">
      <fieldset>
        <legend>My energy is</legend>
        {ENERGY.map(({ value, label }) => (
          <button
            key={value}
            type="button"
            className="chip"
            aria-pressed={moment.energy === value}
            onClick={() =>
              onChange({ ...moment, energy: moment.energy === value ? null : value })
            }
          >
            {label}
          </button>
        ))}
      </fieldset>
      <fieldset>
        <legend>I have</legend>
        {MINUTES.map((minutes) => (
          <button
            key={minutes}
            type="button"
            className="chip"
            aria-pressed={moment.minutes === minutes}
            onClick={() =>
              onChange({ ...moment, minutes: moment.minutes === minutes ? null : minutes })
            }
          >
            {minutes === 60 ? "1 hr" : `${minutes} min`}
          </button>
        ))}
      </fieldset>
    </div>
  );
}
