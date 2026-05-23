"use client";

import { useEffect, useRef, useState } from "react";
import {
  verifyDemoToken,
  streamDemoChat,
  type VenueMetadata,
} from "@/lib/demo-api";

// ─── Types ────────────────────────────────────────────────────────────────────

interface Message {
  role: "user" | "assistant";
  content: string;
}

// ─── Lightweight markdown renderer (same as ChatDrawer) ──────────────────────

function renderMarkdown(text: string): React.ReactNode {
  const lines = text.split("\n");
  const nodes: React.ReactNode[] = [];
  let i = 0;

  while (i < lines.length) {
    const raw = lines[i];

    if (!raw.trim()) {
      nodes.push(<div key={i} className="h-2" />);
      i++;
      continue;
    }

    const headerMatch = raw.match(/^(#{1,3})\s+(.+)/);
    if (headerMatch) {
      const level = headerMatch[1].length;
      const cls =
        level === 1
          ? "text-[17px] font-bold text-on-surface mt-1"
          : level === 2
          ? "text-[16px] font-bold text-on-surface mt-1"
          : "text-[14px] font-semibold text-on-surface-variant uppercase tracking-wide mt-1";
      nodes.push(
        <p key={i} className={cls}>
          {inlineFormat(headerMatch[2])}
        </p>,
      );
      i++;
      continue;
    }

    if (/^[\-\*]\s+/.test(raw)) {
      const bullets: React.ReactNode[] = [];
      while (i < lines.length && /^[\-\*]\s+/.test(lines[i])) {
        bullets.push(
          <li key={i} className="flex gap-xs items-start">
            <span className="text-primary-container mt-[4px] shrink-0 text-[13px]">•</span>
            <span>{inlineFormat(lines[i].replace(/^[\-\*]\s+/, ""))}</span>
          </li>,
        );
        i++;
      }
      nodes.push(
        <ul key={`ul-${i}`} className="flex flex-col gap-[3px] my-1">
          {bullets}
        </ul>,
      );
      continue;
    }

    nodes.push(
      <p key={i} className="leading-relaxed">
        {inlineFormat(raw)}
      </p>,
    );
    i++;
  }

  return <>{nodes}</>;
}

function inlineFormat(text: string): React.ReactNode {
  const parts: React.ReactNode[] = [];
  const regex = /(\*\*(.+?)\*\*|\*(.+?)\*|`(.+?)`)/g;
  let last = 0;
  let match: RegExpExecArray | null;

  while ((match = regex.exec(text)) !== null) {
    if (match.index > last) parts.push(text.slice(last, match.index));
    if (match[2])
      parts.push(
        <strong key={match.index} className="font-semibold text-on-surface">
          {match[2]}
        </strong>,
      );
    else if (match[3])
      parts.push(
        <em key={match.index} className="italic">
          {match[3]}
        </em>,
      );
    else if (match[4])
      parts.push(
        <code
          key={match.index}
          className="bg-surface-container px-[4px] py-[1px] rounded text-[13px] font-data-mono text-primary-container"
        >
          {match[4]}
        </code>,
      );
    last = match.index + match[0].length;
  }
  if (last < text.length) parts.push(text.slice(last));
  return parts.length === 1 ? parts[0] : <>{parts}</>;
}

// ─── Suggested starter questions ─────────────────────────────────────────────

const STARTERS = [
  "What audience does this venue attract?",
  "What's the biggest opportunity here?",
  "Which marketing channel should we focus on first?",
  "Who are the closest competitors?",
];

// ─── Main component ───────────────────────────────────────────────────────────

interface DemoChatProps {
  token: string;
}

export default function DemoChat({ token }: DemoChatProps) {
  const [venue, setVenue]           = useState<VenueMetadata | null>(null);
  const [loadError, setLoadError]   = useState<{ status: number; detail: string } | null>(null);
  const [messages, setMessages]     = useState<Message[]>([]);
  const [input, setInput]           = useState("");
  const [isLoading, setIsLoading]   = useState(false);
  const [error, setError]           = useState<string | null>(null);
  const messagesEndRef              = useRef<HTMLDivElement>(null);
  const inputRef                    = useRef<HTMLInputElement>(null);

  // ── Verify token on mount ────────────────────────────────────────────────
  useEffect(() => {
    verifyDemoToken(token).then(({ data, error: err }) => {
      if (err) {
        setLoadError(err);
      } else {
        setVenue(data);
      }
    });
  }, [token]);

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages]);

  useEffect(() => {
    if (venue) setTimeout(() => inputRef.current?.focus(), 200);
  }, [venue]);

  // ── Submit handler ───────────────────────────────────────────────────────
  const handleSubmit = async (question: string) => {
    if (!question.trim() || isLoading || !venue) return;

    setInput("");
    setError(null);
    setMessages((prev) => [...prev, { role: "user", content: question }]);
    setIsLoading(true);

    let current = "";
    await streamDemoChat(token, question, {
      onChunk: (chunk) => {
        current += chunk;
        setMessages((prev) => {
          const msgs = [...prev];
          if (msgs[msgs.length - 1]?.role === "assistant") {
            return [...msgs.slice(0, -1), { role: "assistant", content: current }];
          }
          return [...msgs, { role: "assistant", content: current }];
        });
      },
      onError: (msg) => {
        setError(msg);
        setIsLoading(false);
      },
      onComplete: () => setIsLoading(false),
    });
  };

  // ── Error states ─────────────────────────────────────────────────────────
  if (loadError) {
    const isExpired = loadError.status === 410;
    return (
      <div className="min-h-screen bg-surface flex flex-col items-center justify-center px-lg text-center">
        <span className="material-symbols-outlined text-[56px] text-on-surface-variant/40 mb-md">
          {isExpired ? "schedule" : "link_off"}
        </span>
        <h1 className="text-[22px] font-bold text-on-surface mb-xs">
          {isExpired ? "This demo link has expired" : "Invalid demo link"}
        </h1>
        <p className="text-[15px] text-on-surface-variant max-w-[400px]">
          {isExpired
            ? "Demo links are valid for 72 hours. Ask your Polynovea contact for a fresh link."
            : loadError.detail}
        </p>
        <a
          href="https://polynovea.com"
          className="mt-lg text-[14px] text-primary hover:underline"
        >
          polynovea.com
        </a>
      </div>
    );
  }

  if (!venue) {
    return (
      <div className="min-h-screen bg-surface flex items-center justify-center">
        <div className="flex flex-col items-center gap-sm text-on-surface-variant">
          <div className="flex gap-[5px]">
            <div className="w-2 h-2 bg-primary rounded-full animate-bounce [animation-delay:0ms]" />
            <div className="w-2 h-2 bg-primary rounded-full animate-bounce [animation-delay:150ms]" />
            <div className="w-2 h-2 bg-primary rounded-full animate-bounce [animation-delay:300ms]" />
          </div>
          <span className="text-[13px]">Loading intelligence…</span>
        </div>
      </div>
    );
  }

  // ── Main demo UI ─────────────────────────────────────────────────────────
  return (
    <div className="min-h-screen bg-surface flex flex-col">

      {/* ── Header ─────────────────────────────────────────────────────── */}
      <header className="bg-surface-dim border-b border-outline-variant px-lg py-md flex items-center justify-between shrink-0">
        <div className="flex items-center gap-sm">
          <span className="material-symbols-outlined text-primary text-[26px]">smart_toy</span>
          <div>
            <p className="text-[11px] font-label-sm uppercase tracking-widest text-on-surface-variant/70">
              Polynovea Intelligence · Preview
            </p>
            <h1 className="text-[18px] font-bold text-on-surface leading-tight">
              {venue.venue_name}
            </h1>
            <p className="text-[13px] text-on-surface-variant">
              {[venue.venue_area, venue.venue_city].filter(Boolean).join(", ")}
            </p>
          </div>
        </div>

      </header>

      {/* ── Messages area ──────────────────────────────────────────────── */}
      <main className="flex-1 overflow-y-auto px-lg py-md space-y-md max-w-[820px] w-full mx-auto custom-scrollbar">

        {/* Empty state with starters */}
        {messages.length === 0 && !isLoading && (
          <div className="flex flex-col items-center pt-xl pb-lg gap-lg">
            <div className="text-center">
              <p className="text-[17px] font-medium text-on-surface">
                What would you like to know about{" "}
                <span className="text-primary">{venue.venue_name}</span>?
              </p>
              <p className="text-[14px] text-on-surface-variant/70 mt-xs">
                Real behavioral intelligence. Powered by Polynovea.
              </p>
            </div>

            <div className="grid grid-cols-1 sm:grid-cols-2 gap-sm w-full max-w-[640px]">
              {STARTERS.map((q) => (
                <button
                  key={q}
                  onClick={() => handleSubmit(q)}
                  className="text-left bg-surface-container hover:bg-surface-container-high border border-outline-variant rounded-xl px-md py-sm text-[14px] text-on-surface-variant hover:text-on-surface transition-colors"
                >
                  {q}
                </button>
              ))}
            </div>
          </div>
        )}

        {/* Message thread */}
        {messages.map((msg, idx) => (
          <div
            key={idx}
            className={`flex ${msg.role === "user" ? "justify-end" : "justify-start"}`}
          >
            <div
              className={`max-w-[88%] px-md py-sm rounded-xl text-[15px] leading-relaxed ${
                msg.role === "user"
                  ? "bg-primary text-surface rounded-br-sm font-body-sm"
                  : "bg-surface-dim text-on-surface rounded-bl-sm border border-outline-variant"
              }`}
            >
              {msg.role === "assistant" ? renderMarkdown(msg.content) : msg.content}
            </div>
          </div>
        ))}

        {/* Typing indicator */}
        {isLoading && messages[messages.length - 1]?.role === "user" && (
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
      </main>

      {/* ── Input bar ──────────────────────────────────────────────────── */}
      <footer className="border-t border-outline-variant bg-surface-dim px-lg py-md shrink-0">
        <div className="max-w-[820px] mx-auto flex flex-col gap-sm">
          <form
            onSubmit={(e) => {
              e.preventDefault();
              handleSubmit(input);
            }}
            className="flex gap-sm"
          >
            <input
              ref={inputRef}
              type="text"
              value={input}
              onChange={(e) => setInput(e.target.value)}
              placeholder={`Ask about ${venue.venue_name}…`}
              disabled={isLoading}
              className="flex-1 bg-surface border border-outline-variant rounded-lg px-md py-sm text-[16px] text-on-surface placeholder-on-surface-variant/50 focus:outline-none focus:border-primary disabled:opacity-50"
            />
            <button
              type="submit"
              disabled={!input.trim() || isLoading}
              className="bg-primary text-surface rounded-lg px-md py-sm hover:opacity-90 disabled:opacity-50 transition-opacity"
            >
              <span className="material-symbols-outlined text-[24px]">send</span>
            </button>
          </form>

          {/* Mobile CTA + branding */}
          <div className="flex items-center justify-between">
            <p className="text-[11px] text-on-surface-variant/50">
              Powered by Polynovea's behavioral intelligence framework
            </p>
          </div>
        </div>
      </footer>

    </div>
  );
}
