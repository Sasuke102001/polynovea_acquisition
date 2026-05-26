import Link from "next/link";
import { getMarketing, getAdBrief, type ChannelCard } from "@/lib/api";
import AIChannelCard from "@/components/AIChannelCard";
import WhatsAppGenerator from "@/components/WhatsAppGenerator";
import AdBriefCard from "@/components/AdBriefCard";
import CinTabBar from "@/components/CinTabBar";

function BenchmarkChip() {
  return (
    <span
      className="inline-flex items-center text-[9px] font-mono uppercase tracking-wider px-1.5 py-0.5 rounded"
      title="Industry benchmark — not Polynovea campaign data"
      style={{ border: "1px solid rgba(39,39,42,0.6)", color: "#71717A", background: "rgba(39,39,42,0.3)" }}
    >
      BENCHMARK
    </span>
  );
}

function WhatsAppCard({ card, venueId, venueName }: { card: ChannelCard; venueId: number; venueName: string }) {
  return (
    <div className="cin-card rounded-xl p-5 flex flex-col gap-4 relative">
      <div
        className="absolute top-0 right-0 px-3 py-1 text-[9px] font-bold uppercase tracking-widest rounded-tr-xl rounded-bl-xl"
        style={{ fontFamily: "'JetBrains Mono', monospace", background: "rgba(124,58,237,0.8)", color: "#fff" }}
      >
        PRIMARY
      </div>
      <div className="flex justify-between items-start pr-20">
        <div>
          <h3 className="text-sm font-bold" style={{ fontFamily: "'Clash Display', 'Inter', sans-serif", color: "#F5F5F5" }}>
            {card.channel_label}
          </h3>
          <div className="flex items-center gap-1.5 mt-1 text-xs" style={{ color: "#A1A1AA" }}>
            <span className="material-symbols-outlined text-[13px]">cycle</span>
            {card.mechanism_label}
          </div>
        </div>
        <div className="text-right">
          <div className="flex items-center gap-1.5 justify-end text-[9px] mb-1" style={{ color: "#71717A" }}>
            Expected ROI <BenchmarkChip />
          </div>
          <div className="text-lg font-mono font-bold sig-emerald">{card.roi_label}</div>
        </div>
      </div>
      <div className="grid grid-cols-1 md:grid-cols-2 gap-5 items-start">
        <div>
          <div className="flex justify-between items-center mb-2">
            <div className="text-[9px] font-bold uppercase tracking-widest" style={{ fontFamily: "'JetBrains Mono', monospace", color: "#71717A" }}>Effectiveness</div>
            <div className="text-sm font-mono" style={{ color: "#F5F5F5" }}>{Math.round(card.effectiveness_score)}/10</div>
          </div>
          <div className="h-1.5 rounded-full overflow-hidden" style={{ background: "rgba(39,39,42,0.8)" }}>
            <div className="h-full rounded-full" style={{ width: `${card.effectiveness_score * 10}%`, background: "rgba(124,58,237,0.7)" }} />
          </div>
          {card.why_it_works && (
            <p className="mt-3 text-[11px] italic" style={{ color: "#71717A" }}>{card.why_it_works}</p>
          )}
          {card.send_timing && (
            <div className="mt-3 flex items-center gap-1.5 text-[11px] border-t pt-3" style={{ borderColor: "rgba(39,39,42,0.6)", color: "#71717A" }}>
              <span className="material-symbols-outlined text-[13px]" style={{ color: "#E6D3A3" }}>schedule_send</span>
              <span><span className="font-bold" style={{ color: "#E6D3A3" }}>Best time to send:</span> {card.send_timing}</span>
            </div>
          )}
        </div>
        <div className="flex flex-col gap-2">
          <div className="text-[9px] font-bold uppercase tracking-widest" style={{ fontFamily: "'JetBrains Mono', monospace", color: "#9A8F6A" }}>
            POLYNOVEA MESSAGE GENERATOR
          </div>
          <WhatsAppGenerator venueId={venueId} venueName={venueName} />
        </div>
      </div>
    </div>
  );
}

function NoTarget({ id }: { id: string }) {
  return (
    <div className="flex flex-col min-h-screen">
      <div className="px-6 pt-6">
        <CinTabBar venueId={id} active="Campaign" />
      </div>
      <div className="flex-1 flex flex-col items-center justify-center gap-5 text-center p-8">
        <span className="material-symbols-outlined text-[56px]" style={{ color: "#27272A" }}>flag</span>
        <h2 className="text-xl font-bold" style={{ fontFamily: "'Clash Display', 'Inter', sans-serif", color: "#F5F5F5" }}>
          No growth target set
        </h2>
        <p className="text-sm max-w-[360px]" style={{ color: "#71717A" }}>
          Go to Transform, pick a segment to grow into, and click{" "}
          <span style={{ color: "#c4b5fd" }}>View Campaign Strategy</span> to build your plan here.
        </p>
        <Link
          href={`/venues/${id}/transform`}
          className="flex items-center gap-1.5 text-xs font-bold uppercase tracking-wider px-4 py-2 rounded transition-colors"
          style={{ fontFamily: "'JetBrains Mono', monospace", color: "#c4b5fd", border: "1px solid rgba(124,58,237,0.4)", background: "rgba(124,58,237,0.08)" }}
        >
          <span className="material-symbols-outlined text-[14px]">arrow_back</span>
          Set target in Transform
        </Link>
      </div>
    </div>
  );
}

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
  let brief;
  try {
    [data, brief] = await Promise.all([
      getMarketing(id, target),
      getAdBrief(id),
    ]);
  } catch {
    return (
      <div className="p-8 text-xs font-mono" style={{ color: "#FB7185" }}>
        Failed to load campaign data. Make sure the backend is running on port 8000.
      </div>
    );
  }

  const growthTarget = data.growth_target;
  if (!growthTarget) return <NoTarget id={id} />;

  const venueName = data.top_segments[0]?.segment_name ?? "this venue";

  return (
    <div className="flex flex-col min-h-screen">
      <div className="px-6 pt-6">
        <CinTabBar venueId={id} active="Campaign" />
      </div>

      <main className="flex-1 overflow-y-auto custom-scrollbar p-6 md:p-8 pb-24">
        <div className="max-w-[1400px] mx-auto space-y-8 cin-stagger">

          {/* ── Campaign header ── */}
          <div
            className="flex items-start gap-4 rounded-xl p-5 flex-wrap"
            style={{ background: "rgba(124,58,237,0.07)", border: "1px solid rgba(124,58,237,0.2)" }}
          >
            <span className="material-symbols-outlined text-[22px] mt-0.5" style={{ color: "#c4b5fd" }}>flag</span>
            <div className="flex-1 min-w-0">
              <div className="text-[9px] font-bold uppercase tracking-widest mb-1" style={{ fontFamily: "'JetBrains Mono', monospace", color: "rgba(196,181,253,0.6)" }}>
                GROWTH TARGET CAMPAIGN
              </div>
              <h2 className="text-xl font-bold" style={{ fontFamily: "'Clash Display', 'Inter', sans-serif", color: "#c4b5fd" }}>
                {growthTarget.target_segment_name}
              </h2>
              <p className="text-xs mt-1" style={{ color: "#71717A" }}>{growthTarget.demographic_label}</p>
            </div>
            <Link
              href={`/venues/${id}/transform`}
              className="text-[10px] uppercase font-mono transition-colors"
              style={{ color: "rgba(196,181,253,0.5)" }}
            >
              Change target ↗
            </Link>
          </div>

          {/* ── Ad Brief ── */}
          <section className="flex flex-col gap-4">
            <div className="flex items-center gap-3 flex-wrap">
              <span className="px-2 py-0.5 text-[9px] font-bold uppercase tracking-widest rounded" style={{ fontFamily: "'JetBrains Mono', monospace", background: "rgba(230,211,163,0.1)", border: "1px solid rgba(230,211,163,0.2)", color: "#E6D3A3" }}>AD BRIEF</span>
              <h2 className="text-sm font-bold uppercase tracking-widest" style={{ fontFamily: "'JetBrains Mono', monospace", color: "#E6D3A3" }}>BRIEF GENERATOR</h2>
              <span className="hidden sm:inline text-[10px]" style={{ color: "#3F3F46" }}>— archetype × channel × India creative rules</span>
            </div>
            <div className="cin-card rounded-xl p-5 md:p-6">
              <AdBriefCard venueId={parseInt(id)} initialBrief={brief} segments={data.top_segments} />
            </div>
          </section>

          {/* ── Acquisition ── */}
          <section className="flex flex-col gap-4">
            <div className="flex items-center gap-3 flex-wrap">
              <span className="px-2 py-0.5 text-[9px] font-bold uppercase tracking-widest rounded" style={{ fontFamily: "'JetBrains Mono', monospace", background: "rgba(16,185,129,0.1)", border: "1px solid rgba(16,185,129,0.2)", color: "#10B981" }}>NEW CUSTOMERS</span>
              <h2 className="text-sm font-bold uppercase tracking-widest sig-emerald" style={{ fontFamily: "'JetBrains Mono', monospace" }}>ACQUISITION</h2>
              <span className="hidden sm:inline text-[10px]" style={{ color: "#3F3F46" }}>— Polynovea executes</span>
            </div>
            <div className="grid grid-cols-1 lg:grid-cols-2 xl:grid-cols-3 gap-4">
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
          <section className="flex flex-col gap-4">
            <div className="flex items-center gap-3 flex-wrap">
              <span className="px-2 py-0.5 text-[9px] font-bold uppercase tracking-widest rounded" style={{ fontFamily: "'JetBrains Mono', monospace", background: "rgba(124,58,237,0.1)", border: "1px solid rgba(124,58,237,0.2)", color: "#c4b5fd" }}>EXISTING CUSTOMERS</span>
              <h2 className="text-sm font-bold uppercase tracking-widest" style={{ fontFamily: "'JetBrains Mono', monospace", color: "#c4b5fd" }}>RETENTION</h2>
              <span className="hidden sm:inline text-[10px]" style={{ color: "#3F3F46" }}>— Convert regulars into {growthTarget.target_segment_name} advocates</span>
            </div>
            <WhatsAppCard card={growthTarget.retention_channel} venueId={parseInt(id)} venueName={venueName} />
          </section>

          {/* ── Platform Consulting ── */}
          <section className="flex flex-col gap-4">
            <div className="flex items-center gap-3 flex-wrap">
              <span className="px-2 py-0.5 text-[9px] font-bold uppercase tracking-widest rounded" style={{ fontFamily: "'JetBrains Mono', monospace", background: "rgba(39,39,42,0.4)", border: "1px solid rgba(39,39,42,0.8)", color: "#A1A1AA" }}>ADVISORY</span>
              <h2 className="text-sm font-bold uppercase tracking-widest" style={{ fontFamily: "'JetBrains Mono', monospace", color: "#A1A1AA" }}>PLATFORM CONSULTING</h2>
              <span className="hidden sm:inline text-[10px]" style={{ color: "#3F3F46" }}>— Polynovea advises, venue executes</span>
            </div>
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
              <AIChannelCard
                venueId={parseInt(id)}
                channel="instagram_consulting"
                title="Instagram (Advisory)"
                badge="ADVISORY"
                targetSegment={target}
              />
            </div>
          </section>

          <footer className="pt-6 border-t text-center" style={{ borderColor: "rgba(39,39,42,0.5)" }}>
            <p className="text-[11px] max-w-2xl mx-auto" style={{ color: "#3F3F46" }}>
              Campaign strategy tailored for <span style={{ color: "#c4b5fd" }}>{growthTarget.target_segment_name}</span>.
              All acquisition campaigns created and run by Polynovea.
            </p>
          </footer>
        </div>
      </main>
    </div>
  );
}
