"use client";

import { useState, useRef, useEffect } from "react";
import { streamChat } from "@/lib/chat-api";

// ─── Types ────────────────────────────────────────────────────────────────────

interface Message {
  role: "user" | "assistant";
  content: string;
}

type CouncilPhase = "idle" | "r1" | "r2" | "synthesis";

interface CouncilEvent {
  round: "r1" | "r2";
  model: string;
  meta: string;
  text: string;
}

type Tab = "marketing" | "competitors" | "transform" | "deep_risk" | "overview" | "audience";

interface ChatDrawerProps {
  venueId: number;
  tab: Tab;
}

// ─── Lightweight markdown renderer ───────────────────────────────────────────

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
      const sz = level === 1 ? "text-[16px]" : level === 2 ? "text-[15px]" : "text-[13px]";
      nodes.push(
        <p key={i} className={`${sz} font-bold mt-1`} style={{ color: "#F5F5F5" }}>
          {inlineFormat(headerMatch[2])}
        </p>
      );
      i++;
      continue;
    }

    if (/^[\-\*]\s+/.test(raw)) {
      const bulletNodes: React.ReactNode[] = [];
      while (i < lines.length && /^[\-\*]\s+/.test(lines[i])) {
        bulletNodes.push(
          <li key={i} className="flex gap-1.5 items-start">
            <span className="mt-[5px] shrink-0 text-[10px]" style={{ color: "#E6D3A3" }}>•</span>
            <span style={{ color: "#A1A1AA" }}>{inlineFormat(lines[i].replace(/^[\-\*]\s+/, ""))}</span>
          </li>
        );
        i++;
      }
      nodes.push(<ul key={`ul-${i}`} className="flex flex-col gap-[3px] my-1">{bulletNodes}</ul>);
      continue;
    }

    if (/^\d+\.\s+/.test(raw)) {
      const listNodes: React.ReactNode[] = [];
      let num = 1;
      while (i < lines.length && /^\d+\.\s+/.test(lines[i])) {
        listNodes.push(
          <li key={i} className="flex gap-1.5 items-start">
            <span className="shrink-0 text-[13px] mt-[2px] min-w-[20px]" style={{ fontFamily: "'JetBrains Mono', monospace", color: "#E6D3A3" }}>{num}.</span>
            <span style={{ color: "#A1A1AA" }}>{inlineFormat(lines[i].replace(/^\d+\.\s+/, ""))}</span>
          </li>
        );
        i++;
        num++;
      }
      nodes.push(<ol key={`ol-${i}`} className="flex flex-col gap-[3px] my-1">{listNodes}</ol>);
      continue;
    }

    nodes.push(
      <p key={i} className="leading-relaxed" style={{ color: "#A1A1AA" }}>
        {inlineFormat(raw)}
      </p>
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
    if (match[2]) parts.push(<strong key={match.index} className="font-semibold" style={{ color: "#F5F5F5" }}>{match[2]}</strong>);
    else if (match[3]) parts.push(<em key={match.index} className="italic">{match[3]}</em>);
    else if (match[4]) parts.push(
      <code key={match.index} className="px-[4px] py-[1px] rounded text-[12px]" style={{ fontFamily: "'JetBrains Mono', monospace", background: "rgba(230,211,163,0.08)", color: "#E6D3A3" }}>
        {match[4]}
      </code>
    );
    last = match.index + match[0].length;
  }
  if (last < text.length) parts.push(text.slice(last));
  return parts.length === 1 ? parts[0] : <>{parts}</>;
}

// ─── Tab metadata ─────────────────────────────────────────────────────────────

const TAB_META: Record<Tab, { label: string; subtitle: string }> = {
  marketing:   { label: "Marketing Assistant",     subtitle: "Content, ads, campaigns, audience" },
  competitors:  { label: "Competitor Analyst",      subtitle: "Positioning, gaps, similar venues" },
  transform:    { label: "Transformation Advisor",  subtitle: "Segment targeting, fitness gaps" },
  deep_risk:    { label: "Risk Analyst",            subtitle: "Churn signals, retention patterns" },
  overview:     { label: "Venue Intelligence",      subtitle: "Health score, fitness, segments" },
  audience:     { label: "Audience Analyst",        subtitle: "Spend, dwell, loyalty, platforms" },
};

const COUNCIL_DELIBERATING = "[COUNCIL:DELIBERATING]";
const COUNCIL_SYNTHESIS    = "[COUNCIL:SYNTHESIS]";
const COUNCIL_PHASE_RE     = /\[COUNCIL:PHASE:(r[12]):([^:]+):([^\]]+)\]([^\n]*)\n/;

const MODEL_META: Record<string, { label: string; color: string }> = {
  nemotron: { label: "LLAMA 3.3",  color: "#a78bfa" },
  deepseek: { label: "LLAMA 3.1",  color: "#67e8f9" },
  mistral:  { label: "MISTRAL",    color: "#fcd34d" },
  qwen:     { label: "QWEN",       color: "#fcd34d" },
};

function metaColor(round: string, meta: string): string {
  if (round === "r1") {
    if (meta === "HIGH")   return "#86efac";
    if (meta === "MEDIUM") return "#fcd34d";
    return "#f87171";
  }
  if (meta === "NONE")  return "#86efac";
  if (meta === "MINOR") return "#fcd34d";
  return "#f87171";
}

function CouncilChamber({ events, phase }: { events: CouncilEvent[]; phase: CouncilPhase }) {
  const r1 = events.filter(e => e.round === "r1");
  const r2 = events.filter(e => e.round === "r2");

  const phaseLabel =
    phase === "synthesis" ? "Synthesising..." :
    phase === "r2"        ? "Round 2 — Debate" :
    phase === "r1"        ? "Round 1 — Analysis" :
                            "Council deliberating";

  return (
    <div
      className="px-4 py-3 rounded-2xl rounded-bl-sm flex flex-col gap-3 max-w-[92%]"
      style={{ background: "rgba(124,58,237,0.06)", border: "1px solid rgba(124,58,237,0.25)" }}
    >
      {/* Header */}
      <div className="flex items-center gap-2">
        <div className="flex gap-[3px]">
          <div className="w-1.5 h-1.5 rounded-full animate-bounce [animation-delay:0ms]"   style={{ background: "#7C3AED" }} />
          <div className="w-1.5 h-1.5 rounded-full animate-bounce [animation-delay:120ms]" style={{ background: "#7C3AED" }} />
          <div className="w-1.5 h-1.5 rounded-full animate-bounce [animation-delay:240ms]" style={{ background: "#7C3AED" }} />
        </div>
        <span className="text-[11px] font-bold uppercase tracking-wider" style={{ fontFamily: "'JetBrains Mono', monospace", color: "#c4b5fd" }}>
          {phaseLabel}
        </span>
      </div>

      {/* Round 1 */}
      {r1.length > 0 && (
        <div className="flex flex-col gap-2">
          <span className="text-[9px] uppercase tracking-widest font-bold" style={{ color: "rgba(167,139,250,0.45)", fontFamily: "'JetBrains Mono', monospace" }}>
            Round 1 — Independent Analysis
          </span>
          {r1.map((ev, i) => <CouncilRow key={i} event={ev} />)}
        </div>
      )}

      {/* Round 2 */}
      {r2.length > 0 && (
        <div className="flex flex-col gap-2">
          <span className="text-[9px] uppercase tracking-widest font-bold" style={{ color: "rgba(167,139,250,0.45)", fontFamily: "'JetBrains Mono', monospace" }}>
            Round 2 — Cross-review
          </span>
          {r2.map((ev, i) => <CouncilRow key={i} event={ev} />)}
        </div>
      )}

      {/* Synthesis indicator */}
      {phase === "synthesis" && (
        <p className="text-[11px]" style={{ color: "#71717A", fontFamily: "'JetBrains Mono', monospace" }}>
          ▶ Synthesising final answer...
        </p>
      )}

      {/* Initial loading hint */}
      {r1.length === 0 && phase === "idle" && (
        <p className="text-[11px]" style={{ color: "#71717A" }}>3 models analysing independently...</p>
      )}
    </div>
  );
}

function CouncilRow({ event }: { event: CouncilEvent }) {
  const disp  = MODEL_META[event.model] ?? { label: event.model.toUpperCase(), color: "#a1a1aa" };
  const mCol  = metaColor(event.round, event.meta);
  return (
    <div className="flex gap-2 items-start">
      <span
        className="shrink-0 text-[9px] font-bold px-1.5 py-[2px] rounded"
        style={{ fontFamily: "'JetBrains Mono', monospace", color: disp.color, background: `${disp.color}18`, border: `1px solid ${disp.color}35` }}
      >
        {disp.label}
      </span>
      <span
        className="shrink-0 text-[9px] font-bold px-1.5 py-[2px] rounded"
        style={{ color: mCol, background: `${mCol}18`, fontFamily: "'JetBrains Mono', monospace" }}
      >
        {event.meta}
      </span>
      <span className="text-[12px] leading-relaxed" style={{ color: "#A1A1AA" }}>
        {event.text}
      </span>
    </div>
  );
}

const STORAGE_KEY = (venueId: number) => `polynovea_chat_${venueId}`;

// ─── Component ────────────────────────────────────────────────────────────────

export default function ChatDrawer({ venueId, tab }: ChatDrawerProps) {
  const [isOpen, setIsOpen]                 = useState(false);
  const [messages, setMessages]             = useState<Message[]>(() => {
    try {
      const stored = localStorage.getItem(STORAGE_KEY(venueId));
      return stored ? (JSON.parse(stored) as Message[]) : [];
    } catch { return []; }
  });
  const [input, setInput]                   = useState("");
  const [isLoading, setIsLoading]           = useState(false);
  const [isDeliberating, setIsDeliberating] = useState(false);
  const [councilEvents, setCouncilEvents]   = useState<CouncilEvent[]>([]);
  const [councilPhase, setCouncilPhase]     = useState<CouncilPhase>("idle");
  const [error, setError]                   = useState<string | null>(null);
  const messagesEndRef                      = useRef<HTMLDivElement>(null);
  const inputRef                            = useRef<HTMLInputElement>(null);

  const persistMessages = (msgs: Message[]) => {
    try { localStorage.setItem(STORAGE_KEY(venueId), JSON.stringify(msgs)); } catch { /* ignore */ }
  };

  useEffect(() => { messagesEndRef.current?.scrollIntoView({ behavior: "smooth" }); }, [messages]);
  useEffect(() => { if (isOpen) setTimeout(() => inputRef.current?.focus(), 100); }, [isOpen]);

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

    if (mode === "council") {
      setCouncilEvents([]);
      setCouncilPhase("idle");
    }

    let currentResponse = "";
    let deliberatingDone = false;
    let synthesisDone    = false;
    let councilBuf       = "";

    const appendToResponse = (text: string) => {
      currentResponse += text;
      setMessages((prev) => {
        const msgs = [...prev];
        if (msgs[msgs.length - 1]?.role === "assistant") {
          msgs[msgs.length - 1] = { role: "assistant", content: currentResponse };
        } else {
          msgs.push({ role: "assistant", content: currentResponse });
        }
        return msgs;
      });
    };

    const parseCouncilEvents = (buf: string): string => {
      let remaining = buf;
      const batch: CouncilEvent[] = [];
      let match: RegExpExecArray | null;
      while ((match = COUNCIL_PHASE_RE.exec(remaining)) !== null) {
        batch.push({
          round: match[1] as "r1" | "r2",
          model: match[2],
          meta:  match[3],
          text:  match[4].trim(),
        });
        remaining = remaining.slice(match.index + match[0].length);
      }
      if (batch.length > 0) {
        setCouncilEvents(prev => [...prev, ...batch]);
        setCouncilPhase(batch[batch.length - 1].round);
      }
      return remaining;
    };

    await streamChat(venueId, tab, userQuestion, {
      onChunk: (chunk) => {
        // Detect DELIBERATING sentinel
        if (!deliberatingDone && chunk.includes(COUNCIL_DELIBERATING)) {
          setIsDeliberating(true);
          deliberatingDone = true;
          chunk = chunk.replace(COUNCIL_DELIBERATING, "");
          if (!chunk) return;
        }

        // Fast mode or synthesis already streaming — append directly
        if (!deliberatingDone || synthesisDone) {
          if (deliberatingDone) setIsDeliberating(false);
          appendToResponse(chunk);
          return;
        }

        // Council mode — buffer and parse events
        councilBuf += chunk;

        // Check for synthesis sentinel
        const synthIdx = councilBuf.indexOf(COUNCIL_SYNTHESIS);
        if (synthIdx !== -1) {
          parseCouncilEvents(councilBuf.slice(0, synthIdx));
          synthesisDone = true;
          setCouncilPhase("synthesis");
          setIsDeliberating(false);
          const tail = councilBuf.slice(synthIdx + COUNCIL_SYNTHESIS.length + 1); // +1 for \n
          councilBuf = "";
          if (tail.trim()) appendToResponse(tail);
          return;
        }

        councilBuf = parseCouncilEvents(councilBuf);
      },
      onError: (msg) => { setIsDeliberating(false); setError(msg); setIsLoading(false); },
      onComplete: () => {
        setIsDeliberating(false);
        setIsLoading(false);
        setMessages((prev) => { persistMessages(prev); return prev; });
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
          title="Ask Polynovea"
          className="fixed bottom-20 left-6 md:bottom-8 md:left-8 z-[60] flex items-center gap-2 px-4 py-3 rounded-full shadow-2xl transition-all"
          style={{
            background: "rgba(230,211,163,0.1)",
            border: "1px solid rgba(230,211,163,0.25)",
            backdropFilter: "blur(12px)",
            boxShadow: "0 8px 32px rgba(0,0,0,0.5), 0 0 0 1px rgba(230,211,163,0.05)",
          }}
          onMouseEnter={(e) => { (e.currentTarget as HTMLElement).style.background = "rgba(230,211,163,0.15)"; (e.currentTarget as HTMLElement).style.borderColor = "rgba(230,211,163,0.4)"; }}
          onMouseLeave={(e) => { (e.currentTarget as HTMLElement).style.background = "rgba(230,211,163,0.1)"; (e.currentTarget as HTMLElement).style.borderColor = "rgba(230,211,163,0.25)"; }}
        >
          <span className="material-symbols-outlined text-[22px]" style={{ color: "#E6D3A3" }}>smart_toy</span>
          <span className="hidden md:inline text-[11px] font-bold uppercase tracking-widest" style={{ fontFamily: "'JetBrains Mono', monospace", color: "#E6D3A3" }}>
            Ask Polynovea
          </span>
        </button>
      )}

      {/* Backdrop + drawer */}
      <div
        className={`fixed inset-0 z-50 transition-opacity duration-300 ${isOpen ? "opacity-100" : "pointer-events-none opacity-0"}`}
        onClick={() => setIsOpen(false)}
      >
        <div className="absolute inset-0" style={{ background: "rgba(0,0,0,0.65)", backdropFilter: "blur(2px)" }} />

        <div
          className={`absolute inset-y-0 right-0 md:bottom-4 md:right-6 md:top-4 md:rounded-2xl w-full md:w-[760px] flex flex-col shadow-2xl transition-transform duration-300 ${isOpen ? "translate-x-0" : "translate-x-full"}`}
          style={{ background: "#0e0e11", border: "1px solid rgba(39,39,42,0.9)", overflow: "hidden" }}
          onClick={(e) => e.stopPropagation()}
        >
          {/* Header */}
          <div
            className="flex items-center justify-between px-5 py-4 shrink-0"
            style={{ background: "rgba(18,18,24,0.97)", borderBottom: "1px solid rgba(39,39,42,0.7)" }}
          >
            <div className="flex items-center gap-3">
              <div
                className="w-8 h-8 rounded-lg flex items-center justify-center shrink-0"
                style={{ background: "rgba(230,211,163,0.08)", border: "1px solid rgba(230,211,163,0.15)" }}
              >
                <span className="material-symbols-outlined text-[16px]" style={{ color: "#E6D3A3" }}>smart_toy</span>
              </div>
              <div>
                <h3 className="text-[16px] font-bold" style={{ fontFamily: "'Clash Display', 'Inter', sans-serif", color: "#F5F5F5" }}>{label}</h3>
                <p className="text-[12px] mt-[1px]" style={{ color: "#71717A" }}>{subtitle}</p>
              </div>
            </div>
            <div className="flex items-center gap-3">
              {messages.length > 0 && !isLoading && (
                <button
                  onClick={handleClearChat}
                  className="text-[11px] flex items-center gap-1 transition-colors"
                  style={{ color: "rgba(161,161,170,0.5)", fontFamily: "'JetBrains Mono', monospace" }}
                  title="Clear chat history"
                  onMouseEnter={(e) => ((e.currentTarget as HTMLElement).style.color = "#FB7185")}
                  onMouseLeave={(e) => ((e.currentTarget as HTMLElement).style.color = "rgba(161,161,170,0.5)")}
                >
                  <span className="material-symbols-outlined text-[13px]">delete_sweep</span>
                  Clear
                </button>
              )}
              <button
                onClick={() => { setIsOpen(false); setInput(""); setError(null); }}
                className="transition-colors"
                style={{ color: "#71717A" }}
                onMouseEnter={(e) => ((e.currentTarget as HTMLElement).style.color = "#F5F5F5")}
                onMouseLeave={(e) => ((e.currentTarget as HTMLElement).style.color = "#71717A")}
              >
                <span className="material-symbols-outlined text-[22px]">close</span>
              </button>
            </div>
          </div>

          {/* Messages */}
          <div className="flex-1 overflow-y-auto px-5 py-5 space-y-4 custom-scrollbar" style={{ background: "#0a0a0a" }}>
            {messages.length === 0 && !isLoading && (
              <div className="flex flex-col items-center justify-center py-16 text-center gap-3">
                <div
                  className="w-14 h-14 rounded-2xl flex items-center justify-center"
                  style={{ background: "rgba(230,211,163,0.06)", border: "1px solid rgba(230,211,163,0.12)" }}
                >
                  <span className="material-symbols-outlined text-[28px]" style={{ color: "rgba(230,211,163,0.4)" }}>smart_toy</span>
                </div>
                <p className="text-[16px] font-bold" style={{ color: "#F5F5F5" }}>Ask anything about this venue.</p>
                <p className="text-[13px]" style={{ color: "#71717A" }}>Powered by Polynovea&apos;s behavioral intelligence framework.</p>
              </div>
            )}

            {messages.map((msg, idx) => (
              <div key={idx} className={`flex ${msg.role === "user" ? "justify-end" : "justify-start"}`}>
                {msg.role === "user" ? (
                  <div
                    className="max-w-[82%] px-4 py-2.5 rounded-2xl rounded-br-sm text-[14px] leading-relaxed"
                    style={{ background: "rgba(230,211,163,0.1)", border: "1px solid rgba(230,211,163,0.2)", color: "#F5F5F5" }}
                  >
                    {msg.content}
                  </div>
                ) : (
                  <div
                    className="max-w-[88%] px-4 py-3 rounded-2xl rounded-bl-sm text-[14px] leading-relaxed"
                    style={{ background: "rgba(24,24,27,0.8)", border: "1px solid rgba(39,39,42,0.7)" }}
                  >
                    {renderMarkdown(msg.content)}
                  </div>
                )}
              </div>
            ))}

            {/* Council chamber — live debate view */}
            {isDeliberating && (
              <div className="flex justify-start">
                <CouncilChamber events={councilEvents} phase={councilPhase} />
              </div>
            )}

            {/* Typing indicator */}
            {isLoading && !isDeliberating && messages[messages.length - 1]?.role === "user" && (
              <div className="flex justify-start">
                <div
                  className="px-4 py-3 rounded-2xl rounded-bl-sm flex items-center gap-1.5"
                  style={{ background: "rgba(24,24,27,0.8)", border: "1px solid rgba(39,39,42,0.7)" }}
                >
                  <div className="w-1.5 h-1.5 rounded-full animate-bounce [animation-delay:0ms]" style={{ background: "#E6D3A3" }} />
                  <div className="w-1.5 h-1.5 rounded-full animate-bounce [animation-delay:150ms]" style={{ background: "#E6D3A3" }} />
                  <div className="w-1.5 h-1.5 rounded-full animate-bounce [animation-delay:300ms]" style={{ background: "#E6D3A3" }} />
                </div>
              </div>
            )}

            {error && (
              <div className="px-4 py-3 rounded-xl text-[13px]" style={{ background: "rgba(251,113,133,0.08)", border: "1px solid rgba(251,113,133,0.2)", color: "#FB7185" }}>
                {error}
              </div>
            )}

            <div ref={messagesEndRef} />
          </div>

          {/* Input bar */}
          <form
            onSubmit={(e) => handleSubmit(e, "fast")}
            className="px-5 py-4 shrink-0"
            style={{ background: "rgba(14,14,17,0.98)", borderTop: "1px solid rgba(39,39,42,0.7)" }}
          >
            <div className="flex gap-2">
              <input
                ref={inputRef}
                type="text"
                value={input}
                onChange={(e) => setInput(e.target.value)}
                placeholder="Ask a question..."
                disabled={isLoading}
                className="flex-1 rounded-xl px-4 py-3 text-[14px] focus:outline-none transition-all disabled:opacity-50"
                style={{ background: "rgba(24,24,27,0.8)", border: "1px solid rgba(39,39,42,0.8)", color: "#F5F5F5", fontFamily: "'Inter', sans-serif" }}
                onFocus={(e) => (e.target.style.borderColor = "rgba(230,211,163,0.4)")}
                onBlur={(e) => (e.target.style.borderColor = "rgba(39,39,42,0.8)")}
              />
              <button
                type="submit"
                disabled={!input.trim() || isLoading}
                className="rounded-xl px-4 py-3 transition-all disabled:opacity-40 flex items-center justify-center"
                style={{ background: "rgba(230,211,163,0.1)", border: "1px solid rgba(230,211,163,0.25)", color: "#E6D3A3" }}
                title="Quick answer"
                onMouseEnter={(e) => { (e.currentTarget as HTMLElement).style.background = "rgba(230,211,163,0.18)"; }}
                onMouseLeave={(e) => { (e.currentTarget as HTMLElement).style.background = "rgba(230,211,163,0.1)"; }}
              >
                <span className="material-symbols-outlined text-[22px]">send</span>
              </button>
            </div>

            <div className="flex flex-col items-end mt-2 gap-[2px]">
              <button
                type="button"
                onClick={(e) => handleSubmit(e, "council")}
                disabled={!input.trim() || isLoading}
                className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-[11px] font-bold uppercase tracking-wider transition-all disabled:opacity-40"
                style={{ fontFamily: "'JetBrains Mono', monospace", background: "rgba(124,58,237,0.1)", border: "1px solid rgba(124,58,237,0.3)", color: "#c4b5fd" }}
                title="Ask the Council of Models"
                onMouseEnter={(e) => { (e.currentTarget as HTMLElement).style.background = "rgba(124,58,237,0.18)"; }}
                onMouseLeave={(e) => { (e.currentTarget as HTMLElement).style.background = "rgba(124,58,237,0.1)"; }}
              >
                <span className="material-symbols-outlined text-[14px]">hub</span>
                Ask the Council
              </button>
              <span className="text-[10px]" style={{ color: "rgba(161,161,170,0.4)", fontFamily: "'JetBrains Mono', monospace" }}>
                3 models · may take 15–20 sec
              </span>
            </div>
          </form>
        </div>
      </div>
    </>
  );
}
