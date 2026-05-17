"""
routers/audience.py
GET /api/venues/{venue_id}/audience  →  AudienceResponse

Audience Behavior tab — shows venue owners who they actually attract and
how those people behave: spend composition, alcohol affinity, dwell economics,
WOM multiplier, platform reach, and the structural insight about their mix.

All intelligence is sourced from the behavioral research DB tables seeded from
behavioral_intelligence_module.md (Kimi, v1.0) and validated research documents.
"""

from fastapi import APIRouter, HTTPException, Path

from database import get_pool
from models import (
    AudienceResponse, AudienceSegmentProfile, AudienceAggregate,
    AudiencePlatformRow, ArchetypeChip, OccasionMultiplier, SpendTrigger,
)
from routers.utils import ARCHETYPE_DESCRIPTORS

router = APIRouter()

_float = lambda v: float(v) if v is not None else 0.0
_int   = lambda v: int(v)   if v is not None else None


# Ordinal mapping for affinity level → 0.0–1.0 score
_AFFINITY_SCORE: dict[str, float] = {
    "none":        0.00,
    "low":         0.10,
    "low_medium":  0.28,
    "medium":      0.48,
    "medium_high": 0.65,
    "high":        0.82,
    "very_high":   0.95,
}

_PLATFORM_LABELS: dict[str, str] = {
    "instagram":     "Instagram",
    "tiktok":        "TikTok / Reels",
    "zomato":        "Zomato",
    "swiggy":        "Swiggy",
    "swiggy_dineout":"Swiggy Dineout",
    "zomato_gold":   "Zomato Gold",
    "google_maps":   "Google Maps",
    "google_reviews":"Google Reviews",
    "direct":        "Direct / Phone",
    "word_of_mouth": "Word of Mouth",
}


def _affinity_label(score: float) -> str:
    if score < 0.20: return "Low"
    if score < 0.38: return "Low-Medium"
    if score < 0.57: return "Medium"
    if score < 0.73: return "Medium-High"
    if score < 0.89: return "High"
    return "Very High"


def _structural_insight(
    alcohol_score: float,
    top_segment_names: list[str],
    dominant_platform: str,
) -> str:
    mix = " + ".join(top_segment_names[:2]) if top_segment_names else "your current mix"
    platform_label = _PLATFORM_LABELS.get(dominant_platform, dominant_platform)

    if alcohol_score < 0.30:
        return (
            f"{mix} is structurally low-alcohol — these segments have low beverage affinity "
            f"regardless of your menu or pricing. Segment composition is the lever, "
            f"not menu engineering. Shifting toward Social Crowd or Couples would increase "
            f"alcohol-ordering likelihood significantly and unlock a higher RevPASH curve. "
            f"Your current audience primarily discovers venues via {platform_label}."
        )
    if alcohol_score < 0.55:
        return (
            f"{mix} has moderate alcohol engagement. Occasion-driven segments are present "
            f"but not dominant. Targeted FOMO and Social Proof mechanics for Social Crowd "
            f"would accelerate beverage revenue without requiring a full segment shift. "
            f"Primary discovery channel for your current mix: {platform_label}."
        )
    return (
        f"{mix} is alcohol-forward — group and social occasion dynamics drive strong beverage "
        f"revenue. Focus on first-round anchoring, group bundle mechanics, and scarcity signals "
        f"(limited cocktails, last-call culture) to maximise the alcohol tail of your revenue curve. "
        f"Primary discovery channel: {platform_label}."
    )


@router.get("/{venue_id}/audience", response_model=AudienceResponse)
async def get_audience(venue_id: int = Path(...)):
    """
    Audience Behavior tab.

    Returns the behavioral profile of this venue's actual customer mix:
    - Per-segment: spend composition, alcohol affinity, dwell economics,
      WOM multiplier, platform usage, spend triggers
    - Aggregate: weighted metrics across top 3 segments + structural insight

    Intelligence sourced from segment_behavioral_profiles and related tables
    seeded from behavioral_intelligence_module.md.
    """
    pool = get_pool()

    async with pool.acquire() as conn:
        venue_row = await conn.fetchrow(
            "SELECT name, area FROM venues WHERE id = $1", venue_id
        )
        if not venue_row:
            raise HTTPException(status_code=404, detail="Venue not found")

        # Top 3 demographic segments with behavioral profiles
        seg_rows = await conn.fetch(
            """
            SELECT
                vds.segment_id,
                vds.alignment_score,
                vds.segment_rank,
                sbp.label                           AS segment_name,
                sbp.food_pct_min,
                sbp.food_pct_max,
                sbp.alcohol_pct_min,
                sbp.alcohol_pct_max,
                sbp.dessert_attach_pct_min,
                sbp.dessert_attach_pct_max,
                sbp.avg_check_vs_baseline_pct_min,
                sbp.avg_check_vs_baseline_pct_max,
                sbp.alcohol_affinity::text          AS alcohol_affinity,
                sbp.alcohol_primary_driver::text    AS alcohol_primary_driver,
                sbp.beverage_preference,
                sbp.peer_influence_coefficient,
                sbp.dwell_min_minutes,
                sbp.dwell_max_minutes,
                sbp.revpash_min_inr,
                sbp.revpash_max_inr,
                sbp.diminishing_returns_minutes,
                sbp.repeat_tendency_pct_min,
                sbp.repeat_tendency_pct_max,
                sbp.repeat_window_days,
                sbp.wom_multiplier_min,
                sbp.wom_multiplier_max,
                sbp.discovery_rate::text            AS discovery_rate,
                sbp.primary_trigger,
                sbp.low_to_high_spend_trigger
            FROM  venue_demographic_scores vds
            JOIN  segment_behavioral_profiles sbp
                  ON sbp.segment_key = vds.segment_id
            WHERE vds.venue_id = $1
            ORDER BY vds.segment_rank
            LIMIT 3
            """,
            venue_id,
        )

        if not seg_rows:
            raise HTTPException(
                status_code=404,
                detail="No segment data found for this venue",
            )

        seg_keys = [r["segment_id"] for r in seg_rows]

        # Top 2 archetypes per segment
        arch_rows = await conn.fetch(
            """
            SELECT
                sbp.segment_key,
                abp.archetype_key,
                abp.label AS archetype_label
            FROM  segment_archetype_affinity saa
            JOIN  segment_behavioral_profiles sbp ON sbp.id = saa.segment_id
            JOIN  archetype_behavioral_profiles abp ON abp.id = saa.archetype_id
            WHERE sbp.segment_key = ANY($1::text[])
              AND saa.affinity_rank <= 2
            ORDER BY sbp.segment_key, saa.affinity_rank
            """,
            seg_keys,
        )

        # Occasion spend multipliers per segment
        occasion_rows = await conn.fetch(
            """
            SELECT
                sbp.segment_key,
                som.occasion_label,
                som.multiplier_min,
                som.multiplier_max,
                som.notes
            FROM  segment_occasion_multipliers som
            JOIN  segment_behavioral_profiles sbp ON sbp.id = som.segment_id
            WHERE sbp.segment_key = ANY($1::text[])
            ORDER BY sbp.segment_key, som.multiplier_max DESC
            """,
            seg_keys,
        )

        # Top spend trigger (staff script) per archetype in top 2 per segment
        trigger_rows = await conn.fetch(
            """
            SELECT
                sbp.segment_key,
                abp.label        AS archetype_name,
                ast.trigger_text,
                ast.staff_script
            FROM  segment_archetype_affinity saa
            JOIN  segment_behavioral_profiles   sbp ON sbp.id = saa.segment_id
            JOIN  archetype_behavioral_profiles abp ON abp.id = saa.archetype_id
            JOIN  archetype_spend_triggers      ast ON ast.archetype_id = abp.id
            WHERE sbp.segment_key = ANY($1::text[])
              AND saa.affinity_rank <= 2
              AND ast.trigger_rank  = 1
            ORDER BY sbp.segment_key, saa.affinity_rank
            """,
            seg_keys,
        )

        # Platform usage per segment (primary + secondary for discovery)
        platform_rows = await conn.fetch(
            """
            SELECT
                sbp.segment_key,
                spu.platform::text   AS platform,
                spu.usage_type::text AS usage_type,
                spu.strength::text   AS strength
            FROM  segment_platform_usage spu
            JOIN  segment_behavioral_profiles sbp ON sbp.id = spu.segment_id
            WHERE sbp.segment_key = ANY($1::text[])
            ORDER BY sbp.segment_key,
                     CASE spu.strength WHEN 'primary' THEN 1 WHEN 'secondary' THEN 2 ELSE 3 END
            """,
            seg_keys,
        )

    # ── Organise arch and platform rows by segment ────────────────────────────

    archs_by_seg: dict[str, list[ArchetypeChip]] = {k: [] for k in seg_keys}
    for r in arch_rows:
        sk = r["segment_key"]
        if sk in archs_by_seg:
            archs_by_seg[sk].append(ArchetypeChip(
                name=r["archetype_label"],
                demographic_label=ARCHETYPE_DESCRIPTORS.get(r["archetype_label"], r["archetype_label"]),
            ))

    occasions_by_seg: dict[str, list[OccasionMultiplier]] = {k: [] for k in seg_keys}
    for r in occasion_rows:
        sk = r["segment_key"]
        if sk in occasions_by_seg:
            occasions_by_seg[sk].append(OccasionMultiplier(
                occasion_label=r["occasion_label"],
                multiplier_min=float(r["multiplier_min"]),
                multiplier_max=float(r["multiplier_max"]),
                notes=r["notes"],
            ))

    triggers_by_seg: dict[str, list[SpendTrigger]] = {k: [] for k in seg_keys}
    for r in trigger_rows:
        sk = r["segment_key"]
        if sk in triggers_by_seg:
            triggers_by_seg[sk].append(SpendTrigger(
                archetype_name=r["archetype_name"],
                trigger_text=r["trigger_text"],
                staff_script=r["staff_script"],
            ))

    plat_by_seg: dict[str, list[AudiencePlatformRow]] = {k: [] for k in seg_keys}
    for r in platform_rows:
        sk = r["segment_key"]
        if sk in plat_by_seg:
            plat_by_seg[sk].append(AudiencePlatformRow(
                platform=r["platform"],
                usage_type=r["usage_type"],
                strength=r["strength"],
            ))

    # ── Build segment profiles ────────────────────────────────────────────────

    segment_profiles: list[AudienceSegmentProfile] = []
    for r in seg_rows:
        affinity_str   = r["alcohol_affinity"] or "low"
        affinity_score = _AFFINITY_SCORE.get(affinity_str, 0.0)

        segment_profiles.append(AudienceSegmentProfile(
            segment_id=r["segment_id"],
            segment_name=r["segment_name"],
            alignment_pct=round(_float(r["alignment_score"]) * 100, 1),
            segment_rank=r["segment_rank"],
            food_pct_min=_int(r["food_pct_min"]),
            food_pct_max=_int(r["food_pct_max"]),
            alcohol_pct_min=_int(r["alcohol_pct_min"]),
            alcohol_pct_max=_int(r["alcohol_pct_max"]),
            dessert_attach_pct_min=_int(r["dessert_attach_pct_min"]),
            dessert_attach_pct_max=_int(r["dessert_attach_pct_max"]),
            avg_check_vs_baseline_pct_min=_int(r["avg_check_vs_baseline_pct_min"]),
            avg_check_vs_baseline_pct_max=_int(r["avg_check_vs_baseline_pct_max"]),
            alcohol_affinity=affinity_str,
            alcohol_affinity_score=affinity_score,
            alcohol_primary_driver=r["alcohol_primary_driver"] or "none",
            beverage_preference=r["beverage_preference"],
            peer_influence_coefficient=_float(r["peer_influence_coefficient"]),
            dwell_min_minutes=_int(r["dwell_min_minutes"]),
            dwell_max_minutes=_int(r["dwell_max_minutes"]),
            revpash_min_inr=_int(r["revpash_min_inr"]),
            revpash_max_inr=_int(r["revpash_max_inr"]),
            diminishing_returns_minutes=_int(r["diminishing_returns_minutes"]),
            repeat_tendency_pct_min=_int(r["repeat_tendency_pct_min"]),
            repeat_tendency_pct_max=_int(r["repeat_tendency_pct_max"]),
            repeat_window_days=_int(r["repeat_window_days"]),
            wom_multiplier_min=_float(r["wom_multiplier_min"]) if r["wom_multiplier_min"] else None,
            wom_multiplier_max=_float(r["wom_multiplier_max"]) if r["wom_multiplier_max"] else None,
            discovery_rate=r["discovery_rate"] or "medium",
            primary_trigger=r["primary_trigger"],
            low_to_high_spend_trigger=r["low_to_high_spend_trigger"],
            top_archetypes=archs_by_seg.get(r["segment_id"], []),
            platforms=plat_by_seg.get(r["segment_id"], []),
            occasion_multipliers=occasions_by_seg.get(r["segment_id"], []),
            spend_triggers=triggers_by_seg.get(r["segment_id"], []),
        ))

    # ── Weighted aggregate across top 3 segments ──────────────────────────────

    total_weight = sum(_float(r["alignment_score"]) for r in seg_rows)
    if total_weight == 0:
        total_weight = 1.0

    def _wavg(values: list[float | None]) -> float:
        num = sum(
            _float(seg_rows[i]["alignment_score"]) * (values[i] or 0.0)
            for i in range(len(seg_rows))
            if i < len(values)
        )
        return num / total_weight

    aff_scores = [_AFFINITY_SCORE.get(r["alcohol_affinity"] or "low", 0.0) for r in seg_rows]
    agg_alcohol = _wavg(aff_scores)

    revpash_mins = [_float(r["revpash_min_inr"]) for r in seg_rows]
    revpash_maxs = [_float(r["revpash_max_inr"]) for r in seg_rows]
    agg_revpash_min = round(_wavg(revpash_mins))
    agg_revpash_max = round(_wavg(revpash_maxs))

    wom_mins = [_float(r["wom_multiplier_min"]) for r in seg_rows]
    agg_wom = round(_wavg(wom_mins), 1)

    peer_coefs = [_float(r["peer_influence_coefficient"]) for r in seg_rows]
    agg_peer = round(_wavg(peer_coefs), 2)

    # Dominant primary discovery platform (most common across top segments)
    discovery_plats: list[str] = []
    for sk in seg_keys:
        for p in plat_by_seg.get(sk, []):
            if p.usage_type == "discovery" and p.strength == "primary":
                discovery_plats.append(p.platform)
    dominant_platform = (
        max(set(discovery_plats), key=discovery_plats.count)
        if discovery_plats
        else "zomato"
    )

    seg_names = [r["segment_name"] for r in seg_rows]
    structural = _structural_insight(agg_alcohol, seg_names, dominant_platform)

    aggregate = AudienceAggregate(
        alcohol_affinity_score=round(agg_alcohol, 3),
        alcohol_affinity_label=_affinity_label(agg_alcohol),
        expected_revpash_min=agg_revpash_min,
        expected_revpash_max=agg_revpash_max,
        avg_wom_multiplier=agg_wom,
        avg_peer_influence=agg_peer,
        dominant_discovery_platform=dominant_platform,
        structural_insight=structural,
    )

    return AudienceResponse(
        venue_id=venue_id,
        venue_name=venue_row["name"],
        venue_area=venue_row["area"] or "",
        segment_profiles=segment_profiles,
        aggregate=aggregate,
    )
