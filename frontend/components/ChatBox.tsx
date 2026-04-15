"use client";

import { FormEvent, useCallback, useMemo, useRef, useState } from "react";

import { queryRag } from "@/lib/api";
import { usePropertyStore } from "@/store/usePropertyStore";

type Message = { id: string; role: "user" | "assistant"; text: string };

type ChatContext = {
  propertyId?: string;
  location?: string;
  propertyDescription?: string;
  propertyTitle?: string;
  latitude?: number | null;
  longitude?: number | null;
};

type ChatBoxProps = {
  context?: ChatContext | null;
};

export function ChatBox({ context }: ChatBoxProps) {
  const activePropertyContext = usePropertyStore((s) => s.activePropertyContext);
  const searchParams = usePropertyStore((s) => s.searchParams);
  const [messages, setMessages] = useState<Message[]>([
    {
      id: "welcome",
      role: "assistant",
      text: "Ask about this area, or ask property-specific questions when a listing is selected."
    }
  ]);
  const [input, setInput] = useState("");
  const [loading, setLoading] = useState(false);
  const listRef = useRef<HTMLDivElement>(null);

  const resolvedContext = useMemo(() => {
    if (context) {
      return context;
    }

    if (activePropertyContext) {
      return {
        propertyId: activePropertyContext.propertyId,
        location: activePropertyContext.location,
        propertyDescription: activePropertyContext.description,
        propertyTitle: activePropertyContext.title,
        latitude: activePropertyContext.latitude,
        longitude: activePropertyContext.longitude
      };
    }

    const searchLocation = [searchParams?.area, searchParams?.city, searchParams?.district]
      .filter(Boolean)
      .join(", ");

    return searchLocation ? { location: searchLocation } : null;
  }, [activePropertyContext, context, searchParams?.area, searchParams?.city, searchParams?.district]);

  const pushAssistant = useCallback((text: string) => {
    setMessages((current) => [
      ...current,
      { id: crypto.randomUUID(), role: "assistant", text }
    ]);
  }, []);

  const onSubmit = (e: FormEvent) => {
    e.preventDefault();
    const trimmed = input.trim();
    if (!trimmed || loading) return;

    setMessages((current) => [
      ...current,
      { id: crypto.randomUUID(), role: "user", text: trimmed }
    ]);
    setInput("");
    setLoading(true);

    void queryRag(trimmed, {
      property_id: resolvedContext?.propertyId,
      location: resolvedContext?.location,
      property_description: resolvedContext?.propertyDescription,
      property_title: resolvedContext?.propertyTitle,
      latitude: resolvedContext?.latitude ?? null,
      longitude: resolvedContext?.longitude ?? null
    })
      .then((response) => {
        pushAssistant(response.answer || "No answer returned from the RAG service.");
      })
      .catch((error: unknown) => {
        pushAssistant(error instanceof Error ? error.message : "RAG request failed.");
      })
      .finally(() => {
        setLoading(false);
      });
  };

  return (
    <div className="flex h-full min-h-[320px] flex-col rounded-2xl border border-white/10 bg-slate-900/40 backdrop-blur-xl">
      <div className="border-b border-white/10 px-4 py-3">
        <p className="text-sm font-semibold text-white">Area assistant</p>
        <p className="text-xs text-slate-500">
          {resolvedContext?.location ? `Context: ${resolvedContext.location}` : "No location context selected"}
        </p>
      </div>
      <div ref={listRef} className="flex-1 space-y-3 overflow-y-auto px-4 py-4 text-sm">
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
      <form onSubmit={onSubmit} className="border-t border-white/10 p-3">
        <div className="flex gap-2">
          <input
            value={input}
            onChange={(e) => setInput(e.target.value)}
            placeholder="Ask about the area..."
            className="flex-1 rounded-xl border border-white/10 bg-white/5 px-3 py-2 text-sm text-slate-100 placeholder:text-slate-500 outline-none focus:ring-2 focus:ring-sky-500/30"
          />
          <button
            type="submit"
            disabled={loading}
            className="rounded-xl bg-sky-500 px-4 py-2 text-sm font-medium text-slate-950 hover:bg-sky-400 disabled:cursor-not-allowed disabled:opacity-60"
          >
            {loading ? "Sending..." : "Send"}
          </button>
        </div>
      </form>
    </div>
  );
}
