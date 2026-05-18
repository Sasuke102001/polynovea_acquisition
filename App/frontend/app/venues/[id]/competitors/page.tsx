"use client";

import { useState, useEffect, useCallback, use } from "react";
import Link from "next/link";
import {
  getCompetitors,
  getCompetitorDeepDive,
  type CompetitorsResponse,
  type CompetitorDeepDive,
  type DeltaBar,
  type FitnessDimension,
  type SimilarVenueCard,
  type ClientVenueCard,
} from "@/lib/api";
import CompetitorDrawer from "@/components/CompetitorDrawer";

const LIMIT = 3;

// ─── Helpers ─────────────────────────────────────────────────────────────────

function deltaColor(delta: number): string {
  if (delta > 0.05) return "#10b981";
  if (delta < -0.05) return "#ef4444";
  return "#8b8b9e";
}

function deltaLabel(delta: number): string {
  if (delta > 0.05) return `+${delta.toFixed(2)} ▲`;
  if (delta < -0.05) return `${delta.toFixed(2)} ▼`;
  return "~ Equal —";
}

function VenueTypeBadge({ label }: { label: string }) {
  return (
    <span className="bg-primary-container/10 text-primary-container border border-primary-container/30 px-xs py-base text-[10px] font-label-sm uppercase tracking-wider rounded">
      {label}
    </span>
  );
}

function ArchetypeBadge({ label }: { label: string }) {
  return (
    <span className="bg-secondary-container/20 text-secondary border border-secondary-container/40 px-xs py-base text-[10px] font-label-sm uppercase tracking-wider rounded">
      {label}
    </span>
  );
}

function SegmentBadge({ label }: { label: string }) {
  return (
    <span className="bg-[#B45309]/20 text-[#FCD34D] border border-[#B45309]/40 px-xs py-base text-[10px] font-label-sm uppercase tracking-wider rounded">
      {label}
    </span>
  );
}

// ─── Delta bar row ────────────────────────────────────────────────────────────

function DeltaBarRow({ bar }: { bar: DeltaBar }) {
  const color = deltaColor(bar.delta);
  const clientPct = Math.round(bar.client_score * 100);
  const similarPct = Math.round(bar.similar_score * 100);
  const absDelta = Math.abs(bar.delta);

  return (
    <div>
      <div className="flex justify-between text-[12px] font-[500] font-body-sm text-[#8B8B9E] mb-xs">
        <span>{bar.label}</span>
        <span className="font-data-mono" style={{ color }}>
          {deltaLabel(bar.delta)}
        </span>
      </div>
      {/* Bar */}
      <div className="h-2 w-full bg-[#121212] rounded-full overflow-hidden border border-[#27272a] flex mb-xs">
        {bar.delta > 0.05 ? (
          <div className="h-full" style={{ width: `${similarPct}%`, backgroundColor: "#10b981" }} />
        ) : bar.delta < -0.05 ? (
          <>
            <div className="h-full bg-outline-variant" style={{ width: `${similarPct}%` }} />
            <div className="h-full bg-signal-risk" style={{ width: `${Math.round(absDelta * 100)}%` }} />
          </>
        ) : (
          <div className="h-full bg-outline-variant" style={{ width: `${clientPct}%` }} />
        )}
      </div>
      <div className="text-[11px] font-body-sm text-[#8B8B9E] italic leading-tight">
        {bar.client_statement}
      </div>
    </div>
  );
}

// ─── Client venue column ─────────────────────────────────────────────────────

function ClientColumn({ venue }: { venue: ClientVenueCard }) {
  const dims = clientDims(venue.fitness_scores);
  return (
    <article className="bg-[#18181B] border border-[#27272A] rounded-lg p-md flex flex-col gap-md relative h-full">
      <div className="absolute top-0 left-0 w-1 h-full bg-primary rounded-l-lg opacity-50" />
      <div>
        <h2 className="text-body-lg font-body-lg font-semibold text-primary">{venue.name}</h2>
        <span className="text-on-surface-variant text-body-sm font-body-sm">{venue.area}</span>
      </div>
      <div className="flex flex-wrap gap-xs">
        {venue.types.slice(0, 3).map((t) => <VenueTypeBadge key={t} label={t} />)}
      </div>
      <div className="flex flex-wrap gap-xs">
        {venue.top_archetypes.slice(0, 2).map((a) => <ArchetypeBadge key={a.name} label={a.name} />)}
      </div>
      <div className="flex flex-wrap gap-xs mb-auto">
        {venue.top_segments.slice(0, 3).map((s) => <SegmentBadge key={s} label={s} />)}
      </div>
      <div className="border-t border-[#27272a] pt-md flex flex-col gap-sm">
        <div className="flex justify-between items-center">
          <span className="text-label-sm font-label-sm text-on-surface-variant uppercase">
            Your Baseline
          </span>
          <span className="text-label-sm font-label-sm text-on-surface-variant text-[10px]">Score</span>
        </div>
        <div className="flex flex-col gap-md mt-sm">
          {dims.map((dim) => (
            <div key={dim.key}>
              <div className="flex justify-between text-[12px] font-[500] font-body-sm text-[#8B8B9E] mb-xs">
                <span>{dim.label}</span>
                <span className="text-primary font-data-mono">{dim.score.toFixed(2)}</span>
              </div>
              <div className="h-2 w-full bg-[#121212] rounded-full overflow-hidden border border-[#27272a]">
                <div className="h-full bg-primary" style={{ width: `${Math.round(dim.score * 100)}%` }} />
              </div>
            </div>
          ))}
        </div>
      </div>
    </article>
  );
}

// ─── Similar venue column ─────────────────────────────────────────────────────

interface SimilarColumnProps {
  venue: SimilarVenueCard;
  onSelect: (id: number) => void;
}

function SimilarColumn({ venue, onSelect }: SimilarColumnProps) {
  // All 7 dimensions, most differentiated first — Equal rows show what can be improved.
  const bars = topDeltaBars(venue.delta_bars, 7);
  return (
    <article className="bg-[#18181B] border border-[#27272A] rounded-lg p-md flex flex-col gap-md h-full">
      {/* Clickable header — opens deep-dive drawer */}
      <button
        onClick={() => onSelect(venue.id)}
        className="text-left group w-full"
        aria-label={`Analyse ${venue.name}`}
      >
        <div className="flex justify-between items-start">
          <h2 className="text-body-lg font-body-lg font-semibold text-on-surface group-hover:text-primary transition-colors">
            {venue.name}
          </h2>
          <span className="material-symbols-outlined text-on-surface-variant group-hover:text-primary text-[18px] transition-colors">
            open_in_new
          </span>
        </div>
        <span className="text-on-surface-variant text-body-sm font-body-sm">{venue.area}</span>
      </button>
      <div className="flex flex-wrap gap-xs">
        {venue.types.slice(0, 4).map((t) => <VenueTypeBadge key={t} label={t} />)}
      </div>
      <div className="flex flex-wrap gap-xs">
        {venue.top_archetypes.slice(0, 2).map((a) => <ArchetypeBadge key={a.name} label={a.name} />)}
      </div>
      <div className="flex flex-wrap gap-xs mb-auto">
        {venue.top_segments.slice(0, 3).map((s) => <SegmentBadge key={s} label={s} />)}
      </div>
      <div className="border-t border-[#27272a] pt-md mt-auto flex flex-col gap-md">
        {bars.map((bar) => <DeltaBarRow key={bar.dimension} bar={bar} />)}
      </div>
    </article>
  );
}

// ─── Page helpers ────────────────────────────────────────────────────────────

// Client baseline: all 7 dimensions sorted by score desc — full picture.
function clientDims(fitnessScores: FitnessDimension[]): FitnessDimension[] {
  return [...fitnessScores].sort((a, b) => b.score - a.score);
}

// Per-competitor: top 4 dimensions sorted by absolute delta — each competitor
// tells its own story, not the same fixed list as every other.
function topDeltaBars(bars: DeltaBar[], n = 4): DeltaBar[] {
  return [...bars]
    .sort((a, b) => Math.abs(b.delta) - Math.abs(a.delta))
    .slice(0, n);
}

export default function CompetitorsPage({
  params,
}: {
  params: Promise<{ id: string }>;
}) {
  const { id } = use(params);
  const [data, setData] = useState<CompetitorsResponse | null>(null);
  const [offset, setOffset] = useState(0);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  // ── Drawer state ────────────────────────────────────────────────────────────
  const [drawerCompId, setDrawerCompId]     = useState<number | null>(null);
  const [deepDive, setDeepDive]             = useState<CompetitorDeepDive | null>(null);
  const [deepDiveLoading, setDeepDiveLoading] = useState(false);
  const [deepDiveError, setDeepDiveError]   = useState<string | null>(null);

  const handleSelectCompetitor = useCallback(
    (compId: number) => {
      setDrawerCompId(compId);
      setDeepDive(null);
      setDeepDiveError(null);
      setDeepDiveLoading(true);
      getCompetitorDeepDive(id, compId)
        .then((d) => { setDeepDive(d); setDeepDiveLoading(false); })
        .catch((e: unknown) => {
          setDeepDiveError(e instanceof Error ? e.message : "Analysis failed");
          setDeepDiveLoading(false);
        });
    },
    [id],
  );

  const handleCloseDrawer = useCallback(() => {
    setDrawerCompId(null);
    setDeepDive(null);
    setDeepDiveError(null);
    setDeepDiveLoading(false);
  }, []);

  useEffect(() => {
    setLoading(true);
    getCompetitors(id, LIMIT, offset)
      .then((d) => { setData(d); setLoading(false); })
      .catch((e: unknown) => {
        setError(e instanceof Error ? e.message : "Load failed");
        setLoading(false);
      });
  }, [id, offset]);

  const totalPages = data ? Math.ceil(data.total_similar / LIMIT) : 0;
  const currentPage = Math.floor(offset / LIMIT) + 1;

  return (
    <div className="p-margin flex flex-col gap-lg max-w-[1400px] w-full mx-auto">
      {/* ── Venue header ── */}
      {data && (
        <div className="flex flex-col gap-xs border-b border-outline-variant pb-md">
          <div className="flex items-baseline gap-sm flex-wrap">
            <h2 className="text-headline-lg font-headline-lg text-primary font-bold">
              {data.client_venue.name}
            </h2>
            <span className="text-on-surface-variant text-body-md font-body-md">{data.client_venue.area}</span>
            <span className="bg-surface-container px-sm py-xs border border-outline-variant rounded text-label-sm font-label-sm text-on-surface uppercase tracking-wider">
              {data.client_venue.city}
            </span>
          </div>
          {/* Tab bar */}
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
                  tab.label === "Competitors"
                    ? "text-primary border-b-2 border-primary"
                    : "text-on-surface-variant hover:text-primary"
                }`}
              >
                {tab.label}
              </Link>
            ))}
          </div>
        </div>
      )}

      {loading && (
        <div className="text-center text-on-surface-variant py-xl">
          <span className="material-symbols-outlined text-primary animate-spin inline-block">
            progress_activity
          </span>
        </div>
      )}

      {error && (
        <div className="bg-error-container border border-error/30 rounded p-md text-on-error-container font-body-sm">
          {error}
        </div>
      )}

      {data && !loading && (
        <>
          {/* ── 4-col comparison grid ── */}
          <section className="overflow-x-auto custom-scrollbar pb-sm">
            <div className="grid grid-cols-1 md:grid-cols-4 gap-md min-w-[1000px] items-stretch">
              <ClientColumn venue={data.client_venue} />
              {data.similar_venues.map((sv) => (
                <SimilarColumn key={sv.id} venue={sv} onSelect={handleSelectCompetitor} />
              ))}
              {/* Placeholder columns if fewer than 3 similar venues */}
              {Array.from({ length: Math.max(0, 3 - data.similar_venues.length) }).map((_, i) => (
                <div
                  key={i}
                  className="bg-[#18181B] border border-dashed border-[#27272a] rounded-lg p-md flex items-center justify-center text-on-surface-variant text-body-sm"
                >
                  No more venues
                </div>
              ))}
            </div>
          </section>

          {/* ── Insight callout ── */}
          {data.insight_callout && (
            <div className="bg-[#18181B] border border-[#27272a] border-l-2 border-l-primary-container rounded p-md flex items-start gap-md">
              <span className="material-symbols-outlined text-primary-container mt-xs flex-shrink-0">
                lightbulb
              </span>
              <p className="text-on-surface text-body-md font-body-md">{data.insight_callout}</p>
            </div>
          )}

          {/* ── Carousel navigation ── */}
          <div className="flex justify-between items-center border-t border-[#27272a] pt-md">
            <button
              onClick={() => setOffset(Math.max(0, offset - LIMIT))}
              disabled={offset === 0}
              className="text-on-surface-variant hover:text-on-surface transition-colors text-label-sm font-label-sm flex items-center gap-xs disabled:opacity-30"
            >
              <span className="material-symbols-outlined text-[16px]">arrow_back</span> Prev
            </button>
            <div className="text-on-surface-variant text-label-sm font-label-sm">
              Viewing{" "}
              <span className="text-on-surface font-bold">
                {offset + 1}–{Math.min(offset + LIMIT, data.total_similar)}
              </span>{" "}
              of{" "}
              <span className="font-data-mono text-data-mono">{data.total_similar}</span>
            </div>
            <button
              onClick={() => setOffset(offset + LIMIT)}
              disabled={currentPage >= totalPages}
              className="text-on-surface-variant hover:text-on-surface transition-colors text-label-sm font-label-sm flex items-center gap-xs disabled:opacity-30"
            >
              Next <span className="material-symbols-outlined text-[16px]">arrow_forward</span>
            </button>
          </div>
        </>
      )}

      {/* ── Competitor deep-dive drawer ── */}
      <CompetitorDrawer
        venueId={Number(id)}
        data={deepDive}
        loading={deepDiveLoading}
        error={deepDiveError}
        onClose={handleCloseDrawer}
      />
    </div>
  );
}
