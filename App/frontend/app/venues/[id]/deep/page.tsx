"use client";

import { useState, useEffect, use, useRef } from "react";
import Link from "next/link";
import {
  getIntelligence,
  getRisk,
  getPrimitives,
  getBenchmarks,
  getTrends,
  type IntelligenceResponse,
  type RiskResponse,
  type PrimitivesResponse,
  type BenchmarksResponse,
  type TrendsResponse,
  type RecommendationRow,
  type ArchetypeBar,
  type PricingPower,
  type RevenueLever,
  type PrimitiveScore,
  type BenchmarkBar,
  type TrendSignal,
  type RisingPattern,
} from "@/lib/api";
import ChatDrawer from "@/components/ChatDrawer";

// ─── Priority tier helpers ────────────────────────────────────────────────────

function tierConfig(tier: string) {
  switch (tier) {
    case "CRITICAL":
      return { color: "#ef4444", bg: "rgba(239,68,68,0.12)", border: "rgba(239,68,68,0.35)" };
    case "HIGH":
      return { color: "#f59e0b", bg: "rgba(245,158,11,0.12)", border: "rgba(245,158,11,0.35)" };
    case "MEDIUM":
      return { color: "#e6d3a3", bg: "rgba(230,211,163,0.10)", border: "rgba(230,211,163,0.25)" };
    case "CANDIDATE":
      return { color: "#a855f7", bg: "rgba(168,85,247,0.10)", border: "rgba(168,85,247,0.25)" };
    default:
      return { color: "#8b8b9e", bg: "rgba(139,139,158,0.08)", border: "rgba(139,139,158,0.20)" };
  }
}

function tierOrder(tier: string): number {
  return { CRITICAL: 0, HIGH: 1, MEDIUM: 2, CANDIDATE: 3, LOW: 4, EXPLORE: 5 }[tier] ?? 6;
}

// ─── Recommendation card (used by Intelligence + Risk) ────────────────────────

function RecommendationCard({ rec }: { rec: RecommendationRow }) {
  const tc = tierConfig(rec.priority_tier);
  const fitPct = Math.min(100, Math.round(rec.fit_score * 100));

  return (
    <div className="bg-[#18181B] border border-[#27272A] rounded-lg overflow-hidden flex">
      <div className="w-1 flex-shrink-0" style={{ backgroundColor: tc.color, opacity: 0.7 }} />
      <div className="flex-1 p-md flex flex-col gap-sm min-w-0">
        <div className="flex items-start justify-between gap-md">
          <div className="flex-1 min-w-0">
            <div className="flex items-center gap-sm flex-wrap mb-xs">
              <span
                className="text-[9px] font-bold px-xs py-[2px] rounded border uppercase tracking-wider flex-shrink-0"
                style={{ color: tc.color, borderColor: tc.border, backgroundColor: tc.bg }}
              >
                {rec.priority_tier}
              </span>
              {rec.recommended ? (
                <span className="text-[10px] text-signal-positive font-label-sm uppercase tracking-wide">
                  ✓ Recommended
                </span>
              ) : (
                <span className="text-[10px] text-signal-warning font-label-sm uppercase tracking-wide">
                  ⚠ Gap to Close
                </span>
              )}
            </div>
            <h4 className="text-body-md font-body-md font-semibold text-on-surface leading-snug">
              {rec.title}
            </h4>
          </div>
          <div className="text-right flex-shrink-0">
            <div className="text-[10px] font-label-sm text-on-surface-variant uppercase mb-[2px]">Fit</div>
            <div className="text-data-mono font-data-mono text-sm font-bold" style={{ color: tc.color }}>
              {fitPct}%
            </div>
          </div>
        </div>
        <div className="h-[3px] bg-[#27272A] rounded-full overflow-hidden">
          <div
            className="h-full rounded-full"
            style={{ width: `${fitPct}%`, backgroundColor: rec.recommended ? "#10b981" : tc.color }}
          />
        </div>
        <p className="text-body-sm font-body-sm text-on-surface-variant leading-relaxed">
          {rec.description}
        </p>
        {rec.expected_impact && (
          <div className="text-[11px] font-label-sm text-on-surface-variant/50 italic border-t border-[#27272A] pt-xs">
            Expected impact: {rec.expected_impact}
          </div>
        )}
      </div>
    </div>
  );
}

// ─── Archetype distribution ───────────────────────────────────────────────────

function ArchetypeSection({ archetypes }: { archetypes: ArchetypeBar[] }) {
  const max = Math.max(...archetypes.map((a) => a.prevalence_pct), 1);
  return (
    <div className="bg-[#18181B] border border-[#27272A] rounded-lg p-md flex flex-col gap-md">
      <div className="flex items-center gap-sm border-b border-[#27272A] pb-sm">
        <span className="material-symbols-outlined text-[#7C3AED] text-[18px]">psychology</span>
        <h3 className="text-label-md font-label-md text-on-surface uppercase tracking-widest">
          Archetype Breakdown
        </h3>
      </div>
      <div className="flex flex-col gap-md">
        {archetypes.map((arc, i) => {
          const barWidth = Math.round((arc.prevalence_pct / max) * 100);
          const opacity = 1 - i * 0.15;
          return (
            <div key={arc.name} className="flex flex-col gap-[6px]">
              <div className="flex justify-between items-baseline">
                <div>
                  <span className="text-body-sm font-body-sm font-semibold text-on-surface">{arc.name}</span>
                  <span className="text-[11px] text-on-surface-variant font-label-sm ml-sm">
                    {arc.demographic_label}
                  </span>
                </div>
                <span
                  className="text-data-mono font-data-mono text-sm flex-shrink-0 ml-md"
                  style={{ color: `rgba(124,58,237,${Math.max(0.5, opacity)})` }}
                >
                  {arc.prevalence_pct}%
                </span>
              </div>
              <div className="h-2 bg-[#27272A] rounded-full overflow-hidden">
                <div
                  className="h-full rounded-full transition-all duration-500"
                  style={{ width: `${barWidth}%`, backgroundColor: "#7C3AED", opacity: Math.max(0.35, opacity) }}
                />
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
}

// ─── Pricing power section ────────────────────────────────────────────────────

function PricingPowerSection({ pricing }: { pricing: PricingPower }) {
  const scorePct = Math.round(pricing.monetization_potential * 100);
  const headroomColor =
    pricing.headroom_label === "HIGH" ? "#10b981" : pricing.headroom_label === "MED" ? "#f59e0b" : "#ef4444";
  const r = 32, circ = 2 * Math.PI * r;
  const offset = circ * (1 - pricing.monetization_potential);

  return (
    <div className="bg-[#18181B] border border-[#27272A] rounded-lg p-md flex flex-col gap-md">
      <div className="flex items-center gap-sm border-b border-[#27272A] pb-sm">
        <span className="material-symbols-outlined text-primary-container text-[18px]">monetization_on</span>
        <h3 className="text-label-md font-label-md text-on-surface uppercase tracking-widest">Pricing Power</h3>
      </div>
      <div className="flex items-center gap-lg">
        <div className="relative flex-shrink-0">
          <svg width="88" height="88" viewBox="0 0 88 88" className="transform -rotate-90">
            <circle cx="44" cy="44" r={r} fill="none" stroke="#27272A" strokeWidth="5" />
            <circle
              cx="44" cy="44" r={r} fill="none" stroke={headroomColor} strokeWidth="5"
              strokeDasharray={circ.toFixed(1)} strokeDashoffset={offset.toFixed(1)} strokeLinecap="round"
            />
          </svg>
          <div className="absolute inset-0 flex flex-col items-center justify-center">
            <span className="text-data-mono font-data-mono text-xl font-bold leading-none" style={{ color: headroomColor }}>
              {scorePct}
            </span>
            <span className="text-[9px] font-label-sm text-on-surface-variant">/100</span>
          </div>
        </div>
        <div>
          <div className="text-label-sm font-label-sm text-on-surface-variant uppercase mb-xs">Revenue Headroom</div>
          <span className="text-xl font-bold font-data-mono" style={{ color: headroomColor }}>
            {pricing.headroom_label}
          </span>
          <p className="text-body-sm font-body-sm text-on-surface-variant mt-xs max-w-[200px]">
            {pricing.headroom_label === "HIGH"
              ? "Strong monetization signals — captures well above average revenue per visit."
              : pricing.headroom_label === "MED"
              ? "Moderate revenue capture — targeted improvements can unlock significant uplift."
              : "Low current monetization — significant behavioral gaps limit revenue capture."}
          </p>
        </div>
      </div>
      <div className="flex flex-col gap-xs border-t border-[#27272A] pt-sm">
        <div className="text-[10px] font-label-sm text-on-surface-variant uppercase tracking-widest mb-xs">
          Revenue Levers
        </div>
        {(pricing.revenue_levers as RevenueLever[]).map((lever) => {
          const isActive = lever.status === "ACTIVE";
          return (
            <div key={lever.label} className="flex items-start gap-sm py-xs border-b border-[#27272A] last:border-0">
              <span
                className="material-symbols-outlined text-[16px] flex-shrink-0 mt-[2px]"
                style={{ color: isActive ? "#10b981" : "#f59e0b" }}
              >
                {isActive ? "check_circle" : "radio_button_unchecked"}
              </span>
              <div className="flex-1 min-w-0">
                <div className="flex items-center justify-between gap-sm">
                  <span className="text-body-sm font-body-sm text-on-surface font-medium">{lever.label}</span>
                  <span
                    className="text-[9px] font-bold px-xs py-[2px] rounded uppercase flex-shrink-0"
                    style={{
                      color: isActive ? "#10b981" : "#f59e0b",
                      backgroundColor: isActive ? "rgba(16,185,129,0.10)" : "rgba(245,158,11,0.10)",
                    }}
                  >
                    {lever.status}
                  </span>
                </div>
                <p className="text-[11px] font-label-sm text-on-surface-variant leading-tight mt-[2px]">
                  {lever.sub}
                </p>
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
}

// ─── Risk Tab ─────────────────────────────────────────────────────────────────

function RiskTab({ data }: { data: RiskResponse }) {
  const cr = data.churn_risk;
  const riskColor =
    cr.level === "HIGH" ? "#ef4444" : cr.level === "MED" ? "#f59e0b" : "#10b981";
  const r = 32, circ = 2 * Math.PI * r;
  // Ring represents retention strength (inverse of churn risk)
  const ringOffset = circ * (1 - cr.score);

  return (
    <div className="flex flex-col gap-lg mt-md">

      {/* ── Churn Risk ring ── */}
      <section className="flex flex-col gap-md">
        <div className="flex items-center gap-sm">
          <span className="bg-signal-risk/10 text-signal-risk text-label-sm font-label-sm px-sm py-xs rounded uppercase border border-signal-risk/20 tracking-wider">
            F9 · CHURN RISK
          </span>
          <h3 className="text-headline-md font-headline-md text-on-surface font-bold">
            Churn & Retention Risk
          </h3>
        </div>

        <div className="bg-[#18181B] border border-[#27272A] rounded-lg p-md flex items-center gap-lg">
          {/* Ring */}
          <div className="relative flex-shrink-0">
            <svg width="88" height="88" viewBox="0 0 88 88" className="transform -rotate-90">
              <circle cx="44" cy="44" r={r} fill="none" stroke="#27272A" strokeWidth="5" />
              <circle
                cx="44" cy="44" r={r} fill="none" stroke={riskColor} strokeWidth="5"
                strokeDasharray={circ.toFixed(1)} strokeDashoffset={ringOffset.toFixed(1)}
                strokeLinecap="round"
              />
            </svg>
            <div className="absolute inset-0 flex flex-col items-center justify-center">
              <span
                className="text-data-mono font-data-mono text-xl font-bold leading-none"
                style={{ color: riskColor }}
              >
                {Math.round(cr.score * 100)}
              </span>
              <span className="text-[9px] font-label-sm text-on-surface-variant">/100</span>
            </div>
          </div>

          <div className="flex-1 min-w-0">
            <div className="text-label-sm font-label-sm text-on-surface-variant uppercase mb-xs">
              Retention Signal
            </div>
            <span className="text-xl font-bold font-data-mono" style={{ color: riskColor }}>
              {cr.level} RISK
            </span>
            <p className="text-body-sm font-body-sm text-on-surface-variant mt-xs">
              {cr.label}
            </p>
          </div>
        </div>
      </section>

      {/* ── Critical interventions ── */}
      <section className="flex flex-col gap-md">
        <div className="flex items-center justify-between gap-md flex-wrap">
          <div className="flex items-center gap-sm">
            <span className="bg-signal-risk/10 text-signal-risk text-label-sm font-label-sm px-sm py-xs rounded uppercase border border-signal-risk/20 tracking-wider">
              INTERVENTIONS
            </span>
            <h3 className="text-headline-md font-headline-md text-on-surface font-bold">
              Priority Actions
            </h3>
          </div>
          <span className="text-data-mono font-data-mono text-on-surface-variant text-sm">
            {data.critical_interventions.length} items
          </span>
        </div>

        {data.critical_interventions.length > 0 ? (
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-sm">
            {data.critical_interventions.map((rec) => (
              <RecommendationCard key={rec.intervention_type} rec={rec} />
            ))}
          </div>
        ) : (
          <div className="bg-[#18181B] border border-dashed border-[#27272A] rounded-lg p-xl text-center">
            <span className="material-symbols-outlined text-signal-positive text-[32px] block mb-sm">
              check_circle
            </span>
            <p className="text-on-surface-variant text-body-sm">
              No critical risk interventions detected for this venue.
            </p>
          </div>
        )}
      </section>

      {/* ── Friction funnel ── */}
      {data.friction_items.length > 0 && (
        <section className="flex flex-col gap-md">
          <div className="flex items-center gap-sm">
            <span className="bg-signal-warning/10 text-signal-warning text-label-sm font-label-sm px-sm py-xs rounded uppercase border border-signal-warning/20 tracking-wider">
              FRICTION FUNNEL
            </span>
            <h3 className="text-headline-md font-headline-md text-on-surface font-bold">
              Repeat Visit Barriers
            </h3>
          </div>
          <div className="flex flex-col gap-sm">
            {data.friction_items.map((item) => (
              <RecommendationCard key={item.intervention_type} rec={item} />
            ))}
          </div>
        </section>
      )}

      <footer className="pt-lg border-t border-[#27272A] text-center pb-md">
        <p className="text-[11px] font-body-sm text-on-surface-variant/40 max-w-2xl mx-auto">
          Risk Analysis — Churn risk derived from behavioral retention signals.
          Scope: repeat visit patterns and friction signals from review analysis.
          Out of scope: loyalty program mechanics, pricing, delivery logistics.
        </p>
      </footer>
    </div>
  );
}

// ─── Primitives Tab ───────────────────────────────────────────────────────────

function primitiveColor(score: number): string {
  if (score >= 0.60) return "#10b981";
  if (score >= 0.40) return "#f59e0b";
  if (score >= 0.20) return "#8b8b9e";
  return "#ef4444";
}

function PrimitiveBar({ prim }: { prim: PrimitiveScore }) {
  const pct = Math.round(prim.score * 100);
  const color = prim.has_signal ? primitiveColor(prim.score) : "#27272A";

  return (
    <div className="flex flex-col gap-[5px]">
      <div className="flex justify-between items-baseline">
        <span
          className="text-body-sm font-body-sm font-medium"
          style={{ color: prim.has_signal ? "#e4e4e7" : "#52525b" }}
        >
          {prim.label}
        </span>
        <span
          className="text-data-mono font-data-mono text-[11px] flex-shrink-0 ml-sm"
          style={{ color: prim.has_signal ? color : "#3f3f46" }}
        >
          {prim.has_signal ? `${pct}%` : "—"}
        </span>
      </div>
      <div className="h-[5px] bg-[#27272A] rounded-full overflow-hidden">
        <div
          className="h-full rounded-full transition-all duration-500"
          style={{ width: `${pct}%`, backgroundColor: color }}
        />
      </div>
    </div>
  );
}

function TopBottomCard({ prims, title, color }: { prims: PrimitiveScore[]; title: string; color: string }) {
  return (
    <div className="bg-[#18181B] border border-[#27272A] rounded-lg p-md flex flex-col gap-sm">
      <div className="text-[10px] font-label-sm uppercase tracking-widest border-b border-[#27272A] pb-xs" style={{ color }}>
        {title}
      </div>
      {prims.map((p) => (
        <div key={p.primitive_id} className="flex items-center justify-between gap-sm">
          <span className="text-body-sm font-body-sm text-on-surface">{p.label}</span>
          <span className="text-data-mono font-data-mono text-[12px] font-bold" style={{ color }}>
            {Math.round(p.score * 100)}%
          </span>
        </div>
      ))}
    </div>
  );
}

function PrimitivesTab({ data }: { data: PrimitivesResponse }) {
  return (
    <div className="flex flex-col gap-lg mt-md">

      {/* ── Stats bar ── */}
      <div className="flex items-center gap-md flex-wrap">
        <span className="bg-primary/10 text-primary text-label-sm font-label-sm px-sm py-xs rounded uppercase border border-primary/20 tracking-wider">
          F10 · PRIMITIVES
        </span>
        <div className="flex items-center gap-xs text-on-surface-variant text-body-sm font-body-sm">
          <span className="material-symbols-outlined text-[16px]">grid_view</span>
          <span>
            <span className="text-on-surface font-bold">{data.total_scored}</span>
            {" "}of {data.groups.reduce((acc, g) => acc + g.primitives.length, 0)} behavioral signals detected
          </span>
        </div>
      </div>

      {/* ── Conflicts (if any) ── */}
      {data.conflicts.length > 0 && (
        <div className="flex flex-col gap-sm">
          {data.conflicts.map((c) => (
            <div
              key={`${c.primitive_a}-${c.primitive_b}`}
              className="bg-[#18181B] border border-signal-warning/30 rounded-lg p-sm flex items-start gap-sm"
            >
              <span className="material-symbols-outlined text-signal-warning text-[16px] flex-shrink-0 mt-[2px]">
                warning
              </span>
              <div>
                <span className="text-[10px] font-label-sm text-signal-warning uppercase tracking-wider">
                  Signal Conflict
                </span>
                <p className="text-body-sm font-body-sm text-on-surface-variant mt-[2px]">
                  <span className="text-on-surface font-semibold">
                    {c.primitive_a.replace(/_/g, " ")} ↔ {c.primitive_b.replace(/_/g, " ")}
                  </span>{" "}
                  — {c.reason}
                </p>
              </div>
            </div>
          ))}
        </div>
      )}

      {/* ── Main grid: groups + top/bottom sidebar ── */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-md">

        {/* Groups (spans 2 cols on lg) */}
        <div className="lg:col-span-2 flex flex-col gap-md">
          {data.groups.map((group) => (
            <div key={group.category} className="bg-[#18181B] border border-[#27272A] rounded-lg p-md">
              <div className="flex items-center gap-sm border-b border-[#27272A] pb-sm mb-md">
                <span className="text-[10px] font-label-sm text-on-surface-variant uppercase tracking-widest">
                  {group.category}
                </span>
                <span className="text-[9px] font-label-sm text-on-surface-variant/40">
                  {group.primitives.filter((p) => p.has_signal).length} / {group.primitives.length} detected
                </span>
              </div>
              <div className="grid grid-cols-1 sm:grid-cols-2 gap-md">
                {group.primitives.map((p) => (
                  <PrimitiveBar key={p.primitive_id} prim={p} />
                ))}
              </div>
            </div>
          ))}
        </div>

        {/* Top 5 / Bottom 5 sidebar */}
        <div className="flex flex-col gap-md">
          <TopBottomCard prims={data.top_5} title="Top 5 Signals" color="#10b981" />
          {data.bottom_5.length > 0 && (
            <TopBottomCard prims={data.bottom_5} title="Lowest Signals" color="#ef4444" />
          )}

          {/* Legend */}
          <div className="bg-[#18181B] border border-[#27272A] rounded-lg p-md">
            <div className="text-[10px] font-label-sm text-on-surface-variant uppercase tracking-widest mb-sm">
              Score Legend
            </div>
            {[
              { label: "Strong ≥ 60%",   color: "#10b981" },
              { label: "Moderate 40–59%", color: "#f59e0b" },
              { label: "Weak 20–39%",    color: "#8b8b9e" },
              { label: "Very weak < 20%", color: "#ef4444" },
              { label: "No data",         color: "#3f3f46" },
            ].map((item) => (
              <div key={item.label} className="flex items-center gap-sm py-[3px]">
                <div className="w-3 h-3 rounded-sm flex-shrink-0" style={{ backgroundColor: item.color }} />
                <span className="text-[11px] font-body-sm text-on-surface-variant">{item.label}</span>
              </div>
            ))}
          </div>
        </div>
      </div>

      <footer className="pt-lg border-t border-[#27272A] text-center pb-md">
        <p className="text-[11px] font-body-sm text-on-surface-variant/40 max-w-2xl mx-auto">
          Primitive signals are extracted from review analysis. A signal is present only when
          review language directly matches its behavioral definition. Absent signals mean
          "no evidence detected" — not necessarily absence of the attribute.
        </p>
      </footer>
    </div>
  );
}

// ─── Benchmarks Tab ───────────────────────────────────────────────────────────

function BenchmarksTab({ data }: { data: BenchmarksResponse }) {
  return (
    <div className="flex flex-col gap-lg mt-md">

      {/* ── Header ── */}
      <section className="flex flex-col gap-md">
        <div className="flex items-center gap-sm">
          <span className="bg-primary/10 text-primary text-label-sm font-label-sm px-sm py-xs rounded uppercase border border-primary/20 tracking-wider">
            F11 · BENCHMARKS
          </span>
          <h3 className="text-headline-md font-headline-md text-on-surface font-bold">
            Performance vs. Market
          </h3>
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-2 gap-md">
          {/* City comparison card */}
          <div className="bg-[#18181B] border border-[#27272A] rounded-lg p-md">
            <div className="text-label-sm font-label-sm text-on-surface-variant uppercase mb-sm">
              City Comparison
            </div>
            <p className="text-headline-sm font-headline-sm text-on-surface font-bold">
              {data.city_comparison}
            </p>
            <p className="text-body-sm font-body-sm text-on-surface-variant mt-xs">
              {data.city_comparison === "Above city average"
                ? "This venue outperforms most competitors in your market."
                : data.city_comparison === "Below city average"
                ? "There's opportunity to close performance gaps vs. the city average."
                : "Mixed performance across dimensions — leverage strengths, close gaps."}
            </p>
          </div>

          {/* Peer insight card */}
          <div className="bg-[#18181B] border border-[#27272A] rounded-lg p-md">
            <div className="text-label-sm font-label-sm text-on-surface-variant uppercase mb-sm">
              Peer Insight
            </div>
            <p className="text-headline-sm font-headline-sm text-on-surface font-bold">
              {data.peer_insight}
            </p>
          </div>
        </div>
      </section>

      {/* ── Benchmark bars ── */}
      <section className="flex flex-col gap-md">
        <div className="flex items-center gap-sm">
          <span className="bg-primary/10 text-primary text-label-sm font-label-sm px-sm py-xs rounded uppercase border border-primary/20 tracking-wider">
            DIMENSIONS
          </span>
          <h3 className="text-headline-md font-headline-md text-on-surface font-bold">
            Dimension Comparison
          </h3>
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-2 gap-lg">
          {data.benchmark_bars.map((bar) => {
            const max = Math.max(bar.client_score, bar.city_avg, bar.peer_avg, 1);
            const clientWidth = (bar.client_score / max) * 100;
            const cityWidth = (bar.city_avg / max) * 100;
            const peerWidth = (bar.peer_avg / max) * 100;

            return (
              <div key={bar.dimension} className="bg-[#18181B] border border-[#27272A] rounded-lg p-md">
                <div className="flex justify-between items-baseline mb-md">
                  <h4 className="text-body-md font-body-md font-semibold text-on-surface">
                    {bar.label}
                  </h4>
                  <span className="text-data-mono font-data-mono text-[12px] text-on-surface-variant">
                    {Math.round(bar.client_score * 100)}%
                  </span>
                </div>

                <div className="flex flex-col gap-[10px]">
                  {/* Client score */}
                  <div>
                    <div className="flex justify-between items-baseline gap-xs mb-[4px]">
                      <span className="text-[11px] font-label-sm text-on-surface-variant uppercase">
                        Your Venue
                      </span>
                      <span className="text-data-mono font-data-mono text-[11px] font-bold text-primary">
                        {Math.round(bar.client_score * 100)}%
                      </span>
                    </div>
                    <div className="h-[6px] bg-[#27272A] rounded-full overflow-hidden">
                      <div
                        className="h-full rounded-full bg-primary"
                        style={{ width: `${clientWidth}%` }}
                      />
                    </div>
                  </div>

                  {/* City avg */}
                  <div>
                    <div className="flex justify-between items-baseline gap-xs mb-[4px]">
                      <span className="text-[11px] font-label-sm text-on-surface-variant uppercase">
                        City Avg
                      </span>
                      <span className="text-data-mono font-data-mono text-[11px] text-on-surface-variant">
                        {Math.round(bar.city_avg * 100)}%
                      </span>
                    </div>
                    <div className="h-[6px] bg-[#27272A] rounded-full overflow-hidden">
                      <div
                        className="h-full rounded-full bg-[#8b8b9e] opacity-40"
                        style={{ width: `${cityWidth}%` }}
                      />
                    </div>
                  </div>

                  {/* Peer avg */}
                  <div>
                    <div className="flex justify-between items-baseline gap-xs mb-[4px]">
                      <span className="text-[11px] font-label-sm text-on-surface-variant uppercase">
                        Peer Avg
                      </span>
                      <span className="text-data-mono font-data-mono text-[11px] text-on-surface-variant">
                        {Math.round(bar.peer_avg * 100)}%
                      </span>
                    </div>
                    <div className="h-[6px] bg-[#27272A] rounded-full overflow-hidden">
                      <div
                        className="h-full rounded-full bg-[#f59e0b] opacity-40"
                        style={{ width: `${peerWidth}%` }}
                      />
                    </div>
                  </div>
                </div>

                {/* Percentile badge */}
                <div className="mt-md pt-md border-t border-[#27272A]">
                  <span className="inline-block bg-primary/10 text-primary text-[10px] font-label-sm px-xs py-[3px] rounded uppercase">
                    {bar.client_percentile}th percentile
                  </span>
                </div>
              </div>
            );
          })}
        </div>
      </section>

      <footer className="pt-lg border-t border-[#27272A] text-center pb-md">
        <p className="text-[11px] font-body-sm text-on-surface-variant/40 max-w-2xl mx-auto">
          Benchmarks compare your venue's fitness dimensions to the city average and peer group average.
          City: all venues in {data.city}. Peer group: similar venues attracting your primary customer segment.
        </p>
      </footer>
    </div>
  );
}

// ─── Trends Tab ───────────────────────────────────────────────────────────────

function TrendsTab({ data }: { data: TrendsResponse }) {
  return (
    <div className="flex flex-col gap-lg mt-md">

      {/* ── Header ── */}
      <section className="flex flex-col gap-md">
        <div className="flex items-center gap-sm">
          <span className="bg-primary/10 text-primary text-label-sm font-label-sm px-sm py-xs rounded uppercase border border-primary/20 tracking-wider">
            F12 · TRENDS
          </span>
          <h3 className="text-headline-md font-headline-md text-on-surface font-bold">
            Market Trends & Patterns
          </h3>
        </div>

        <div className="bg-[#18181B] border border-[#27272A] rounded-lg p-md">
          <p className="text-body-sm font-body-sm text-on-surface-variant italic">
            {data.insight_callout}
          </p>
        </div>
      </section>

      {/* ── Trend signals ── */}
      {data.trend_signals.length > 0 && (
        <section className="flex flex-col gap-md">
          <div className="flex items-center gap-sm">
            <span className="bg-signal-warning/10 text-signal-warning text-label-sm font-label-sm px-sm py-xs rounded uppercase border border-signal-warning/20 tracking-wider">
              EMERGING & DECLINING
            </span>
            <h3 className="text-headline-md font-headline-md text-on-surface font-bold">
              Signal Direction
            </h3>
          </div>

          <div className="grid grid-cols-1 lg:grid-cols-2 gap-sm">
            {data.trend_signals.map((sig, i) => {
              const isEmerg = sig.signal_label === "Emerging";
              const color = isEmerg ? "#10b981" : sig.signal_label === "Declining" ? "#ef4444" : "#f59e0b";
              const icon = isEmerg ? "trending_up" : "trending_down";

              return (
                <div
                  key={i}
                  className="bg-[#18181B] border border-[#27272A] rounded-lg p-md flex items-start gap-sm"
                >
                  <span className="material-symbols-outlined text-[20px] flex-shrink-0 mt-[2px]" style={{ color }}>
                    {icon}
                  </span>
                  <div className="flex-1 min-w-0">
                    <div className="flex items-center gap-xs mb-xs">
                      <span
                        className="text-[9px] font-bold px-xs py-[2px] rounded uppercase"
                        style={{ color, backgroundColor: `${color}20`, borderColor: `${color}40`, border: `1px solid` }}
                      >
                        {sig.signal_label}
                      </span>
                      <span className="text-data-mono font-data-mono text-[11px]" style={{ color }}>
                        {Math.round(sig.confidence * 100)}%
                      </span>
                    </div>
                    <p className="text-body-sm font-body-sm text-on-surface-variant">
                      {sig.pattern_description}
                    </p>
                  </div>
                </div>
              );
            })}
          </div>
        </section>
      )}

      {/* ── Rising patterns ── */}
      {data.rising_patterns.length > 0 && (
        <section className="flex flex-col gap-md">
          <div className="flex items-center gap-sm">
            <span className="bg-primary/10 text-primary text-label-sm font-label-sm px-sm py-xs rounded uppercase border border-primary/20 tracking-wider">
              TOP PATTERNS
            </span>
            <h3 className="text-headline-md font-headline-md text-on-surface font-bold">
              Rising Behavioral Patterns
            </h3>
          </div>

          <div className="flex flex-col gap-sm">
            {data.rising_patterns.map((pat, i) => (
              <div key={pat.pattern_name} className="bg-[#18181B] border border-[#27272A] rounded-lg p-md">
                <div className="flex items-start justify-between gap-md mb-sm">
                  <div className="flex-1 min-w-0">
                    <h4 className="text-body-md font-body-md font-semibold text-on-surface">
                      {pat.pattern_name}
                    </h4>
                    <p className="text-[11px] font-label-sm text-on-surface-variant mt-[2px]">
                      Prevalence: {pat.prevalence_pct.toFixed(1)}% of venues
                    </p>
                  </div>

                  <div className="text-right flex-shrink-0">
                    <div className="text-[10px] font-label-sm text-on-surface-variant uppercase mb-[2px]">
                      Confidence
                    </div>
                    <div
                      className="text-data-mono font-data-mono text-sm font-bold"
                      style={{
                        color:
                          pat.status === "Rising"
                            ? "#10b981"
                            : pat.status === "Declining"
                            ? "#ef4444"
                            : "#f59e0b",
                      }}
                    >
                      {Math.round(pat.confidence * 100)}%
                    </div>
                  </div>
                </div>

                <div className="h-[3px] bg-[#27272A] rounded-full overflow-hidden">
                  <div
                    className="h-full rounded-full"
                    style={{
                      width: `${pat.confidence * 100}%`,
                      backgroundColor:
                        pat.status === "Rising"
                          ? "#10b981"
                          : pat.status === "Declining"
                          ? "#ef4444"
                          : "#f59e0b",
                    }}
                  />
                </div>
              </div>
            ))}
          </div>
        </section>
      )}

      <footer className="pt-lg border-t border-[#27272A] text-center pb-md">
        <p className="text-[11px] font-body-sm text-on-surface-variant/40 max-w-2xl mx-auto">
          Trends track emerging and declining behavioral patterns in your market area.
          Emerging patterns represent new opportunities; declining patterns indicate shifting customer preferences.
        </p>
      </footer>
    </div>
  );
}

// ─── Coming soon placeholder ──────────────────────────────────────────────────

function ComingSoon({ tab }: { tab: string }) {
  return (
    <div className="flex flex-col items-center justify-center py-[80px] gap-md">
      <span className="material-symbols-outlined text-primary text-[48px] opacity-40">construction</span>
      <div className="text-center">
        <p className="text-headline-md font-headline-md text-on-surface opacity-40">{tab}</p>
        <p className="text-body-sm font-body-sm text-on-surface-variant mt-xs">
          This tab is under development. Check back in the next release.
        </p>
      </div>
    </div>
  );
}

// ─── Deep tabs config ─────────────────────────────────────────────────────────

const DEEP_TABS = [
  { id: "intelligence", label: "Intelligence", icon: "psychology_alt", available: true },
  { id: "risk",         label: "Risk",         icon: "warning",        available: true },
  { id: "primitives",   label: "Primitives",   icon: "grid_view",      available: true },
  { id: "benchmarks",   label: "Benchmarks",   icon: "leaderboard",    available: true },
  { id: "trends",       label: "Trends",       icon: "trending_up",    available: true },
];

// ─── Page ─────────────────────────────────────────────────────────────────────

export default function DeepAnalysisPage({
  params,
}: {
  params: Promise<{ id: string }>;
}) {
  const { id } = use(params);
  const [activeTab, setActiveTab] = useState("intelligence");

  // Per-tab data
  const [intelligenceData, setIntelligenceData] = useState<IntelligenceResponse | null>(null);
  const [riskData, setRiskData] = useState<RiskResponse | null>(null);
  const [primitivesData, setPrimitivesData] = useState<PrimitivesResponse | null>(null);
  const [benchmarksData, setBenchmarksData] = useState<BenchmarksResponse | null>(null);
  const [trendsData, setTrendsData] = useState<TrendsResponse | null>(null);

  // Per-tab loading / error keyed by tab id
  const [tabLoading, setTabLoading] = useState<Record<string, boolean>>({ intelligence: true });
  const [tabError, setTabError] = useState<Record<string, string | null>>({});

  // Track which (tab, venue) pairs have already been fetched to avoid re-fetching
  const fetchedRef = useRef(new Set<string>());

  useEffect(() => {
    const key = `${activeTab}:${id}`;
    if (fetchedRef.current.has(key)) return;
    fetchedRef.current.add(key);

    setTabLoading((prev) => ({ ...prev, [activeTab]: true }));
    setTabError((prev) => ({ ...prev, [activeTab]: null }));

    const load = async () => {
      try {
        switch (activeTab) {
          case "intelligence": {
            const d = await getIntelligence(id);
            setIntelligenceData(d);
            break;
          }
          case "risk": {
            const d = await getRisk(id);
            setRiskData(d);
            break;
          }
          case "primitives": {
            const d = await getPrimitives(id);
            setPrimitivesData(d);
            break;
          }
          case "benchmarks": {
            const d = await getBenchmarks(id);
            setBenchmarksData(d);
            break;
          }
          case "trends": {
            const d = await getTrends(id);
            setTrendsData(d);
            break;
          }
        }
      } catch (e: unknown) {
        setTabError((prev) => ({
          ...prev,
          [activeTab]: e instanceof Error ? e.message : "Load failed",
        }));
      } finally {
        setTabLoading((prev) => ({ ...prev, [activeTab]: false }));
      }
    };

    load();
  }, [activeTab, id]);

  // Derived counts for the intelligence header summary
  const sortedRecs = intelligenceData
    ? [...intelligenceData.recommendations].sort(
        (a, b) => tierOrder(a.priority_tier) - tierOrder(b.priority_tier),
      )
    : [];
  const criticalCount = sortedRecs.filter((r) => r.priority_tier === "CRITICAL").length;
  const highCount     = sortedRecs.filter((r) => r.priority_tier === "HIGH").length;

  const loading = tabLoading[activeTab] ?? false;
  const error   = tabError[activeTab] ?? null;

  return (
    <div className="flex flex-col min-h-screen bg-background">
      {/* ── Top nav: venue tabs ── */}
      <div className="px-margin py-sm border-b border-[#27272A]">
        <div className="flex gap-md overflow-x-auto no-scrollbar">
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
              className="pb-sm px-sm text-label-md font-label-md whitespace-nowrap text-on-surface-variant hover:text-primary transition-colors"
            >
              {tab.label}
            </Link>
          ))}
        </div>
      </div>

      {/* ── Deep Analysis header ── */}
      <div className="px-margin pt-lg pb-sm flex flex-col gap-md max-w-[1400px] w-full mx-auto">
        <div className="flex items-center justify-between gap-md flex-wrap">
          <div className="flex items-center gap-sm">
            <span className="material-symbols-outlined text-primary text-[20px]">bolt</span>
            <h2 className="text-headline-md font-headline-md text-primary font-bold tracking-tight">
              DEEP ANALYSIS
            </h2>
            <span className="bg-primary/10 text-primary border border-primary/20 text-[9px] font-bold px-xs py-[2px] rounded uppercase tracking-widest ml-xs">
              CONSULTANT MODE
            </span>
          </div>

          {/* Intelligence triage chips — only shown on that tab */}
          {activeTab === "intelligence" && intelligenceData && (
            <div className="flex items-center gap-sm">
              {criticalCount > 0 && (
                <span className="bg-[rgba(239,68,68,0.12)] text-[#ef4444] border border-[rgba(239,68,68,0.3)] text-label-sm font-label-sm px-sm py-xs rounded flex items-center gap-xs">
                  <span className="material-symbols-outlined text-[14px]">priority_high</span>
                  {criticalCount} CRITICAL
                </span>
              )}
              {highCount > 0 && (
                <span className="bg-[rgba(245,158,11,0.12)] text-[#f59e0b] border border-[rgba(245,158,11,0.3)] text-label-sm font-label-sm px-sm py-xs rounded flex items-center gap-xs">
                  <span className="material-symbols-outlined text-[14px]">warning</span>
                  {highCount} HIGH
                </span>
              )}
              <span className="text-on-surface-variant text-label-sm font-label-sm">
                {sortedRecs.length} total interventions
              </span>
            </div>
          )}
        </div>

        {/* ── Deep analysis sub-tabs ── */}
        <div className="flex gap-xs overflow-x-auto no-scrollbar border-b border-[#27272A]">
          {DEEP_TABS.map((tab) => (
            <button
              key={tab.id}
              onClick={() => tab.available && setActiveTab(tab.id)}
              disabled={!tab.available}
              className={`pb-sm px-sm text-label-md font-label-md whitespace-nowrap transition-colors flex items-center gap-xs ${
                activeTab === tab.id
                  ? "text-primary border-b-2 border-primary"
                  : tab.available
                  ? "text-on-surface-variant hover:text-on-surface"
                  : "text-on-surface-variant/30 cursor-not-allowed"
              }`}
            >
              <span className="material-symbols-outlined text-[15px]">{tab.icon}</span>
              {tab.label}
              {!tab.available && (
                <span className="text-[8px] font-label-sm opacity-50 ml-xs">SOON</span>
              )}
            </button>
          ))}
        </div>
      </div>

      {/* ── Content area ── */}
      <main className="flex-1 overflow-y-auto custom-scrollbar px-margin pb-24 max-w-[1400px] w-full mx-auto">

        {loading && (
          <div className="flex items-center justify-center py-[80px]">
            <span className="material-symbols-outlined text-primary text-[48px] animate-spin">
              progress_activity
            </span>
          </div>
        )}

        {error && !loading && (
          <div className="mt-lg bg-error-container border border-error/30 rounded p-md text-on-error-container font-body-sm">
            {error}
          </div>
        )}

        {/* Intelligence tab */}
        {!loading && !error && activeTab === "intelligence" && intelligenceData && (
          <div className="flex flex-col gap-lg mt-md">
            <section className="flex flex-col gap-md">
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-sm">
                  <span className="bg-primary/10 text-primary text-label-sm font-label-sm px-sm py-xs rounded uppercase border border-primary/20 tracking-wider">
                    F3 · RECOMMENDATIONS
                  </span>
                  <h3 className="text-headline-md font-headline-md text-on-surface font-bold">
                    Personalized Interventions
                  </h3>
                </div>
                <span className="text-data-mono font-data-mono text-on-surface-variant text-sm">
                  {sortedRecs.length} actions
                </span>
              </div>
              <div className="grid grid-cols-1 lg:grid-cols-2 gap-sm">
                {sortedRecs.map((rec) => (
                  <RecommendationCard key={rec.intervention_type} rec={rec} />
                ))}
                {sortedRecs.length === 0 && (
                  <div className="col-span-2 bg-[#18181B] border border-dashed border-[#27272A] rounded-lg p-xl text-center text-on-surface-variant text-body-sm">
                    No intervention triggers found for this venue.
                  </div>
                )}
              </div>
            </section>

            <div className="grid grid-cols-1 lg:grid-cols-2 gap-md">
              <section className="flex flex-col gap-md">
                <div className="flex items-center gap-sm">
                  <span className="bg-[#7C3AED]/10 text-[#7C3AED] text-label-sm font-label-sm px-sm py-xs rounded uppercase border border-[#7C3AED]/20 tracking-wider">
                    F5 · ARCHETYPES
                  </span>
                  <h3 className="text-headline-md font-headline-md text-on-surface font-bold">
                    Archetype Breakdown
                  </h3>
                </div>
                <ArchetypeSection archetypes={intelligenceData.archetype_distribution} />
              </section>

              <section className="flex flex-col gap-md">
                <div className="flex items-center gap-sm">
                  <span className="bg-primary/10 text-primary text-label-sm font-label-sm px-sm py-xs rounded uppercase border border-primary/20 tracking-wider">
                    F8 · PRICING POWER
                  </span>
                  <h3 className="text-headline-md font-headline-md text-on-surface font-bold">
                    Revenue Headroom
                  </h3>
                </div>
                <PricingPowerSection pricing={intelligenceData.pricing_power} />
              </section>
            </div>

            <footer className="pt-lg border-t border-[#27272A] text-center pb-md">
              <p className="text-[11px] font-body-sm text-on-surface-variant/40 max-w-2xl mx-auto">
                Deep Analysis — Consultant Mode. Recommendations derived exclusively from
                behavioral signals in intervention_triggers. Out of scope: menu engineering,
                pricing strategy, delivery logistics, staffing decisions.
              </p>
            </footer>
          </div>
        )}

        {/* Risk tab */}
        {!loading && !error && activeTab === "risk" && riskData && (
          <RiskTab data={riskData} />
        )}

        {/* Primitives tab */}
        {!loading && !error && activeTab === "primitives" && primitivesData && (
          <PrimitivesTab data={primitivesData} />
        )}

        {/* Benchmarks tab */}
        {!loading && !error && activeTab === "benchmarks" && benchmarksData && (
          <BenchmarksTab data={benchmarksData} />
        )}

        {/* Trends tab */}
        {!loading && !error && activeTab === "trends" && trendsData && (
          <TrendsTab data={trendsData} />
        )}

        {/* Coming soon tabs */}
        {!loading && !error && !["intelligence", "risk", "primitives", "benchmarks", "trends"].includes(activeTab) && (
          <ComingSoon tab={DEEP_TABS.find((t) => t.id === activeTab)?.label ?? activeTab} />
        )}
      </main>
      <ChatDrawer venueId={parseInt(id)} tab="deep_risk" />
    </div>
  );
}
