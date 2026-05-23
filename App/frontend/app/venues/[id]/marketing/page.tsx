import {
  getMarketing,
  getAdBrief,
  type ChannelCard,
  type MarketingSegmentCard,
} from "@/lib/api";
import WhatsAppGenerator from "@/components/WhatsAppGenerator";
import AIChannelCard from "@/components/AIChannelCard";
import AdBriefCard from "@/components/AdBriefCard";
import CinTabBar from "@/components/CinTabBar";

// Channels rendered as AI suggestion cards (content is AI-generated, not static)
const AI_CHANNELS = new Set(["instagram_organic", "instagram_ads", "google_ads", "instagram_consulting", "zomato_swiggy"]);

// ─── Segment card ─────────────────────────────────────────────────────────────

function SegmentCard({ seg }: { seg: MarketingSegmentCard }) {
  return (
    <div className="cin-card rounded-xl p-5 flex flex-col gap-3">
      <div className="flex justify-between items-start">
        <div>
          <h4 className="text-sm font-bold" style={{ fontFamily: "'Clash Display', 'Inter', sans-serif", color: "#F5F5F5" }}>{seg.segment_name}</h4>
          <div className="text-2xl font-bold mt-1 gold-glow" style={{ fontFamily: "'JetBrains Mono', monospace" }}>
            {seg.alignment_pct}%
          </div>
        </div>
        <span
          className="px-2 py-0.5 text-[9px] font-bold rounded uppercase tracking-widest"
          style={{ fontFamily: "'JetBrains Mono', monospace", background: "rgba(124,58,237,0.2)", border: "1px solid rgba(124,58,237,0.3)", color: "#c4b5fd" }}
        >
          {seg.top_archetype.name}
        </span>
      </div>
      <div className="flex items-center gap-2 text-xs mt-auto pt-3 border-t" style={{ borderColor: "rgba(39,39,42,0.6)", color: "#71717A" }}>
        <span className="material-symbols-outlined text-[14px]">schedule</span>
        {seg.visit_time}
      </div>
    </div>
  );
}

// ─── Copy hooks block (Instagram) ─────────────────────────────────────────────

function CopyHooksBlock({ hooks }: { hooks: string[] }) {
  return (
    <div
      className="rounded p-3 flex flex-col gap-2"
      style={{ background: "rgba(10,10,10,0.6)", border: "1px solid rgba(39,39,42,0.7)" }}
    >
      <div className="text-[9px] font-bold uppercase tracking-widest" style={{ fontFamily: "'JetBrains Mono', monospace", color: "#71717A" }}>
        CAPTION HOOKS
      </div>
      <div className="flex flex-col gap-2">
        {hooks.map((hook, i) => (
          <div key={i} className="flex gap-2 items-start">
            <span className="text-[10px] font-bold mt-[3px] shrink-0" style={{ fontFamily: "'JetBrains Mono', monospace", color: "#E6D3A3" }}>
              {String(i + 1).padStart(2, "0")}
            </span>
            <p className="text-xs leading-relaxed" style={{ color: "#A1A1AA" }}>{hook}</p>
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
      className="inline-flex items-center text-[9px] font-bold uppercase tracking-wider px-[5px] py-[1px] rounded"
      style={{ fontFamily: "'JetBrains Mono', monospace", border: "1px solid rgba(75,70,59,0.4)", color: "rgba(161,161,170,0.6)", background: "rgba(31,31,34,0.4)" }}
      title="Industry benchmark — not Polynovea campaign data"
    >
      BENCHMARK
    </span>
  );
}

// ─── Acquisition channel card ─────────────────────────────────────────────────

function AcquisitionCard({ card }: { card: ChannelCard }) {
  const isTopRec = card.badge === "#1 RECOMMENDED" || card.badge === "#1 for Growth";

  return (
    <div className="cin-card rounded-xl p-5 flex flex-col gap-4 relative overflow-hidden">
      {card.badge && (
        <div
          className="absolute top-0 right-0 text-[9px] font-bold px-2 py-1 rounded-bl uppercase flex items-center gap-1"
          style={{ background: isTopRec ? "rgba(230,211,163,0.15)" : "rgba(245,158,11,0.15)", border: `0 0 0 1px ${isTopRec ? "rgba(230,211,163,0.3)" : "rgba(245,158,11,0.3)"}`, color: isTopRec ? "#E6D3A3" : "#F59E0B", fontFamily: "'JetBrains Mono', monospace" }}
        >
          <span className="material-symbols-outlined text-[12px]">stars</span>
          {card.badge}
        </div>
      )}

      <div className="pr-10">
        <h3 className="text-xl font-bold" style={{ fontFamily: "'Clash Display', 'Inter', sans-serif", color: "#F5F5F5" }}>
          {card.channel_label}
        </h3>
        <div className="flex items-center gap-1.5 mt-1.5 text-xs" style={{ color: "#E6D3A3" }}>
          <span className="material-symbols-outlined text-[14px]">psychology</span>
          Mechanism: {card.mechanism_label}
        </div>
      </div>

      <div className="grid grid-cols-2 gap-3 border-y py-3" style={{ borderColor: "rgba(39,39,42,0.6)" }}>
        <div>
          <div className="text-[9px] font-bold uppercase tracking-widest mb-1.5" style={{ fontFamily: "'JetBrains Mono', monospace", color: "#71717A" }}>Relevance Score</div>
          <div className="flex items-center gap-2">
            <div className="text-lg font-bold" style={{ fontFamily: "'JetBrains Mono', monospace", color: "#F5F5F5" }}>
              {Math.round(card.effectiveness_score)}/10
            </div>
            <div className="flex-1 h-1 rounded-full overflow-hidden" style={{ background: "rgba(42,42,45,0.6)" }}>
              <div className="h-full rounded-full" style={{ width: `${card.effectiveness_score * 10}%`, background: "#10B981" }} />
            </div>
          </div>
        </div>
        <div>
          <div className="flex items-center gap-1.5 mb-1.5 text-[9px] font-bold uppercase tracking-widest" style={{ fontFamily: "'JetBrains Mono', monospace", color: "#71717A" }}>
            Expected ROI <BenchmarkChip />
          </div>
          <div className="text-lg font-bold sig-emerald" style={{ fontFamily: "'JetBrains Mono', monospace" }}>
            {card.roi_label}
          </div>
        </div>
      </div>

      {card.why_it_works && (
        <div className="rounded p-3 text-xs italic" style={{ background: "rgba(10,10,10,0.5)", border: "1px solid rgba(39,39,42,0.6)", color: "#A1A1AA" }}>
          &ldquo;{card.why_it_works}&rdquo;
        </div>
      )}

      {card.copy_hooks && card.copy_hooks.length > 0 && <CopyHooksBlock hooks={card.copy_hooks} />}

      {card.action_checklist && card.action_checklist.length > 0 && (
        <div className="rounded p-3" style={{ background: "rgba(10,10,10,0.5)", border: "1px solid rgba(39,39,42,0.6)" }}>
          <div className="text-[9px] font-bold uppercase tracking-widest mb-2" style={{ fontFamily: "'JetBrains Mono', monospace", color: "#71717A" }}>
            LISTING CHECKLIST
          </div>
          <ul className="flex flex-col gap-1.5">
            {card.action_checklist.map((item) => (
              <li key={item} className="flex items-start gap-1.5 text-xs" style={{ color: "#A1A1AA" }}>
                <span className="material-symbols-outlined text-[13px] mt-[2px] shrink-0" style={{ color: "#10B981" }}>check_circle</span>
                {item}
              </li>
            ))}
          </ul>
        </div>
      )}

      <div className="mt-auto pt-1">
        <div className="text-[9px] font-bold uppercase tracking-widest mb-1.5" style={{ fontFamily: "'JetBrains Mono', monospace", color: "#71717A" }}>Target Segments:</div>
        <div className="flex flex-wrap gap-1.5">
          {card.target_segments.map((seg) => (
            <span
              key={seg}
              className="text-[9px] font-bold px-2 py-0.5 rounded uppercase tracking-widest"
              style={{ fontFamily: "'JetBrains Mono', monospace", background: "rgba(245,158,11,0.1)", border: "1px solid rgba(245,158,11,0.3)", color: "#F59E0B" }}
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
    <div className="cin-card rounded-xl p-5 flex flex-col gap-4 relative">
      <div
        className="absolute top-0 right-0 text-[9px] font-bold px-2 py-1 rounded-bl uppercase flex items-center gap-1"
        style={{ background: "rgba(124,58,237,0.2)", border: "1px solid rgba(124,58,237,0.3)", color: "#c4b5fd", fontFamily: "'JetBrains Mono', monospace" }}
      >
        PRIMARY
      </div>
      <div className="flex justify-between items-start pr-16">
        <div>
          <h3 className="text-xl font-bold" style={{ fontFamily: "'Clash Display', 'Inter', sans-serif", color: "#F5F5F5" }}>
            {card.channel_label}
          </h3>
          <div className="flex items-center gap-1.5 mt-1 text-xs" style={{ color: "#E6D3A3" }}>
            <span className="material-symbols-outlined text-[14px]">cycle</span>
            Mechanism: {card.mechanism_label}
          </div>
        </div>
        <div className="text-right">
          <div className="flex items-center gap-1.5 justify-end mb-1" style={{ color: "#71717A" }}>
            <span className="text-[9px] font-bold uppercase tracking-widest" style={{ fontFamily: "'JetBrains Mono', monospace" }}>Expected ROI</span>
            <BenchmarkChip />
          </div>
          <div className="text-lg font-bold sig-emerald" style={{ fontFamily: "'JetBrains Mono', monospace" }}>
            {card.roi_label}
          </div>
        </div>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-4 items-start">
        <div>
          <div className="flex justify-between items-center mb-1.5">
            <div className="text-[9px] font-bold uppercase tracking-widest" style={{ fontFamily: "'JetBrains Mono', monospace", color: "#71717A" }}>
              Effectiveness
            </div>
            <div className="text-sm font-bold" style={{ fontFamily: "'JetBrains Mono', monospace", color: "#F5F5F5" }}>
              {Math.round(card.effectiveness_score)}/10
            </div>
          </div>
          <div className="h-1.5 rounded-full overflow-hidden" style={{ background: "rgba(42,42,45,0.6)" }}>
            <div
              className="h-full rounded-full"
              style={{ width: `${card.effectiveness_score * 10}%`, background: "#7C3AED" }}
            />
          </div>
          {card.why_it_works && (
            <p className="mt-2 text-xs italic" style={{ color: "#A1A1AA" }}>
              {card.why_it_works}
            </p>
          )}
          {card.send_timing && (
            <div className="mt-3 flex items-center gap-1.5 text-[11px] border-t pt-3" style={{ borderColor: "rgba(39,39,42,0.6)", color: "#71717A" }}>
              <span className="material-symbols-outlined text-[14px]" style={{ color: "#E6D3A3" }}>schedule_send</span>
              <span><span className="font-bold" style={{ color: "#E6D3A3" }}>Best time to send:</span> {card.send_timing}</span>
            </div>
          )}
        </div>

        <div className="flex flex-col gap-2">
          <div className="text-[9px] font-bold uppercase tracking-widest" style={{ fontFamily: "'JetBrains Mono', monospace", color: "rgba(230,211,163,0.7)" }}>
            POLYNOVEA MESSAGE GENERATOR
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
    <div className="cin-card rounded-xl p-4 flex flex-col gap-3">
      <div className="flex justify-between items-start flex-wrap gap-3">
        <div>
          <h4 className="text-lg font-bold" style={{ fontFamily: "'Clash Display', 'Inter', sans-serif", color: "#F5F5F5" }}>
            {card.channel_label}
          </h4>
          <div className="flex items-center gap-1.5 mt-1 text-xs" style={{ color: "#A1A1AA" }}>
            <span className="material-symbols-outlined text-[14px]">psychology</span>
            {card.mechanism_label}
          </div>
        </div>
        <div className="text-right">
          <div className="flex items-center gap-1.5 justify-end mb-1">
            <span className="text-[9px] font-bold uppercase tracking-widest" style={{ fontFamily: "'JetBrains Mono', monospace", color: "#71717A" }}>Expected ROI</span>
            <BenchmarkChip />
          </div>
          <div className="font-bold sig-emerald" style={{ fontFamily: "'JetBrains Mono', monospace" }}>
            {card.roi_label}
          </div>
        </div>
      </div>

      <div className="flex items-center gap-3">
        <span className="text-[9px] font-bold uppercase tracking-widest" style={{ fontFamily: "'JetBrains Mono', monospace", color: "#71717A" }}>
          Effectiveness:
        </span>
        <span className="text-sm font-bold" style={{ fontFamily: "'JetBrains Mono', monospace", color: "#F5F5F5" }}>
          {Math.round(card.effectiveness_score)}/10
        </span>
        <div className="flex-1 h-1 rounded-full overflow-hidden max-w-[120px]" style={{ background: "rgba(42,42,45,0.6)" }}>
          <div
            className="h-full rounded-full"
            style={{ width: `${card.effectiveness_score * 10}%`, background: "#c4b5fd" }}
          />
        </div>
      </div>

      {card.why_it_works && (
        <p className="text-xs italic" style={{ color: "#71717A" }}>
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
  let brief;
  try {
    [data, brief] = await Promise.all([
      getMarketing(id),
      getAdBrief(id),
    ]);
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
    <div className="flex flex-col min-h-screen">
      {/* Tab bar header */}
      <div className="px-6 pt-6 flex flex-col gap-4">
        <CinTabBar venueId={id} active="Marketing" />
      </div>

      {/* Content */}
      <main className="flex-1 overflow-y-auto custom-scrollbar p-6 md:p-8 pb-24">
        <div className="max-w-[1400px] mx-auto space-y-8 cin-stagger">

          {/* ── Section 1: Customer Segments ── */}
          <section className="cin-card rounded-xl p-5 md:p-6 flex flex-col gap-4">
            <h3 className="text-[10px] font-bold tracking-widest uppercase" style={{ fontFamily: "'JetBrains Mono', monospace", color: "#71717A" }}>
              YOUR CUSTOMERS
            </h3>
            <div className="grid grid-cols-1 md:grid-cols-3 gap-sm">
              {data.top_segments.map((seg) => (
                <SegmentCard key={seg.segment_id} seg={seg} />
              ))}
            </div>
          </section>

          {/* ── Section 2: Ad Brief Generator ── */}
          <section className="flex flex-col gap-4">
            <div className="flex items-center gap-3 flex-wrap">
              <span
                className="px-2 py-0.5 text-[9px] font-bold uppercase tracking-widest rounded"
                style={{ fontFamily: "'JetBrains Mono', monospace", background: "rgba(230,211,163,0.1)", border: "1px solid rgba(230,211,163,0.2)", color: "#E6D3A3" }}
              >
                AD BRIEF
              </span>
              <h2 className="text-sm font-bold uppercase tracking-widest" style={{ fontFamily: "'JetBrains Mono', monospace", color: "#E6D3A3" }}>
                BRIEF GENERATOR
              </h2>
              <span className="hidden sm:inline text-[10px]" style={{ color: "#3F3F46" }}>
                — archetype × channel × India creative rules
              </span>
            </div>
            <div className="cin-card rounded-xl p-5 md:p-6">
              <AdBriefCard venueId={parseInt(id)} initialBrief={brief} />
            </div>
          </section>

          {/* ── Section 3: Acquisition ── */}
          <section className="flex flex-col gap-4">
            <div className="flex items-center gap-3 flex-wrap">
              <span
                className="px-2 py-0.5 text-[9px] font-bold uppercase tracking-widest rounded"
                style={{ fontFamily: "'JetBrains Mono', monospace", background: "rgba(16,185,129,0.1)", border: "1px solid rgba(16,185,129,0.2)", color: "#10B981" }}
              >
                NEW CUSTOMERS
              </span>
              <h2 className="text-sm font-bold uppercase tracking-widest sig-emerald" style={{ fontFamily: "'JetBrains Mono', monospace" }}>
                ACQUISITION
              </h2>
              <span className="hidden sm:inline text-[10px]" style={{ color: "#3F3F46" }}>
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
          <section className="flex flex-col gap-4">
            <div className="flex items-center gap-3 flex-wrap">
              <span
                className="px-2 py-0.5 text-[9px] font-bold uppercase tracking-widest rounded"
                style={{ fontFamily: "'JetBrains Mono', monospace", background: "rgba(124,58,237,0.12)", border: "1px solid rgba(124,58,237,0.2)", color: "#c4b5fd" }}
              >
                EXISTING CUSTOMERS
              </span>
              <h2 className="text-sm font-bold uppercase tracking-widest" style={{ fontFamily: "'JetBrains Mono', monospace", color: "#c4b5fd" }}>
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
            <section className="flex flex-col gap-4">
              <div className="flex items-center gap-3 flex-wrap">
                <span
                  className="px-2 py-0.5 text-[9px] font-bold uppercase tracking-widest rounded"
                  style={{ fontFamily: "'JetBrains Mono', monospace", background: "rgba(75,70,59,0.2)", border: "1px solid rgba(75,70,59,0.4)", color: "#A1A1AA" }}
                >
                  ADVISORY
                </span>
                <h2 className="text-sm font-bold uppercase tracking-widest" style={{ fontFamily: "'JetBrains Mono', monospace", color: "#A1A1AA" }}>
                  PLATFORM CONSULTING
                </h2>
                <span className="hidden sm:inline text-[10px]" style={{ color: "#3F3F46" }}>
                  — Polynovea advises, venue executes
                </span>
              </div>
              <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
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
          <div className="border-t pt-4" style={{ borderColor: "rgba(39,39,42,0.5)" }}>
            <p className="text-[11px] italic max-w-2xl" style={{ color: "rgba(161,161,170,0.5)" }}>
              * ROI ranges are industry benchmarks (research confidence: MEDIUM). Results will be
              updated after first Polynovea campaign.
            </p>
          </div>

          <footer className="pt-6 border-t text-center" style={{ borderColor: "rgba(39,39,42,0.5)" }}>
            <p className="text-[11px] max-w-2xl mx-auto" style={{ color: "rgba(161,161,170,0.6)" }}>
              Polynovea execution strategy. All campaigns are created and run by Polynovea — review
              metrics post-campaign.
            </p>
          </footer>
        </div>
      </main>
    </div>
  );
}
