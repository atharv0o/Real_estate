"use client";

import { FormEvent, useCallback, useRef, useState } from "react";

type Message = { id: string; role: "user" | "assistant"; text: string };

/**
 * Lightweight AI-style chat shell — wire to your RAG endpoint later.
 */
export function ChatBox() {
  const [messages, setMessages] = useState<Message[]>([
    {
      id: "welcome",
      role: "assistant",
      text: "Ask about this area — e.g. average price trends, schools nearby, or investment outlook."
    }
  ]);
  const [input, setInput] = useState("");
  const listRef = useRef<HTMLDivElement>(null);

  const pushAssistant = useCallback((text: string) => {
    setMessages((m) => [
      ...m,
      { id: crypto.randomUUID(), role: "assistant", text }
    ]);
  }, []);

  const onSubmit = (e: FormEvent) => {
    e.preventDefault();
    const trimmed = input.trim();
    if (!trimmed) return;

    setMessages((m) => [
      ...m,
      { id: crypto.randomUUID(), role: "user", text: trimmed }
    ]);
    setInput("");

    // Placeholder “AI” reply — replace with streaming API
    window.setTimeout(() => {
      pushAssistant(
        "This is a demo reply. Connect your RAG backend to answer with live property and document context."
      );
    }, 400);
  };

  return (
    <div className="flex h-full min-h-[320px] flex-col rounded-2xl border border-white/10 bg-slate-900/40 backdrop-blur-xl">
      <div className="border-b border-white/10 px-4 py-3">
        <p className="text-sm font-semibold text-white">Area assistant</p>
        <p className="text-xs text-slate-500">Demo UI — no backend attached</p>
      </div>
      <div
        ref={listRef}
        className="flex-1 space-y-3 overflow-y-auto px-4 py-4 text-sm"
      >
        {messages.map((msg) => (
          <div
            key={msg.id}
            className={
              msg.role === "user"
                ? "ml-8 rounded-2xl rounded-br-md bg-sky-600/30 px-3 py-2 text-slate-100"
                : "mr-8 rounded-2xl rounded-bl-md border border-white/5 bg-slate-800/60 px-3 py-2 text-slate-300"
            }
          >
            {msg.text}
          </div>
        ))}
      </div>
      <form
        onSubmit={onSubmit}
        className="border-t border-white/10 p-3"
      >
        <div className="flex gap-2">
          <input
            value={input}
            onChange={(e) => setInput(e.target.value)}
            placeholder="Ask about the area..."
            className="flex-1 rounded-xl border border-white/10 bg-white/5 px-3 py-2 text-sm text-slate-100 placeholder:text-slate-500 outline-none focus:ring-2 focus:ring-sky-500/30"
          />
          <button
            type="submit"
            className="rounded-xl bg-sky-500 px-4 py-2 text-sm font-medium text-slate-950 hover:bg-sky-400"
          >
            Send
          </button>
        </div>
      </form>
    </div>
  );
}
