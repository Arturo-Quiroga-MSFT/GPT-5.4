/**
 * ChatInput — textarea + send button at the bottom of the chat.
 *
 * • Enter submits; Shift+Enter inserts a newline.
 * • Disabled while a response is streaming.
 */
import { useState, type KeyboardEvent } from "react";

interface Props {
  onSend: (message: string) => void;
  disabled: boolean;
}

export function ChatInput({ onSend, disabled }: Props) {
  const [value, setValue] = useState("");

  function submit() {
    const msg = value.trim();
    if (!msg || disabled) return;
    onSend(msg);
    setValue("");
  }

  function handleKeyDown(e: KeyboardEvent<HTMLTextAreaElement>) {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      submit();
    }
  }

  return (
    <div className="chat-input-row">
      <textarea
        className="chat-input"
        rows={2}
        value={value}
        onChange={(e) => setValue(e.target.value)}
        onKeyDown={handleKeyDown}
        placeholder="Ask about a stock, e.g. 'Analyse MSFT for the last 60 days'… (Enter to send)"
        disabled={disabled}
        aria-label="Chat message"
      />
      <button
        className="send-btn"
        onClick={submit}
        disabled={disabled || !value.trim()}
        aria-label="Send message"
      >
        Send ↑
      </button>
    </div>
  );
}
