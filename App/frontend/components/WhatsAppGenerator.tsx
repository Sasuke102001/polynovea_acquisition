"use client";

import { useState } from "react";
import { streamChat } from "@/lib/chat-api";

const SEGMENTS = [
  { value: "families",       label: "Families" },
  { value: "couples",        label: "Couples" },
  { value: "office_workers", label: "Office Workers" },
  { value: "college_kids",   label: "College Kids" },
  { value: "premium",        label: "Premium Diners" },
  { value: "solo_diners",    label: "Solo Diners" },
  { value: "working_women",  label: "Working Women" },
];

const OCCASIONS = [
  { value: "weekend_lunch",   label: "Weekend Lunch" },
  { value: "weekday_lunch",   label: "Weekday Lunch Offer" },
  { value: "special_event",   label: "Special Event (Live Music / Quiz Night)" },
  { value: "festival",        label: "Festival / Holiday" },
  { value: "new_menu",        label: "New Menu Announcement" },
  { value: "re_engagement",   label: "Re-engagement (Lapsed Customers)" },
  { value: "birthday",        label: "Birthday / Anniversary" },
];

interface Props {
  venueId: number;
  venueName: string;
}

export default function WhatsAppGenerator({ venueId, venueName }: Props) {
  const [segment, setSegment]   = useState("families");
  const [occasion, setOccasion] = useState("weekend_lunch");
  const [custom, setCustom]     = useState("");
  const [message, setMessage]   = useState("");
  const [loading, setLoading]   = useState(false);
  const [copied, setCopied]     = useState(false);

  const segLabel = SEGMENTS.find((s) => s.value === segment)?.label ?? segment;
  const occLabel = OCCASIONS.find((o) => o.value === occasion)?.label ?? occasion;

  const generate = async () => {
    setLoading(true);
    setMessage("");
    setCopied(false);

    const prompt = custom.trim()
      ? custom.trim()
      : `Write a WhatsApp message template for ${venueName} targeting ${segLabel} customers for ${occLabel}. ` +
        `Requirements: under 160 characters, conversational tone, no emojis unless essential, ` +
        `use [Name] for personalisation placeholder, feel personal not promotional. ` +
        `Return only the message text, nothing else.`;

    let result = "";
    await streamChat(venueId, "marketing", prompt, {
      onChunk: (chunk) => {
        result += chunk;
        setMessage(result);
      },
      onError: () => setLoading(false),
      onComplete: () => setLoading(false),
    });
  };

  const copy = () => {
    navigator.clipboard.writeText(message);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  return (
    <div className="flex flex-col gap-md">
      {/* Controls */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-sm">
        <div className="flex flex-col gap-xs">
          <label className="text-[10px] font-data-mono uppercase tracking-widest text-on-surface-variant">
            Customer Segment
          </label>
          <select
            value={segment}
            onChange={(e) => setSegment(e.target.value)}
            className="bg-surface border border-outline-variant rounded px-sm py-xs text-body-sm font-body-sm text-on-surface focus:outline-none focus:border-primary"
          >
            {SEGMENTS.map((s) => (
              <option key={s.value} value={s.value}>{s.label}</option>
            ))}
          </select>
        </div>
        <div className="flex flex-col gap-xs">
          <label className="text-[10px] font-data-mono uppercase tracking-widest text-on-surface-variant">
            Occasion / Context
          </label>
          <select
            value={occasion}
            onChange={(e) => setOccasion(e.target.value)}
            className="bg-surface border border-outline-variant rounded px-sm py-xs text-body-sm font-body-sm text-on-surface focus:outline-none focus:border-primary"
          >
            {OCCASIONS.map((o) => (
              <option key={o.value} value={o.value}>{o.label}</option>
            ))}
          </select>
        </div>
      </div>

      {/* Custom prompt override */}
      <div className="flex flex-col gap-xs">
        <label className="text-[10px] font-data-mono uppercase tracking-widest text-on-surface-variant">
          Custom Instructions (optional — overrides above)
        </label>
        <input
          type="text"
          value={custom}
          onChange={(e) => setCustom(e.target.value)}
          placeholder="e.g. Diwali offer for loyal families, include 20% off"
          className="bg-surface border border-outline-variant rounded px-sm py-xs text-body-sm font-body-sm text-on-surface placeholder-on-surface-variant/50 focus:outline-none focus:border-primary"
        />
      </div>

      <button
        onClick={generate}
        disabled={loading}
        className="self-start flex items-center gap-xs bg-primary text-surface px-md py-sm rounded text-label-sm font-label-sm hover:opacity-90 disabled:opacity-50 transition-opacity"
      >
        {loading ? (
          <>
            <div className="w-3 h-3 border-2 border-surface/30 border-t-surface rounded-full animate-spin" />
            Generating...
          </>
        ) : (
          <>
            <span className="material-symbols-outlined text-sm">auto_awesome</span>
            Generate Message
          </>
        )}
      </button>

      {/* Output */}
      {message && (
        <div className="bg-[#24242F] border border-[#E6D3A3] rounded-lg p-md flex flex-col gap-sm">
          <div className="flex items-center justify-between">
            <div className="text-[10px] font-bold text-[#E6D3A3] uppercase tracking-[1px]">
              GENERATED — {segLabel} · {occLabel}
            </div>
            <span className={`text-[10px] font-data-mono ${message.length > 160 ? "text-error" : "text-on-surface-variant/60"}`}>
              {message.length} chars {message.length > 160 ? "⚠ over limit" : ""}
            </span>
          </div>
          <p className="text-[14px] text-white leading-[1.8] font-body-sm whitespace-pre-wrap">
            {message}
          </p>
          <div className="flex gap-sm pt-xs border-t border-[#E6D3A3]/20">
            <button
              onClick={copy}
              className="flex items-center gap-xs border border-[#E6D3A3] text-[#E6D3A3] text-[12px] px-md py-xs rounded hover:bg-[#E6D3A3]/10 transition-colors"
            >
              <span className="material-symbols-outlined text-sm">
                {copied ? "check" : "content_copy"}
              </span>
              {copied ? "Copied" : "Copy"}
            </button>
            <button
              onClick={generate}
              className="flex items-center gap-xs border border-outline-variant text-on-surface-variant text-[12px] px-md py-xs rounded hover:bg-surface-container transition-colors"
            >
              <span className="material-symbols-outlined text-sm">refresh</span>
              Regenerate
            </button>
          </div>
        </div>
      )}
    </div>
  );
}
