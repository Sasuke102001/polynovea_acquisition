import Link from "next/link";
import { getOverview } from "@/lib/api";
import ScoreOrb from "@/components/ScoreOrb";
import Tilt3DCard from "@/components/Tilt3DCard";

// ─── Fitness key → orb label mapping ─────────────────────────────────────────

const ORB_META: Record<string, string> = {
  social_dwell:  "Social Dwell",
  destination:   "Destination",
  retention:     "Retention",
  repeat:        "Repeat Habit",
  office_lunch:  "Office Lunch",
  operational:   "Operational",
};

// ─── Tab bar (server-safe) ────────────────────────────────────────────────────

function VenueTabs({ venueId }: { venueId: string }) {
  const tabs = [
    { label: "Overview",    href: `/venues/${venueId}` },
    { label: "Competitors", href: `/venues/${venueId}/competitors` },
    { label: "Transform",   href: `/venues/${venueId}/transform` },
    { label: "Marketing",   href: `/venues/${venueId}/marketing` },
    { label: "Campaign",    href: `/venues/${venueId}/campaign` },
    { label: "Audience",    href: `/venues/${venueId}/audience` },
  ];

  return (
    <div className="flex gap-6 overflow-x-auto no-scrollbar pb-1" style={{ borderBottom: "1px solid rgba(39,39,42,0.6)" }}>
      {tabs.map((t) => (
        <Link
          key={t.label}
          href={t.href}
          className="whitespace-nowrap pb-2 text-xs font-medium tracking-wider uppercase transition-colors"
          style={{
            fontFamily: "'JetBrains Mono', monospace",
            color: t.label === "Overview" ? "#E6D3A3" : "#71717A",
            borderBottom: t.label === "Overview" ? "2px solid #E6D3A3" : "2px solid transparent",
          }}
        >
          {t.label}
        </Link>
      ))}
    </div>
  );
}

// ─── Signal dot ──────────────────────────────────────────────────────────────

function SignalDot({ score }: { score: number }) {
  const color = score >= 0.6 ? "#10B981" : score >= 0.35 ? "#F59E0B" : "#FB7185";
  return (
    <span
      className="inline-block w-2 h-2 rounded-full mt-1.5 flex-shrink-0"
      style={{ background: color, boxShadow: `0 0 6px ${color}` }}
    />
  );
}

// ─── Page ─────────────────────────────────────────────────────────────────────

export default async function OverviewPage({
  params,
}: {
  params: Promise<{ id: string }>;
}) {
  const { id } = await params;

  let data;
  try {
    data = await getOverview(id);
  } catch {
    return (
      <div className="p-8 text-xs font-mono" style={{ color: "#FB7185" }}>
        Failed to load venue overview. Make sure the backend is running on port 8000.
      </div>
    );
  }

  const { venue, fitness_radar, customer_profile, health_score, working_for_you, gaps_to_close } = data;

  // Use all dimensions from API, with canonical label override where available
  const orbs = fitness_radar.dimensions.map((d) => ({
    key: d.key,
    label: ORB_META[d.key] ?? d.label,
    score: d.score,
  }));

  // All segments (up to 3)
  const primary = customer_profile.top_segments[0];
  const secondarySegments = customer_profile.top_segments.slice(1, 3);

  return (
    <div className="p-6 md:p-8 flex flex-col gap-8 max-w-[1400px] w-full mx-auto cin-stagger">

      {/* ── Venue header ── */}
      <div className="flex flex-col gap-3">
        <div className="flex items-baseline gap-3 flex-wrap">
          <h1
            className="text-3xl md:text-4xl font-bold tracking-tight gold-glow"
            style={{ fontFamily: "'Clash Display', 'Inter', sans-serif" }}
          >
            {venue.name}
          </h1>
          <span className="text-sm" style={{ color: "#71717A" }}>
            {venue.area}, {venue.city}
          </span>
        </div>

        {venue.types.length > 0 && (
          <div className="flex flex-wrap gap-2">
            {venue.types.map((t) => (
              <span
                key={t}
                className="px-2 py-0.5 text-[9px] font-bold uppercase tracking-widest rounded"
                style={{
                  fontFamily: "'JetBrains Mono', monospace",
                  background: "rgba(230,211,163,0.08)",
                  border: "1px solid rgba(230,211,163,0.18)",
                  color: "#A1A1AA",
                }}
              >
                {t}
              </span>
            ))}
          </div>
        )}

        <VenueTabs venueId={id} />
      </div>

      {/* ── Main grid ── */}
      <div className="grid grid-cols-1 lg:grid-cols-5 gap-6">

        {/* Left: 6 score orbs */}
        <div
          className="lg:col-span-3 flex flex-col gap-5"
          style={{ perspective: "1200px", transformStyle: "preserve-3d" }}
        >
          <h2 className="text-sm font-bold tracking-widest uppercase" style={{ fontFamily: "'JetBrains Mono', monospace", color: "#A1A1AA" }}>
            Venue Intelligence Scores
          </h2>

          <div
            className="grid grid-cols-3 gap-6 p-6 rounded-xl"
            style={{
              background: "rgba(24,24,27,0.5)",
              backdropFilter: "blur(16px)",
              border: "1px solid rgba(39,39,42,0.6)",
              boxShadow: "0 24px 48px -12px rgba(0,0,0,0.7)",
            }}
          >
            {orbs.map((o) => (
              <ScoreOrb key={o.key} label={o.label} score={o.score} />
            ))}
          </div>

          {/* Working For You + Gaps To Close */}
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-4 mt-2">
            {/* Working For You */}
            <Tilt3DCard
              className="cin-card rounded-xl p-5 flex flex-col gap-3"
              intensity={6}
            >
              <div className="flex items-center gap-2 pb-3" style={{ borderBottom: "1px solid rgba(16,185,129,0.2)" }}>
                <span className="material-symbols-outlined text-[16px] sig-emerald">trending_up</span>
                <span className="text-[10px] font-bold tracking-widest uppercase" style={{ fontFamily: "'JetBrains Mono', monospace", color: "#10B981" }}>
                  Working For You
                </span>
              </div>
              <div className="flex flex-col gap-3">
                {working_for_you.map((card) => (
                  <div key={card.title} className="flex items-start gap-3">
                    <span className="material-symbols-outlined text-[14px] mt-0.5 flex-shrink-0 sig-emerald">check_circle</span>
                    <div>
                      <p className="text-xs font-medium" style={{ color: "#F5F5F5" }}>{card.title}</p>
                      <p className="text-[11px] mt-0.5" style={{ color: "#71717A" }}>{card.subtitle}</p>
                    </div>
                  </div>
                ))}
              </div>
            </Tilt3DCard>

            {/* Gaps To Close */}
            <Tilt3DCard
              className="cin-card rounded-xl p-5 flex flex-col gap-3"
              intensity={6}
            >
              <div className="flex items-center gap-2 pb-3" style={{ borderBottom: "1px solid rgba(251,113,133,0.2)" }}>
                <span className="material-symbols-outlined text-[16px] sig-coral">warning</span>
                <span className="text-[10px] font-bold tracking-widest uppercase" style={{ fontFamily: "'JetBrains Mono', monospace", color: "#FB7185" }}>
                  Gaps To Close
                </span>
              </div>
              <div className="flex flex-col gap-3">
                {gaps_to_close.map((card) => (
                  <div key={card.title} className="flex items-start gap-3">
                    <span className="material-symbols-outlined text-[14px] mt-0.5 flex-shrink-0 sig-coral">trending_down</span>
                    <div>
                      <p className="text-xs font-medium" style={{ color: "#F5F5F5" }}>{card.title}</p>
                      <p className="text-[11px] mt-0.5" style={{ color: "#71717A" }}>{card.subtitle}</p>
                      {card.priority_tier && (
                        <span
                          className="inline-block mt-1 text-[8px] font-bold px-1.5 py-0.5 rounded uppercase tracking-widest"
                          style={{ fontFamily: "'JetBrains Mono', monospace", color: "#FB7185", border: "1px solid rgba(251,113,133,0.3)", background: "rgba(251,113,133,0.08)" }}
                        >
                          {card.priority_tier}
                        </span>
                      )}
                    </div>
                  </div>
                ))}
              </div>
            </Tilt3DCard>
          </div>
        </div>

        {/* Right: Primary segment + Venue Signal + archetype distribution */}
        <div className="lg:col-span-2 flex flex-col gap-5">

          {/* Customer Segments card — primary + secondary + tertiary */}
          <Tilt3DCard className="cin-card rounded-xl p-5 relative overflow-hidden group" intensity={6}>
            <div
              className="absolute top-3 right-3 opacity-8 group-hover:opacity-15 transition-opacity"
            >
              <span className="material-symbols-outlined text-[48px]" style={{ color: "#E6D3A3" }}>groups</span>
            </div>
            <div className="text-[9px] font-bold uppercase tracking-widest mb-4" style={{ fontFamily: "'JetBrains Mono', monospace", color: "#71717A" }}>
              Customer Segments
            </div>
            {primary ? (
              <div className="flex flex-col gap-3">
                {/* Primary */}
                <div className="pb-3" style={{ borderBottom: "1px solid rgba(39,39,42,0.6)" }}>
                  <div className="text-[9px] uppercase tracking-widest mb-1" style={{ fontFamily: "'JetBrains Mono', monospace", color: "#9A8F6A" }}>Primary</div>
                  <div className="flex items-start justify-between gap-2">
                    <div className="flex-1">
                      <div className="text-base font-bold" style={{ fontFamily: "'Clash Display', 'Inter', sans-serif", color: "#F5F5F5" }}>
                        {primary.segment_name}
                      </div>
                      {primary.demographic_label && (
                        <p className="text-[10px] mt-0.5" style={{ color: "#71717A" }}>{primary.demographic_label}</p>
                      )}
                      {primary.archetypes.length > 0 && (
                        <div className="flex flex-wrap gap-1.5 mt-2">
                          {primary.archetypes.slice(0, 2).map((a) => (
                            <span key={a.name} className="px-1.5 py-0.5 text-[8px] font-bold rounded" style={{ fontFamily: "'JetBrains Mono', monospace", background: "rgba(124,58,237,0.2)", border: "1px solid rgba(124,58,237,0.3)", color: "#c4b5fd" }}>
                              {a.name}
                            </span>
                          ))}
                        </div>
                      )}
                    </div>
                    <span className="text-xl font-mono font-bold flex-shrink-0 sig-emerald">{primary.alignment_pct}%</span>
                  </div>
                </div>

                {/* Secondary / Tertiary */}
                {secondarySegments.map((seg, i) => {
                  const isWeak = seg.alignment_pct < 15;
                  return (
                    <div key={seg.segment_id} className="flex items-start justify-between gap-2" style={{ opacity: isWeak ? 0.5 : 1 }}>
                      <div className="flex-1">
                        <div className="text-[9px] uppercase tracking-widest mb-0.5" style={{ fontFamily: "'JetBrains Mono', monospace", color: "#71717A" }}>
                          {i === 0 ? "Secondary" : "Tertiary"}
                        </div>
                        <div className="text-sm font-medium" style={{ color: "#A1A1AA" }}>{seg.segment_name}</div>
                        {seg.demographic_label && (
                          <p className="text-[10px]" style={{ color: "#52525B" }}>{seg.demographic_label}</p>
                        )}
                      </div>
                      <span className="text-sm font-mono font-bold flex-shrink-0" style={{ color: "#A1A1AA" }}>{seg.alignment_pct}%</span>
                    </div>
                  );
                })}
              </div>
            ) : (
              <div className="text-xs" style={{ color: "#71717A" }}>No segment data available</div>
            )}
          </Tilt3DCard>

          {/* Venue Signal Score */}
          <Tilt3DCard className="cin-card rounded-xl p-6 relative overflow-hidden" intensity={6}>
            {/* Gradient accent line */}
            <div
              className="absolute left-0 top-0 bottom-0 w-0.5 rounded-full"
              style={{ background: "linear-gradient(to bottom, #10B981, #F59E0B, #FB7185)" }}
            />
            <div className="pl-3">
              <div className="flex items-center justify-between mb-4">
                <div className="text-[10px] font-bold uppercase tracking-widest" style={{ fontFamily: "'JetBrains Mono', monospace", color: "#71717A" }}>
                  Venue Signal Score
                </div>
                {health_score.data_confidence && (
                  <span
                    className="text-[8px] font-bold px-1.5 py-0.5 rounded uppercase tracking-widest"
                    style={{
                      fontFamily: "'JetBrains Mono', monospace",
                      color: health_score.data_confidence === "HIGH" ? "#10B981" : health_score.data_confidence === "MED" ? "#F59E0B" : "#FB7185",
                      border: `1px solid ${health_score.data_confidence === "HIGH" ? "rgba(16,185,129,0.3)" : health_score.data_confidence === "MED" ? "rgba(245,158,11,0.3)" : "rgba(251,113,133,0.3)"}`,
                      background: `${health_score.data_confidence === "HIGH" ? "rgba(16,185,129,0.08)" : health_score.data_confidence === "MED" ? "rgba(245,158,11,0.08)" : "rgba(251,113,133,0.08)"}`,
                    }}
                  >
                    {health_score.data_confidence} DATA
                  </span>
                )}
              </div>

              {/* Score ring */}
              <div className="flex items-center gap-5">
                <div className="relative w-24 h-24 flex-shrink-0">
                  <svg className="w-full h-full" viewBox="0 0 100 100" style={{ transform: "rotate(-90deg)" }}>
                    <circle cx="50" cy="50" r="42" fill="none" stroke="rgba(39,39,42,0.8)" strokeWidth="5" />
                    <circle
                      cx="50"
                      cy="50"
                      r="42"
                      fill="none"
                      stroke="#E6D3A3"
                      strokeDasharray={`${(263.9 * health_score.score / 100).toFixed(1)} 263.9`}
                      strokeWidth="5"
                      strokeLinecap="round"
                      style={{ filter: "drop-shadow(0 0 6px rgba(230,211,163,0.5))", transition: "stroke-dasharray 1.2s ease" }}
                    />
                  </svg>
                  <div className="absolute inset-0 flex flex-col items-center justify-center">
                    <span className="text-2xl font-mono font-bold gold-glow">{health_score.score}</span>
                    <span className="text-[9px]" style={{ color: "#71717A" }}>/100</span>
                  </div>
                </div>

                <div className="flex flex-col gap-3">
                  <div>
                    <div className="text-[9px] uppercase tracking-widest mb-1" style={{ fontFamily: "'JetBrains Mono', monospace", color: "#71717A" }}>Operational Q.</div>
                    <div className="text-lg font-mono font-bold" style={{ color: "#F5F5F5" }}>{health_score.operational_quality.toFixed(2)}</div>
                  </div>
                  <div>
                    <div className="text-[9px] uppercase tracking-widest mb-1" style={{ fontFamily: "'JetBrains Mono', monospace", color: "#71717A" }}>Retention Str.</div>
                    <div className="text-lg font-mono font-bold sig-emerald">{health_score.retention_strength.toFixed(2)}</div>
                  </div>
                </div>
              </div>
            </div>
          </Tilt3DCard>

          {/* Archetype Distribution */}
          <Tilt3DCard className="cin-card rounded-xl p-5 flex flex-col gap-4" intensity={5}>
            <div className="text-[10px] font-bold uppercase tracking-widest" style={{ fontFamily: "'JetBrains Mono', monospace", color: "#71717A" }}>
              Archetype Distribution
            </div>
            <div className="flex flex-col gap-3">
              {customer_profile.archetype_distribution.slice(0, 4).map((arc) => (
                <div key={arc.name}>
                  <div className="flex justify-between items-baseline text-[11px] mb-1.5">
                    <div>
                      <span className="font-medium" style={{ color: "#F5F5F5" }}>{arc.name}</span>
                      {arc.demographic_label && (
                        <span className="ml-1.5 text-[10px]" style={{ color: "#71717A" }}>{arc.demographic_label}</span>
                      )}
                    </div>
                    <span className="font-mono" style={{ color: "#A1A1AA" }}>{arc.prevalence_pct}%</span>
                  </div>
                  <div className="h-1 w-full rounded-full overflow-hidden" style={{ background: "rgba(39,39,42,0.8)" }}>
                    <div
                      className="h-full rounded-full"
                      style={{
                        width: `${arc.prevalence_pct}%`,
                        background: "linear-gradient(90deg, rgba(230,211,163,0.6), rgba(230,211,163,0.3))",
                        boxShadow: "0 0 6px rgba(230,211,163,0.2)",
                        transition: "width 1s ease",
                      }}
                    />
                  </div>
                </div>
              ))}
            </div>
          </Tilt3DCard>

          {/* Live Operational Signals — from gaps/working signals */}
          <Tilt3DCard className="cin-card rounded-xl p-5 relative overflow-hidden" intensity={5}>
            <div
              className="absolute left-0 top-0 bottom-0 w-0.5"
              style={{ background: "linear-gradient(to bottom, #10B981, #F59E0B, #FB7185)" }}
            />
            <div className="pl-4">
              <div className="flex items-center justify-between mb-4">
                <span className="text-[10px] font-bold uppercase tracking-widest" style={{ fontFamily: "'JetBrains Mono', monospace", color: "#A1A1AA" }}>
                  Live Intelligence Signals
                </span>
                <span className="material-symbols-outlined text-[16px] animate-pulse" style={{ color: "#E6D3A3" }}>auto_awesome</span>
              </div>
              <ul className="flex flex-col gap-3">
                {[...working_for_you.slice(0, 2), ...gaps_to_close.slice(0, 1)].map((item, i) => {
                  const isGap = i >= working_for_you.slice(0, 2).length;
                  return (
                    <li key={item.title} className="flex items-start gap-3">
                      <SignalDot score={isGap ? 0.2 : 0.8} />
                      <div>
                        <p className="text-xs font-medium" style={{ color: "#F5F5F5" }}>{item.title}</p>
                        <p className="text-[11px] mt-0.5" style={{ color: "#71717A" }}>{item.subtitle}</p>
                      </div>
                    </li>
                  );
                })}
              </ul>
            </div>
          </Tilt3DCard>
        </div>
      </div>
    </div>
  );
}
