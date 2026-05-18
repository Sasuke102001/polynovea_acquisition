"use client";

import { useState } from "react";
import { streamChat } from "@/lib/chat-api";

// Structured prompts per channel — system prompt in chat.py provides all venue context
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

const CHANNEL_ACCENT: Record<string, string> = {
  instagram_organic:    "#E1306C",   // Instagram pink
  instagram_ads:        "#1877F2",   // Meta blue
  google_ads:           "#4285F4",   // Google blue
  instagram_consulting: "#9CA3AF",   // Muted grey for advisory
  zomato_swiggy:        "#E23744",   // Zomato red
};

interface Props {
  venueId: number;
  channel: string;
  title: string;
  badge?: string | null;
  targetSegments?: string[];
  targetSegment?: string;   // from Transform tab — overrides primary segment focus
}

export default function AIChannelCard({ venueId, channel, title, badge, targetSegments, targetSegment }: Props) {
  const [content, setContent]     = useState("");
  const [loading, setLoading]     = useState(false);
  const [userBrief, setUserBrief] = useState("");

  const basePrompt = CHANNEL_PROMPTS[channel];
  const icon       = CHANNEL_ICONS[channel]  ?? "auto_awesome";
  const accent     = CHANNEL_ACCENT[channel] ?? "#F59E0B";

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


  const badgeBg   = badge === "#1 RECOMMENDED" ? "#F6E0B5" : "#1E293B";
  const badgeText = badge === "#1 RECOMMENDED" ? "#241A00" : accent;

  return (
    <div className="bg-brand-surface border border-brand-border rounded-lg overflow-hidden flex flex-col relative">

      {/* Badge */}
      {badge && (
        <div
          className="absolute top-0 right-0 text-label-sm font-label-sm px-sm py-xs rounded-bl uppercase font-bold flex items-center gap-xs"
          style={{ backgroundColor: badgeBg, color: badgeText }}
        >
          <span className="material-symbols-outlined text-sm">auto_awesome</span>
          {badge}
        </div>
      )}

      {/* Header */}
      <div className="flex items-center gap-sm p-md pb-sm border-b border-brand-border pr-xl flex-wrap">
        <span
          className="material-symbols-outlined text-[20px]"
          style={{ color: accent }}
        >
          {icon}
        </span>
        <h3 className="text-headline-lg font-headline-lg text-on-surface font-bold">{title}</h3>
        {targetSegment && (
          <span className="text-[10px] font-data-mono uppercase tracking-widest px-xs py-[2px] rounded border border-[#7C3AED]/40 text-[#C4B5FD] bg-[#7C3AED]/10">
            TARGET: {targetSegment}
          </span>
        )}
      </div>

      {/* AI suggestion body */}
      <div className="flex-1 p-md flex flex-col gap-sm">
        {content && (
          <div className="bg-background border border-brand-border rounded p-sm flex flex-col gap-xs">
            <div className="flex items-center gap-xs mb-xs">
              <span className="material-symbols-outlined text-sm" style={{ color: accent }}>
                auto_awesome
              </span>
              <span
                className="text-[10px] font-data-mono uppercase tracking-widest font-bold"
                style={{ color: accent }}
              >
                POLYNOVEA INSIGHT
              </span>
              {loading && (
                <div
                  className="w-2 h-2 border rounded-full animate-spin ml-auto"
                  style={{ borderColor: `${accent}40`, borderTopColor: accent }}
                />
              )}
            </div>
            <p className="text-[13px] text-on-surface leading-[1.9] whitespace-pre-wrap font-body-sm">
              {content}
            </p>
          </div>
        )}
      </div>

      {/* Brief input */}
      <div className="px-md pb-sm flex flex-col gap-[6px]">
        <label className="text-[9px] font-data-mono uppercase tracking-widest text-on-surface-variant/50">
          Your direction <span className="normal-case tracking-normal font-sans not-italic opacity-60">— optional</span>
        </label>
        <textarea
          value={userBrief}
          onChange={(e) => setUserBrief(e.target.value)}
          disabled={loading}
          placeholder={`e.g. "Meme format, 3 slides" · "Focus on weekend couples" · "Punchy 5-word hook only"`}
          rows={2}
          className="w-full bg-background border border-brand-border rounded px-sm py-xs text-[12px] text-on-surface placeholder-on-surface-variant/35 resize-none focus:outline-none focus:border-primary/60 disabled:opacity-40 leading-relaxed"
        />
      </div>

      {/* Footer: segments + action */}
      <div className="px-md pb-md flex items-center justify-between gap-sm flex-wrap">
        {targetSegments && targetSegments.length > 0 && (
          <div className="flex flex-wrap gap-xs">
            {targetSegments.map((seg) => (
              <span
                key={seg}
                className="text-label-sm font-label-sm px-sm py-xs rounded border"
                style={{ color: accent, borderColor: `${accent}40`, backgroundColor: `${accent}10` }}
              >
                {seg}
              </span>
            ))}
          </div>
        )}
        <button
          onClick={generate}
          disabled={loading}
          className="ml-auto flex items-center gap-xs border border-outline-variant text-on-surface-variant text-[12px] px-md py-xs rounded hover:bg-surface-container transition-colors disabled:opacity-40"
        >
          {loading ? (
            <>
              <div className="w-3 h-3 border-2 border-outline-variant border-t-on-surface-variant rounded-full animate-spin" />
              Generating…
            </>
          ) : (
            <>
              <span className="material-symbols-outlined text-sm">
                {content ? "refresh" : "auto_awesome"}
              </span>
              {content ? "Regenerate" : "Generate suggestion"}
            </>
          )}
        </button>
      </div>
    </div>
  );
}
