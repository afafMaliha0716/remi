interface Props {
  size?: number;
  /** "happy" closes the eyes into arcs, for celebrations. */
  mood?: "calm" | "happy";
}

/** Remi: a scallop shell drawn in a single line weight. */
export function Mascot({ size = 48, mood = "calm" }: Props) {
  return (
    <svg
      className="mascot"
      width={size}
      height={size}
      viewBox="0 0 64 64"
      fill="none"
      stroke="currentColor"
      strokeWidth="2.5"
      strokeLinecap="round"
      strokeLinejoin="round"
      aria-hidden="true"
    >
      <path d="M32 10C17 10 7 22 7 35c0 7 4 12 9 15l10 4h12l10-4c5-3 9-8 9-15C57 22 47 10 32 10z" />
      <path d="M26 54l-2 3h16l-2-3" />
      <path d="M20 16l5 11M32 12v13M44 16l-5 11" opacity=".45" />
      {mood === "happy" ? (
        <path d="M22 37q3-3 6 0M36 37q3-3 6 0" />
      ) : (
        <>
          <circle cx="25" cy="37" r="1.4" fill="currentColor" />
          <circle cx="39" cy="37" r="1.4" fill="currentColor" />
        </>
      )}
      <path d="M28 43q4 3.5 8 0" />
    </svg>
  );
}
