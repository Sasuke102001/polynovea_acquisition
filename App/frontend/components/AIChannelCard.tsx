"use client";

import { useState } from "react";
import { streamChat } from "@/lib/chat-api";

// ─── Prompts ──────────────────────────────────────────────────────────────────

const CHANNEL_PROMPTS: Record<string, string> = {
  instagram_organic: `Generate Instagram content direction for our next live music show at this venue.

WHAT TO SHOOT: [3 specific shots + angles for the seating area during the show]
AVOID: [2 things to never show]
ON-SCREEN TEXT — Event Post: [exact overlay text format]
ON-SCREEN TEXT — Performance Reel: [exact overlay text format]
CAPTION TEMPLATE: [full caption with [Artist], [Genre], [Area] placeholders]
HASHTAGS: [location + genre + broad stack, 8–10 tags]

Keep it specific to this venue's atmosphere and primary audience. Under 220 words.`,

  instagram_ads: `Generate a Meta and Instagram paid ads targeting brief for our live music shows at this venue.

PRIMARY AUDIENCE: [age range, gender split if relevant, top 3 interest categories]
LOCATION RADIUS: [radius in km + area-specific logic]
BEST TIMING: [days + hours + why]
AD OBJECTIVE: [awareness / reach / conversions — and reasoning]
CREATIVE FORMAT: [Reels / Stories / Feed — which format and why]
COPY HOOK: [one punchy ad headline, under 10 words]

Base everything on this venue's primary customer segment and area. Under 200 words.`,

  google_ads: `Generate a Google Ads targeting brief for live music shows at this venue.

KEYWORDS: [6–8 search phrases — mix of broad + specific intent]
NEGATIVE KEYWORDS: [3–4 terms to exclude]
AUDIENCE SEGMENTS: [in-market + custom intent audiences]
LOCATION: [radius + targeting logic]
SCHEDULE: [which days/hours to run + reasoning]
BID STRATEGY: [recommendation with one-line reasoning]

Be specific to the venue's location, type, and primary audience. Under 200 words.`,

  instagram_consulting: `Generate Instagram account management advice for the venue's own Instagram account — not Polynovea's account.

POSTING FREQUENCY: [posts per week + Stories cadence]
CONTENT MIX: [% breakdown of content types the venue should post]
STORIES STRATEGY: [daily approach — what to post and when]
ENGAGEMENT: [how to handle comments, DMs, tags]
PROFILE TIP: [one specific improvement to bio, highlights, or grid layout]

Tailor all advice to this venue's customer segments and neighbourhood context. Under 200 words.`,

  zomato_swiggy: `Generate a Zomato and Swiggy platform optimisation brief for this venue.

MENU CURATION: [3–4 high-margin dishes to prioritise for delivery — based on cuisine type and primary segment]
PRICING STRATEGY: [delivery markup logic — what % uplift and which items to bundle into combos]
PHOTO BRIEF: [which 3 dishes to shoot first + composition notes for platform thumbnails]
AVAILABILITY WINDOWS: [which hours to stay active on platforms + reasoning tied to the venue's peak segments]
REVIEW STRATEGY: [how to respond to negative ratings + one tactic to lift review volume from regulars]
PACKAGING NOTE: [one specific packaging fix that protects food quality and photographs well for listing images]

Ground everything in the venue's cuisine type, area, and primary customer segment. Under 200 words.`,
};

const CHANNEL_ICONS: Record<string, string> = {
  instagram_organic:    "photo_camera",
  instagram_ads:        "ads_click",
  google_ads:           "search",
  instagram_consulting: "tips_and_updates",
  zomato_swiggy:        "delivery_dining",
};

// Cinematic-toned accent per channel — muted enough to sit on #0e0e11
const CHANNEL_ACCENT: Record<string, string> = {
  instagram_organic:    "#E6D3A3",   // gold — owned channel
  instagram_ads:        "#E6D3A3",   // gold — paid
  google_ads:           "#E6D3A3",   // gold — search
  instagram_consulting: "#A1A1AA",   // muted — advisory
  zomato_swiggy:        "#A1A1AA",   // muted — advisory
};

// Badge label per channel
const CHANNEL_BADGE_LABEL: Record<string, string> = {
  instagram_organic:    "CONTENT",
  instagram_ads:        "META & INSTA ADS",
  google_ads:           "GOOGLE ADS",
  instagram_consulting: "ADVISORY",
  zomato_swiggy:        "PLATFORM ADVISORY",
};

interface Props {
  venueId: number;
  channel: string;
  title: string;
  badge?: string | null;
  targetSegments?: string[];
  targetSegment?: string;
}

export default function AIChannelCard({ venueId, channel, title, badge, targetSegments, targetSegment }: Props) {
  const [content, setContent]     = useState("");
  const [loading, setLoading]     = useState(false);
  const [userBrief, setUserBrief] = useState("");

  const basePrompt    = CHANNEL_PROMPTS[channel];
  const icon          = CHANNEL_ICONS[channel]  ?? "auto_awesome";
  const accent        = CHANNEL_ACCENT[channel] ?? "#E6D3A3";
  const isAdvisory    = channel === "instagram_consulting" || channel === "zomato_swiggy";
  const channelBadge  = CHANNEL_BADGE_LABEL[channel];
  const isTopRec      = badge === "#1 RECOMMENDED" || badge === "#1 for Growth";

  const generate = async () => {
    if (!basePrompt) return;
    setLoading(true);
    setContent("");

    let prompt = targetSegment
      ? `${basePrompt}\n\nGROWTH TARGET: We are specifically trying to attract "${targetSegment}" as a new customer segment. Prioritise this audience in all suggestions above — targeting, content angles, copy hooks, and timing should all skew toward attracting "${targetSegment}" customers, even if they are not currently the venue's primary segment.`
      : basePrompt;

    if (userBrief.trim()) {
      prompt += `\n\nCLIENT DIRECTION: ${userBrief.trim()}\n\nApply this direction specifically — lean into the angle, format, or idea provided while still grounding everything in the venue data, segment research, and Polynovea context above.`;
    }

    let result = "";
    await streamChat(venueId, "marketing", prompt, {
      onChunk:    (chunk) => { result += chunk; setContent(result); },
      onError:    ()      => setLoading(false),
      onComplete: ()      => setLoading(false),
    });
  };

  return (
    <div
      className="cin-card rounded-xl overflow-hidden flex flex-col relative"
      style={{ minHeight: 0 }}
    >
      {/* Channel type badge — top right */}
      {channelBadge && (
        <div
          className="absolute top-0 right-0 text-[9px] font-bold px-2 py-1 rounded-bl uppercase tracking-wider flex items-center gap-1"
          style={{
            fontFamily: "'JetBrains Mono', monospace",
            background: isAdvisory ? "rgba(75,70,59,0.3)" : "rgba(230,211,163,0.1)",
            border: `0 0 0 1px ${isAdvisory ? "rgba(75,70,59,0.5)" : "rgba(230,211,163,0.25)"}`,
            color: isAdvisory ? "#A1A1AA" : "#E6D3A3",
          }}
        >
          <span className="material-symbols-outlined text-[11px]">auto_awesome</span>
          {channelBadge}
        </div>
      )}

      {/* #1 recommended badge */}
      {badge && isTopRec && (
        <div
          className="absolute top-0 left-0 text-[9px] font-bold px-2 py-1 rounded-br uppercase tracking-wider flex items-center gap-1"
          style={{ fontFamily: "'JetBrains Mono', monospace", background: "rgba(230,211,163,0.15)", border: "0 0 0 1px rgba(230,211,163,0.3)", color: "#E6D3A3" }}
        >
          <span className="material-symbols-outlined text-[11px]">stars</span>
          {badge}
        </div>
      )}

      {/* Header */}
      <div
        className="flex items-center gap-3 px-5 pt-5 pb-4 flex-wrap"
        style={{ paddingTop: (badge && isTopRec) || channelBadge ? "2.5rem" : "1.25rem" }}
      >
        <span className="material-symbols-outlined text-[22px]" style={{ color: accent }}>{icon}</span>
        <h3 className="text-xl font-bold flex-1 min-w-0" style={{ fontFamily: "'Clash Display', 'Inter', sans-serif", color: "#F5F5F5" }}>
          {title}
        </h3>
        {targetSegment && (
          <span
            className="text-[9px] font-bold uppercase tracking-widest px-2 py-0.5 rounded"
            style={{ fontFamily: "'JetBrains Mono', monospace", border: "1px solid rgba(124,58,237,0.4)", color: "#c4b5fd", background: "rgba(124,58,237,0.1)" }}
          >
            TARGET: {targetSegment}
          </span>
        )}
      </div>

      {/* AI output */}
      <div className="flex-1 px-5 pb-3 flex flex-col gap-3">
        {content && (
          <div
            className="rounded-lg p-3 flex flex-col gap-2"
            style={{ background: "rgba(10,10,10,0.6)", border: "1px solid rgba(39,39,42,0.7)" }}
          >
            <div className="flex items-center gap-1.5">
              <span className="material-symbols-outlined text-[13px]" style={{ color: accent }}>auto_awesome</span>
              <span className="text-[9px] font-bold uppercase tracking-widest" style={{ fontFamily: "'JetBrains Mono', monospace", color: accent }}>
                POLYNOVEA INSIGHT
              </span>
              {loading && (
                <div
                  className="w-2 h-2 border rounded-full animate-spin ml-auto"
                  style={{ borderColor: "rgba(230,211,163,0.2)", borderTopColor: "#E6D3A3" }}
                />
              )}
            </div>
            <p className="text-[13px] leading-[1.85] whitespace-pre-wrap" style={{ color: "#A1A1AA" }}>
              {content}
            </p>
          </div>
        )}
      </div>

      {/* Brief input */}
      <div className="px-5 pb-3 flex flex-col gap-1.5">
        <label className="text-[9px] font-bold uppercase tracking-widest" style={{ fontFamily: "'JetBrains Mono', monospace", color: "#71717A" }}>
          Your direction <span className="normal-case tracking-normal font-sans opacity-60">— optional</span>
        </label>
        <textarea
          value={userBrief}
          onChange={(e) => setUserBrief(e.target.value)}
          disabled={loading}
          placeholder={`e.g. "Meme format, 3 slides" · "Focus on weekend couples" · "Punchy 5-word hook only"`}
          rows={2}
          className="w-full rounded-lg px-3 py-2 text-[12px] resize-none focus:outline-none transition-all disabled:opacity-40 leading-relaxed"
          style={{ background: "rgba(24,24,27,0.7)", border: "1px solid rgba(39,39,42,0.7)", color: "#F5F5F5", fontFamily: "'Inter', sans-serif" }}
          onFocus={(e) => (e.target.style.borderColor = "rgba(230,211,163,0.35)")}
          onBlur={(e) => (e.target.style.borderColor = "rgba(39,39,42,0.7)")}
        />
      </div>

      {/* Footer: segments + generate button */}
      <div className="px-5 pb-5 flex items-center justify-between gap-3 flex-wrap">
        {targetSegments && targetSegments.length > 0 && (
          <div className="flex flex-wrap gap-1.5">
            {targetSegments.map((seg) => (
              <span
                key={seg}
                className="text-[9px] font-bold px-2 py-0.5 rounded uppercase tracking-widest"
                style={{ fontFamily: "'JetBrains Mono', monospace", color: "#F59E0B", borderColor: "rgba(245,158,11,0.3)", border: "1px solid rgba(245,158,11,0.3)", background: "rgba(245,158,11,0.08)" }}
              >
                {seg}
              </span>
            ))}
          </div>
        )}
        <button
          onClick={generate}
          disabled={loading}
          className="ml-auto flex items-center gap-1.5 text-[11px] font-bold uppercase tracking-wider px-3 py-1.5 rounded-lg transition-all disabled:opacity-40"
          style={{ fontFamily: "'JetBrains Mono', monospace", border: "1px solid rgba(39,39,42,0.8)", color: "#A1A1AA", background: "rgba(24,24,27,0.6)" }}
          onMouseEnter={(e) => { (e.currentTarget as HTMLElement).style.borderColor = "rgba(230,211,163,0.3)"; (e.currentTarget as HTMLElement).style.color = "#E6D3A3"; }}
          onMouseLeave={(e) => { (e.currentTarget as HTMLElement).style.borderColor = "rgba(39,39,42,0.8)"; (e.currentTarget as HTMLElement).style.color = "#A1A1AA"; }}
        >
          {loading ? (
            <>
              <div className="w-3 h-3 border-2 rounded-full animate-spin" style={{ borderColor: "rgba(230,211,163,0.2)", borderTopColor: "#E6D3A3" }} />
              Generating…
            </>
          ) : (
            <>
              <span className="material-symbols-outlined text-[14px]">{content ? "refresh" : "auto_awesome"}</span>
              {content ? "Regenerate" : "Generate suggestion"}
            </>
          )}
        </button>
      </div>
    </div>
  );
}
