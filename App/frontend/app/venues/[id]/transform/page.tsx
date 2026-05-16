"use client";

import { useState, useEffect, use } from "react";
import Link from "next/link";
import {
  getTransform,
  type TransformResponse,
  type DeltaBar,
  type SimilarVenueCard,
} from "@/lib/api";

const LIMIT = 40;

// ─── Tier config ──────────────────────────────────────────────────────────────

type Tier = "role_model" | "transition" | "pure_target";

const TIER_CONFIG: Record<Tier, { label: string; color: string; borderColor: string }> = {
  role_model:  { label: "ROLE MODEL",   color: "#E6D3A3", borderColor: "#E6D3A3" },
  transition:  { label: "TRANSITION",   color: "#F59E0B", borderColor: "#F59E0B" },
  pure_target: { label: "PURE TARGET",  color: "#8b8b9e", borderColor: "#4b4b5e" },
};

// ─── Helpers ─────────────────────────────────────────────────────────────────

function deltaColor(delta: number): string {
  if (delta > 0.05) return "#34d399";
  if (delta < -0.05) return "#f87171";
  return "#8b8b9e";
}

function deltaLabel(delta: number): string {
  if (delta > 0.05) return `+${delta.toFixed(2)} up`;
  if (delta < -0.05) return `${delta.toFixed(2)} dn`;
  return "Equal";
}

// ─── Delta metric row ─────────────────────────────────────────────────────────

function DeltaMetric({ bar }: { bar: DeltaBar }) {
  const color = deltaColor(bar.delta);
  return (
    <div className="flex flex-col gap-[2px]">
      <div className="flex justify-between items-center">
        <span className="text-label-sm font-label-sm text-on-surface-variant">{bar.label}</span>
        <span className="text-data-mono font-data-mono text-[12px]" style={{ color }}>
          {deltaLabel(bar.delta)}
        </span>
      </div>
      <p className="text-[11px] text-on-surface-variant/80 leading-tight">{bar.client_statement}</p>
    </div>
  );
}

// ─── Similar venue card (with tier badge) ────────────────────────────────────

function SimilarCard({
  venue,
}: {
  venue: SimilarVenueCard;
}) {
  const bars = [...venue.delta_bars].sort(
    (a, b) => Math.abs(b.delta) - Math.abs(a.delta)
  );
  const tier = venue.tier as Tier | null | undefined;
  const tierConf = tier ? TIER_CONFIG[tier] : null;

  return (
    <div className="w-72 flex-shrink-0 flex flex-col gap-sm">
      <div className="bg-surface border border-outline-variant p-md flex flex-col gap-sm h-full relative">
        {/* Tier badge */}
        {tierConf && (
          <div
            className="absolute top-0 right-0 text-[9px] font-bold uppercase tracking-wider px-xs py-[2px] rounded-bl"
            style={{
              color: "#0d0d11",
              backgroundColor: tierConf.color,
            }}
          >
            {tierConf.label}
          </div>
        )}
        {/* Left accent stripe */}
        {tier === "role_model" && (
          <div className="absolute top-0 left-0 w-[3px] h-full bg-[#E6D3A3] rounded-l" />
        )}

        <h4 className="text-headline-md font-headline-md text-on-surface truncate pr-xl">
          {venue.name}
        </h4>

        <div className="flex flex-wrap gap-xs">
          {venue.types.slice(0, 2).map((t) => (
            <span
              key={t}
              className="text-label-sm font-label-sm text-primary-container px-xs py-[2px] bg-primary-container/10 rounded uppercase"
            >
              {t}
            </span>
          ))}
        </div>

        <div className="flex flex-wrap gap-xs">
          {venue.top_archetypes.slice(0, 2).map((a) => (
            <span
              key={a.name}
              className="text-label-sm font-label-sm text-secondary px-xs py-[2px] bg-secondary/10 rounded uppercase"
            >
              {a.name}
            </span>
          ))}
        </div>

        <div className="flex flex-wrap gap-xs mb-sm">
          {venue.top_segments.slice(0, 3).map((s) => (
            <span
              key={s}
              className="text-label-sm font-label-sm text-[#F59E0B] px-xs py-[2px] bg-[#F59E0B]/10 rounded uppercase"
            >
              {s}
            </span>
          ))}
        </div>

        <div className="flex flex-col gap-xs mt-auto pt-sm border-t border-outline-variant/50">
          {bars.map((bar) => (
            <DeltaMetric key={bar.dimension} bar={bar} />
          ))}
        </div>
      </div>
    </div>
  );
}

// ─── Page ────────────────────────────────────────────────────────────────────

const ALL_SEGMENTS = [
  { id: "office_workers", label: "Office Workers" },
  { id: "college_kids",   label: "College Kids" },
  { id: "couples",        label: "Couples" },
  { id: "families",       label: "Families" },
  { id: "premium",        label: "Premium" },
  { id: "solo_diners",    label: "Solo Diners" },
  { id: "working_women",  label: "Working Women" },
];

export default function TransformPage({
  params,
}: {
  params: Promise<{ id: string }>;
}) {
  const { id } = use(params);
  const [selectedSegment, setSelectedSegment] = useState<string | null>(null);
  const [data, setData] = useState<TransformResponse | null>(null);
  const [loading, setLoading] = useState(false);
  const [growthTarget, setGrowthTarget] = useState<string | null>(null);
  const [targetConfirmed, setTargetConfirmed] = useState(false);

  // Read stored growth target from localStorage on mount
  useEffect(() => {
    const stored = localStorage.getItem(`polynovea_target_${id}`);
    if (stored) setGrowthTarget(stored);
  }, [id]);

  // Initial load to get current segments (no target)
  useEffect(() => {
    setLoading(true);
    getTransform(id, undefined, LIMIT, 0)
      .then((d) => {
        setData(d);
        setLoading(false);
      })
      .catch(() => setLoading(false));
  }, [id]);

  // Reload when segment changes
  useEffect(() => {
    if (!selectedSegment) return;
    setLoading(true);
    getTransform(id, selectedSegment, LIMIT, 0)
      .then((d) => { setData(d); setLoading(false); })
      .catch(() => setLoading(false));
  }, [id, selectedSegment]);

  const currentSegmentIds = new Set(
    data?.current_segments.filter((s) => s.is_current).map((s) => s.segment_id) ?? [],
  );

  const selectedLabel = ALL_SEGMENTS.find((s) => s.id === selectedSegment)?.label ?? "";

  function handleSetTarget() {
    if (!selectedSegment) return;
    localStorage.setItem(`polynovea_target_${id}`, selectedSegment);
    setGrowthTarget(selectedSegment);
    setTargetConfirmed(true);
    setTimeout(() => setTargetConfirmed(false), 3000);
  }

  function handleClearTarget() {
    localStorage.removeItem(`polynovea_target_${id}`);
    setGrowthTarget(null);
    setTargetConfirmed(false);
  }

  const growthTargetLabel = ALL_SEGMENTS.find((s) => s.id === growthTarget)?.label;

  return (
    <div className="p-md md:p-margin flex flex-col gap-lg max-w-[1400px] w-full mx-auto">
      {/* ── Venue header / tab bar ── */}
      <div className="flex flex-col gap-xs border-b border-outline-variant pb-md">
        <div className="flex gap-md border-b border-outline-variant mt-sm overflow-x-auto no-scrollbar">
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
                tab.label === "Transform"
                  ? "text-primary border-b-2 border-primary"
                  : "text-on-surface-variant hover:text-primary"
              }`}
            >
              {tab.label}
            </Link>
          ))}
        </div>
      </div>

      {/* ── Target Selector ── */}
      <section className="bg-[#1A1A24] border border-outline-variant p-lg flex flex-col gap-md">
        {/* You currently attract */}
        <div className="flex items-center gap-md flex-wrap">
          <span className="text-body-sm font-body-sm text-on-surface-variant whitespace-nowrap">
            You currently attract:
          </span>
          <div className="flex flex-wrap gap-sm">
            {data?.current_segments
              .filter((s) => s.is_current)
              .map((s) => (
                <span
                  key={s.segment_id}
                  className="px-sm py-xs bg-primary-container/10 border border-primary-container text-primary-container text-label-sm font-label-sm rounded uppercase"
                >
                  {s.segment_name}
                </span>
              ))}
          </div>
        </div>

        <div className="h-px w-full bg-outline-variant/50" />

        {/* Segment selector */}
        <div className="flex flex-col sm:flex-row sm:items-center gap-md flex-wrap">
          <span className="text-body-sm font-body-sm text-on-surface-variant whitespace-nowrap">
            Who do you want to attract?
          </span>
          <div className="flex flex-wrap gap-sm">
            {ALL_SEGMENTS.map((seg) => {
              const isCurrent = currentSegmentIds.has(seg.id);
              const isSelected = selectedSegment === seg.id;

              if (isCurrent) {
                return (
                  <div key={seg.id} className="group relative">
                    <button
                      disabled
                      className="px-sm py-xs border border-primary-container text-primary-container text-label-sm font-label-sm rounded uppercase opacity-40 cursor-not-allowed"
                    >
                      {seg.label}
                    </button>
                    <div className="absolute bottom-full left-1/2 -translate-x-1/2 mb-xs hidden group-hover:block px-xs py-[2px] bg-surface-container-high border border-outline-variant text-label-sm font-label-sm text-on-surface-variant whitespace-nowrap z-10">
                      Already yours
                    </div>
                  </div>
                );
              }

              return (
                <button
                  key={seg.id}
                  onClick={() => setSelectedSegment(isSelected ? null : seg.id)}
                  className={`px-sm py-xs border text-label-sm font-label-sm rounded uppercase transition-colors flex items-center gap-xs ${
                    isSelected
                      ? "bg-secondary border-secondary text-on-secondary"
                      : "border-outline-variant text-secondary hover:bg-surface-variant"
                  }`}
                >
                  {isSelected && (
                    <span className="material-symbols-outlined text-[14px]">check</span>
                  )}
                  {seg.label}
                </button>
              );
            })}
          </div>
        </div>
      </section>

      {/* ── Results ── */}
      {selectedSegment && (
        <>
          {loading && (
            <div className="text-center text-on-surface-variant py-xl">
              <span className="material-symbols-outlined text-primary animate-spin inline-block">
                progress_activity
              </span>
            </div>
          )}

          {!loading && data && (
            <>
              <div className="flex items-center justify-between flex-wrap gap-md">
                <h3 className="text-headline-md font-headline-md text-on-surface">
                  To attract{" "}
                  <span className="text-primary">{selectedLabel}</span>
                  , study these venues
                </h3>

                {/* Set as Target Audience button */}
                {growthTarget !== selectedSegment && (
                  <button
                    onClick={handleSetTarget}
                    className="flex items-center gap-xs px-md py-xs bg-[#7C3AED]/10 border border-[#7C3AED]/40 text-[#7C3AED] text-label-sm font-label-sm rounded uppercase hover:bg-[#7C3AED]/20 transition-colors"
                  >
                    <span className="material-symbols-outlined text-[14px]">flag</span>
                    Set as Growth Target
                  </button>
                )}
                {growthTarget === selectedSegment && (
                  <div className="flex items-center gap-xs px-md py-xs bg-[#7C3AED]/10 border border-[#7C3AED]/40 text-[#7C3AED] text-label-sm font-label-sm rounded">
                    <span className="material-symbols-outlined text-[14px]">check_circle</span>
                    Growth Target Set
                    <button
                      onClick={handleClearTarget}
                      className="ml-sm text-on-surface-variant/60 hover:text-on-surface-variant text-[10px] uppercase"
                    >
                      Clear
                    </button>
                  </div>
                )}
              </div>

              {/* Tier legend */}
              <div className="flex gap-md flex-wrap text-[10px] font-data-mono text-on-surface-variant">
                {(Object.keys(TIER_CONFIG) as Tier[]).map((t) => (
                  <span key={t} className="flex items-center gap-xs">
                    <span
                      className="inline-block w-2 h-2 rounded-sm"
                      style={{ backgroundColor: TIER_CONFIG[t].color }}
                    />
                    {TIER_CONFIG[t].label}
                  </span>
                ))}
              </div>

              {/* Baseline strip */}
              <div className="bg-surface border border-outline-variant px-md py-sm flex items-center gap-md flex-wrap">
                <span className="text-[10px] font-data-mono uppercase tracking-widest text-on-surface-variant flex-shrink-0">
                  Baseline (You)
                </span>
                <div className="flex flex-wrap gap-xs">
                  {data.current_segments.filter((s) => s.is_current).map((s) => (
                    <span
                      key={s.segment_id}
                      className="text-label-sm font-label-sm text-secondary border border-outline-variant px-xs py-[2px] rounded uppercase bg-surface-container-low"
                    >
                      {s.segment_name}
                    </span>
                  ))}
                </div>
                <span className="text-[10px] text-on-surface-variant/40 font-data-mono ml-auto">
                  Delta bars compare each venue to your scores
                </span>
              </div>

              {/* Tier waterfall — grid per tier */}
              <section className="flex flex-col gap-xl">
                {data.similar_venues.length === 0 && (
                  <div className="bg-surface border border-dashed border-outline-variant p-md flex items-center justify-center text-on-surface-variant text-body-sm">
                    No venues found for this segment
                  </div>
                )}

                {(["role_model", "transition", "pure_target"] as Tier[]).map((tier) => {
                  const allVenues = data.similar_venues.filter((sv) => sv.tier === tier);
                  if (!allVenues.length) return null;
                  const venues = allVenues.slice(0, 12);
                  const tierConf = TIER_CONFIG[tier];
                  return (
                    <div key={tier} className="flex flex-col gap-sm">
                      {/* Tier header */}
                      <div className="flex items-center gap-sm border-b border-outline-variant pb-xs">
                        <span
                          className="inline-block w-[10px] h-[10px] rounded-sm flex-shrink-0"
                          style={{ backgroundColor: tierConf.color }}
                        />
                        <span
                          className="text-[11px] font-data-mono uppercase tracking-widest font-bold"
                          style={{ color: tierConf.color }}
                        >
                          {tierConf.label}
                        </span>
                        <span className="text-[10px] text-on-surface-variant/50 font-data-mono">
                          — showing {venues.length} of {allVenues.length}
                        </span>
                      </div>

                      {/* Horizontal scroll */}
                      <div className="overflow-x-auto custom-scrollbar pb-sm">
                        <div className="flex gap-md min-w-max">
                          {venues.map((sv) => (
                            <SimilarCard key={sv.id} venue={sv} />
                          ))}
                        </div>
                      </div>
                    </div>
                  );
                })}
              </section>

              {/* Gap callout */}
              {data.gap_callout && (
                <div className="bg-surface-container-high border-y border-r border-outline-variant border-l-2 border-l-[#F59E0B] p-md flex items-start gap-md">
                  <span className="material-symbols-outlined text-[#F59E0B] mt-[2px] flex-shrink-0">
                    tips_and_updates
                  </span>
                  <p className="text-body-sm font-body-sm text-on-surface max-w-3xl whitespace-pre-line">
                    {data.gap_callout}
                  </p>
                </div>
              )}

              {/* Growth target confirmation banner */}
              {growthTarget === selectedSegment && (
                <div className="bg-[#7C3AED]/10 border border-[#7C3AED]/40 rounded p-md flex items-center justify-between gap-md flex-wrap">
                  <div className="flex items-center gap-sm text-[#C4B5FD] text-body-sm font-body-sm">
                    <span className="material-symbols-outlined text-[18px]">check_circle</span>
                    <span>
                      <span className="font-bold">{growthTargetLabel}</span> set as growth target
                      {targetConfirmed && (
                        <span className="ml-sm text-[#A78BFA] text-[11px]">Saved!</span>
                      )}
                    </span>
                  </div>
                  <Link
                    href={`/venues/${id}/campaign?target=${selectedSegment}`}
                    className="flex items-center gap-xs text-label-sm font-label-sm text-[#7C3AED] border border-[#7C3AED]/50 px-md py-xs rounded hover:bg-[#7C3AED]/20 transition-colors uppercase"
                  >
                    View Campaign Strategy
                    <span className="material-symbols-outlined text-[14px]">arrow_forward</span>
                  </Link>
                </div>
              )}
            </>
          )}
        </>
      )}

      {!selectedSegment && !loading && (
        <div className="text-center text-on-surface-variant py-xl">
          <span className="material-symbols-outlined text-primary text-[48px] mb-md block">
            auto_graph
          </span>
          <p className="font-body-md text-body-md">
            Select a target segment above to see venues you can learn from.
          </p>
          {growthTargetLabel && (
            <p className="mt-sm text-label-sm font-label-sm text-[#C4B5FD]">
              Growth target set:{" "}
              <button
                onClick={() => setSelectedSegment(growthTarget)}
                className="underline hover:text-[#7C3AED] transition-colors"
              >
                {growthTargetLabel}
              </button>
            </p>
          )}
        </div>
      )}
    </div>
  );
}
