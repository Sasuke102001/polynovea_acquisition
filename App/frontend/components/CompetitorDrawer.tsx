"use client";

/**
 * CompetitorDrawer
 * Right-side sliding drawer that shows an AI-generated behavioral deep-dive
 * for a selected competitor. Triggered by clicking any SimilarColumn card.
 *
 * Shows:
 *  - Competitor header + bucket badge
 *  - "What to learn" — top dims where competitor outperforms (green)
 *  - "What to avoid" — top dims where client outperforms (red)
 *  - Strategic brief
 */

import { useEffect, useRef } from "react";
import type { CompetitorDeepDive, CompetitorInsight } from "@/lib/api";

// ─── Helpers ─────────────────────────────────────────────────────────────────

function scoreBar(score: number, color: string) {
  return (
    <div className="h-1.5 w-full bg-[#121212] rounded-full overflow-hidden border border-[#27272a] mt-1">
      <div
        className="h-full rounded-full transition-all duration-300"
        style={{ width: `${Math.round(score * 100)}%`, backgroundColor: color }}
      />
    </div>
  );
}

function bucketColor(label: string): string {
  switch (label) {
    case "Direct Peer":   return "bg-primary/20 text-primary border-primary/40";
    case "Close Match":   return "bg-secondary/20 text-secondary border-secondary/40";
    case "Partial Match": return "bg-[#B45309]/20 text-[#FCD34D] border-[#B45309]/40";
    default:              return "bg-outline-variant/20 text-on-surface-variant border-outline-variant/40";
  }
}

// ─── Insight card ─────────────────────────────────────────────────────────────

interface InsightCardProps {
  insight: CompetitorInsight;
  mode: "learn" | "avoid";
  clientName: string;
  compName: string;
}

function InsightCard({ insight, mode, clientName, compName }: InsightCardProps) {
  const isLearn   = mode === "learn";
  const accentColor = isLearn ? "#10b981" : "#ef4444";
  const bgClass     = isLearn
    ? "bg-[#10b981]/5 border-[#10b981]/20"
    : "bg-[#ef4444]/5 border-[#ef4444]/20";

  const clientPct = Math.round(insight.client_score * 100);
  const compPct   = Math.round(insight.competitor_score * 100);
  const deltaPct  = Math.round(Math.abs(insight.delta) * 100);

  return (
    <div className={`rounded-lg border p-sm flex flex-col gap-sm ${bgClass}`}>
      {/* Dimension header */}
      <div className="flex items-center justify-between">
        <span className="text-[12px] font-[600] text-on-surface uppercase tracking-wide">
          {insight.label}
        </span>
        <span
          className="text-[11px] font-data-mono font-bold"
          style={{ color: accentColor }}
        >
          {isLearn ? `+${deltaPct}pts` : `-${deltaPct}pts`}
        </span>
      </div>

      {/* Score comparison */}
      <div className="grid grid-cols-2 gap-xs">
        <div>
          <div className="flex justify-between text-[10px] text-on-surface-variant mb-[2px]">
            <span className="truncate">{clientName}</span>
            <span className="font-data-mono text-on-surface">{clientPct}</span>
          </div>
          {scoreBar(insight.client_score, isLearn ? "#8b8b9e" : accentColor)}
        </div>
        <div>
          <div className="flex justify-between text-[10px] text-on-surface-variant mb-[2px]">
            <span className="truncate">{compName}</span>
            <span className="font-data-mono" style={{ color: accentColor }}>{compPct}</span>
          </div>
          {scoreBar(insight.competitor_score, isLearn ? accentColor : "#8b8b9e")}
        </div>
      </div>

      {/* Narrative */}
      <p className="text-[11px] text-on-surface-variant leading-relaxed font-body-sm">
        {insight.narrative}
      </p>
    </div>
  );
}

// ─── Skeleton ────────────────────────────────────────────────────────────────

function DrawerSkeleton() {
  return (
    <div className="flex flex-col gap-md animate-pulse p-md">
      {/* Header */}
      <div className="h-5 w-2/3 bg-[#27272a] rounded" />
      <div className="h-3 w-1/3 bg-[#27272a] rounded" />
      <div className="h-6 w-24 bg-[#27272a] rounded-full" />

      {/* Learn section */}
      <div className="h-3 w-32 bg-[#27272a] rounded mt-sm" />
      {[1, 2, 3].map((i) => (
        <div key={i} className="h-24 bg-[#18181B] border border-[#27272a] rounded-lg" />
      ))}

      {/* Avoid section */}
      <div className="h-3 w-28 bg-[#27272a] rounded mt-sm" />
      {[1, 2].map((i) => (
        <div key={i} className="h-24 bg-[#18181B] border border-[#27272a] rounded-lg" />
      ))}

      {/* Brief */}
      <div className="h-20 bg-[#18181B] border border-[#27272a] rounded-lg" />
    </div>
  );
}

// ─── Main drawer ──────────────────────────────────────────────────────────────

interface CompetitorDrawerProps {
  venueId: number;
  data: CompetitorDeepDive | null;
  loading: boolean;
  error: string | null;
  onClose: () => void;
}

export default function CompetitorDrawer({
  venueId,
  data,
  loading,
  error,
  onClose,
}: CompetitorDrawerProps) {
  const drawerRef = useRef<HTMLDivElement>(null);

  // Close on Escape key
  useEffect(() => {
    function handleKey(e: KeyboardEvent) {
      if (e.key === "Escape") onClose();
    }
    window.addEventListener("keydown", handleKey);
    return () => window.removeEventListener("keydown", handleKey);
  }, [onClose]);

  const isOpen = loading || !!data || !!error;

  return (
    <>
      {/* Backdrop */}
      <div
        className={`fixed inset-0 z-40 bg-black/50 transition-opacity duration-200 ${
          isOpen ? "opacity-100 pointer-events-auto" : "opacity-0 pointer-events-none"
        }`}
        onClick={onClose}
        aria-hidden="true"
      />

      {/* Drawer panel */}
      <div
        ref={drawerRef}
        className={`fixed top-0 right-0 h-full z-50 w-[440px] max-w-[95vw]
          bg-[#0f0f0f] border-l border-[#27272a] shadow-2xl
          flex flex-col
          transition-transform duration-300 ease-in-out
          ${isOpen ? "translate-x-0" : "translate-x-full"}`}
        aria-label="Competitor analysis"
        role="dialog"
      >
        {/* ── Sticky header bar ── */}
        <div className="flex items-center justify-between px-md py-sm border-b border-[#27272a] flex-shrink-0">
          <span className="text-label-sm font-label-sm text-on-surface-variant uppercase tracking-wider">
            Competitor Analysis
          </span>
          <button
            onClick={onClose}
            className="text-on-surface-variant hover:text-on-surface transition-colors p-xs rounded"
            aria-label="Close"
          >
            <span className="material-symbols-outlined text-[20px]">close</span>
          </button>
        </div>

        {/* ── Scrollable body ── */}
        <div className="flex-1 overflow-y-auto custom-scrollbar">
          {loading && <DrawerSkeleton />}

          {error && !loading && (
            <div className="p-md">
              <div className="bg-error-container border border-error/30 rounded p-md text-on-error-container text-body-sm font-body-sm">
                {error}
              </div>
            </div>
          )}

          {data && !loading && (
            <div className="flex flex-col gap-lg p-md">
              {/* ── Competitor header ── */}
              <div className="flex flex-col gap-xs">
                <h2 className="text-headline-sm font-headline-sm font-bold text-on-surface leading-tight">
                  {data.competitor_name}
                </h2>
                <p className="text-body-sm font-body-sm text-on-surface-variant">
                  {[data.competitor_area, data.competitor_city]
                    .filter(Boolean)
                    .join(", ")}
                </p>
                <div className="flex flex-wrap gap-xs mt-xs">
                  {data.competitor_types.slice(0, 3).map((t) => (
                    <span
                      key={t}
                      className="bg-primary-container/10 text-primary-container border border-primary-container/30 px-xs py-base text-[10px] font-label-sm uppercase tracking-wider rounded"
                    >
                      {t}
                    </span>
                  ))}
                  <span
                    className={`px-xs py-base text-[10px] font-label-sm uppercase tracking-wider rounded border ${bucketColor(data.bucket_label)}`}
                  >
                    {data.bucket_label}
                  </span>
                </div>
              </div>

              {/* ── Learn from section ── */}
              {data.learn_from.length > 0 && (
                <section className="flex flex-col gap-sm">
                  <div className="flex items-center gap-xs">
                    <span className="material-symbols-outlined text-[#10b981] text-[16px]">
                      arrow_upward
                    </span>
                    <h3 className="text-label-md font-label-md text-[#10b981] uppercase tracking-wide">
                      What to learn
                    </h3>
                  </div>
                  <p className="text-[11px] text-on-surface-variant font-body-sm -mt-xs">
                    Dimensions where {data.competitor_name} outperforms your venue
                  </p>
                  {data.learn_from.map((insight) => (
                    <InsightCard
                      key={insight.dimension}
                      insight={insight}
                      mode="learn"
                      clientName={data.client_name}
                      compName={data.competitor_name}
                    />
                  ))}
                </section>
              )}

              {/* ── Avoid section ── */}
              {data.avoid.length > 0 && (
                <section className="flex flex-col gap-sm">
                  <div className="flex items-center gap-xs">
                    <span className="material-symbols-outlined text-[#ef4444] text-[16px]">
                      arrow_downward
                    </span>
                    <h3 className="text-label-md font-label-md text-[#ef4444] uppercase tracking-wide">
                      What to avoid
                    </h3>
                  </div>
                  <p className="text-[11px] text-on-surface-variant font-body-sm -mt-xs">
                    Dimensions where {data.competitor_name} is weaker — don&apos;t copy this
                  </p>
                  {data.avoid.map((insight) => (
                    <InsightCard
                      key={insight.dimension}
                      insight={insight}
                      mode="avoid"
                      clientName={data.client_name}
                      compName={data.competitor_name}
                    />
                  ))}
                </section>
              )}

              {/* Parity fallback */}
              {data.learn_from.length === 0 && data.avoid.length === 0 && (
                <div className="bg-[#18181B] border border-[#27272a] rounded-lg p-md text-on-surface-variant text-body-sm font-body-sm text-center">
                  These venues are closely matched across all fitness dimensions — delta &lt; 2pts on every dimension.
                </div>
              )}

              {/* ── Strategic brief ── */}
              {data.strategic_brief && (
                <section className="flex flex-col gap-sm">
                  <div className="flex items-center gap-xs">
                    <span className="material-symbols-outlined text-primary-container text-[16px]">
                      analytics
                    </span>
                    <h3 className="text-label-md font-label-md text-primary-container uppercase tracking-wide">
                      Strategic picture
                    </h3>
                  </div>
                  <div className="bg-[#18181B] border border-[#27272a] border-l-2 border-l-primary-container rounded-lg p-md">
                    <p className="text-body-sm font-body-sm text-on-surface leading-relaxed">
                      {data.strategic_brief}
                    </p>
                  </div>
                </section>
              )}

              {/* ── Footer spacer ── */}
              <div className="h-4" />
            </div>
          )}
        </div>
      </div>
    </>
  );
}
