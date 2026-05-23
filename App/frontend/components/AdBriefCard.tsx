"use client";

import { useState } from "react";
import { getAdBrief, type AdBrief } from "@/lib/api";
import { streamBriefContent } from "@/lib/chat-api";

const CHANNELS = [
  { key: "whatsapp",        label: "WhatsApp" },
  { key: "instagram_reels", label: "Reels" },
  { key: "instagram_ads",   label: "Meta Ads" },
  { key: "google_ads",      label: "Google" },
  { key: "sms",             label: "SMS" },
];

// ─── Shared style helpers ─────────────────────────────────────────────────────

const mono: React.CSSProperties = { fontFamily: "'JetBrains Mono', monospace" };
const label = (extra?: React.CSSProperties): React.CSSProperties => ({
  fontFamily: "'JetBrains Mono', monospace",
  color: "#71717A",
  fontSize: "9px",
  fontWeight: 700,
  letterSpacing: "0.1em",
  textTransform: "uppercase",
  ...extra,
});
const infoBox = (tint: string): React.CSSProperties => ({
  background: `rgba(${tint},0.06)`,
  border: `1px solid rgba(${tint},0.2)`,
  borderRadius: 8,
  padding: "12px",
});
const subCard: React.CSSProperties = {
  background: "rgba(10,10,10,0.55)",
  border: "1px solid rgba(39,39,42,0.7)",
  borderRadius: 8,
  padding: "12px",
};

// ─── Component ────────────────────────────────────────────────────────────────

interface Props {
  venueId: number;
  initialBrief: AdBrief;
}

export default function AdBriefCard({ venueId, initialBrief }: Props) {
  const [brief, setBrief]           = useState<AdBrief>(initialBrief);
  const [loading, setLoading]       = useState(false);
  const [active, setActive]         = useState(initialBrief.channel);
  const [direction, setDirection]   = useState("");
  const [content, setContent]       = useState("");
  const [generating, setGenerating] = useState(false);
  const [copied, setCopied]         = useState(false);

  async function switchChannel(ch: string) {
    if (ch === active) return;
    setActive(ch);
    setContent("");
    setLoading(true);
    try {
      const next = await getAdBrief(venueId, ch);
      setBrief(next);
    } finally {
      setLoading(false);
    }
  }

  async function generateContent() {
    setGenerating(true);
    setContent("");
    setCopied(false);
    let result = "";
    await streamBriefContent(venueId, active, direction, {
      onChunk:    (chunk) => { result += chunk; setContent(result); },
      onError:    ()      => setGenerating(false),
      onComplete: ()      => setGenerating(false),
    });
  }

  return (
    <div className={`flex flex-col gap-4 transition-opacity ${loading ? "opacity-50" : ""}`}>

      {/* Channel selector */}
      <div className="flex flex-wrap gap-1.5">
        {CHANNELS.map((ch) => (
          <button
            key={ch.key}
            onClick={() => switchChannel(ch.key)}
            className="text-[11px] font-bold px-3 py-1 rounded transition-all"
            style={active === ch.key
              ? { ...mono, background: "rgba(230,211,163,0.12)", border: "1px solid rgba(230,211,163,0.35)", color: "#E6D3A3" }
              : { ...mono, background: "rgba(24,24,27,0.6)", border: "1px solid rgba(39,39,42,0.7)", color: "#71717A" }
            }
            onMouseEnter={(e) => { if (active !== ch.key) { (e.currentTarget as HTMLElement).style.borderColor = "rgba(230,211,163,0.2)"; (e.currentTarget as HTMLElement).style.color = "#A1A1AA"; } }}
            onMouseLeave={(e) => { if (active !== ch.key) { (e.currentTarget as HTMLElement).style.borderColor = "rgba(39,39,42,0.7)"; (e.currentTarget as HTMLElement).style.color = "#71717A"; } }}
          >
            {ch.label}
          </button>
        ))}
      </div>

      {/* Target row */}
      <div className="flex flex-wrap items-center gap-2 text-[12px]" style={{ color: "#71717A" }}>
        <span>Segment: <span className="font-bold" style={{ color: "#F5F5F5" }}>{brief.target_segment}</span></span>
        <span style={{ color: "rgba(39,39,42,0.8)" }}>·</span>
        <span>Archetype: <span className="font-bold" style={{ color: "#E6D3A3" }}>{brief.target_archetype}</span></span>
        <span style={{ color: "rgba(39,39,42,0.8)" }}>·</span>
        <span>Channel: <span className="font-bold" style={{ color: "#F5F5F5" }}>{brief.channel_label}</span></span>
        <span style={{ color: "rgba(39,39,42,0.8)" }}>·</span>
        <span className="text-[10px]" style={{ ...mono, color: "#71717A" }}>Language: {brief.language_rec}</span>
        {brief.trust_first && (
          <>
            <span style={{ color: "rgba(39,39,42,0.8)" }}>·</span>
            <span className="text-[9px] font-bold uppercase px-1.5 py-0.5 rounded" style={{ ...mono, background: "rgba(245,158,11,0.15)", border: "1px solid rgba(245,158,11,0.3)", color: "#F59E0B" }}>
              TRUST FIRST
            </span>
          </>
        )}
      </div>

      {/* Main brief grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
        {[
          { key: "tone",             label: "TONE",             body: brief.tone,             extra: <><div className="pt-2 mt-1 border-t" style={{ borderColor: "rgba(39,39,42,0.5)" }}><span className="text-[10px] mr-1" style={{ ...mono, color: "#71717A" }}>Driver:</span><span className="text-[11px] font-bold" style={{ ...mono, color: "#E6D3A3" }}>{brief.emotional_driver}</span></div></> },
          { key: "hook",             label: "HOOK FORMULA",     body: brief.hook },
          { key: "cta",              label: "CTA STYLE",        body: brief.cta },
          { key: "visual_direction", label: "VISUAL DIRECTION", body: brief.visual_direction },
        ].map(({ key, label: lbl, body, extra }) => (
          <div key={key} style={subCard} className="flex flex-col gap-1.5">
            <div style={label()}>{lbl}</div>
            <p className="text-[13px] leading-relaxed" style={{ color: "#A1A1AA" }}>{body}</p>
            {extra}
          </div>
        ))}
      </div>

      {/* Content Generator */}
      <div className="rounded-xl p-4 flex flex-col gap-3" style={{ background: "rgba(230,211,163,0.04)", border: "1px solid rgba(230,211,163,0.15)" }}>
        <div style={label({ color: "#9A8F6A" })}>GENERATE CONTENT FROM BRIEF</div>
        <div className="flex gap-2 items-end">
          <div className="flex-1 flex flex-col gap-1.5">
            <label style={label()}>Direction (optional)</label>
            <input
              type="text"
              value={direction}
              onChange={(e) => setDirection(e.target.value)}
              onKeyDown={(e) => e.key === "Enter" && !generating && generateContent()}
              placeholder="e.g. promote Sunday brunch, mention quiet corner seating, Diwali offer…"
              className="w-full rounded-lg px-3 py-2 text-[13px] focus:outline-none transition-all"
              style={{ background: "rgba(24,24,27,0.8)", border: "1px solid rgba(39,39,42,0.7)", color: "#F5F5F5", fontFamily: "'Inter', sans-serif" }}
              onFocus={(e) => (e.target.style.borderColor = "rgba(230,211,163,0.35)")}
              onBlur={(e) => (e.target.style.borderColor = "rgba(39,39,42,0.7)")}
            />
          </div>
          <button
            onClick={generateContent}
            disabled={generating || loading}
            className="flex items-center gap-1.5 px-3 py-2 rounded-lg text-[12px] font-bold uppercase tracking-wider transition-all disabled:opacity-40 shrink-0"
            style={{ ...mono, background: "rgba(230,211,163,0.1)", border: "1px solid rgba(230,211,163,0.3)", color: "#E6D3A3" }}
          >
            {generating ? (
              <><div className="w-3 h-3 border-2 rounded-full animate-spin" style={{ borderColor: "rgba(230,211,163,0.2)", borderTopColor: "#E6D3A3" }} />Generating…</>
            ) : (
              <><span className="material-symbols-outlined text-[14px]">auto_awesome</span>Generate</>
            )}
          </button>
        </div>

        {content && (
          <div className="rounded-xl p-4 flex flex-col gap-3" style={{ background: "rgba(14,14,17,0.8)", border: "1px solid rgba(230,211,163,0.15)" }}>
            <div className="flex items-center justify-between flex-wrap gap-2">
              <div className="text-[9px] font-bold uppercase tracking-widest" style={{ ...mono, color: "#E6D3A3" }}>
                GENERATED · {brief.channel_label} · {brief.target_archetype}
              </div>
              <div className="flex gap-1.5">
                <button
                  onClick={() => { navigator.clipboard.writeText(content); setCopied(true); setTimeout(() => setCopied(false), 2000); }}
                  className="flex items-center gap-1 text-[11px] font-bold px-2 py-0.5 rounded transition-all"
                  style={{ ...mono, border: "1px solid rgba(230,211,163,0.3)", color: "#E6D3A3", background: "rgba(230,211,163,0.06)" }}
                >
                  <span className="material-symbols-outlined text-[13px]">{copied ? "check" : "content_copy"}</span>
                  {copied ? "Copied" : "Copy"}
                </button>
                <button
                  onClick={generateContent}
                  disabled={generating}
                  className="flex items-center gap-1 text-[11px] font-bold px-2 py-0.5 rounded transition-all disabled:opacity-40"
                  style={{ border: "1px solid rgba(39,39,42,0.7)", color: "#71717A", background: "rgba(24,24,27,0.6)" }}
                >
                  <span className="material-symbols-outlined text-[13px]">refresh</span>
                  Redo
                </button>
              </div>
            </div>
            <p className="text-[13px] leading-[1.8] whitespace-pre-wrap" style={{ color: "#A1A1AA" }}>{content}</p>
          </div>
        )}
      </div>

      {/* Platform rules */}
      <div style={subCard} className="flex flex-col gap-3">
        <div style={label()}>{brief.channel_label.toUpperCase()} — PLATFORM RULES</div>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-3 text-[13px]">
          {[
            { k: "Format",     v: brief.platform_rules.format },
            { k: "Hook Style", v: brief.platform_rules.hook_style },
            { k: "CTA",        v: brief.platform_rules.cta },
          ].map(({ k, v }) => (
            <div key={k}>
              <div className="text-[9px] uppercase tracking-wider mb-1" style={{ ...mono, color: "#71717A" }}>{k}</div>
              <p style={{ color: "#A1A1AA" }}>{v}</p>
            </div>
          ))}
        </div>
        <div className="border-t pt-3" style={{ borderColor: "rgba(39,39,42,0.5)" }}>
          <div className="text-[9px] uppercase tracking-wider mb-1.5" style={{ ...mono, color: "#F59E0B" }}>Platform Don&apos;ts</div>
          <ul className="flex flex-col gap-1.5">
            {brief.platform_rules.dont.map((d, i) => (
              <li key={i} className="flex items-start gap-1.5 text-[12px]" style={{ color: "#A1A1AA" }}>
                <span className="material-symbols-outlined text-[13px] mt-[2px] shrink-0" style={{ color: "#F59E0B" }}>block</span>
                {d}
              </li>
            ))}
          </ul>
        </div>
      </div>

      {/* Copy starters */}
      <div style={subCard} className="flex flex-col gap-3">
        <div style={label()}>COPY STARTERS</div>
        <div className="flex flex-col gap-3">
          {brief.copy_hooks.map((hook, i) => (
            <div key={i} className="flex gap-2 items-start">
              <span className="text-[10px] font-bold mt-[3px] shrink-0" style={{ ...mono, color: "#E6D3A3" }}>
                {String(i + 1).padStart(2, "0")}
              </span>
              <p className="text-[13px] leading-relaxed" style={{ color: "#A1A1AA" }}>{hook}</p>
            </div>
          ))}
        </div>
      </div>

      {/* India creative rules */}
      <div style={infoBox("230,211,163")} className="flex flex-col gap-3">
        <div style={label({ color: "#E6D3A3" })}>INDIA CREATIVE RULES — APPLY ALWAYS</div>
        <ul className="flex flex-col gap-1.5">
          {brief.india_rules.map((rule, i) => (
            <li key={i} className="flex items-start gap-1.5 text-[12px]" style={{ color: "#A1A1AA" }}>
              <span className="material-symbols-outlined text-[13px] mt-[2px] shrink-0" style={{ color: "#E6D3A3" }}>info</span>
              {rule}
            </li>
          ))}
        </ul>
      </div>

      {/* Don't say */}
      <div style={infoBox("251,113,133")} className="flex flex-col gap-3">
        <div style={label({ color: "#FB7185" })}>DON&apos;T SAY / DON&apos;T DO</div>
        <ul className="flex flex-col gap-1.5">
          {brief.dont_say.map((d, i) => (
            <li key={i} className="flex items-start gap-1.5 text-[12px]" style={{ color: "#A1A1AA" }}>
              <span className="material-symbols-outlined text-[13px] mt-[2px] shrink-0" style={{ color: "#FB7185" }}>cancel</span>
              {d}
            </li>
          ))}
        </ul>
      </div>

      {/* Anti-pattern flags */}
      {brief.anti_pattern_flags.length > 0 && (
        <div style={infoBox("245,158,11")} className="flex flex-col gap-3">
          <div style={label({ color: "#F59E0B" })}>AUTO-DETECTED RISKS</div>
          <ul className="flex flex-col gap-1.5">
            {brief.anti_pattern_flags.map((flag, i) => (
              <li key={i} className="flex items-start gap-1.5 text-[12px]" style={{ color: "#A1A1AA" }}>
                <span className="material-symbols-outlined text-[13px] mt-[2px] shrink-0" style={{ color: "#F59E0B" }}>warning</span>
                {flag}
              </li>
            ))}
          </ul>
        </div>
      )}

      {/* Occasion anchor */}
      {brief.occasion_anchor && (
        <div className="flex items-start gap-1.5 text-[12px] border-t pt-3" style={{ borderColor: "rgba(39,39,42,0.5)", color: "#71717A" }}>
          <span className="material-symbols-outlined text-[14px] mt-[1px] shrink-0" style={{ color: "#E6D3A3" }}>calendar_month</span>
          {brief.occasion_anchor}
        </div>
      )}

      <div className="text-[10px] text-right" style={{ ...mono, color: "rgba(161,161,170,0.35)" }}>
        DATA CONFIDENCE: {brief.data_confidence} · Source: india_fb_ad_brief_generator_research.md (Kimi 2026)
      </div>
    </div>
  );
}
