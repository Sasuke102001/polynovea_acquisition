import Link from "next/link";
import { getOverview, type FitnessDimension } from "@/lib/api";
import ScoreRing from "@/components/ScoreRing";

// ─── Radar SVG (server component — pure math, no client JS needed) ────────────

function FitnessRadar({ dimensions }: { dimensions: FitnessDimension[] }) {
  const cx = 100, cy = 100, maxR = 72;
  const FLOOR = 0.05;  // visual minimum radius — prevents all points at dead centre
  const n = dimensions.length;
  const startAngle = -Math.PI / 2;

  const toPoint = (angle: number, r: number): [number, number] => [
    cx + r * Math.cos(angle),
    cy + r * Math.sin(angle),
  ];

  const axes = dimensions.map((dim, i) => ({
    ...dim,
    angle: startAngle + (i * 2 * Math.PI) / n,
  }));

  const gridLevels = [0.25, 0.5, 0.75, 1.0];

  const polyPts = (level: number) =>
    axes
      .map((a) => {
        const [x, y] = toPoint(a.angle, maxR * level);
        return `${x.toFixed(1)},${y.toFixed(1)}`;
      })
      .join(" ");

  // Apply visual floor — score stays truthful, polygon stays readable
  const dataPoints = axes.map((a) =>
    toPoint(a.angle, maxR * Math.max(Math.min(a.score, 1), FLOOR)),
  );
  const dataPoly = dataPoints.map(([x, y]) => `${x.toFixed(1)},${y.toFixed(1)}`).join(" ");

  // LOW_SIGNAL watermark: ≥3 dimensions have no meaningful data
  const lowSignalCount = dimensions.filter((d) => d.score < 0.05).length;
  const showLowSignal = lowSignalCount >= 3;

  return (
    <svg viewBox="0 0 200 200" className="w-full max-w-[220px] h-auto mx-auto">
      {/* Grid rings */}
      {gridLevels.map((level, i) => (
        <polygon
          key={i}
          points={polyPts(level)}
          fill="none"
          stroke="#27272a"
          strokeWidth="1"
        />
      ))}

      {/* Axis lines */}
      {axes.map((a, i) => {
        const [ex, ey] = toPoint(a.angle, maxR);
        return (
          <line
            key={i}
            x1={cx}
            y1={cy}
            x2={ex.toFixed(1)}
            y2={ey.toFixed(1)}
            stroke="#27272a"
            strokeWidth="1"
          />
        );
      })}

      {/* LOW SIGNAL watermark */}
      {showLowSignal && (
        <text
          x="100"
          y="100"
          fill="rgba(255,255,255,0.07)"
          fontSize="13"
          textAnchor="middle"
          dominantBaseline="middle"
          fontWeight="bold"
          letterSpacing="2"
          transform="rotate(-30, 100, 100)"
        >
          LOW SIGNAL
        </text>
      )}

      {/* Data polygon */}
      <polygon
        points={dataPoly}
        fill="rgba(230,211,163,0.15)"
        stroke="#E6D3A3"
        strokeWidth="1.5"
      />

      {/* Data points */}
      {dataPoints.map(([x, y], i) => (
        <circle key={i} cx={x.toFixed(1)} cy={y.toFixed(1)} r="3" fill="#E6D3A3" />
      ))}

      {/* Labels — label + score on each axis regardless of score value */}
      {axes.map((a, i) => {
        const labelR = maxR + 28;
        const [lx, ly] = toPoint(a.angle, labelR);
        return (
          <g key={i}>
            <text
              x={lx.toFixed(1)}
              y={(ly - 5).toFixed(1)}
              fill="#cec6b7"
              fontSize="7.5"
              textAnchor="middle"
              dominantBaseline="middle"
            >
              {a.label}
            </text>
            <text
              x={lx.toFixed(1)}
              y={(ly + 6).toFixed(1)}
              fill={a.score < 0.05 ? "#555566" : "#e6d3a3"}
              fontSize="8"
              textAnchor="middle"
              fontFamily="JetBrains Mono, monospace"
            >
              {a.score.toFixed(2)}
            </text>
          </g>
        );
      })}
    </svg>
  );
}

// ─── Tab bar ────────────────────────────────────────────────────────────────

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
            tab.label === "Overview"
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

// ─── Page ────────────────────────────────────────────────────────────────────

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
      <div className="p-margin text-error font-body-sm text-body-sm">
        Failed to load venue overview. Make sure the backend is running on port 8000.
      </div>
    );
  }

  const { venue, fitness_radar, customer_profile, health_score, working_for_you, gaps_to_close } = data;

  return (
    <div className="p-margin flex flex-col gap-lg max-w-[1400px] w-full mx-auto">
      {/* ── Venue header ── */}
      <div className="flex flex-col gap-xs border-b border-outline-variant pb-md">
        <div className="flex items-baseline gap-sm flex-wrap">
          <h2 className="text-headline-lg font-headline-lg text-primary-container font-bold">
            {venue.name}
          </h2>
          <div className="flex items-center gap-xs text-on-surface-variant">
            <span className="material-symbols-outlined text-[16px]">location_on</span>
            <span className="text-body-sm font-body-sm">
              {venue.area}, {venue.city}
            </span>
          </div>
        </div>

        {/* Venue type chips */}
        {venue.types.length > 0 && (
          <div className="flex flex-wrap gap-xs">
            {venue.types.map((t) => (
              <span
                key={t}
                className="inline-flex items-center px-xs py-[2px] rounded font-label-sm text-label-sm uppercase bg-primary-container/10 text-primary-container border border-primary-container/20"
              >
                {t}
              </span>
            ))}
          </div>
        )}

        <VenueTabs venueId={id} />
      </div>

      {/* ── Bento grid: Radar | Customers | Health ── */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-md">
        {/* Col 1 — Fitness Radar */}
        <div className="lg:col-span-4 bg-surface border border-outline-variant rounded flex flex-col p-md">
          <div className="flex justify-between items-center mb-md pb-xs border-b border-outline-variant">
            <h3 className="text-label-md font-label-md text-on-surface tracking-wide uppercase">
              Fitness Profile
            </h3>
            <span className="material-symbols-outlined text-outline text-[18px]">radar</span>
          </div>
          <div className="flex-1 flex items-center justify-center">
            <FitnessRadar dimensions={fitness_radar.dimensions} />
          </div>
        </div>

        {/* Col 2 — Your Customers */}
        <div className="lg:col-span-4 bg-surface border border-outline-variant rounded flex flex-col p-md">
          <div className="flex justify-between items-center mb-md pb-xs border-b border-outline-variant">
            <h3 className="text-label-md font-label-md text-on-surface tracking-wide uppercase">
              Your Customers
            </h3>
            <span className="material-symbols-outlined text-secondary text-[18px]">group_add</span>
          </div>

          {/* Top segments — up to 3, rank-3 shown as "Emerging" if weak signal */}
          <div className="flex flex-col gap-sm mb-md">
            {customer_profile.top_segments.map((seg, i) => {
              const isWeak = i === 2 && seg.alignment_pct < 15;
              const rankLabel =
                i === 0 ? "Primary Segment"
                : i === 1 ? "Secondary Segment"
                : seg.alignment_pct === 0 ? "Emerging Signal"
                : "Tertiary Signal";
              return (
                <div
                  key={seg.segment_id}
                  className={`flex flex-col border-b border-surface-variant pb-xs gap-[6px] ${isWeak ? "opacity-55" : ""}`}
                >
                  <div className="flex justify-between items-start">
                    <div>
                      <span className={`text-label-sm font-label-sm ${i === 2 ? "text-outline/60 italic" : "text-outline"}`}>
                        {rankLabel}
                      </span>
                      <div className="text-body-md font-body-md text-on-surface">
                        {seg.segment_name}
                      </div>
                      <div className="text-[11px] text-on-surface-variant mt-0.5">
                        {seg.demographic_label}
                      </div>
                    </div>
                    <span className={`text-data-mono font-data-mono mt-5 ${isWeak ? "text-outline/60" : "text-secondary"}`}>
                      {seg.alignment_pct}%
                    </span>
                  </div>
                  {seg.archetypes.length > 0 && (
                    <div className="flex flex-wrap gap-[6px]">
                      {seg.archetypes.slice(0, 2).map((a) => (
                        <span
                          key={a.name}
                          className={`px-2 py-0.5 rounded text-[10px] font-data-mono ${isWeak ? "bg-[#7C3AED]/20 text-[#7C3AED]/60 border border-[#7C3AED]/20" : "bg-[#7C3AED] text-white"}`}
                          title={a.demographic_label}
                        >
                          {a.name}
                        </span>
                      ))}
                    </div>
                  )}
                </div>
              );
            })}
          </div>

          {/* Archetype distribution */}
          <div className="mt-auto">
            <span className="text-label-sm font-label-sm text-outline mb-sm block">
              Archetype Distribution
            </span>
            <div className="flex flex-col gap-xs">
              {customer_profile.archetype_distribution.slice(0, 4).map((arc) => (
                <div key={arc.name}>
                  <div className="flex justify-between items-start text-[11px] font-data-mono mb-1 text-on-surface-variant">
                    <div className="flex flex-col">
                      <span className="text-on-surface">{arc.name}</span>
                      <span className="text-[10px]">{arc.demographic_label}</span>
                    </div>
                    <span>{arc.prevalence_pct}%</span>
                  </div>
                  <div className="h-1 w-full bg-surface-container-highest rounded overflow-hidden">
                    <div
                      className="h-full bg-secondary"
                      style={{ width: `${arc.prevalence_pct}%`, opacity: 0.85 }}
                    />
                  </div>
                </div>
              ))}
            </div>
          </div>
        </div>

        {/* Col 3 — Venue Health */}
        <div className="lg:col-span-4 bg-surface border border-outline-variant rounded flex flex-col p-md relative overflow-hidden">
          {/* AI pulse dot */}
          <div className="absolute top-md right-md flex items-center justify-center w-6 h-6 rounded-full bg-secondary-container/20 border border-secondary-container">
            <div className="w-1.5 h-1.5 rounded-full bg-secondary animate-pulse" />
          </div>

          <div className="mb-md pb-xs border-b border-outline-variant flex items-center justify-between">
            <h3 className="text-label-md font-label-md text-on-surface tracking-wide uppercase">
              Venue Signal Score
            </h3>
            {health_score.data_confidence && (
              <span
                className={`text-[9px] font-data-mono px-xs py-[1px] rounded border uppercase tracking-wider ${
                  health_score.data_confidence === "HIGH"
                    ? "text-signal-positive border-signal-positive/40 bg-signal-positive/10"
                    : health_score.data_confidence === "MED"
                    ? "text-primary-container border-primary-container/40 bg-primary-container/10"
                    : "text-signal-risk border-signal-risk/40 bg-signal-risk/10"
                }`}
                title="Data confidence: how many fitness dimensions have signal"
              >
                {health_score.data_confidence} DATA
              </span>
            )}
          </div>

          <div className="flex-1 flex flex-col items-center justify-center py-sm">
            {/* Large score ring */}
            <div className="relative w-32 h-32 flex items-center justify-center mb-md">
              <svg className="w-full h-full transform -rotate-90" viewBox="0 0 100 100">
                <circle cx="50" cy="50" fill="none" r="45" stroke="#27272a" strokeWidth="4" />
                <circle
                  cx="50"
                  cy="50"
                  fill="none"
                  r="45"
                  stroke="#E6D3A3"
                  strokeDasharray="282.7"
                  strokeDashoffset={(282.7 * (1 - health_score.score / 100)).toFixed(1)}
                  strokeWidth="4"
                  className="transition-all duration-1000"
                />
              </svg>
              <div className="absolute flex flex-col items-center">
                <span className="text-display-lg font-display-lg text-primary-container leading-none">
                  {health_score.score}
                </span>
                <span className="text-label-sm font-label-sm text-outline">/100</span>
              </div>
            </div>

            {/* Component scores */}
            <div className="w-full grid grid-cols-2 gap-sm text-center border-t border-surface-variant pt-sm">
              <div className="flex flex-col">
                <span className="text-[10px] font-data-mono text-outline mb-1">Operational Q.</span>
                <span className="text-body-md font-data-mono text-on-surface border border-outline-variant bg-surface-container-low px-2 py-1 rounded">
                  {health_score.operational_quality.toFixed(2)}
                </span>
              </div>
              <div className="flex flex-col">
                <span className="text-[10px] font-data-mono text-outline mb-1">Retention Str.</span>
                <span className="text-body-md font-data-mono text-secondary border border-outline-variant bg-surface-container-low px-2 py-1 rounded">
                  {health_score.retention_strength.toFixed(2)}
                </span>
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* ── Working For You / Gaps To Close ── */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-md">
        {/* Working For You */}
        <div className="bg-surface border-t-2 border-signal-positive border-x border-b border-x-surface-variant border-b-surface-variant rounded flex flex-col p-md">
          <div className="flex items-center gap-sm mb-md pb-xs border-b border-surface-variant">
            <span className="material-symbols-outlined text-signal-positive text-[18px]">trending_up</span>
            <h3 className="text-label-md font-label-md text-on-surface tracking-wide uppercase">
              Working For You
            </h3>
          </div>
          <div className="flex flex-col gap-sm">
            {working_for_you.map((card) => (
              <div
                key={card.title}
                className="bg-surface-container-low border border-surface-variant p-sm flex items-start gap-sm"
              >
                <span className="material-symbols-outlined text-primary-container text-[18px] mt-0.5 flex-shrink-0">
                  check_circle
                </span>
                <div>
                  <h4 className="text-label-sm font-label-sm text-on-surface">{card.title}</h4>
                  <p className="text-body-sm font-body-sm text-on-surface-variant mt-1">
                    {card.subtitle}
                  </p>
                </div>
              </div>
            ))}
          </div>
        </div>

        {/* Gaps To Close */}
        <div className="bg-surface border-t-2 border-error border-x border-b border-x-surface-variant border-b-surface-variant rounded flex flex-col p-md">
          <div className="flex items-center gap-sm mb-md pb-xs border-b border-surface-variant">
            <span className="material-symbols-outlined text-error text-[18px]">warning</span>
            <h3 className="text-label-md font-label-md text-on-surface tracking-wide uppercase">
              Gaps To Close
            </h3>
          </div>
          <div className="flex flex-col gap-sm">
            {gaps_to_close.map((card) => (
              <div
                key={card.title}
                className="bg-surface-container-low border border-surface-variant p-sm flex items-start gap-sm"
              >
                <span className="material-symbols-outlined text-error text-[18px] mt-0.5 flex-shrink-0">
                  trending_down
                </span>
                <div>
                  <h4 className="text-label-sm font-label-sm text-on-surface">{card.title}</h4>
                  <p className="text-body-sm font-body-sm text-on-surface-variant mt-1">
                    {card.subtitle}
                  </p>
                  {card.priority_tier && (
                    <span className="inline-block mt-1 text-[9px] font-label-sm px-xs py-[1px] rounded border border-signal-risk/40 text-signal-risk uppercase">
                      {card.priority_tier}
                    </span>
                  )}
                </div>
              </div>
            ))}
          </div>
        </div>
      </div>
    </div>
  );
}
