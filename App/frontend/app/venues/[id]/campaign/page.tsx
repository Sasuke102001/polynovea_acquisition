import Link from "next/link";
import { getMarketing, type ChannelCard } from "@/lib/api";
import ChatDrawer from "@/components/ChatDrawer";
import AIChannelCard from "@/components/AIChannelCard";
import WhatsAppGenerator from "@/components/WhatsAppGenerator";

// ─── Shared small components ──────────────────────────────────────────────────

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
            <div className="text-label-sm font-label-sm text-on-surface-variant uppercase">Effectiveness</div>
            <div className="text-data-mono font-data-mono text-on-surface">
              {Math.round(card.effectiveness_score)}/10
            </div>
          </div>
          <div className="h-1.5 bg-surface-container-high rounded-full overflow-hidden">
            <div className="h-full bg-[#7C3AED]" style={{ width: `${card.effectiveness_score * 10}%` }} />
          </div>
          {card.why_it_works && (
            <p className="mt-sm text-body-sm font-body-sm text-on-surface-variant italic text-[12px]">
              {card.why_it_works}
            </p>
          )}
          {card.send_timing && (
            <div className="mt-sm flex items-center gap-xs text-[11px] text-on-surface-variant/70 border-t border-brand-border pt-sm">
              <span className="material-symbols-outlined text-sm text-primary-container">schedule_send</span>
              <span>
                <span className="font-bold text-primary-container">Best time to send:</span> {card.send_timing}
              </span>
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

// ─── Nav ─────────────────────────────────────────────────────────────────────

function VenueTabs({ venueId }: { venueId: string }) {
  return (
    <div className="flex gap-md border-b border-outline-variant mt-sm overflow-x-auto no-scrollbar">
      {[
        { label: "Overview",    href: `/venues/${venueId}` },
        { label: "Competitors", href: `/venues/${venueId}/competitors` },
        { label: "Transform",   href: `/venues/${venueId}/transform` },
        { label: "Marketing",   href: `/venues/${venueId}/marketing` },
        { label: "Campaign",    href: `/venues/${venueId}/campaign` },
        { label: "Audience",    href: `/venues/${venueId}/audience` },
      ].map((tab) => (
        <Link
          key={tab.label}
          href={tab.href}
          className={`pb-sm px-sm text-label-md font-label-md whitespace-nowrap transition-colors ${
            tab.label === "Campaign"
              ? "text-primary border-b-2 border-primary"
              : "text-on-surface-variant hover:text-primary"
          }`}
        >
          {tab.label}
        </Link>
      ))}
    </div>
  );
}

// ─── Empty state ──────────────────────────────────────────────────────────────

function NoTarget({ id }: { id: string }) {
  return (
    <div className="flex flex-col min-h-screen bg-background">
      <div className="px-margin py-lg border-b border-brand-border">
        <VenueTabs venueId={id} />
      </div>
      <div className="flex-1 flex flex-col items-center justify-center gap-md text-center p-margin">
        <span className="material-symbols-outlined text-[56px] text-on-surface-variant/30">flag</span>
        <h2 className="text-headline-md font-headline-md text-on-surface">No growth target set</h2>
        <p className="text-body-md font-body-md text-on-surface-variant max-w-sm">
          Go to Transform, pick a segment to grow into, and click{" "}
          <span className="text-[#C4B5FD]">View Campaign Strategy</span> to build your plan here.
        </p>
        <Link
          href={`/venues/${id}/transform`}
          className="flex items-center gap-xs text-label-sm font-label-sm text-[#7C3AED] border border-[#7C3AED]/50 px-md py-sm rounded hover:bg-[#7C3AED]/20 transition-colors uppercase mt-sm"
        >
          <span className="material-symbols-outlined text-[16px]">arrow_back</span>
          Set target in Transform
        </Link>
      </div>
    </div>
  );
}

// ─── Page ────────────────────────────────────────────────────────────────────

export default async function CampaignPage({
  params,
  searchParams,
}: {
  params: Promise<{ id: string }>;
  searchParams: Promise<{ target?: string }>;
}) {
  const { id } = await params;
  const { target } = await searchParams;

  if (!target) return <NoTarget id={id} />;

  let data;
  try {
    data = await getMarketing(id, target);
  } catch {
    return (
      <div className="p-margin text-error font-body-sm">
        Failed to load campaign data. Make sure the backend is running on port 8000.
      </div>
    );
  }

  const growthTarget = data.growth_target;
  if (!growthTarget) return <NoTarget id={id} />;

  const venueName = data.top_segments[0]?.segment_name ?? "this venue";

  return (
    <div className="flex flex-col min-h-screen bg-background">
      {/* Tab bar */}
      <div className="px-margin py-lg border-b border-brand-border">
        <VenueTabs venueId={id} />
      </div>

      <main className="flex-1 overflow-y-auto custom-scrollbar p-margin lg:px-xl pb-24 bg-background">
        <div className="max-w-[1400px] mx-auto space-y-8">

          {/* ── Campaign header ── */}
          <div className="flex items-start gap-md border border-[#7C3AED]/30 rounded-lg p-md bg-[#7C3AED]/5">
            <span className="material-symbols-outlined text-[#7C3AED] text-[24px] mt-[2px]">flag</span>
            <div>
              <div className="text-[10px] font-data-mono uppercase tracking-wider text-[#7C3AED]/70 mb-xs">
                GROWTH TARGET CAMPAIGN
              </div>
              <h2 className="text-headline-lg font-headline-lg text-[#C4B5FD] font-bold">
                {growthTarget.target_segment_name}
              </h2>
              <p className="text-body-sm font-body-sm text-on-surface-variant">
                {growthTarget.demographic_label}
              </p>
            </div>
            <Link
              href={`/venues/${id}/transform`}
              className="ml-auto text-[10px] text-on-surface-variant/60 hover:text-on-surface-variant transition-colors uppercase font-data-mono whitespace-nowrap"
            >
              Change target ↗
            </Link>
          </div>

          {/* ── Acquisition ── */}
          <section className="flex flex-col gap-md">
            <div className="flex items-center gap-sm">
              <span className="bg-signal-positive/20 text-signal-positive text-label-sm font-label-sm px-sm py-xs rounded uppercase tracking-wider border border-signal-positive/30">
                NEW CUSTOMERS
              </span>
              <h2 className="text-headline-md font-headline-md text-signal-positive font-bold">ACQUISITION</h2>
              <span className="text-[10px] text-on-surface-variant/50 font-body-sm">— Polynovea executes</span>
            </div>
            <div className="grid grid-cols-1 lg:grid-cols-2 xl:grid-cols-3 gap-md">
              {[
                { channel: "instagram_organic", title: "Instagram Content",    badge: "#1 RECOMMENDED" },
                { channel: "instagram_ads",     title: "Meta & Instagram Ads", badge: "META & INSTA ADS" },
                { channel: "google_ads",        title: "Google Ads",           badge: "GOOGLE ADS" },
              ].map(({ channel, title, badge }) => (
                <AIChannelCard
                  key={channel}
                  venueId={parseInt(id)}
                  channel={channel}
                  title={title}
                  badge={badge}
                  targetSegment={target}
                />
              ))}
            </div>
          </section>

          {/* ── Retention ── */}
          <section className="flex flex-col gap-md">
            <div className="flex items-center gap-sm">
              <span className="bg-[#7C3AED]/20 text-[#7C3AED] text-label-sm font-label-sm px-sm py-xs rounded uppercase tracking-wider border border-[#7C3AED]/30">
                EXISTING CUSTOMERS
              </span>
              <h2 className="text-headline-md font-headline-md text-[#7C3AED] font-bold">RETENTION</h2>
              <span className="text-[10px] text-on-surface-variant/50 font-body-sm">
                — Convert regulars into {growthTarget.target_segment_name} advocates
              </span>
            </div>
            <WhatsAppCard
              card={growthTarget.retention_channel}
              venueId={parseInt(id)}
              venueName={venueName}
            />
          </section>

          {/* ── Platform Consulting ── */}
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
              <AIChannelCard
                venueId={parseInt(id)}
                channel="instagram_consulting"
                title="Instagram (Advisory)"
                badge="ADVISORY"
                targetSegment={target}
              />
            </div>
          </section>

          <footer className="pt-lg border-t border-brand-border text-center">
            <p className="text-[11px] font-body-sm text-on-surface-variant/60 max-w-2xl mx-auto">
              Campaign strategy tailored for <span className="text-[#C4B5FD]">{growthTarget.target_segment_name}</span>.
              All acquisition campaigns created and run by Polynovea.
            </p>
          </footer>
        </div>
      </main>

      <ChatDrawer venueId={parseInt(id)} tab="marketing" />
    </div>
  );
}
