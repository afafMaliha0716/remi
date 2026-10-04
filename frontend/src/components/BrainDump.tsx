import { useState } from "react";

interface Props {
  busy: boolean;
  onSubmit: (text: string) => Promise<void>;
}

/** The free-form box where everything in the user's head goes. */
export function BrainDump({ busy, onSubmit }: Props) {
  const [text, setText] = useState("");

  async function submit() {
    const trimmed = text.trim();
    if (!trimmed || busy) return;
    await onSubmit(trimmed);
    setText("");
  }

  return (
    <form
      className="dump"
      onSubmit={(event) => {
        event.preventDefault();
        void submit();
      }}
    >
      <label htmlFor="dump">What's on your mind?</label>
      <textarea
        id="dump"
        rows={4}
        value={text}
        placeholder="Type it all out, messy is fine. e.g. email my advisor tomorrow, finish the lab report by Friday, do laundry"
        onChange={(event) => setText(event.target.value)}
        onKeyDown={(event) => {
          if (event.key === "Enter" && (event.metaKey || event.ctrlKey)) void submit();
        }}
      />
      <button className="button primary" type="submit" disabled={busy || !text.trim()}>
        {busy ? "Sorting…" : "Sort it out"}
      </button>
    </form>
  );
}
