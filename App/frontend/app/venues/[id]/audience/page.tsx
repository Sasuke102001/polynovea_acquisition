import Link from "next/link";
import { getAudience, type AudienceSegmentProfile, type AudienceAggregate } from "@/lib/api";

// ─── Helpers ─────────────────────────────────────────────────────────────────

const PLATFORM_LABELS: Record<string, string> = {
  instagram:      "Instagram",
  tiktok:         "TikTok",
  zomato:         "Zomato",
  swiggy:         "Swiggy",
  swiggy_dineout: "Swiggy Dineout",
  zomato_gold:    "Zomato Gold",
  google_maps:    "Google Maps",
  google_reviews: "Google Reviews",
  direct:         "Direct",
  word_of_mouth:  "Word of Mouth",
};

const USAGE_LABELS: Record<string, string> = {
  discovery:        "Discovery",
  validation:       "Validation",
  booking:          "Booking",
  post_visit_review:"Review",
  wom:              "WOM",
};

const DRIVER_LABELS: Record<string, string> = {
  habit:          "Habit",
  social_occasion:"Social Occasion",
  identity:       "Identity",
  fomo:           "FOMO",
  discovery:      "Discovery",
  none:           "—",
};

// ─── Sub-components ───────────────────────────────────────────────────────────

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
  const color =
    score < 0.30 ? "#52525b"
    : score < 0.50 ? "#d97706"
    : score < 0.70 ? "#ea580c"
    : "#ef4444";
  return (
    <div className="flex items-center gap-sm">
      <div className="flex-1 h-1.5 bg-surface-variant rounded-full overflow-hidden">
        <div
          className="h-full rounded-full transition-all"
          style={{ width: `${pct}%`, backgroundColor: color }}
        />
      </div>
      <span className="text-[10px] font-data-mono text-on-surface-variant w-8 text-right">
        {pct}%
      </span>
    </div>
  );
}

function MetricChip({
  icon, label, value, sub,
}: { icon: string; label: string; value: string; sub?: string }) {
  return (
    <div className="bg-surface border border-outline-variant rounded p-md flex flex-col gap-xs">
      <div className="flex items-center gap-xs text-on-surface-variant">
        <span className="material-symbols-outlined text-[16px]">{icon}</span>
        <span className="text-label-sm font-label-sm uppercase tracking-wider">{label}</span>
      </div>
      <div className="text-headline-md font-headline-md text-primary font-bold">{value}</div>
      {sub && <div className="text-body-sm font-body-sm text-on-surface-variant">{sub}</div>}
    </div>
  );
}

function SegmentCard({ seg }: { seg: AudienceSegmentProfile }) {
  const revpash =
    seg.revpash_min_inr && seg.revpash_max_inr
      ? `₹${seg.revpash_min_inr}–${seg.revpash_max_inr}`
      : "—";
  const dwell =
    seg.dwell_min_minutes && seg.dwell_max_minutes
      ? `${seg.dwell_min_minutes}–${seg.dwell_max_minutes} min`
      : "—";
  const wom =
    seg.wom_multiplier_min != null
      ? `${seg.wom_multiplier_min}x`
      : "—";
  const repeat =
    seg.repeat_tendency_pct_min && seg.repeat_tendency_pct_max
      ? `${seg.repeat_tendency_pct_min}–${seg.repeat_tendency_pct_max}% / ${seg.repeat_window_days}d`
      : "—";

  const discoveryPlatform =
    seg.platforms
      .filter((p) => p.usage_type === "discovery" && p.strength === "primary")
      .map((p) => PLATFORM_LABELS[p.platform] ?? p.platform)[0] ?? "—";

  return (
    <div className="bg-surface border border-brand-border rounded p-md flex flex-col gap-md">
      {/* Header */}
      <div className="flex justify-between items-start border-b border-outline-variant pb-sm">
        <div>
          <h3 className="text-headline-md font-headline-md text-on-surface font-bold">
            {seg.segment_name}
          </h3>
          <div className="text-display-lg font-display-lg text-primary font-bold mt-[2px]">
            {seg.alignment_pct.toFixed(0)}%
          </div>
          <div className="text-label-sm font-label-sm text-on-surface-variant">
            #{seg.segment_rank} segment
          </div>
        </div>
        <AffinityBadge affinity={seg.alcohol_affinity} />
      </div>

      {/* Alcohol section */}
      <div className="flex flex-col gap-xs">
        <div className="text-label-sm font-label-sm text-on-surface-variant uppercase tracking-wider">
          Alcohol
        </div>
        <AffinityBar score={seg.alcohol_affinity_score} />
        <div className="text-body-sm font-body-sm text-on-surface-variant">
          Driver:{" "}
          <span className="text-on-surface">
            {DRIVER_LABELS[seg.alcohol_primary_driver] ?? seg.alcohol_primary_driver}
          </span>
          {seg.beverage_preference && (
            <span className="text-outline"> · {seg.beverage_preference}</span>
          )}
        </div>
      </div>

      {/* Spend composition */}
      {(seg.food_pct_min || seg.alcohol_pct_min || seg.dessert_attach_pct_min) && (
        <div className="flex flex-col gap-xs">
          <div className="text-label-sm font-label-sm text-on-surface-variant uppercase tracking-wider">
            Spend Mix
          </div>
          <div className="grid grid-cols-3 gap-xs text-center">
            {seg.food_pct_min != null && (
              <div className="bg-amber-950/30 rounded p-xs">
                <div className="text-[10px] font-data-mono text-amber-300">FOOD</div>
                <div className="text-body-sm font-body-sm text-on-surface">
                  {seg.food_pct_min}–{seg.food_pct_max}%
                </div>
              </div>
            )}
            {seg.alcohol_pct_min != null && (
              <div className="bg-red-950/30 rounded p-xs">
                <div className="text-[10px] font-data-mono text-red-300">ALCOHOL</div>
                <div className="text-body-sm font-body-sm text-on-surface">
                  {seg.alcohol_pct_min}–{seg.alcohol_pct_max}%
                </div>
              </div>
            )}
            {seg.dessert_attach_pct_min != null && (
              <div className="bg-purple-950/30 rounded p-xs">
                <div className="text-[10px] font-data-mono text-purple-300">DESSERT</div>
                <div className="text-body-sm font-body-sm text-on-surface">
                  {seg.dessert_attach_pct_min}–{seg.dessert_attach_pct_max}%
                </div>
              </div>
            )}
          </div>
          {seg.avg_check_vs_baseline_pct_min != null && (
            <div className="text-body-sm font-body-sm text-on-surface-variant">
              Avg check:{" "}
              <span className="text-on-surface">
                {seg.avg_check_vs_baseline_pct_min >= 0 ? "+" : ""}
                {seg.avg_check_vs_baseline_pct_min}
                {seg.avg_check_vs_baseline_pct_min !== seg.avg_check_vs_baseline_pct_max
                  ? `–${seg.avg_check_vs_baseline_pct_max && seg.avg_check_vs_baseline_pct_max >= 0 ? "+" : ""}${seg.avg_check_vs_baseline_pct_max}`
                  : ""}
                % vs baseline
              </span>
            </div>
          )}
        </div>
      )}

      {/* Economics grid */}
      <div className="grid grid-cols-2 gap-xs text-body-sm font-body-sm">
        <div>
          <span className="text-on-surface-variant">Dwell:</span>{" "}
          <span className="text-on-surface font-data-mono">{dwell}</span>
        </div>
        <div>
          <span className="text-on-surface-variant">RevPASH:</span>{" "}
          <span className="text-on-surface font-data-mono">{revpash}</span>
        </div>
        <div>
          <span className="text-on-surface-variant">WOM:</span>{" "}
          <span className="text-on-surface font-data-mono">{wom}</span>
        </div>
        <div>
          <span className="text-on-surface-variant">Repeat:</span>{" "}
          <span className="text-on-surface font-data-mono">{repeat}</span>
        </div>
        <div>
          <span className="text-on-surface-variant">Peer:</span>{" "}
          <span className="text-on-surface font-data-mono">{seg.peer_influence_coefficient.toFixed(2)}</span>
        </div>
        <div>
          <span className="text-on-surface-variant">Discovers via:</span>{" "}
          <span className="text-on-surface">{discoveryPlatform}</span>
        </div>
      </div>

      {/* Archetypes */}
      {seg.top_archetypes.length > 0 && (
        <div className="flex flex-col gap-xs">
          <div className="text-label-sm font-label-sm text-on-surface-variant uppercase tracking-wider">
            Primary Archetypes
          </div>
          <div className="flex flex-col gap-xs">
            {seg.top_archetypes.map((a) => (
              <div key={a.name} className="flex items-center gap-sm">
                <span className="w-2 h-2 rounded-full bg-[#7C3AED] flex-shrink-0" />
                <div>
                  <span className="text-body-sm font-body-sm text-on-surface">{a.name}</span>
                  <span className="text-label-sm font-label-sm text-on-surface-variant ml-xs">
                    · {a.demographic_label}
                  </span>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Spend trigger */}
      {seg.low_to_high_spend_trigger && (
        <div className="border-t border-outline-variant pt-sm">
          <div className="text-label-sm font-label-sm text-on-surface-variant uppercase tracking-wider mb-xs">
            Upsell Lever
          </div>
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

function AggregateRow({ agg }: { agg: AudienceAggregate }) {
  return (
    <div className="grid grid-cols-2 lg:grid-cols-4 gap-md">
      <MetricChip
        icon="local_bar"
        label="Alcohol Affinity"
        value={agg.alcohol_affinity_label}
        sub={`Score: ${(agg.alcohol_affinity_score * 100).toFixed(0)}% weighted avg`}
      />
      <MetricChip
        icon="payments"
        label="Expected RevPASH"
        value={`₹${agg.expected_revpash_min}–${agg.expected_revpash_max}`}
        sub="Per hour, per cover"
      />
      <MetricChip
        icon="record_voice_over"
        label="WOM Multiplier"
        value={`${agg.avg_wom_multiplier}×`}
        sub="Avg referral reach per visit"
      />
      <MetricChip
        icon="groups"
        label="Peer Influence"
        value={agg.avg_peer_influence.toFixed(2)}
        sub="0.0 = independent · 1.0 = herd"
      />
    </div>
  );
}

// ─── Tab bar (matches other pages) ───────────────────────────────────────────

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
    <div className="flex gap-md border-b border-outline-variant mt-sm overflow-x-auto no-scrollbar">
      {tabs.map((tab) => (
        <Link
          key={tab.label}
          href={tab.href}
          className={`pb-sm px-sm text-label-md font-label-md whitespace-nowrap transition-colors ${
            tab.label === "Audience"
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

// ─── Page ─────────────────────────────────────────────────────────────────────

export default async function AudiencePage({
  params,
}: {
  params: Promise<{ id: string }>;
}) {
  const { id } = await params;

  let data;
  try {
    data = await getAudience(id);
  } catch {
    return (
      <div className="p-margin text-error font-body-sm text-body-sm">
        Failed to load audience data. Make sure the backend is running on port 8000.
      </div>
    );
  }

  const { venue_name, venue_area, segment_profiles, aggregate } = data;

  return (
    <div className="p-margin flex flex-col gap-lg max-w-[1400px] w-full mx-auto">
      {/* ── Venue header ── */}
      <div className="flex flex-col gap-xs border-b border-outline-variant pb-md">
        <div className="flex items-baseline gap-sm flex-wrap">
          <h2 className="text-headline-lg font-headline-lg text-primary-container font-bold">
            {venue_name}
          </h2>
          <div className="flex items-center gap-xs text-on-surface-variant">
            <span className="material-symbols-outlined text-[16px]">location_on</span>
            <span className="text-body-sm font-body-sm">{venue_area}</span>
          </div>
        </div>
        <VenueTabs venueId={id} />
      </div>

      {/* ── Structural insight banner ── */}
      <div className="bg-surface border border-primary/30 rounded p-md flex gap-md">
        <span className="material-symbols-outlined text-primary text-[24px] flex-shrink-0 mt-[2px]">
          psychology
        </span>
        <div className="flex flex-col gap-xs">
          <div className="text-label-md font-label-md text-primary uppercase tracking-wider">
            Structural Insight
          </div>
          <p className="text-body-md font-body-md text-on-surface leading-relaxed">
            {aggregate.structural_insight}
          </p>
          <Link
            href={`/venues/${id}/transform`}
            className="text-label-sm font-label-sm text-primary/80 hover:text-primary flex items-center gap-xs mt-xs"
          >
            Explore segment shifts in Transform
            <span className="material-symbols-outlined text-[14px]">arrow_forward</span>
          </Link>
        </div>
      </div>

      {/* ── Aggregate metrics ── */}
      <div className="flex flex-col gap-sm">
        <h3 className="text-label-md font-label-md text-on-surface-variant uppercase tracking-wider">
          Aggregate Profile — Weighted Across Your Top Segments
        </h3>
        <AggregateRow agg={aggregate} />
      </div>

      {/* ── Segment behavioral profiles ── */}
      <div className="flex flex-col gap-sm">
        <div className="flex items-center justify-between">
          <h3 className="text-label-md font-label-md text-on-surface-variant uppercase tracking-wider">
            Segment Behavioral Profiles
          </h3>
          <span className="text-label-sm font-label-sm text-on-surface-variant">
            Source: Behavioral Intelligence Module v1.0 · Urban India
          </span>
        </div>
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-md">
          {segment_profiles.map((seg) => (
            <SegmentCard key={seg.segment_id} seg={seg} />
          ))}
        </div>
      </div>

      {/* ── Platform reach map ── */}
      <div className="bg-surface border border-outline-variant rounded p-md flex flex-col gap-md">
        <div className="flex justify-between items-center border-b border-outline-variant pb-sm">
          <h3 className="text-label-md font-label-md text-on-surface uppercase tracking-wider">
            Platform Reach Map
          </h3>
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
                  <tr
                    key={seg.segment_id}
                    className="border-b border-surface-variant last:border-0"
                  >
                    <td className="py-sm pr-md text-on-surface font-label-md font-label-md">
                      {seg.segment_name}
                    </td>
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
          <span className="text-primary">
            {PLATFORM_LABELS[aggregate.dominant_discovery_platform] ?? aggregate.dominant_discovery_platform}
          </span>
          {" "}— concentrate organic content budget here first.
        </div>
      </div>

    </div>
  );
}
