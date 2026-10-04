import { useEffect, useRef, useState } from "react";
import { api } from "../api";
import { SendIcon } from "../components/Icons";
import { Mascot } from "../components/Mascot";
import type { ChatMessage, CoachMode, Task } from "../types";

const PROMPTS: { mode: CoachMode; label: string }[] = [
  { mode: "plan_day", label: "Plan my day" },
  { mode: "overwhelm", label: "I'm overwhelmed" },
  { mode: "lost_item", label: "I lost something" },
];

interface Props {
  tasks: Task[];
  onFocus: (task: Task) => void;
  onError: (message: string) => void;
}

export function Coach({ tasks, onFocus, onError }: Props) {
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [text, setText] = useState("");
  const [waiting, setWaiting] = useState(false);
  // The task Remi pointed at in its latest reply, offered as a focus button.
  const [suggestedId, setSuggestedId] = useState<number | null>(null);
  const end = useRef<HTMLDivElement>(null);

  useEffect(() => {
    api.messages().then(setMessages).catch((e: Error) => onError(e.message));
  }, [onError]);

  useEffect(() => {
    end.current?.scrollIntoView({ block: "end" });
  }, [messages, waiting]);

  async function send(message: string, mode?: CoachMode) {
    if (!message.trim() || waiting) return;
    const mine: ChatMessage = {
      id: -Date.now(),
      role: "user",
      content: message,
      created_at: new Date().toISOString(),
    };
    setMessages((current) => [...current, mine]);
    setText("");
    setSuggestedId(null);
    setWaiting(true);
    try {
      const response = await api.coach(message, mode);
      setMessages((current) => [...current, response.reply]);
      setSuggestedId(response.suggested_task_id);
    } catch (cause) {
      onError(cause instanceof Error ? cause.message : "Something went wrong.");
    } finally {
      setWaiting(false);
    }
  }

  const suggested = tasks.find((task) => task.id === suggestedId);

  return (
    <div className="screen chat">
      <header className="chat-head">
        <Mascot size={36} />
        <div>
          <h1>Remi</h1>
          <p className="muted">Your coach</p>
        </div>
      </header>

      <div className="chat-log" aria-live="polite">
        {messages.length === 0 && !waiting && (
          <p className="chat-intro">
            Hi, I'm Remi. Tell me what's going on, or pick one of the options below and I'll take
            it from there.
          </p>
        )}
        {messages.map((message) => (
          <p key={message.id} className={`bubble ${message.role}`}>
            {message.content}
          </p>
        ))}
        {waiting && <p className="bubble remi typing">Remi is typing</p>}
        {suggested && !waiting && (
          <button className="button primary suggest" onClick={() => onFocus(suggested)}>
            Start focus on "{suggested.title}"
          </button>
        )}
        <div ref={end} />
      </div>

      <div className="chips">
        {PROMPTS.map(({ mode, label }) => (
          <button key={mode} className="chip" disabled={waiting} onClick={() => send(label, mode)}>
            {label}
          </button>
        ))}
      </div>

      <form
        className="composer"
        onSubmit={(event) => {
          event.preventDefault();
          void send(text);
        }}
      >
        <input
          value={text}
          onChange={(event) => setText(event.target.value)}
          placeholder="Message Remi"
          aria-label="Message Remi"
        />
        <button className="round" type="submit" disabled={waiting || !text.trim()} aria-label="Send">
          <SendIcon size={20} />
        </button>
      </form>
    </div>
  );
}
