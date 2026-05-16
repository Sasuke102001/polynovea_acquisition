import Link from "next/link";
import {
  getMarketing,
  type ChannelCard,
  type MarketingSegmentCard,
} from "@/lib/api";
import WhatsAppGenerator from "@/components/WhatsAppGenerator";
import AIChannelCard from "@/components/AIChannelCard";

// Channels rendered as AI suggestion cards (content is AI-generated, not static)
const AI_CHANNELS = new Set(["instagram_organic", "instagram_ads", "google_ads", "instagram_consulting", "zomato_swiggy"]);

// ─── Segment card ─────────────────────────────────────────────────────────────

function SegmentCard({ seg }: { seg: MarketingSegmentCard }) {
  return (
    <div className="bg-background border border-brand-border p-md flex flex-col gap-sm rounded">
      <div className="flex justify-between items-start">
        <div>
          <h4 className="text-headline-md font-headline-md text-on-surface">{seg.segment_name}</h4>
          <div className="text-display-lg font-display-lg text-primary-container mt-xs font-bold">
            {seg.alignment_pct}%
          </div>
        </div>
        <span className="bg-[#7C3AED] text-white text-label-sm font-label-sm px-sm py-xs rounded-full uppercase tracking-wider">
          {seg.top_archetype.name}
        </span>
      </div>
      <div className="flex items-center gap-xs text-on-surface-variant text-body-sm font-body-sm mt-auto pt-sm border-t border-brand-border">
        <span className="material-symbols-outlined text-base">schedule</span>
        {seg.visit_time}
      </div>
    </div>
  );
}

// ─── Copy hooks block (Instagram) ─────────────────────────────────────────────

function CopyHooksBlock({ hooks }: { hooks: string[] }) {
  return (
    <div className="bg-background border border-brand-border rounded p-sm flex flex-col gap-sm">
      <div className="text-[10px] font-data-mono uppercase tracking-widest text-brand-label">
        CAPTION HOOKS
      </div>
      <div className="flex flex-col gap-sm">
        {hooks.map((hook, i) => (
          <div key={i} className="flex gap-sm items-start">
            <span className="text-[10px] font-data-mono text-primary-container mt-[3px] shrink-0">
              {String(i + 1).padStart(2, "0")}
            </span>
            <p className="text-body-sm font-body-sm text-on-surface leading-relaxed">{hook}</p>
          </div>
        ))}
      </div>
    </div>
  );
}

// ─── ROI benchmark chip ───────────────────────────────────────────────────────

function BenchmarkChip() {
  return (
    <span
      className="inline-flex items-center text-[9px] font-data-mono uppercase tracking-wider px-[5px] py-[1px] rounded border border-outline-variant/60 text-on-surface-variant/60 bg-surface-container/40"
      title="Industry benchmark — not Polynovea campaign data"
    >
      BENCHMARK
    </span>
  );
}

// ─── Acquisition channel card ─────────────────────────────────────────────────

function AcquisitionCard({ card }: { card: ChannelCard }) {
  const badgeBg = card.badge === "#1 RECOMMENDED" || card.badge === "#1 for Growth"
    ? "#F6E0B5"
    : "#F59E0B";
  const badgeText = "#241A00";

  return (
    <div className="bg-brand-surface border border-brand-border rounded p-md flex flex-col gap-md relative overflow-hidden">
      {card.badge && (
        <div
          className="absolute top-0 right-0 text-label-sm font-label-sm px-sm py-xs rounded-bl uppercase font-bold flex items-center gap-xs"
          style={{ backgroundColor: badgeBg, color: badgeText }}
        >
          <span className="material-symbols-outlined text-sm">stars</span>
          {card.badge}
        </div>
      )}

      <div className="pr-xl">
        <h3 className="text-headline-lg font-headline-lg text-on-surface font-bold">
          {card.channel_label}
        </h3>
        <div className="flex items-center gap-xs mt-sm text-body-sm font-body-sm text-primary-container">
          <span className="material-symbols-outlined text-sm">psychology</span>
          Mechanism: {card.mechanism_label}
        </div>
      </div>

      <div className="grid grid-cols-2 gap-sm border-y border-brand-border py-sm">
        <div>
          <div className="text-label-sm font-label-sm text-on-surface-variant mb-xs">Relevance Score</div>
          <div className="flex items-center gap-sm">
            <div className="text-data-mono font-data-mono text-on-surface text-lg">
              {Math.round(card.effectiveness_score)}/10
            </div>
            <div className="flex-1 h-1 bg-surface-container-high rounded-full overflow-hidden">
              <div
                className="h-full bg-signal-positive"
                style={{ width: `${card.effectiveness_score * 10}%` }}
              />
            </div>
          </div>
        </div>
        <div>
          <div className="flex items-center gap-xs text-label-sm font-label-sm text-on-surface-variant mb-xs">
            Expected ROI <BenchmarkChip />
          </div>
          <div className="text-data-mono font-data-mono text-signal-positive text-lg">
            {card.roi_label}
          </div>
        </div>
      </div>

      {card.why_it_works && (
        <div className="bg-background border border-brand-border p-sm rounded text-body-sm font-body-sm text-on-surface-variant italic">
          &ldquo;{card.why_it_works}&rdquo;
        </div>
      )}

      {card.copy_hooks && card.copy_hooks.length > 0 && <CopyHooksBlock hooks={card.copy_hooks} />}

      {card.action_checklist && card.action_checklist.length > 0 && (
        <div className="bg-background border border-brand-border p-sm rounded">
          <div className="text-[10px] font-data-mono uppercase tracking-widest text-brand-label mb-sm">
            LISTING CHECKLIST
          </div>
          <ul className="flex flex-col gap-xs">
            {card.action_checklist.map((item) => (
              <li key={item} className="flex items-start gap-xs text-body-sm font-body-sm text-on-surface-variant">
                <span className="material-symbols-outlined text-sm text-signal-positive mt-[2px] shrink-0">check_circle</span>
                {item}
              </li>
            ))}
          </ul>
        </div>
      )}

      <div className="mt-auto pt-sm">
        <div className="text-label-sm font-label-sm text-on-surface-variant mb-xs">Target Segments:</div>
        <div className="flex flex-wrap gap-xs">
          {card.target_segments.map((seg) => (
            <span
              key={seg}
              className="bg-[#F59E0B]/10 text-[#F59E0B] border border-[#F59E0B]/30 text-label-sm font-label-sm px-sm py-xs rounded"
            >
              {seg}
            </span>
          ))}
        </div>
      </div>
    </div>
  );
}

// ─── WhatsApp featured retention card ────────────────────────────────────────

function WhatsAppCard({ card, venueId, venueName }: { card: ChannelCard; venueId: number; venueName: string }) {
  return (
    <div className="bg-brand-surface border border-brand-border rounded p-md flex flex-col gap-md relative">
      <div className="absolute top-0 right-0 bg-[#7C3AED] text-white text-label-sm font-label-sm px-sm py-xs rounded-bl uppercase font-bold flex items-center gap-xs">
        PRIMARY
      </div>
      <div className="flex justify-between items-start pr-xl">
        <div>
          <h3 className="text-headline-lg font-headline-lg text-on-surface font-bold">
            {card.channel_label}
          </h3>
          <div className="flex items-center gap-xs mt-xs text-body-sm font-body-sm text-primary-container">
            <span className="material-symbols-outlined text-sm">cycle</span>
            Mechanism: {card.mechanism_label}
          </div>
        </div>
        <div className="text-right">
          <div className="flex items-center gap-xs justify-end text-label-sm font-label-sm text-on-surface-variant mb-xs">
            Expected ROI <BenchmarkChip />
          </div>
          <div className="text-data-mono font-data-mono text-signal-positive text-lg">
            {card.roi_label}
          </div>
        </div>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-md items-start">
        <div>
          <div className="flex justify-between items-center mb-xs">
            <div className="text-label-sm font-label-sm text-on-surface-variant uppercase">
              Effectiveness
            </div>
            <div className="text-data-mono font-data-mono text-on-surface">
              {Math.round(card.effectiveness_score)}/10
            </div>
          </div>
          <div className="h-1.5 bg-surface-container-high rounded-full overflow-hidden">
            <div
              className="h-full bg-[#7C3AED]"
              style={{ width: `${card.effectiveness_score * 10}%` }}
            />
          </div>
          {card.why_it_works && (
            <p className="mt-sm text-body-sm font-body-sm text-on-surface-variant italic text-[12px]">
              {card.why_it_works}
            </p>
          )}
          {card.send_timing && (
            <div className="mt-sm flex items-center gap-xs text-[11px] text-on-surface-variant/70 border-t border-brand-border pt-sm">
              <span className="material-symbols-outlined text-sm text-primary-container">schedule_send</span>
              <span><span className="font-bold text-primary-container">Best time to send:</span> {card.send_timing}</span>
            </div>
          )}
        </div>

        <div className="flex flex-col gap-xs">
          <div className="text-[10px] font-data-mono uppercase tracking-widest text-[#E6D3A3]/70">
            AI MESSAGE GENERATOR
          </div>
          <WhatsAppGenerator venueId={venueId} venueName={venueName} />
        </div>
      </div>
    </div>
  );
}

// ─── Full retention card (Email / SMS — replaces collapsed row) ───────────────

function RetentionCard({ card }: { card: ChannelCard }) {
  return (
    <div className="bg-brand-surface border border-brand-border rounded p-md flex flex-col gap-sm">
      <div className="flex justify-between items-start flex-wrap gap-sm">
        <div>
          <h4 className="text-headline-md font-headline-md text-on-surface font-bold">
            {card.channel_label}
          </h4>
          <div className="flex items-center gap-xs mt-xs text-body-sm font-body-sm text-on-surface-variant">
            <span className="material-symbols-outlined text-sm">psychology</span>
            {card.mechanism_label}
          </div>
        </div>
        <div className="text-right">
          <div className="flex items-center gap-xs justify-end text-label-sm font-label-sm text-on-surface-variant mb-xs">
            Expected ROI <BenchmarkChip />
          </div>
          <div className="text-data-mono font-data-mono text-signal-positive">
            {card.roi_label}
          </div>
        </div>
      </div>

      <div className="flex items-center gap-sm">
        <span className="text-label-sm font-label-sm text-on-surface-variant">
          Effectiveness:
        </span>
        <span className="text-data-mono font-data-mono text-on-surface">
          {Math.round(card.effectiveness_score)}/10
        </span>
        <div className="flex-1 h-1 bg-surface-container-high rounded-full overflow-hidden max-w-[120px]">
          <div
            className="h-full bg-secondary"
            style={{ width: `${card.effectiveness_score * 10}%` }}
          />
        </div>
      </div>

      {card.why_it_works && (
        <p className="text-body-sm font-body-sm text-on-surface-variant italic text-[12px]">
          {card.why_it_works}
        </p>
      )}
    </div>
  );
}

// ─── Growth Target section ────────────────────────────────────────────────────

// ─── Page ────────────────────────────────────────────────────────────────────

export default async function MarketingPage({
  params,
}: {
  params: Promise<{ id: string }>;
}) {
  const { id } = await params;

  let data;
  try {
    data = await getMarketing(id);
  } catch {
    return (
      <div className="p-margin text-error font-body-sm">
        Failed to load marketing data. Make sure the backend is running on port 8000.
      </div>
    );
  }

  const [whatsapp, ...otherRetention] = data.retention_channels;
  const venueName = data.top_segments[0]?.segment_name ?? "this venue";

  return (
    <div className="flex flex-col min-h-screen bg-background">
      {/* Tab bar header */}
      <div className="px-margin py-lg border-b border-brand-border flex flex-col gap-md">
        <div className="flex gap-md border-b border-outline-variant overflow-x-auto no-scrollbar">
          {[
            { label: "Overview",    href: `/venues/${id}` },
            { label: "Competitors", href: `/venues/${id}/competitors` },
            { label: "Transform",   href: `/venues/${id}/transform` },
            { label: "Marketing",   href: `/venues/${id}/marketing` },
            { label: "Campaign",    href: `/venues/${id}/campaign` },
            { label: "Audience",    href: `/venues/${id}/audience` },
          ].map((tab) => (
            <Link
              key={tab.label}
              href={tab.href}
              className={`pb-sm px-sm text-label-md font-label-md whitespace-nowrap transition-colors ${
                tab.label === "Marketing"
                  ? "text-primary border-b-2 border-primary"
                  : "text-on-surface-variant hover:text-primary"
              }`}
            >
              {tab.label}
            </Link>
          ))}
        </div>
      </div>

      {/* Content */}
      <main className="flex-1 overflow-y-auto custom-scrollbar p-margin lg:px-xl pb-24 bg-background">
        <div className="max-w-[1400px] mx-auto space-y-8">

          {/* ── Section 1: Customer Segments ── */}
          <section className="bg-brand-surface border border-brand-border rounded-lg p-md md:p-lg flex flex-col gap-md">
            <h3 className="text-label-sm font-label-sm text-brand-label tracking-widest uppercase">
              YOUR CUSTOMERS
            </h3>
            <div className="grid grid-cols-1 md:grid-cols-3 gap-sm">
              {data.top_segments.map((seg) => (
                <SegmentCard key={seg.segment_id} seg={seg} />
              ))}
            </div>
          </section>

          {/* ── Section 2: Acquisition ── */}
          <section className="flex flex-col gap-md">
            <div className="flex items-center gap-sm">
              <span className="bg-signal-positive/20 text-signal-positive text-label-sm font-label-sm px-sm py-xs rounded uppercase tracking-wider border border-signal-positive/30">
                NEW CUSTOMERS
              </span>
              <h2 className="text-headline-md font-headline-md text-signal-positive font-bold">
                ACQUISITION
              </h2>
              <span className="text-[10px] text-on-surface-variant/50 font-body-sm">
                — Polynovea executes
              </span>
            </div>
            <div className="grid grid-cols-1 lg:grid-cols-2 xl:grid-cols-3 gap-md">
              {data.acquisition_channels.map((card) =>
                AI_CHANNELS.has(card.channel) ? (
                  <AIChannelCard
                    key={card.channel}
                    venueId={parseInt(id)}
                    channel={card.channel}
                    title={card.channel_label}
                    badge={card.badge}
                    targetSegments={card.target_segments}
                    targetSegment={undefined}
                  />
                ) : (
                  <AcquisitionCard key={card.channel} card={card} />
                )
              )}
            </div>

          </section>

          {/* ── Section 3: Retention ── */}
          <section className="flex flex-col gap-md">
            <div className="flex items-center gap-sm">
              <span className="bg-[#7C3AED]/20 text-[#7C3AED] text-label-sm font-label-sm px-sm py-xs rounded uppercase tracking-wider border border-[#7C3AED]/30">
                EXISTING CUSTOMERS
              </span>
              <h2 className="text-headline-md font-headline-md text-[#7C3AED] font-bold">
                RETENTION
              </h2>
            </div>
            <div className="flex flex-col gap-sm">
              {whatsapp && <WhatsAppCard card={whatsapp} venueId={parseInt(id)} venueName={venueName} />}
              {otherRetention.map((card) => (
                <RetentionCard key={card.channel} card={card} />
              ))}
            </div>
          </section>

          {/* ── Section 4: Platform Consulting ── */}
          {data.consulting_channels.length > 0 && (
            <section className="flex flex-col gap-md">
              <div className="flex items-center gap-sm">
                <span className="bg-outline-variant/20 text-on-surface-variant text-label-sm font-label-sm px-sm py-xs rounded uppercase tracking-wider border border-outline-variant/40">
                  ADVISORY
                </span>
                <h2 className="text-headline-md font-headline-md text-on-surface-variant font-bold">
                  PLATFORM CONSULTING
                </h2>
                <span className="text-[10px] text-on-surface-variant/50 font-body-sm">
                  — Polynovea advises, venue executes
                </span>
              </div>
              <div className="grid grid-cols-1 lg:grid-cols-2 gap-md">
                {data.consulting_channels.map((card) =>
                  AI_CHANNELS.has(card.channel) ? (
                    <AIChannelCard
                      key={card.channel}
                      venueId={parseInt(id)}
                      channel={card.channel}
                      title={card.channel_label}
                      badge={card.badge}
                      targetSegments={card.target_segments}
                      targetSegment={undefined}
                    />
                  ) : (
                    <AcquisitionCard key={card.channel} card={card} />
                  )
                )}
              </div>
            </section>
          )}

          {/* ── Benchmark footnote ── */}
          <div className="border-t border-brand-border pt-sm">
            <p className="text-[11px] font-body-sm text-on-surface-variant/50 italic max-w-2xl">
              * ROI ranges are industry benchmarks (research confidence: MEDIUM). Results will be
              updated after first Polynovea campaign.
            </p>
          </div>

          <footer className="pt-lg border-t border-brand-border text-center">
            <p className="text-[11px] font-body-sm text-on-surface-variant/60 max-w-2xl mx-auto">
              Polynovea execution strategy. All campaigns are created and run by Polynovea — review
              metrics post-campaign.
            </p>
          </footer>
        </div>
      </main>
    </div>
  );
}
