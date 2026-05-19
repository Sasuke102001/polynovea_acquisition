"use client";

import { useState, useMemo } from "react";
import type { AudienceResponse, AudienceSegmentProfile } from "@/lib/api";

// ─── Constants ───────────────────────────────────────────────────────────────

const AFFINITY_SCORE: Record<string, number> = {
  none: 0.00, low: 0.10, low_medium: 0.28, medium: 0.48,
  medium_high: 0.65, high: 0.82, very_high: 0.95,
};

const PLATFORM_LABELS: Record<string, string> = {
  instagram: "Instagram", tiktok: "TikTok", zomato: "Zomato",
  swiggy: "Swiggy", swiggy_dineout: "Swiggy Dineout", zomato_gold: "Zomato Gold",
  google_maps: "Google Maps", google_reviews: "Google Reviews",
  direct: "Direct", word_of_mouth: "Word of Mouth",
};

const DRIVER_LABELS: Record<string, string> = {
  habit: "Habit", social_occasion: "Social Occasion", identity: "Identity",
  fomo: "FOMO", discovery: "Discovery", none: "—",
};

// ─── Shared sub-components ────────────────────────────────────────────────────

function AffinityBadge({ affinity }: { affinity: string }) {
  const map: Record<string, { bg: string; text: string; label: string }> = {
    none:        { bg: "bg-surface-container",   text: "text-outline",      label: "NONE" },
    low:         { bg: "bg-surface-container",   text: "text-outline",      label: "LOW" },
    low_medium:  { bg: "bg-blue-950/60",         text: "text-blue-300",     label: "LOW-MED" },
    medium:      { bg: "bg-amber-950/60",        text: "text-amber-300",    label: "MEDIUM" },
    medium_high: { bg: "bg-orange-950/60",       text: "text-orange-300",   label: "MED-HIGH" },
    high:        { bg: "bg-red-950/60",          text: "text-red-300",      label: "HIGH" },
    very_high:   { bg: "bg-red-900/60",          text: "text-red-200",      label: "VERY HIGH" },
  };
  const s = map[affinity] ?? map.low;
  return (
    <span className={`text-[10px] font-data-mono px-xs py-[2px] rounded border border-outline-variant uppercase tracking-wider ${s.bg} ${s.text}`}>
      {s.label}
    </span>
  );
}

function AffinityBar({ score }: { score: number }) {
  const pct = Math.round(score * 100);
  const color = score < 0.30 ? "#52525b" : score < 0.50 ? "#d97706" : score < 0.70 ? "#ea580c" : "#ef4444";
  return (
    <div className="flex items-center gap-sm">
      <div className="flex-1 h-1.5 bg-surface-variant rounded-full overflow-hidden">
        <div className="h-full rounded-full transition-all" style={{ width: `${pct}%`, backgroundColor: color }} />
      </div>
      <span className="text-[10px] font-data-mono text-on-surface-variant w-8 text-right">{pct}%</span>
    </div>
  );
}

function SegmentCard({ seg }: { seg: AudienceSegmentProfile }) {
  const revpash = seg.revpash_min_inr && seg.revpash_max_inr
    ? `₹${seg.revpash_min_inr}–${seg.revpash_max_inr}` : "—";
  const dwell = seg.dwell_min_minutes && seg.dwell_max_minutes
    ? `${seg.dwell_min_minutes}–${seg.dwell_max_minutes} min` : "—";
  const wom = seg.wom_multiplier_min != null
    ? seg.wom_multiplier_max && seg.wom_multiplier_max !== seg.wom_multiplier_min
      ? `${seg.wom_multiplier_min}–${seg.wom_multiplier_max}×` : `${seg.wom_multiplier_min}×`
    : "—";
  const repeat = seg.repeat_tendency_pct_min && seg.repeat_tendency_pct_max
    ? `${seg.repeat_tendency_pct_min}–${seg.repeat_tendency_pct_max}% / ${seg.repeat_window_days}d` : "—";
  const discoveryPlatform = seg.platforms
    .filter((p) => p.usage_type === "discovery" && p.strength === "primary")
    .map((p) => PLATFORM_LABELS[p.platform] ?? p.platform)[0] ?? "—";

  return (
    <div className="bg-surface border border-brand-border rounded p-md flex flex-col gap-md">
      <div className="flex justify-between items-start border-b border-outline-variant pb-sm">
        <div>
          <h3 className="text-headline-md font-headline-md text-on-surface font-bold">{seg.segment_name}</h3>
          {seg.alignment_pct > 0 && (
            <div className="text-display-lg font-display-lg text-primary font-bold mt-[2px]">
              {seg.alignment_pct.toFixed(0)}%
            </div>
          )}
          {seg.segment_rank > 0 && seg.alignment_pct > 0 && (
            <div className="text-label-sm font-label-sm text-on-surface-variant">#{seg.segment_rank} segment</div>
          )}
        </div>
        <AffinityBadge affinity={seg.alcohol_affinity} />
      </div>

      <div className="flex flex-col gap-xs">
        <div className="text-label-sm font-label-sm text-on-surface-variant uppercase tracking-wider">Alcohol</div>
        <AffinityBar score={seg.alcohol_affinity_score} />
        <div className="text-body-sm font-body-sm text-on-surface-variant">
          Driver: <span className="text-on-surface">{DRIVER_LABELS[seg.alcohol_primary_driver] ?? seg.alcohol_primary_driver}</span>
          {seg.beverage_preference && <span className="text-outline"> · {seg.beverage_preference}</span>}
        </div>
      </div>

      {(seg.food_pct_min || seg.alcohol_pct_min || seg.dessert_attach_pct_min) && (
        <div className="flex flex-col gap-xs">
          <div className="text-label-sm font-label-sm text-on-surface-variant uppercase tracking-wider">Spend Mix</div>
          <div className="grid grid-cols-3 gap-xs text-center">
            {seg.food_pct_min != null && (
              <div className="bg-amber-950/30 rounded p-xs">
                <div className="text-[10px] font-data-mono text-amber-300">FOOD</div>
                <div className="text-body-sm font-body-sm text-on-surface">{seg.food_pct_min}–{seg.food_pct_max}%</div>
              </div>
            )}
            {seg.alcohol_pct_min != null && (
              <div className="bg-red-950/30 rounded p-xs">
                <div className="text-[10px] font-data-mono text-red-300">ALCOHOL</div>
                <div className="text-body-sm font-body-sm text-on-surface">{seg.alcohol_pct_min}–{seg.alcohol_pct_max}%</div>
              </div>
            )}
            {seg.dessert_attach_pct_min != null && (
              <div className="bg-purple-950/30 rounded p-xs">
                <div className="text-[10px] font-data-mono text-purple-300">DESSERT</div>
                <div className="text-body-sm font-body-sm text-on-surface">{seg.dessert_attach_pct_min}–{seg.dessert_attach_pct_max}%</div>
              </div>
            )}
          </div>
        </div>
      )}

      <div className="grid grid-cols-2 gap-xs text-body-sm font-body-sm">
        <div><span className="text-on-surface-variant">Dwell:</span> <span className="text-on-surface font-data-mono">{dwell}</span></div>
        <div><span className="text-on-surface-variant">RevPASH:</span> <span className="text-on-surface font-data-mono">{revpash}</span></div>
        <div><span className="text-on-surface-variant">WOM:</span> <span className="text-on-surface font-data-mono">{wom}</span></div>
        <div><span className="text-on-surface-variant">Repeat:</span> <span className="text-on-surface font-data-mono">{repeat}</span></div>
        <div><span className="text-on-surface-variant">Peer:</span> <span className="text-on-surface font-data-mono">{seg.peer_influence_coefficient.toFixed(2)}</span></div>
        <div><span className="text-on-surface-variant">Discovers via:</span> <span className="text-on-surface">{discoveryPlatform}</span></div>
      </div>

      {seg.occasion_multipliers.length > 0 && (
        <div className="flex flex-col gap-xs">
          <div className="text-label-sm font-label-sm text-on-surface-variant uppercase tracking-wider">Spend by Occasion</div>
          <div className="flex flex-col gap-[3px]">
            {seg.occasion_multipliers.map((o) => (
              <div key={o.occasion_label} className="flex items-center justify-between text-body-sm font-body-sm">
                <span className="text-on-surface-variant">{o.occasion_label}</span>
                <span className="font-data-mono text-primary">
                  {o.multiplier_min === o.multiplier_max ? `${o.multiplier_min}×` : `${o.multiplier_min}–${o.multiplier_max}×`}
                </span>
              </div>
            ))}
          </div>
        </div>
      )}

      {seg.top_archetypes.length > 0 && (
        <div className="flex flex-col gap-xs">
          <div className="text-label-sm font-label-sm text-on-surface-variant uppercase tracking-wider">Primary Archetypes</div>
          <div className="flex flex-col gap-sm">
            {seg.top_archetypes.map((a) => {
              const trigger = seg.spend_triggers.find((t) => t.archetype_name === a.name);
              return (
                <div key={a.name} className="flex flex-col gap-[3px]">
                  <div className="flex items-center gap-sm">
                    <span className="w-2 h-2 rounded-full bg-[#7C3AED] flex-shrink-0" />
                    <div>
                      <span className="text-body-sm font-body-sm text-on-surface">{a.name}</span>
                      <span className="text-label-sm font-label-sm text-on-surface-variant ml-xs">· {a.demographic_label}</span>
                    </div>
                  </div>
                  {trigger?.staff_script && (
                    <div className="ml-[20px] bg-surface-variant/40 border border-outline-variant rounded px-sm py-xs">
                      <span className="text-[10px] font-data-mono text-primary/70 uppercase tracking-wider mr-xs">Say:</span>
                      <span className="text-[11px] font-body-sm text-on-surface-variant italic">"{trigger.staff_script}"</span>
                    </div>
                  )}
                </div>
              );
            })}
          </div>
        </div>
      )}

      {seg.low_to_high_spend_trigger && (
        <div className="border-t border-outline-variant pt-sm">
          <div className="text-label-sm font-label-sm text-on-surface-variant uppercase tracking-wider mb-xs">Upsell Lever</div>
          <div className="text-body-sm font-body-sm text-on-surface-variant leading-relaxed">
            {seg.low_to_high_spend_trigger.length > 140
              ? seg.low_to_high_spend_trigger.slice(0, 140) + "…"
              : seg.low_to_high_spend_trigger}
          </div>
        </div>
      )}
    </div>
  );
}

// ─── Aggregate metrics row ────────────────────────────────────────────────────

interface SimAggregate {
  alcoholScore: number;
  alcoholLabel: string;
  revpashMin: number;
  revpashMax: number;
  wom: number;
  peer: number;
  dominantPlatform: string;
}

function affinityLabel(score: number): string {
  if (score < 0.20) return "Low";
  if (score < 0.38) return "Low-Medium";
  if (score < 0.57) return "Medium";
  if (score < 0.73) return "Medium-High";
  if (score < 0.89) return "High";
  return "Very High";
}

interface MetricProps {
  icon: string;
  label: string;
  value: string;
  sub?: string;
  delta?: number | null;
}

function MetricChip({ icon, label, value, sub, delta }: MetricProps) {
  const deltaColor = delta == null ? "" : delta > 0.05 ? "text-signal-positive" : delta < -0.05 ? "text-signal-error" : "text-on-surface-variant";
  const deltaText = delta == null ? null : delta > 0 ? `+${delta.toFixed(2)}` : delta.toFixed(2);
  return (
    <div className="bg-surface border border-outline-variant rounded p-md flex flex-col gap-xs">
      <div className="flex items-center justify-between text-on-surface-variant">
        <div className="flex items-center gap-xs">
          <span className="material-symbols-outlined text-[16px]">{icon}</span>
          <span className="text-label-sm font-label-sm uppercase tracking-wider">{label}</span>
        </div>
        {deltaText != null && (
          <span className={`text-[10px] font-data-mono ${deltaColor}`}>{deltaText}</span>
        )}
      </div>
      <div className="text-headline-md font-headline-md text-primary font-bold">{value}</div>
      {sub && <div className="text-body-sm font-body-sm text-on-surface-variant">{sub}</div>}
    </div>
  );
}

// ─── Simulator ────────────────────────────────────────────────────────────────

function computeAggregate(segs: AudienceSegmentProfile[]): SimAggregate {
  if (segs.length === 0) {
    return { alcoholScore: 0, alcoholLabel: "—", revpashMin: 0, revpashMax: 0, wom: 0, peer: 0, dominantPlatform: "—" };
  }
  const w = 1 / segs.length;
  const alcoholScore = segs.reduce((s, seg) => s + w * (AFFINITY_SCORE[seg.alcohol_affinity] ?? 0), 0);
  const revpashMin = Math.round(segs.reduce((s, seg) => s + w * (seg.revpash_min_inr ?? 0), 0));
  const revpashMax = Math.round(segs.reduce((s, seg) => s + w * (seg.revpash_max_inr ?? 0), 0));
  const wom = Math.round(segs.reduce((s, seg) => s + w * (seg.wom_multiplier_min ?? 0), 0) * 10) / 10;
  const peer = Math.round(segs.reduce((s, seg) => s + w * seg.peer_influence_coefficient, 0) * 100) / 100;

  const discoveryPlats: string[] = [];
  segs.forEach((seg) =>
    seg.platforms.filter((p) => p.usage_type === "discovery" && p.strength === "primary")
      .forEach((p) => discoveryPlats.push(p.platform))
  );
  const dominantPlatform = discoveryPlats.length
    ? max(discoveryPlats) : "zomato";

  return { alcoholScore, alcoholLabel: affinityLabel(alcoholScore), revpashMin, revpashMax, wom, peer, dominantPlatform };
}

function max(arr: string[]): string {
  const freq: Record<string, number> = {};
  arr.forEach((s) => { freq[s] = (freq[s] ?? 0) + 1; });
  return Object.entries(freq).sort((a, b) => b[1] - a[1])[0][0];
}

interface SimulatorProps {
  allSegments: AudienceSegmentProfile[];
  currentSegmentIds: Set<string>;
  currentAggregate: { alcoholScore: number; revpashMin: number; revpashMax: number; wom: number; peer: number };
}

function AudienceSimulator({ allSegments, currentSegmentIds, currentAggregate }: SimulatorProps) {
  const [selected, setSelected] = useState<Set<string>>(new Set(currentSegmentIds));

  function toggle(id: string) {
    setSelected((prev) => {
      const next = new Set(prev);
      if (next.has(id)) {
        if (next.size === 1) return prev;
        next.delete(id);
      } else {
        next.add(id);
      }
      return next;
    });
  }

  const selectedSegs = useMemo(
    () => allSegments.filter((s) => selected.has(s.segment_id)),
    [allSegments, selected],
  );

  const agg = useMemo(() => computeAggregate(selectedSegs), [selectedSegs]);

  const delta = {
    alcohol: agg.alcoholScore - currentAggregate.alcoholScore,
    revpash: agg.revpashMin - currentAggregate.revpashMin,
    wom: agg.wom - currentAggregate.wom,
    peer: agg.peer - currentAggregate.peer,
  };

  const isCurrentMix =
    selected.size === currentSegmentIds.size &&
    [...selected].every((id) => currentSegmentIds.has(id));

  return (
    <div className="flex flex-col gap-lg">
      {/* Segment picker */}
      <div className="bg-[#1A1A24] border border-outline-variant rounded-lg p-lg flex flex-col gap-md">
        <div className="text-[10px] font-data-mono uppercase tracking-widest text-on-surface-variant/60">
          SELECT TARGET SEGMENT MIX
        </div>
        <div className="flex flex-wrap gap-sm">
          {allSegments.map((seg) => {
            const isCurrent = currentSegmentIds.has(seg.segment_id);
            const isSelected = selected.has(seg.segment_id);
            return (
              <button
                key={seg.segment_id}
                onClick={() => toggle(seg.segment_id)}
                className={`
                  px-sm py-xs border text-label-sm font-label-sm rounded uppercase transition-colors flex items-center gap-xs
                  ${isSelected
                    ? "bg-primary border-primary text-on-primary"
                    : "border-outline-variant text-on-surface-variant hover:border-primary/50 hover:text-on-surface"
                  }
                `}
              >
                {isSelected && <span className="material-symbols-outlined text-[13px]">check</span>}
                {seg.segment_name}
                {isCurrent && (
                  <span className="text-[8px] font-data-mono tracking-wider opacity-70 ml-[2px]">CURRENT</span>
                )}
              </button>
            );
          })}
        </div>
        <div className="text-[10px] text-on-surface-variant/50 font-body-sm">
          {selected.size} segment{selected.size !== 1 ? "s" : ""} selected · Equal weight · Min 1 required
        </div>
      </div>

      {/* Live aggregate */}
      <div className="flex flex-col gap-sm">
        <div className="flex items-center gap-sm">
          <div className="text-label-md font-label-md text-on-surface-variant uppercase tracking-wider">
            Projected Aggregate
          </div>
          {!isCurrentMix && (
            <span className="text-[10px] font-data-mono text-primary bg-primary/10 border border-primary/30 px-xs py-[2px] rounded uppercase tracking-wider">
              LIVE PREVIEW
            </span>
          )}
          {isCurrentMix && (
            <span className="text-[10px] font-data-mono text-on-surface-variant/50 uppercase tracking-wider">
              (same as current)
            </span>
          )}
        </div>
        <div className="grid grid-cols-2 lg:grid-cols-4 gap-md">
          <MetricChip
            icon="local_bar"
            label="Alcohol Affinity"
            value={agg.alcoholLabel}
            sub={`Score: ${(agg.alcoholScore * 100).toFixed(0)}% weighted avg`}
            delta={isCurrentMix ? null : delta.alcohol}
          />
          <MetricChip
            icon="payments"
            label="Expected RevPASH"
            value={`₹${agg.revpashMin}–${agg.revpashMax}`}
            sub="Per hour, per cover"
            delta={isCurrentMix ? null : delta.revpash / 200}
          />
          <MetricChip
            icon="record_voice_over"
            label="WOM Multiplier"
            value={`${agg.wom}×`}
            sub="Avg referral reach per visit"
            delta={isCurrentMix ? null : delta.wom / 5}
          />
          <MetricChip
            icon="groups"
            label="Peer Influence"
            value={agg.peer.toFixed(2)}
            sub="0.0 = independent · 1.0 = herd"
            delta={isCurrentMix ? null : delta.peer}
          />
        </div>

        {/* Alcohol insight bar */}
        <div className="bg-surface border border-outline-variant rounded p-md flex flex-col gap-xs">
          <div className="text-[10px] font-data-mono uppercase tracking-wider text-on-surface-variant/60">
            ALCOHOL AFFINITY — PROJECTED MIX
          </div>
          <AffinityBar score={agg.alcoholScore} />
          {!isCurrentMix && (
            <div className="flex items-center gap-xs text-body-sm font-body-sm text-on-surface-variant mt-xs">
              <span className="text-on-surface-variant/50">Current:</span>
              <div className="flex-1 h-1 bg-surface-container-high rounded-full overflow-hidden max-w-[120px]">
                <div
                  className="h-full rounded-full bg-outline-variant"
                  style={{ width: `${Math.round(currentAggregate.alcoholScore * 100)}%` }}
                />
              </div>
              <span className="text-[10px] font-data-mono text-on-surface-variant/50">
                {Math.round(currentAggregate.alcoholScore * 100)}%
              </span>
              <span className="mx-xs text-outline-variant">→</span>
              <span
                className={`text-[10px] font-data-mono font-bold ${
                  delta.alcohol > 0.05 ? "text-signal-positive" :
                  delta.alcohol < -0.05 ? "text-signal-error" : "text-on-surface-variant"
                }`}
              >
                {Math.round(agg.alcoholScore * 100)}%
                {" "}({delta.alcohol >= 0 ? "+" : ""}{Math.round(delta.alcohol * 100)}pts)
              </span>
            </div>
          )}
        </div>

        {/* Dominant platform note */}
        <div className="text-[11px] text-on-surface-variant/60 font-body-sm border-t border-outline-variant/50 pt-sm">
          Dominant discovery channel for this mix:{" "}
          <span className="text-primary">{PLATFORM_LABELS[agg.dominantPlatform] ?? agg.dominantPlatform}</span>
          {" "}— concentrate organic content budget here first.
        </div>
      </div>

      {/* Selected segment cards */}
      <div className="flex flex-col gap-sm">
        <h3 className="text-label-md font-label-md text-on-surface-variant uppercase tracking-wider">
          Selected Segment Profiles
        </h3>
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-md">
          {selectedSegs.map((seg) => (
            <SegmentCard key={seg.segment_id} seg={seg} />
          ))}
        </div>
      </div>
    </div>
  );
}

// ─── Current Mix view ─────────────────────────────────────────────────────────

function CurrentView({ data }: { data: AudienceResponse }) {
  const { segment_profiles, aggregate } = data;
  return (
    <div className="flex flex-col gap-lg">
      {/* Structural insight */}
      <div className="bg-surface border border-primary/30 rounded p-md flex gap-md">
        <span className="material-symbols-outlined text-primary text-[24px] flex-shrink-0 mt-[2px]">psychology</span>
        <div className="flex flex-col gap-xs">
          <div className="text-label-md font-label-md text-primary uppercase tracking-wider">Structural Insight</div>
          <p className="text-body-md font-body-md text-on-surface leading-relaxed">{aggregate.structural_insight}</p>
        </div>
      </div>

      {/* Aggregate */}
      <div className="flex flex-col gap-sm">
        <h3 className="text-label-md font-label-md text-on-surface-variant uppercase tracking-wider">
          Aggregate Profile — Weighted Across Your Top Segments
        </h3>
        <div className="grid grid-cols-2 lg:grid-cols-4 gap-md">
          <MetricChip icon="local_bar"        label="Alcohol Affinity"  value={aggregate.alcohol_affinity_label} sub={`Score: ${(aggregate.alcohol_affinity_score * 100).toFixed(0)}% weighted avg`} />
          <MetricChip icon="payments"         label="Expected RevPASH"  value={`₹${aggregate.expected_revpash_min}–${aggregate.expected_revpash_max}`} sub="Per hour, per cover" />
          <MetricChip icon="record_voice_over" label="WOM Multiplier"   value={`${aggregate.avg_wom_multiplier}×`} sub="Avg referral reach per visit" />
          <MetricChip icon="groups"           label="Peer Influence"    value={aggregate.avg_peer_influence.toFixed(2)} sub="0.0 = independent · 1.0 = herd" />
        </div>
      </div>

      {/* Segment profiles */}
      <div className="flex flex-col gap-sm">
        <div className="flex items-center justify-between">
          <h3 className="text-label-md font-label-md text-on-surface-variant uppercase tracking-wider">Segment Behavioral Profiles</h3>
          <span className="text-label-sm font-label-sm text-on-surface-variant">Source: Behavioral Intelligence Module v1.0 · Urban India</span>
        </div>
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-md">
          {segment_profiles.map((seg) => <SegmentCard key={seg.segment_id} seg={seg} />)}
        </div>
      </div>

      {/* Platform table */}
      <div className="bg-surface border border-outline-variant rounded p-md flex flex-col gap-md">
        <div className="flex justify-between items-center border-b border-outline-variant pb-sm">
          <h3 className="text-label-md font-label-md text-on-surface uppercase tracking-wider">Platform Reach Map</h3>
          <span className="material-symbols-outlined text-outline text-[18px]">share</span>
        </div>
        <div className="overflow-x-auto">
          <table className="w-full text-body-sm font-body-sm">
            <thead>
              <tr className="text-on-surface-variant text-label-sm font-label-sm uppercase tracking-wider border-b border-outline-variant">
                <th className="text-left pb-sm pr-md">Segment</th>
                <th className="text-left pb-sm pr-md">Discovery</th>
                <th className="text-left pb-sm pr-md">Validation</th>
                <th className="text-left pb-sm pr-md">Booking</th>
                <th className="text-left pb-sm">Post-Visit Review</th>
              </tr>
            </thead>
            <tbody>
              {segment_profiles.map((seg) => {
                const byType = (type: string) =>
                  seg.platforms
                    .filter((p) => p.usage_type === type && p.strength !== "minimal")
                    .map((p) => PLATFORM_LABELS[p.platform] ?? p.platform)
                    .join(", ") || "—";
                return (
                  <tr key={seg.segment_id} className="border-b border-surface-variant last:border-0">
                    <td className="py-sm pr-md text-on-surface font-label-md">{seg.segment_name}</td>
                    <td className="py-sm pr-md text-on-surface-variant">{byType("discovery")}</td>
                    <td className="py-sm pr-md text-on-surface-variant">{byType("validation")}</td>
                    <td className="py-sm pr-md text-on-surface-variant">{byType("booking")}</td>
                    <td className="py-sm text-on-surface-variant">{byType("post_visit_review")}</td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        </div>
        <div className="text-label-sm font-label-sm text-on-surface-variant/60 border-t border-outline-variant pt-sm">
          Dominant discovery channel across your mix:{" "}
          <span className="text-primary">{PLATFORM_LABELS[aggregate.dominant_discovery_platform] ?? aggregate.dominant_discovery_platform}</span>
          {" "}— concentrate organic content budget here first.
        </div>
      </div>
    </div>
  );
}

// ─── Main client component ────────────────────────────────────────────────────

type Tab = "current" | "simulator";

interface Props {
  currentData: AudienceResponse;
  allSegments: AudienceSegmentProfile[];
}

export default function AudienceClient({ currentData, allSegments }: Props) {
  const [tab, setTab] = useState<Tab>("current");

  const currentSegmentIds = useMemo(
    () => new Set(currentData.segment_profiles.map((s) => s.segment_id)),
    [currentData],
  );

  const currentAggregate = {
    alcoholScore: currentData.aggregate.alcohol_affinity_score,
    revpashMin: currentData.aggregate.expected_revpash_min,
    revpashMax: currentData.aggregate.expected_revpash_max,
    wom: currentData.aggregate.avg_wom_multiplier,
    peer: currentData.aggregate.avg_peer_influence,
  };

  return (
    <div className="flex flex-col gap-lg">
      {/* Sub-tab bar */}
      <div className="flex gap-xs border-b border-outline-variant">
        {[
          { id: "current" as Tab,   label: "Current Mix",        icon: "groups" },
          { id: "simulator" as Tab, label: "Audience Simulator", icon: "tune" },
        ].map((t) => (
          <button
            key={t.id}
            onClick={() => setTab(t.id)}
            className={`flex items-center gap-xs pb-sm px-sm text-label-md font-label-md whitespace-nowrap border-b-2 transition-colors -mb-px ${
              tab === t.id
                ? "text-primary border-primary"
                : "text-on-surface-variant border-transparent hover:text-on-surface hover:border-outline-variant"
            }`}
          >
            <span className="material-symbols-outlined text-[16px]">{t.icon}</span>
            {t.label}
          </button>
        ))}
      </div>

      {/* Tab content */}
      {tab === "current" && <CurrentView data={currentData} />}
      {tab === "simulator" && (
        <AudienceSimulator
          allSegments={allSegments}
          currentSegmentIds={currentSegmentIds}
          currentAggregate={currentAggregate}
        />
      )}
    </div>
  );
}
