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
import CinTabBar from "@/components/CinTabBar";

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
    <span
      className="px-2 py-0.5 text-[9px] font-bold uppercase tracking-widest rounded"
      style={{ fontFamily: "'JetBrains Mono', monospace", background: "rgba(230,211,163,0.08)", border: "1px solid rgba(230,211,163,0.18)", color: "#A1A1AA" }}
    >
      {label}
    </span>
  );
}

function ArchetypeBadge({ label }: { label: string }) {
  return (
    <span
      className="px-2 py-0.5 text-[9px] font-bold rounded"
      style={{ fontFamily: "'JetBrains Mono', monospace", background: "rgba(124,58,237,0.15)", border: "1px solid rgba(124,58,237,0.25)", color: "#c4b5fd" }}
    >
      {label}
    </span>
  );
}

function SegmentBadge({ label }: { label: string }) {
  return (
    <span
      className="px-2 py-0.5 text-[9px] font-bold rounded uppercase tracking-widest"
      style={{ fontFamily: "'JetBrains Mono', monospace", background: "rgba(245,158,11,0.1)", border: "1px solid rgba(245,158,11,0.2)", color: "#F59E0B" }}
    >
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
    <article className="cin-card rounded-xl p-5 flex flex-col gap-4 relative h-full">
      <div className="absolute top-0 left-0 w-0.5 h-full rounded-l-xl" style={{ background: "#E6D3A3", boxShadow: "0 0 8px rgba(230,211,163,0.3)" }} />
      <div className="pl-1">
        <h2 className="text-base font-bold gold-glow" style={{ fontFamily: "'Clash Display', 'Inter', sans-serif" }}>{venue.name}</h2>
        <span className="text-xs" style={{ color: "#71717A" }}>{venue.area}</span>
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
      <div className="border-t pt-4 flex flex-col gap-3" style={{ borderColor: "rgba(39,39,42,0.6)" }}>
        <div className="flex justify-between items-center">
          <span className="text-[9px] font-bold uppercase tracking-widest" style={{ fontFamily: "'JetBrains Mono', monospace", color: "#71717A" }}>
            Your Baseline
          </span>
          <span className="text-[9px]" style={{ fontFamily: "'JetBrains Mono', monospace", color: "#71717A" }}>Score</span>
        </div>
        <div className="flex flex-col gap-3">
          {dims.map((dim) => (
            <div key={dim.key}>
              <div className="flex justify-between text-[11px] mb-1" style={{ color: "#A1A1AA" }}>
                <span>{dim.label}</span>
                <span className="font-mono" style={{ color: "#E6D3A3" }}>{dim.score.toFixed(2)}</span>
              </div>
              <div className="h-1.5 w-full rounded-full overflow-hidden" style={{ background: "rgba(39,39,42,0.8)" }}>
                <div className="h-full rounded-full" style={{ width: `${Math.round(dim.score * 100)}%`, background: "linear-gradient(90deg, rgba(230,211,163,0.7), rgba(230,211,163,0.3))" }} />
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
  const bars = topDeltaBars(venue.delta_bars, 7);
  return (
    <article className="cin-card rounded-xl p-5 flex flex-col gap-4 h-full">
      <button
        onClick={() => onSelect(venue.id)}
        className="text-left group w-full"
        aria-label={`Analyse ${venue.name}`}
      >
        <div className="flex justify-between items-start">
          <h2 className="text-base font-bold transition-colors" style={{ fontFamily: "'Clash Display', 'Inter', sans-serif", color: "#F5F5F5" }}>
            {venue.name}
          </h2>
          <span className="material-symbols-outlined text-[16px] transition-colors" style={{ color: "#71717A" }}>
            open_in_new
          </span>
        </div>
        <span className="text-xs" style={{ color: "#71717A" }}>{venue.area}</span>
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
      <div className="border-t mt-auto pt-4 flex flex-col gap-4" style={{ borderColor: "rgba(39,39,42,0.6)" }}>
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
    <div className="p-6 md:p-8 flex flex-col gap-6 max-w-[1400px] w-full mx-auto">
      {/* ── Venue header ── */}
      {data && (
        <div className="flex flex-col gap-3">
          <div className="flex items-baseline gap-3 flex-wrap">
            <h2
              className="text-2xl md:text-3xl font-bold gold-glow"
              style={{ fontFamily: "'Clash Display', 'Inter', sans-serif" }}
            >
              {data.client_venue.name}
            </h2>
            <span className="text-sm" style={{ color: "#71717A" }}>{data.client_venue.area}</span>
            <span
              className="px-2 py-0.5 text-[9px] font-bold uppercase tracking-widest rounded"
              style={{ fontFamily: "'JetBrains Mono', monospace", background: "rgba(39,39,42,0.6)", border: "1px solid rgba(39,39,42,0.8)", color: "#A1A1AA" }}
            >
              {data.client_venue.city}
            </span>
          </div>
          <CinTabBar venueId={id} active="Competitors" />
        </div>
      )}

      {loading && (
        <div className="flex items-center justify-center py-16">
          <span className="material-symbols-outlined animate-spin text-[28px]" style={{ color: "#E6D3A3" }}>progress_activity</span>
        </div>
      )}

      {error && (
        <div className="rounded-xl p-4 text-sm" style={{ background: "rgba(251,113,133,0.08)", border: "1px solid rgba(251,113,133,0.2)", color: "#FB7185" }}>
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
            <div
              className="rounded-xl p-4 flex items-start gap-3"
              style={{ background: "rgba(230,211,163,0.06)", border: "1px solid rgba(230,211,163,0.15)", borderLeft: "2px solid rgba(230,211,163,0.5)" }}
            >
              <span className="material-symbols-outlined text-[16px] flex-shrink-0" style={{ color: "#E6D3A3" }}>lightbulb</span>
              <p className="text-sm" style={{ color: "#A1A1AA" }}>{data.insight_callout}</p>
            </div>
          )}

          {/* ── Carousel navigation ── */}
          <div className="flex justify-between items-center border-t pt-5" style={{ borderColor: "rgba(39,39,42,0.6)" }}>
            <button
              onClick={() => setOffset(Math.max(0, offset - LIMIT))}
              disabled={offset === 0}
              className="flex items-center gap-1.5 text-xs font-bold uppercase tracking-wider transition-colors disabled:opacity-30"
              style={{ fontFamily: "'JetBrains Mono', monospace", color: "#71717A" }}
            >
              <span className="material-symbols-outlined text-[14px]">arrow_back</span> Prev
            </button>
            <div className="text-xs" style={{ fontFamily: "'JetBrains Mono', monospace", color: "#71717A" }}>
              <span style={{ color: "#F5F5F5" }}>{offset + 1}–{Math.min(offset + LIMIT, data.total_similar)}</span>
              {" "}of{" "}
              <span style={{ color: "#E6D3A3" }}>{data.total_similar}</span>
            </div>
            <button
              onClick={() => setOffset(offset + LIMIT)}
              disabled={currentPage >= totalPages}
              className="flex items-center gap-1.5 text-xs font-bold uppercase tracking-wider transition-colors disabled:opacity-30"
              style={{ fontFamily: "'JetBrains Mono', monospace", color: "#71717A" }}
            >
              Next <span className="material-symbols-outlined text-[14px]">arrow_forward</span>
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
