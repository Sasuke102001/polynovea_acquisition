"use client";

import { useState, useRef, useEffect } from "react";
import { streamChat } from "@/lib/chat-api";

// ─── Types ────────────────────────────────────────────────────────────────────

interface Message {
  role: "user" | "assistant";
  content: string;
}

type Tab = "marketing" | "competitors" | "transform" | "deep_risk" | "overview" | "audience";

interface ChatDrawerProps {
  venueId: number;
  tab: Tab;
}

// ─── Lightweight markdown renderer ───────────────────────────────────────────
// Handles: **bold**, *italic*, `code`, headers (###), bullets (-), blank lines.
// No external dependency — pure JSX.

function renderMarkdown(text: string): React.ReactNode {
  const lines = text.split("\n");
  const nodes: React.ReactNode[] = [];
  let i = 0;

  while (i < lines.length) {
    const raw = lines[i];

    // Blank line → spacing
    if (!raw.trim()) {
      nodes.push(<div key={i} className="h-2" />);
      i++;
      continue;
    }

    // Header: ###, ##, #
    const headerMatch = raw.match(/^(#{1,3})\s+(.+)/);
    if (headerMatch) {
      const level = headerMatch[1].length;
      const className = level === 1
        ? "text-[17px] font-bold text-on-surface mt-1"
        : level === 2
        ? "text-[16px] font-bold text-on-surface mt-1"
        : "text-[14px] font-semibold text-on-surface-variant uppercase tracking-wide mt-1";
      nodes.push(<p key={i} className={className}>{inlineFormat(headerMatch[2])}</p>);
      i++;
      continue;
    }

    // Bullet: - item or * item
    if (/^[\-\*]\s+/.test(raw)) {
      const bulletNodes: React.ReactNode[] = [];
      while (i < lines.length && /^[\-\*]\s+/.test(lines[i])) {
        bulletNodes.push(
          <li key={i} className="flex gap-xs items-start">
            <span className="text-primary-container mt-[4px] shrink-0 text-[13px]">•</span>
            <span>{inlineFormat(lines[i].replace(/^[\-\*]\s+/, ""))}</span>
          </li>
        );
        i++;
      }
      nodes.push(<ul key={`ul-${i}`} className="flex flex-col gap-[3px] my-1">{bulletNodes}</ul>);
      continue;
    }

    // Numbered list: 1. item
    if (/^\d+\.\s+/.test(raw)) {
      const listNodes: React.ReactNode[] = [];
      let num = 1;
      while (i < lines.length && /^\d+\.\s+/.test(lines[i])) {
        listNodes.push(
          <li key={i} className="flex gap-xs items-start">
            <span className="text-primary-container shrink-0 text-[14px] font-data-mono mt-[2px] min-w-[20px]">{num}.</span>
            <span>{inlineFormat(lines[i].replace(/^\d+\.\s+/, ""))}</span>
          </li>
        );
        i++;
        num++;
      }
      nodes.push(<ol key={`ol-${i}`} className="flex flex-col gap-[3px] my-1">{listNodes}</ol>);
      continue;
    }

    // Paragraph
    nodes.push(
      <p key={i} className="leading-relaxed">
        {inlineFormat(raw)}
      </p>
    );
    i++;
  }

  return <>{nodes}</>;
}

// Inline: **bold**, *italic*, `code`
function inlineFormat(text: string): React.ReactNode {
  const parts: React.ReactNode[] = [];
  // Pattern: **bold**, *italic*, `code`
  const regex = /(\*\*(.+?)\*\*|\*(.+?)\*|`(.+?)`)/g;
  let last = 0;
  let match: RegExpExecArray | null;

  while ((match = regex.exec(text)) !== null) {
    if (match.index > last) parts.push(text.slice(last, match.index));
    if (match[2]) parts.push(<strong key={match.index} className="font-semibold text-on-surface">{match[2]}</strong>);
    else if (match[3]) parts.push(<em key={match.index} className="italic">{match[3]}</em>);
    else if (match[4]) parts.push(<code key={match.index} className="bg-surface-container px-[4px] py-[1px] rounded text-[13px] font-data-mono text-primary-container">{match[4]}</code>);
    last = match.index + match[0].length;
  }
  if (last < text.length) parts.push(text.slice(last));
  return parts.length === 1 ? parts[0] : <>{parts}</>;
}

// ─── Tab metadata ─────────────────────────────────────────────────────────────

const TAB_META: Record<Tab, { label: string; subtitle: string }> = {
  marketing:   { label: "Marketing Assistant",       subtitle: "Content, ads, campaigns, audience" },
  competitors:  { label: "Competitor Analyst",        subtitle: "Positioning, gaps, similar venues" },
  transform:    { label: "Transformation Advisor",    subtitle: "Segment targeting, fitness gaps" },
  deep_risk:    { label: "Risk Analyst",              subtitle: "Churn signals, retention patterns" },
  overview:     { label: "Venue Intelligence",        subtitle: "Health score, fitness, segments" },
  audience:     { label: "Audience Analyst",          subtitle: "Spend, dwell, loyalty, platforms" },
};

// ─── Component ───────────────────────────────────────────────────────────────

const COUNCIL_DELIBERATING = "[COUNCIL:DELIBERATING]";

const STORAGE_KEY = (venueId: number) => `polynovea_chat_${venueId}`;

export default function ChatDrawer({ venueId, tab }: ChatDrawerProps) {
  const [isOpen, setIsOpen]             = useState(false);
  const [messages, setMessages]         = useState<Message[]>(() => {
    try {
      const stored = localStorage.getItem(STORAGE_KEY(venueId));
      return stored ? (JSON.parse(stored) as Message[]) : [];
    } catch { return []; }
  });
  const [input, setInput]               = useState("");
  const [isLoading, setIsLoading]       = useState(false);
  const [isDeliberating, setIsDeliberating] = useState(false);
  const [error, setError]               = useState<string | null>(null);
  const messagesEndRef                  = useRef<HTMLDivElement>(null);
  const inputRef                        = useRef<HTMLInputElement>(null);

  // Save to localStorage — called only on user send and response complete, not on every chunk
  const persistMessages = (msgs: Message[]) => {
    try {
      localStorage.setItem(STORAGE_KEY(venueId), JSON.stringify(msgs));
    } catch { /* storage full — silently ignore */ }
  };

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages]);

  useEffect(() => {
    if (isOpen) setTimeout(() => inputRef.current?.focus(), 100);
  }, [isOpen]);

  const handleClearChat = () => {
    setMessages([]);
    setError(null);
    try { localStorage.removeItem(STORAGE_KEY(venueId)); } catch { /* ignore */ }
  };

  const handleSubmit = async (
    e: React.FormEvent | React.MouseEvent,
    mode: "fast" | "council" = "fast",
  ) => {
    e.preventDefault();
    if (!input.trim() || isLoading) return;

    const userQuestion = input.trim();
    setInput("");
    setError(null);

    const withUserMsg = (prev: Message[]) => [...prev, { role: "user" as const, content: userQuestion }];
    setMessages(withUserMsg);
    persistMessages(withUserMsg(messages));
    setIsLoading(true);

    let currentResponse = "";
    let deliberatingDone = false;

    await streamChat(venueId, tab, userQuestion, {
      onChunk: (chunk) => {
        // Council sentinel — show deliberating spinner, strip the marker
        if (!deliberatingDone && chunk.includes(COUNCIL_DELIBERATING)) {
          setIsDeliberating(true);
          deliberatingDone = true;
          chunk = chunk.replace(COUNCIL_DELIBERATING, "");
          if (!chunk) return;
        }
        // Real content arriving — dismiss deliberating state
        if (isDeliberating || deliberatingDone) setIsDeliberating(false);

        currentResponse += chunk;
        setMessages((prev) => {
          const msgs = [...prev];
          if (msgs[msgs.length - 1]?.role === "assistant") {
            msgs[msgs.length - 1] = { role: "assistant", content: currentResponse };
          } else {
            msgs.push({ role: "assistant", content: currentResponse });
          }
          return msgs;
        });
      },
      onError: (msg) => {
        setIsDeliberating(false);
        setError(msg);
        setIsLoading(false);
      },
      onComplete: () => {
        setIsDeliberating(false);
        setIsLoading(false);
        // Save to localStorage once — after full response, not on every chunk
        setMessages((prev) => {
          persistMessages(prev);
          return prev;
        });
      },
    }, mode);
  };

  const { label, subtitle } = TAB_META[tab] ?? { label: "Polynovea Intelligence", subtitle: "" };

  return (
    <>
      {/* Floating button */}
      {!isOpen && (
        <button
          onClick={() => setIsOpen(true)}
          className="fixed bottom-6 left-6 md:bottom-8 md:left-8 z-40 bg-primary text-surface rounded-full p-3 md:p-4 shadow-lg hover:opacity-90 transition-opacity"
          title="Ask Polynovea"
        >
          <span className="material-symbols-outlined text-[24px] md:text-[28px]">smart_toy</span>
        </button>
      )}

      {/* Backdrop + drawer */}
      <div
        className={`fixed inset-0 z-50 transition-opacity duration-300 ${isOpen ? "opacity-100" : "pointer-events-none opacity-0"}`}
        onClick={() => setIsOpen(false)}
      >
        <div className="absolute inset-0 bg-black/50" />

        <div
          className={`absolute inset-y-0 right-0 md:bottom-4 md:right-6 md:top-4 md:rounded-xl w-full md:w-[760px] bg-surface border border-outline-variant shadow-2xl transition-transform duration-300 flex flex-col ${
            isOpen ? "translate-x-0" : "translate-x-full"
          }`}
          onClick={(e) => e.stopPropagation()}
        >
          {/* Header */}
          <div className="flex items-center justify-between px-lg py-md border-b border-outline-variant bg-surface-dim rounded-t-xl shrink-0">
            <div>
              <h3 className="text-[18px] font-bold text-on-surface">{label}</h3>
              <p className="text-[14px] text-on-surface-variant mt-[2px]">{subtitle}</p>
            </div>
            <div className="flex items-center gap-sm">
              {messages.length > 0 && !isLoading && (
                <button
                  onClick={handleClearChat}
                  className="text-[12px] text-on-surface-variant/60 hover:text-error transition-colors flex items-center gap-[3px]"
                  title="Clear chat history"
                >
                  <span className="material-symbols-outlined text-[14px]">delete_sweep</span>
                  Clear
                </button>
              )}
              <button
                onClick={() => { setIsOpen(false); setInput(""); setError(null); }}
                className="text-on-surface-variant hover:text-on-surface transition-colors"
              >
                <span className="material-symbols-outlined">close</span>
              </button>
            </div>
          </div>

          {/* Messages */}
          <div className="flex-1 overflow-y-auto px-lg py-md space-y-md bg-surface custom-scrollbar">
            {messages.length === 0 && !isLoading && (
              <div className="text-center text-on-surface-variant py-xl">
                <span className="material-symbols-outlined text-[48px] text-on-surface-variant/40">smart_toy</span>
                <p className="text-[17px] font-medium mt-sm">Ask anything about this venue.</p>
                <p className="text-[14px] text-on-surface-variant/60 mt-xs">Powered by Polynovea's behavioral intelligence framework.</p>
              </div>
            )}

            {messages.map((msg, idx) => (
              <div key={idx} className={`flex ${msg.role === "user" ? "justify-end" : "justify-start"}`}>
                <div
                  className={`max-w-[88%] px-md py-sm rounded-xl text-[15px] leading-relaxed ${
                    msg.role === "user"
                      ? "bg-primary text-surface rounded-br-sm font-body-sm"
                      : "bg-surface-dim text-on-surface rounded-bl-sm border border-outline-variant"
                  }`}
                >
                  {msg.role === "assistant"
                    ? renderMarkdown(msg.content)
                    : msg.content}
                </div>
              </div>
            ))}

            {isDeliberating && (
              <div className="flex justify-start">
                <div className="bg-surface-dim border border-[#7C3AED]/40 rounded-xl rounded-bl-sm px-md py-sm flex flex-col gap-xs max-w-[88%]">
                  <div className="flex items-center gap-sm">
                    <div className="flex gap-[3px]">
                      <div className="w-1.5 h-1.5 bg-[#7C3AED] rounded-full animate-bounce [animation-delay:0ms]" />
                      <div className="w-1.5 h-1.5 bg-[#7C3AED] rounded-full animate-bounce [animation-delay:120ms]" />
                      <div className="w-1.5 h-1.5 bg-[#7C3AED] rounded-full animate-bounce [animation-delay:240ms]" />
                    </div>
                    <span className="text-[12px] font-data-mono text-[#7C3AED] uppercase tracking-wider">
                      Council deliberating
                    </span>
                  </div>
                  <p className="text-[11px] text-on-surface-variant/60 font-body-sm">
                    3 models analysing · debating · synthesising
                  </p>
                </div>
              </div>
            )}

            {isLoading && !isDeliberating && messages[messages.length - 1]?.role === "user" && (
              <div className="flex justify-start">
                <div className="bg-surface-dim border border-outline-variant rounded-xl rounded-bl-sm px-md py-sm flex items-center gap-xs">
                  <div className="w-1.5 h-1.5 bg-primary rounded-full animate-bounce [animation-delay:0ms]" />
                  <div className="w-1.5 h-1.5 bg-primary rounded-full animate-bounce [animation-delay:150ms]" />
                  <div className="w-1.5 h-1.5 bg-primary rounded-full animate-bounce [animation-delay:300ms]" />
                </div>
              </div>
            )}

            {error && (
              <div className="bg-error/10 border border-error/40 text-error px-md py-sm rounded-lg text-[14px]">
                {error}
              </div>
            )}

            <div ref={messagesEndRef} />
          </div>

          {/* Input */}
          <form onSubmit={(e) => handleSubmit(e, "fast")} className="px-lg py-md border-t border-outline-variant bg-surface-dim rounded-b-xl shrink-0">
            <div className="flex gap-sm">
              <input
                ref={inputRef}
                type="text"
                value={input}
                onChange={(e) => setInput(e.target.value)}
                placeholder="Ask a question…"
                disabled={isLoading}
                className="flex-1 bg-surface border border-outline-variant rounded-lg px-md py-sm text-[16px] text-on-surface placeholder-on-surface-variant/50 focus:outline-none focus:border-primary disabled:opacity-50"
              />
              {/* Fast send */}
              <button
                type="submit"
                disabled={!input.trim() || isLoading}
                className="bg-primary text-surface rounded-lg px-md py-sm hover:opacity-90 disabled:opacity-50 transition-opacity"
                title="Quick answer"
              >
                <span className="material-symbols-outlined text-[24px]">send</span>
              </button>
            </div>

            {/* Council button */}
            <div className="flex flex-col items-end mt-xs gap-[2px]">
              <button
                type="button"
                onClick={(e) => handleSubmit(e, "council")}
                disabled={!input.trim() || isLoading}
                className="flex items-center gap-xs bg-surface border border-[#7C3AED]/50 text-[#7C3AED] rounded-lg px-sm py-[5px] text-[12px] font-label-sm hover:bg-[#7C3AED]/10 disabled:opacity-40 transition-colors"
                title="Ask the Council of Models"
              >
                <span className="material-symbols-outlined text-[15px]">hub</span>
                Ask the Council
              </button>
              <span className="text-[10px] text-on-surface-variant/50 font-body-sm">
                3 models · may take 15–20 sec
              </span>
            </div>
          </form>
        </div>
      </div>
    </>
  );
}
