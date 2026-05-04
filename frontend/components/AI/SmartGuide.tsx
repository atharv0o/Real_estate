"use client";

import { FormEvent, useMemo, useState } from "react";
import { AnimatePresence, motion } from "framer-motion";
import { Bot, Minus, Send, Sparkles, X } from "lucide-react";
import { usePathname } from "next/navigation";

import { Button } from "@/components/ui/button";
import { Card, CardContent } from "@/components/ui/card";
import { cn } from "@/lib/utils";

type ChatMessage = {
  id: number;
  role: "assistant" | "user";
  content: string;
};

const quickSuggestions = [
  "Analyze current Pune market trends",
  "How does Algorand escrow work?",
  "Check property trust scores"
];

const propertyInsights: Record<string, { label: string; insight: string }> = {
  "p-01": {
    label: "property P-01 in Kharadi",
    insight:
      "I see you're looking at property P-01 in Kharadi. Based on my data, this area is seeing a 12% annual increase in rental demand."
  }
};

const defaultGreeting =
  "Hi, I'm Smart Guide. Ask me about Pune pricing signals, Algorand escrow, or trust scoring for verified properties.";

function buildResponse(prompt: string, routeInsight?: string) {
  const normalized = prompt.toLowerCase();

  if (routeInsight) {
    return `${routeInsight} I can also compare nearby micro-markets, explain the trust score, or outline escrow steps for this listing.`;
  }

  if (normalized.includes("pune") || normalized.includes("market")) {
    return "Pune demand remains strongest around Kharadi, Baner, Hinjewadi, and Wakad. In this simulation, I would retrieve live RAG context from transaction history, rental yield movement, and fresh listing velocity before ranking the best entry points.";
  }

  if (normalized.includes("algorand") || normalized.includes("escrow")) {
    return "Algorand escrow can lock buyer funds in a smart contract until verification milestones are met. Once title, KYC, and property checks pass, the contract releases funds and records the settlement trail on-chain.";
  }

  if (normalized.includes("trust") || normalized.includes("score")) {
    return "Property trust scores usually combine document freshness, seller verification, price anomaly checks, title signals, and blockchain proof. A high score means fewer red flags, not a substitute for legal diligence.";
  }

  return "I found a relevant simulated knowledge path: market momentum, verification confidence, and escrow readiness. Share a locality or property ID and I will narrow the guidance.";
}

export function SmartGuide() {
  const pathname = usePathname();
  const [isOpen, setIsOpen] = useState(false);
  const [isMinimized, setIsMinimized] = useState(false);
  const [isThinking, setIsThinking] = useState(false);
  const [input, setInput] = useState("");
  const [messages, setMessages] = useState<ChatMessage[]>([
    { id: 1, role: "assistant", content: defaultGreeting }
  ]);

  const activeProperty = useMemo(() => {
    const match = pathname?.match(/\/property\/([^/?#]+)/);
    if (!match?.[1]) return undefined;
    return propertyInsights[decodeURIComponent(match[1]).toLowerCase()];
  }, [pathname]);

  const submitPrompt = (prompt: string) => {
    const trimmed = prompt.trim();
    if (!trimmed || isThinking) return;

    const nextUserMessage: ChatMessage = {
      id: Date.now(),
      role: "user",
      content: trimmed
    };

    setMessages((current) => [...current, nextUserMessage]);
    setInput("");
    setIsThinking(true);

    window.setTimeout(() => {
      setMessages((current) => [
        ...current,
        {
          id: Date.now() + 1,
          role: "assistant",
          content: buildResponse(trimmed, activeProperty?.insight)
        }
      ]);
      setIsThinking(false);
    }, 900);
  };

  const handleSubmit = (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    submitPrompt(input);
  };

  return (
    <div className="fixed bottom-5 right-5 z-[110] flex flex-col items-end gap-3 sm:bottom-6 sm:right-6">
      <AnimatePresence>
        {isOpen && !isMinimized && (
          <motion.div
            initial={{ opacity: 0, y: 18, scale: 0.96 }}
            animate={{ opacity: 1, y: 0, scale: 1 }}
            exit={{ opacity: 0, y: 18, scale: 0.96 }}
            transition={{ duration: 0.2, ease: "easeOut" }}
            className="w-[calc(100vw-2.5rem)] max-w-[390px]"
          >
            <Card className="overflow-hidden border-white/15 bg-slate-950/80 shadow-[0_24px_80px_rgba(2,6,23,0.48)] backdrop-blur-2xl">
              <div className="flex items-center justify-between border-b border-white/10 bg-white/5 px-4 py-3">
                <div className="flex min-w-0 items-center gap-3">
                  <span className="flex h-10 w-10 shrink-0 items-center justify-center rounded-full bg-gradient-to-br from-emerald-400 to-blue-500 text-white shadow-[0_0_34px_rgba(16,185,129,0.35)]">
                    <Bot className="h-5 w-5" />
                  </span>
                  <div className="min-w-0">
                    <p className="truncate font-display text-sm font-semibold text-white">
                      Smart Guide
                    </p>
                    <p className="truncate text-xs text-slate-300">
                      RAG market assistant
                    </p>
                  </div>
                </div>
                <div className="flex items-center gap-1">
                  <Button
                    type="button"
                    variant="ghost"
                    size="icon"
                    className="h-8 w-8 text-slate-300 hover:bg-white/10 hover:text-white"
                    onClick={() => setIsMinimized(true)}
                    title="Minimize Smart Guide"
                  >
                    <Minus className="h-4 w-4" />
                  </Button>
                  <Button
                    type="button"
                    variant="ghost"
                    size="icon"
                    className="h-8 w-8 text-slate-300 hover:bg-white/10 hover:text-white"
                    onClick={() => {
                      setIsOpen(false);
                      setIsMinimized(false);
                    }}
                    title="Close Smart Guide"
                  >
                    <X className="h-4 w-4" />
                  </Button>
                </div>
              </div>

              <CardContent className="space-y-4 p-4">
                {activeProperty && (
                  <div className="rounded-lg border border-emerald-400/20 bg-emerald-400/10 px-3 py-2 text-xs text-emerald-100">
                    Context detected: {activeProperty.label}
                  </div>
                )}

                <div className="flex max-h-[360px] min-h-[280px] flex-col gap-3 overflow-y-auto pr-1">
                  {messages.map((message) => (
                    <div
                      key={message.id}
                      className={cn(
                        "flex",
                        message.role === "user" ? "justify-end" : "justify-start"
                      )}
                    >
                      <div
                        className={cn(
                          "max-w-[84%] rounded-2xl px-3.5 py-2.5 text-sm leading-relaxed shadow-sm",
                          message.role === "assistant"
                            ? "bg-gradient-to-br from-emerald-500 to-blue-600 text-white"
                            : "bg-slate-800 text-slate-100"
                        )}
                      >
                        {message.content}
                      </div>
                    </div>
                  ))}

                  {isThinking && (
                    <motion.div
                      initial={{ opacity: 0, y: 8 }}
                      animate={{ opacity: 1, y: 0 }}
                      className="flex justify-start"
                    >
                      <div className="flex max-w-[84%] items-center gap-2 rounded-2xl bg-gradient-to-br from-emerald-500 to-blue-600 px-3.5 py-2.5 text-sm text-white shadow-sm">
                        <span>AI is thinking</span>
                        <span className="flex gap-1" aria-hidden="true">
                          {[0, 1, 2].map((dot) => (
                            <motion.span
                              key={dot}
                              animate={{ opacity: [0.35, 1, 0.35], y: [0, -2, 0] }}
                              transition={{
                                duration: 0.9,
                                repeat: Infinity,
                                delay: dot * 0.12
                              }}
                              className="h-1.5 w-1.5 rounded-full bg-white"
                            />
                          ))}
                        </span>
                      </div>
                    </motion.div>
                  )}
                </div>

                <div className="flex flex-wrap gap-2">
                  {quickSuggestions.map((suggestion) => (
                    <button
                      key={suggestion}
                      type="button"
                      onClick={() => submitPrompt(suggestion)}
                      className="rounded-full border border-white/10 bg-white/5 px-3 py-1.5 text-left text-xs font-medium text-slate-200 transition hover:border-emerald-300/40 hover:bg-emerald-400/10 hover:text-white"
                    >
                      {suggestion}
                    </button>
                  ))}
                </div>

                <form onSubmit={handleSubmit} className="flex items-center gap-2">
                  <input
                    value={input}
                    onChange={(event) => setInput(event.target.value)}
                    placeholder="Ask Smart Guide..."
                    className="h-11 min-w-0 flex-1 rounded-full border border-white/10 bg-slate-900/80 px-4 text-sm text-white outline-none transition placeholder:text-slate-500 focus:border-emerald-300/50 focus:ring-2 focus:ring-emerald-400/20"
                  />
                  <Button
                    type="submit"
                    size="icon"
                    className="h-11 w-11 bg-blue-600 text-white hover:bg-blue-500"
                    disabled={isThinking || !input.trim()}
                    title="Send message"
                  >
                    <Send className="h-4 w-4" />
                  </Button>
                </form>
              </CardContent>
            </Card>
          </motion.div>
        )}
      </AnimatePresence>

      <Button
        type="button"
        size="icon"
        className="h-14 w-14 bg-gradient-to-br from-emerald-400 to-blue-600 text-white shadow-[0_18px_44px_rgba(37,99,235,0.36)] hover:from-emerald-300 hover:to-blue-500"
        onClick={() => {
          setIsOpen((current) => !current || isMinimized);
          setIsMinimized(false);
        }}
        title={isOpen && isMinimized ? "Restore Smart Guide" : "Open Smart Guide"}
      >
        <AnimatePresence mode="wait" initial={false}>
          <motion.span
            key={isOpen && !isMinimized ? "sparkles" : "bot"}
            initial={{ opacity: 0, rotate: -16, scale: 0.8 }}
            animate={{ opacity: 1, rotate: 0, scale: 1 }}
            exit={{ opacity: 0, rotate: 16, scale: 0.8 }}
            transition={{ duration: 0.18 }}
          >
            {isOpen && !isMinimized ? (
              <Sparkles className="h-6 w-6" />
            ) : (
              <Bot className="h-6 w-6" />
            )}
          </motion.span>
        </AnimatePresence>
      </Button>
    </div>
  );
}
