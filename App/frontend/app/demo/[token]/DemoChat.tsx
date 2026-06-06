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

function modeBadge(level: number): { label: string; background: string; border: string; color: string } {
  switch (level) {
    case 1:
      return { label: "1 AI Model", background: "rgba(59,130,246,0.2)", border: "1px solid rgba(59,130,246,0.4)", color: "#60a5fa" };
    case 2:
      return { label: "Council", background: "rgba(168,85,247,0.2)", border: "1px solid rgba(168,85,247,0.4)", color: "#d8b4fe" };
    case 3:
      return { label: "Prism", background: "rgba(234,179,8,0.2)", border: "1px solid rgba(234,179,8,0.4)", color: "#eab308" };
    case 4:
      return { label: "Council + Prism", background: "rgba(16,185,129,0.18)", border: "1px solid rgba(16,185,129,0.35)", color: "#34d399" };
    default:
      return { label: `Level ${level}`, background: "rgba(113,113,122,0.2)", border: "1px solid rgba(113,113,122,0.35)", color: "#a1a1aa" };
  }
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

// ─── Council mode helpers ─────────────────────────────────────────────────────

interface CouncilEvent {
  round: "r1" | "r2";
  model: string;
  meta: string;
  text: string;
}

const COUNCIL_DELIBERATING = "[COUNCIL:DELIBERATING]";
const COUNCIL_SYNTHESIS    = "[COUNCIL:SYNTHESIS]";

const MODEL_META: Record<string, { label: string; color: string }> = {
  nemotron: { label: "LLAMA 3.3",  color: "#a78bfa" },
  deepseek: { label: "LLAMA 3.1",  color: "#67e8f9" },
  mistral:  { label: "MISTRAL",    color: "#fcd34d" },
  qwen:     { label: "QWEN",       color: "#fcd34d" },
};

function parsePhaseEvents(buf: string): CouncilEvent[] {
  const re = /\[COUNCIL:PHASE:(r[12]):([^:]+):([^\]]+)\]([^\n]*)\n/g;
  const events: CouncilEvent[] = [];
  let match: RegExpExecArray | null;
  while ((match = re.exec(buf)) !== null) {
    events.push({ round: match[1] as "r1" | "r2", model: match[2], meta: match[3], text: match[4].trim() });
  }
  return events;
}

function CouncilProgressPanel({ phase, events }: { phase: "r1" | "r2" | "synthesis" | null; events: CouncilEvent[] }) {
  const r1Done = events.filter((e) => e.round === "r1");
  const r2Done = events.filter((e) => e.round === "r2");

  const steps = [
    {
      id: "r1",
      label: "Round 1 — Independent analysis",
      detail: r1Done.length > 0
        ? r1Done.map((e) => MODEL_META[e.model]?.label ?? e.model.toUpperCase()).join(" · ")
        : "3 models thinking…",
      done: r1Done.length >= 3,
      active: phase === "r1" || phase === null,
    },
    {
      id: "r2",
      label: "Round 2 — Cross-reviewing positions",
      detail: r2Done.length > 0
        ? r2Done.map((e) => MODEL_META[e.model]?.label ?? e.model.toUpperCase()).join(" · ")
        : "Models deliberating…",
      done: r2Done.length >= 3,
      active: phase === "r2",
    },
    {
      id: "synthesis",
      label: "Synthesizing final answer",
      detail: phase === "synthesis" ? "Streaming…" : "",
      done: false,
      active: phase === "synthesis",
    },
  ];

  return (
    <div style={{ background: "rgba(168,85,247,0.06)", border: "1px solid rgba(168,85,247,0.2)", borderRadius: 12, padding: "12px 16px" }}>
      <div style={{ display: "flex", alignItems: "center", gap: 6, marginBottom: 10 }}>
        <span style={{ color: "#d8b4fe", fontSize: 10, fontFamily: "'JetBrains Mono', monospace", fontWeight: 700, letterSpacing: "0.1em" }}>
          COUNCIL · DELIBERATING
        </span>
        <div className="flex gap-1">
          {[0, 150, 300].map((d) => (
            <div key={d} className="w-1 h-1 rounded-full animate-bounce" style={{ background: "#a78bfa", animationDelay: `${d}ms` }} />
          ))}
        </div>
      </div>
      <div style={{ display: "flex", flexDirection: "column", gap: 8 }}>
        {steps.map((step) => (
          <div key={step.id} style={{ display: "flex", alignItems: "flex-start", gap: 8 }}>
            <div style={{
              width: 14, height: 14, borderRadius: "50%", flexShrink: 0, marginTop: 3,
              background: step.done ? "#a78bfa" : step.active ? "rgba(167,139,250,0.25)" : "transparent",
              border: `1px solid ${step.done ? "#a78bfa" : step.active ? "#a78bfa" : "rgba(63,63,70,0.8)"}`,
              display: "flex", alignItems: "center", justifyContent: "center",
            }}>
              {step.done && <span style={{ color: "#0A0A0A", fontSize: 8, fontWeight: 900 }}>✓</span>}
            </div>
            <div>
              <p style={{ fontSize: 12, fontWeight: 600, color: step.done ? "#d8b4fe" : step.active ? "#F5F5F5" : "#52525B", margin: 0 }}>
                {step.label}
              </p>
              {step.detail && (
                <p style={{ fontSize: 10, color: "#71717A", margin: "2px 0 0", fontFamily: "'JetBrains Mono', monospace" }}>
                  {step.detail}
                </p>
              )}
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}

// ─── Suggested starter questions ─────────────────────────────────────────────

const STARTERS_M2 = [
  "What audience does this venue attract?",
  "What's the biggest opportunity here?",
  "Which marketing channel should we focus on first?",
  "Who are the closest competitors?",
];

const STARTERS_M3 = [
  "Why do my regulars keep coming back?",
  "What's stopping my audience from spending more per visit?",
  "What does choosing this venue say about my customer?",
  "Which cultural occasions should I build campaigns around?",
];

function getStarters(demoLevel: number): string[] {
  return demoLevel === 3 || demoLevel === 4 ? STARTERS_M3 : STARTERS_M2;
}

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
  const [isDeliberating, setIsDeliberating]   = useState(false);
  const [councilPhase, setCouncilPhase]       = useState<"r1" | "r2" | "synthesis" | null>(null);
  const [councilEvents, setCouncilEvents]     = useState<CouncilEvent[]>([]);
  const messagesEndRef              = useRef<HTMLDivElement>(null);
  const inputRef                    = useRef<HTMLInputElement>(null);
  const badge                       = venue ? modeBadge(venue.demo_level) : null;

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

    // Reset council state for new message
    setIsDeliberating(false);
    setCouncilPhase(null);
    setCouncilEvents([]);

    setInput("");
    setError(null);
    setMessages((prev) => [...prev, { role: "user", content: question }]);
    setIsLoading(true);

    const isCouncil = venue.demo_level === 2 || venue.demo_level === 4;
    let deliberatingDone = false;
    let synthesisDone = false;
    let councilBuf = "";
    let current = "";

    const appendToResponse = (text: string) => {
      current += text;
      setMessages((prev) => {
        const msgs = [...prev];
        if (msgs[msgs.length - 1]?.role === "assistant") {
          return [...msgs.slice(0, -1), { role: "assistant", content: current }];
        }
        return [...msgs, { role: "assistant", content: current }];
      });
    };

    const absorbPhaseEvents = (buf: string) => {
      const events = parsePhaseEvents(buf);
      if (events.length === 0) return;
      setCouncilEvents((prev) => {
        const seen = new Set(prev.map((e) => `${e.round}:${e.model}`));
        const fresh = events.filter((e) => !seen.has(`${e.round}:${e.model}`));
        if (fresh.length === 0) return prev;
        const next = [...prev, ...fresh];
        const hasR2 = next.some((e) => e.round === "r2");
        setCouncilPhase(hasR2 ? "r2" : "r1");
        return next;
      });
    };

    await streamDemoChat(token, question, {
      onChunk: (chunk) => {
        if (isCouncil && !synthesisDone) {
          if (!deliberatingDone && chunk.includes(COUNCIL_DELIBERATING)) {
            setIsDeliberating(true);
            deliberatingDone = true;
            chunk = chunk.replace(COUNCIL_DELIBERATING, "");
            if (!chunk.trim()) return;
          }

          councilBuf += chunk;
          const synthIdx = councilBuf.indexOf(COUNCIL_SYNTHESIS);
          if (synthIdx !== -1) {
            absorbPhaseEvents(councilBuf.slice(0, synthIdx));
            synthesisDone = true;
            setCouncilPhase("synthesis");
            // Keep isDeliberating=true so the panel stays visible while synthesis streams.
            // It will be cleared in onComplete.
            const tail = councilBuf.slice(synthIdx + COUNCIL_SYNTHESIS.length + 1);
            councilBuf = "";
            if (tail.trim()) appendToResponse(tail);
            return;
          }

          absorbPhaseEvents(councilBuf);
          return;
        }
        appendToResponse(chunk);
      },
      onError: (msg) => {
        setError(msg);
        setIsDeliberating(false);
        setIsLoading(false);
      },
      onComplete: () => {
        setIsDeliberating(false);
        setIsLoading(false);
      },
    });
  };

  // ── Error states ─────────────────────────────────────────────────────────
  if (loadError) {
    const isExpired = loadError.status === 410;
    return (
      <div className="min-h-screen flex flex-col items-center justify-center px-8 text-center" style={{ background: "#0A0A0A" }}>
        <span className="material-symbols-outlined text-[52px] mb-5" style={{ color: "#27272A" }}>
          {isExpired ? "schedule" : "link_off"}
        </span>
        <h1 className="text-xl font-bold mb-2" style={{ fontFamily: "'Clash Display', 'Inter', sans-serif", color: "#F5F5F5" }}>
          {isExpired ? "This demo link has expired" : "Invalid demo link"}
        </h1>
        <p className="text-sm max-w-[400px]" style={{ color: "#71717A" }}>
          {isExpired
            ? "Demo links are valid for 72 hours. Ask your Polynovea contact for a fresh link."
            : loadError.detail}
        </p>
        <a href="https://polynovea.in" className="mt-8 text-sm gold-glow hover:underline">
          polynovea.in
        </a>
      </div>
    );
  }

  if (!venue) {
    return (
      <div className="min-h-screen flex items-center justify-center" style={{ background: "#0A0A0A" }}>
        <div className="flex flex-col items-center gap-3">
          <div className="flex gap-1.5">
            {[0, 150, 300].map((d) => (
              <div key={d} className="w-2 h-2 rounded-full animate-bounce" style={{ background: "#E6D3A3", animationDelay: `${d}ms` }} />
            ))}
          </div>
          <span className="text-xs font-mono" style={{ color: "#71717A" }}>Loading intelligence…</span>
        </div>
      </div>
    );
  }

  // ── Main demo UI ─────────────────────────────────────────────────────────
  return (
    <div className="min-h-screen flex flex-col" style={{ background: "#0A0A0A", color: "#F5F5F5" }}>

      {/* ── Header ─────────────────────────────────────────────────────── */}
      <header
        className="flex items-center px-6 py-4 shrink-0"
        style={{
          background: "rgba(10,10,10,0.9)",
          backdropFilter: "blur(20px)",
          borderBottom: "1px solid rgba(39,39,42,0.6)",
          boxShadow: "0 4px 24px rgba(0,0,0,0.4)",
        }}
      >
        <div className="flex items-center gap-3">
          <div
            className="w-8 h-8 rounded-lg flex items-center justify-center"
            style={{ background: "rgba(230,211,163,0.1)", border: "1px solid rgba(230,211,163,0.2)" }}
          >
            <span className="material-symbols-outlined text-[16px]" style={{ color: "#E6D3A3" }}>smart_toy</span>
          </div>
          <div className="flex-1">
            <p className="text-[9px] font-bold uppercase tracking-widest" style={{ fontFamily: "'JetBrains Mono', monospace", color: "#9A8F6A" }}>
              Polynovea Intelligence · Preview
            </p>
            <div className="flex items-center gap-2">
              <h1 className="text-base font-bold leading-tight gold-glow" style={{ fontFamily: "'Clash Display', 'Inter', sans-serif" }}>
                {venue.venue_name}
              </h1>
              {/* NEW: Level Badge */}
              <span
                className="text-[10px] font-bold px-2 py-1 rounded"
                style={{
                  background: badge?.background,
                  border: badge?.border,
                  color: badge?.color,
                }}
              >
                {badge?.label}
              </span>
            </div>
            <p className="text-[11px]" style={{ color: "#71717A" }}>
              {[venue.venue_area, venue.venue_city].filter(Boolean).join(", ")}
            </p>
          </div>
        </div>
      </header>

      {/* ── Messages area ──────────────────────────────────────────────── */}
      <main className="flex-1 overflow-y-auto px-5 py-6 space-y-4 max-w-[820px] w-full mx-auto custom-scrollbar">

        {/* Empty state with starters */}
        {messages.length === 0 && !isLoading && (
          <div className="flex flex-col items-center pt-12 pb-8 gap-8">
            <div className="text-center">
              <p className="text-base font-medium" style={{ color: "#F5F5F5" }}>
                What would you like to know about{" "}
                <span style={{ color: "#E6D3A3" }}>{venue.venue_name}</span>?
              </p>
              <p className="text-sm mt-1" style={{ color: "#71717A" }}>
                Real behavioral intelligence. Powered by Polynovea.
              </p>
            </div>

            <div className="grid grid-cols-1 sm:grid-cols-2 gap-3 w-full max-w-[640px]">
              {getStarters(venue.demo_level).map((q) => (
                <button
                  key={q}
                  onClick={() => handleSubmit(q)}
                  className="text-left rounded-xl px-4 py-3 text-sm transition-all duration-200"
                  style={{
                    background: "rgba(24,24,27,0.6)",
                    border: "1px solid rgba(39,39,42,0.7)",
                    color: "#A1A1AA",
                  }}
                  onMouseEnter={(e) => {
                    (e.currentTarget as HTMLElement).style.borderColor = "rgba(230,211,163,0.25)";
                    (e.currentTarget as HTMLElement).style.color = "#F5F5F5";
                  }}
                  onMouseLeave={(e) => {
                    (e.currentTarget as HTMLElement).style.borderColor = "rgba(39,39,42,0.7)";
                    (e.currentTarget as HTMLElement).style.color = "#A1A1AA";
                  }}
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
              className="max-w-[88%] px-4 py-3 rounded-2xl text-[14px] leading-relaxed"
              style={
                msg.role === "user"
                  ? { background: "rgba(230,211,163,0.12)", border: "1px solid rgba(230,211,163,0.2)", color: "#F5F5F5", borderBottomRightRadius: 4 }
                  : { background: "rgba(24,24,27,0.8)", border: "1px solid rgba(39,39,42,0.7)", color: "#E4E1E6", borderBottomLeftRadius: 4 }
              }
            >
              {msg.role === "assistant" ? renderMarkdown(msg.content) : msg.content}
            </div>
          </div>
        ))}

        {/* Council deliberation panel — visible through synthesis, hidden on complete */}
        {isLoading && (isDeliberating || councilPhase !== null) && (
          <div className="flex justify-start">
            <div className="max-w-[88%] w-full">
              <CouncilProgressPanel phase={councilPhase} events={councilEvents} />
            </div>
          </div>
        )}

        {/* Typing indicator (non-council or initial load) */}
        {isLoading && !isDeliberating && councilPhase === null && messages[messages.length - 1]?.role === "user" && (
          <div className="flex justify-start">
            <div
              className="rounded-2xl px-4 py-3 flex items-center gap-1.5"
              style={{ background: "rgba(24,24,27,0.8)", border: "1px solid rgba(39,39,42,0.7)", borderBottomLeftRadius: 4 }}
            >
              {[0, 150, 300].map((d) => (
                <div key={d} className="w-1.5 h-1.5 rounded-full animate-bounce" style={{ background: "#E6D3A3", animationDelay: `${d}ms` }} />
              ))}
            </div>
          </div>
        )}

        {error && (
          <div className="rounded-xl px-4 py-3 text-sm" style={{ background: "rgba(251,113,133,0.08)", border: "1px solid rgba(251,113,133,0.2)", color: "#FB7185" }}>
            {error}
          </div>
        )}

        <div ref={messagesEndRef} />
      </main>

      {/* ── Input bar ──────────────────────────────────────────────────── */}
      <footer
        className="px-5 py-4 shrink-0"
        style={{
          background: "rgba(10,10,10,0.9)",
          backdropFilter: "blur(20px)",
          borderTop: "1px solid rgba(39,39,42,0.6)",
        }}
      >
        <div className="max-w-[820px] mx-auto flex flex-col gap-2">
          <form
            onSubmit={(e) => {
              e.preventDefault();
              handleSubmit(input);
            }}
            className="flex gap-3"
          >
            <input
              ref={inputRef}
              type="text"
              value={input}
              onChange={(e) => setInput(e.target.value)}
              placeholder={`Ask about ${venue.venue_name}…`}
              disabled={isLoading}
              className="flex-1 rounded-xl px-4 py-3 text-sm focus:outline-none disabled:opacity-50 transition-all"
              style={{
                background: "rgba(24,24,27,0.8)",
                border: "1px solid rgba(39,39,42,0.8)",
                color: "#F5F5F5",
                fontFamily: "'Inter', sans-serif",
              }}
              onFocus={(e) => (e.target.style.borderColor = "rgba(230,211,163,0.4)")}
              onBlur={(e) => (e.target.style.borderColor = "rgba(39,39,42,0.8)")}
            />
            <button
              type="submit"
              disabled={!input.trim() || isLoading}
              className="rounded-xl px-4 py-3 flex items-center justify-center transition-all disabled:opacity-40"
              style={{ background: "rgba(230,211,163,0.12)", border: "1px solid rgba(230,211,163,0.25)", color: "#E6D3A3" }}
            >
              <span className="material-symbols-outlined text-[20px]">send</span>
            </button>
          </form>

          <div className="flex items-center justify-between">
            <p className="text-[10px]" style={{ fontFamily: "'JetBrains Mono', monospace", color: "#3F3F46" }}>
              Powered by Polynovea's behavioral intelligence framework
            </p>
          </div>
        </div>
      </footer>

    </div>
  );
}
