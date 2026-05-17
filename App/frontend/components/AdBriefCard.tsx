"use client";

import { useState } from "react";
import { getAdBrief, type AdBrief } from "@/lib/api";

const CHANNELS = [
  { key: "whatsapp",        label: "WhatsApp" },
  { key: "instagram_reels", label: "Reels" },
  { key: "instagram_ads",   label: "Meta Ads" },
  { key: "google_ads",      label: "Google" },
  { key: "sms",             label: "SMS" },
  { key: "zomato_swiggy",   label: "Zomato" },
];

interface Props {
  venueId: number;
  initialBrief: AdBrief;
}

export default function AdBriefCard({ venueId, initialBrief }: Props) {
  const [brief, setBrief]     = useState<AdBrief>(initialBrief);
  const [loading, setLoading] = useState(false);
  const [active, setActive]   = useState(initialBrief.channel);

  async function switchChannel(ch: string) {
    if (ch === active) return;
    setActive(ch);
    setLoading(true);
    try {
      const next = await getAdBrief(venueId, ch);
      setBrief(next);
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className={`flex flex-col gap-md transition-opacity ${loading ? "opacity-50" : ""}`}>

      {/* Channel selector */}
      <div className="flex flex-wrap gap-xs">
        {CHANNELS.map((ch) => (
          <button
            key={ch.key}
            onClick={() => switchChannel(ch.key)}
            className={`text-label-sm font-label-sm px-sm py-xs rounded border transition-colors ${
              active === ch.key
                ? "bg-primary text-on-primary border-primary"
                : "bg-surface-container text-on-surface-variant border-outline-variant hover:border-primary/50"
            }`}
          >
            {ch.label}
          </button>
        ))}
      </div>

      {/* Target row */}
      <div className="flex flex-wrap items-center gap-sm text-body-sm font-body-sm text-on-surface-variant">
        <span>
          Segment: <span className="text-on-surface font-bold">{brief.target_segment}</span>
        </span>
        <span className="text-outline-variant">·</span>
        <span>
          Archetype: <span className="text-primary font-bold">{brief.target_archetype}</span>
        </span>
        <span className="text-outline-variant">·</span>
        <span>
          Channel: <span className="text-on-surface font-bold">{brief.channel_label}</span>
        </span>
        <span className="text-outline-variant">·</span>
        <span className="text-[10px] font-data-mono uppercase tracking-wider text-on-surface-variant/60">
          Language: {brief.language_rec}
        </span>
        {brief.trust_first && (
          <>
            <span className="text-outline-variant">·</span>
            <span className="bg-signal-warning/20 text-signal-warning border border-signal-warning/30 text-[10px] font-data-mono uppercase px-xs py-[2px] rounded tracking-wider">
              TRUST FIRST
            </span>
          </>
        )}
      </div>

      {/* Main brief grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-sm">

        {/* Tone + driver */}
        <div className="bg-background border border-brand-border rounded p-sm flex flex-col gap-xs">
          <div className="text-[10px] font-data-mono uppercase tracking-widest text-brand-label">TONE</div>
          <p className="text-body-sm font-body-sm text-on-surface leading-relaxed">{brief.tone}</p>
          <div className="pt-xs border-t border-brand-border">
            <span className="text-[10px] font-data-mono uppercase tracking-widest text-on-surface-variant/60 mr-xs">Driver:</span>
            <span className="text-[11px] font-data-mono text-primary">{brief.emotional_driver}</span>
          </div>
        </div>

        {/* Hook formula */}
        <div className="bg-background border border-brand-border rounded p-sm flex flex-col gap-xs">
          <div className="text-[10px] font-data-mono uppercase tracking-widest text-brand-label">HOOK FORMULA</div>
          <p className="text-body-sm font-body-sm text-on-surface leading-relaxed">{brief.hook}</p>
        </div>

        {/* CTA */}
        <div className="bg-background border border-brand-border rounded p-sm flex flex-col gap-xs">
          <div className="text-[10px] font-data-mono uppercase tracking-widest text-brand-label">CTA STYLE</div>
          <p className="text-body-sm font-body-sm text-on-surface leading-relaxed">{brief.cta}</p>
        </div>

        {/* Visual direction */}
        <div className="bg-background border border-brand-border rounded p-sm flex flex-col gap-xs">
          <div className="text-[10px] font-data-mono uppercase tracking-widest text-brand-label">VISUAL DIRECTION</div>
          <p className="text-body-sm font-body-sm text-on-surface leading-relaxed">{brief.visual_direction}</p>
        </div>
      </div>

      {/* Platform rules */}
      <div className="bg-background border border-brand-border rounded p-sm flex flex-col gap-sm">
        <div className="text-[10px] font-data-mono uppercase tracking-widest text-brand-label">
          {brief.channel_label.toUpperCase()} — PLATFORM RULES
        </div>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-sm text-body-sm font-body-sm">
          <div>
            <div className="text-[10px] text-on-surface-variant uppercase tracking-wider mb-xs">Format</div>
            <p className="text-on-surface leading-relaxed">{brief.platform_rules.format}</p>
          </div>
          <div>
            <div className="text-[10px] text-on-surface-variant uppercase tracking-wider mb-xs">Hook Style</div>
            <p className="text-on-surface leading-relaxed">{brief.platform_rules.hook_style}</p>
          </div>
          <div>
            <div className="text-[10px] text-on-surface-variant uppercase tracking-wider mb-xs">CTA</div>
            <p className="text-on-surface leading-relaxed">{brief.platform_rules.cta}</p>
          </div>
        </div>
        <div className="border-t border-brand-border pt-sm">
          <div className="text-[10px] text-signal-warning uppercase tracking-wider mb-xs">Platform Don&apos;ts</div>
          <ul className="flex flex-col gap-xs">
            {brief.platform_rules.dont.map((d, i) => (
              <li key={i} className="flex items-start gap-xs text-[11px] text-on-surface-variant">
                <span className="material-symbols-outlined text-signal-warning text-sm mt-[2px] shrink-0">block</span>
                {d}
              </li>
            ))}
          </ul>
        </div>
      </div>

      {/* Copy hooks */}
      <div className="bg-background border border-brand-border rounded p-sm flex flex-col gap-sm">
        <div className="text-[10px] font-data-mono uppercase tracking-widest text-brand-label">COPY STARTERS</div>
        <div className="flex flex-col gap-sm">
          {brief.copy_hooks.map((hook, i) => (
            <div key={i} className="flex gap-sm items-start">
              <span className="text-[10px] font-data-mono text-primary-container mt-[3px] shrink-0">
                {String(i + 1).padStart(2, "0")}
              </span>
              <p className="text-body-sm font-body-sm text-on-surface leading-relaxed">{hook}</p>
            </div>
          ))}
        </div>
      </div>

      {/* India rules */}
      <div className="bg-[#F6E0B5]/10 border border-[#F6E0B5]/30 rounded p-sm flex flex-col gap-sm">
        <div className="text-[10px] font-data-mono uppercase tracking-widest text-[#E6D3A3]">
          INDIA CREATIVE RULES — APPLY ALWAYS
        </div>
        <ul className="flex flex-col gap-xs">
          {brief.india_rules.map((rule, i) => (
            <li key={i} className="flex items-start gap-xs text-[11px] text-on-surface-variant/80">
              <span className="material-symbols-outlined text-[#E6D3A3] text-sm mt-[2px] shrink-0">info</span>
              {rule}
            </li>
          ))}
        </ul>
      </div>

      {/* Don't say */}
      <div className="bg-signal-error/5 border border-signal-error/20 rounded p-sm flex flex-col gap-sm">
        <div className="text-[10px] font-data-mono uppercase tracking-widest text-signal-error/80">
          DON&apos;T SAY / DON&apos;T DO
        </div>
        <ul className="flex flex-col gap-xs">
          {brief.dont_say.map((d, i) => (
            <li key={i} className="flex items-start gap-xs text-[11px] text-on-surface-variant">
              <span className="material-symbols-outlined text-signal-error text-sm mt-[2px] shrink-0">cancel</span>
              {d}
            </li>
          ))}
        </ul>
      </div>

      {/* Anti-pattern flags */}
      {brief.anti_pattern_flags.length > 0 && (
        <div className="bg-signal-warning/10 border border-signal-warning/30 rounded p-sm flex flex-col gap-sm">
          <div className="text-[10px] font-data-mono uppercase tracking-widest text-signal-warning">
            AUTO-DETECTED RISKS
          </div>
          <ul className="flex flex-col gap-xs">
            {brief.anti_pattern_flags.map((flag, i) => (
              <li key={i} className="flex items-start gap-xs text-[11px] text-on-surface-variant">
                <span className="material-symbols-outlined text-signal-warning text-sm mt-[2px] shrink-0">warning</span>
                {flag}
              </li>
            ))}
          </ul>
        </div>
      )}

      {/* Occasion anchor */}
      {brief.occasion_anchor && (
        <div className="flex items-start gap-xs text-[11px] text-on-surface-variant/70 border-t border-brand-border pt-sm">
          <span className="material-symbols-outlined text-primary-container text-sm mt-[1px] shrink-0">calendar_month</span>
          {brief.occasion_anchor}
        </div>
      )}

      <div className="text-[10px] font-data-mono text-on-surface-variant/40 text-right">
        DATA CONFIDENCE: {brief.data_confidence} · Source: india_fb_ad_brief_generator_research.md (Kimi 2026)
      </div>
    </div>
  );
}
