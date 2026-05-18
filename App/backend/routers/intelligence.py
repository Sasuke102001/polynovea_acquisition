"""
routers/intelligence.py
GET /api/venues/{venue_id}/intelligence  →  IntelligenceResponse  (Screen 6 — Deep Analysis)

Intelligence tab — full recommendation list, archetype distribution, pricing power.
This is the Consultant Mode view, not shown to clients by default.

Recommendations scope: ONLY behavioral signals from intervention_triggers.
NEVER: menu engineering, pricing strategy, delivery logistics, staffing decisions.
"""

from fastapi import APIRouter, HTTPException, Path
from typing import Any

from database import get_pool
from models import IntelligenceResponse, RecommendationRow, ArchetypeBar, PricingPower, ArchetypeIntervention
from routers.utils import (
    make_archetype_chip, intervention_title,
    SEGMENT_TOP_ARCHETYPES,
    DIM_LABELS,
)

router = APIRouter()

_float = lambda v: float(v) if v is not None else 0.0


def _headroom_label(score: float) -> str:
    """Monetization potential → headroom label."""
    if score >= 0.70: return "HIGH"
    if score >= 0.45: return "MED"
    return "LOW"


def _revenue_levers(fd: dict) -> list[dict[str, Any]]:
    """
    Derive revenue levers from venue's fitness profile.
    Each lever: {label, status ("ACTIVE" | "GAP"), sub}
    Uses behavioral fitness signals ONLY — not pricing or menu data.
    """
    levers = []

    # Destination pull → premium occasion revenue
    dest = _float(fd.get("fitness_for_destination_visit"))
    levers.append({
        "label":  "Destination Occasion Revenue",
        "status": "ACTIVE" if dest >= 0.60 else "GAP",
        "sub":    (
            f"Destination visit score {round(dest * 100)}% — "
            + ("strong pull for planned occasion visits" if dest >= 0.60
               else "low intentional visit rate limits per-cover spend")
        ),
    })

    # Retention → repeat customer LTV
    ret = _float(fd.get("retention_strength"))
    levers.append({
        "label":  "Repeat Customer LTV",
        "status": "ACTIVE" if ret >= 0.60 else "GAP",
        "sub":    (
            f"Retention score {round(ret * 100)}% — "
            + ("strong repeat base supports predictable revenue" if ret >= 0.60
               else "retention gap means low repeat-visit contribution to revenue")
        ),
    })

    # Social dwell → table-turn efficiency
    dwell = _float(fd.get("fitness_for_social_dwell"))
    levers.append({
        "label":  "Dwell-Time Conversion",
        "status": "ACTIVE" if dwell >= 0.55 else "GAP",
        "sub":    (
            f"Social dwell score {round(dwell * 100)}% — "
            + ("customers linger; opportunity to monetise with add-ons" if dwell >= 0.55
               else "low dwell time limits add-on and upsell conversion")
        ),
    })

    # Premium / high-energy signal → group event revenue
    group = _float(fd.get("fitness_for_group_energy"))
    levers.append({
        "label":  "Group & Event Revenue",
        "status": "ACTIVE" if group >= 0.55 else "GAP",
        "sub":    (
            f"Group energy score {round(group * 100)}% — "
            + ("well-suited for group bookings and events" if group >= 0.55
               else "low group energy limits event and large-party covers")
        ),
    })

    # Operational quality → service capacity / table turns
    ops = _float(fd.get("operational_quality"))
    levers.append({
        "label":  "Service Capacity (Ops Quality)",
        "status": "ACTIVE" if ops >= 0.65 else "GAP",
        "sub":    (
            f"Operational quality {round(ops * 100)}% — "
            + ("consistent service supports higher table-turn rate" if ops >= 0.65
               else "service friction reduces effective covers per shift")
        ),
    })

    return levers


# ─── Route ───────────────────────────────────────────────────────────────────

@router.get("/{venue_id}/intelligence", response_model=IntelligenceResponse)
async def get_intelligence(venue_id: int = Path(...)):
    """
    Deep Analysis — Intelligence tab.

    Returns:
    - Full ranked recommendation list (all intervention_triggers, sorted by priority)
    - Archetype distribution for primary segment
    - Pricing power: monetization_potential + revenue levers from fitness profile

    All recommendations come strictly from intervention_triggers (behavioral signals).
    Scope: seating signals, dwell gaps, retention mechanisms, platform visibility,
           atmosphere signals, segment capture, fitness vs benchmark gaps.
    Out of scope: menu changes, price points, delivery logistics, staff headcount.
    """
    pool = get_pool()

    async with pool.acquire() as conn:
        exists = await conn.fetchval("SELECT id FROM venues WHERE id = $1", venue_id)
        if not exists:
            raise HTTPException(status_code=404, detail="Venue not found")

        # All intervention triggers (full list for deep analysis)
        trigger_rows = await conn.fetch(
            """
            SELECT
                intervention_type,
                description,
                priority_tier,
                fit_score,
                tier_description,
                recommended
            FROM   intervention_triggers
            WHERE  venue_id = $1
            ORDER  BY
                CASE priority_tier
                    WHEN 'CRITICAL' THEN 1
                    WHEN 'HIGH'     THEN 2
                    WHEN 'MEDIUM'   THEN 3
                    WHEN 'LOW'      THEN 4
                    ELSE 5
                END,
                fit_score DESC
            """,
            venue_id,
        )

        # Primary segment → archetype distribution
        primary_seg_row = await conn.fetchrow(
            """
            SELECT segment_id FROM venue_demographic_scores
            WHERE  venue_id = $1 ORDER BY segment_rank LIMIT 1
            """,
            venue_id,
        )
        primary_seg = primary_seg_row["segment_id"] if primary_seg_row else "office_workers"

        arc_rows = await conn.fetch(
            """
            SELECT archetype_name, prevalence_percentage
            FROM   demographic_archetype_mapping
            WHERE  segment_id = $1
            ORDER  BY prevalence_percentage DESC
            LIMIT  5
            """,
            primary_seg,
        )

        # Archetype-level interventions for primary segment
        archetype_intervention_rows = await conn.fetch(
            """
            SELECT segment_id, archetype_name, intervention_type, description, expected_roi
            FROM   demographic_archetype_interventions
            WHERE  segment_id = $1
            ORDER  BY archetype_name, expected_roi DESC NULLS LAST
            LIMIT  12
            """,
            primary_seg,
        )

        # Fitness scores for pricing power
        fd = await conn.fetchrow(
            """
            SELECT
                fitness_for_destination_visit, fitness_for_social_dwell,
                fitness_for_group_energy, operational_quality,
                retention_strength, monetization_potential
            FROM venue_fitness_dimensions WHERE venue_id = $1 AND source = 'blended'
            """,
            venue_id,
        )

    # ── Recommendations ───────────────────────────────────────────────────────
    recommendations: list[RecommendationRow] = [
        RecommendationRow(
            intervention_type=r["intervention_type"],
            title=intervention_title(r["intervention_type"]),
            description=r["description"],
            priority_tier=r["priority_tier"] or "LOW",
            fit_score=_float(r["fit_score"]),
            expected_impact=r["tier_description"] or "",
            recommended=bool(r["recommended"]),
        )
        for r in trigger_rows
    ]

    # ── Archetype distribution ─────────────────────────────────────────────────
    archetype_dist: list[ArchetypeBar] = [
        ArchetypeBar(
            name=r["archetype_name"],
            demographic_label=make_archetype_chip(r["archetype_name"]).demographic_label,
            prevalence_pct=round(_float(r["prevalence_percentage"])),
        )
        for r in arc_rows
    ]

    # ── Pricing power ─────────────────────────────────────────────────────────
    mon_potential = _float(fd["monetization_potential"]) if fd else 0.0
    fd_dict = {
        "fitness_for_destination_visit": _float(fd["fitness_for_destination_visit"]) if fd else 0.0,
        "fitness_for_social_dwell":      _float(fd["fitness_for_social_dwell"]) if fd else 0.0,
        "fitness_for_group_energy":      _float(fd["fitness_for_group_energy"]) if fd else 0.0,
        "operational_quality":           _float(fd["operational_quality"]) if fd else 0.0,
        "retention_strength":            _float(fd["retention_strength"]) if fd else 0.0,
        "monetization_potential":        mon_potential,
    }
    pricing_power = PricingPower(
        monetization_potential=mon_potential,
        headroom_label=_headroom_label(mon_potential),
        revenue_levers=_revenue_levers(fd_dict),
    )

    archetype_interventions: list[ArchetypeIntervention] = [
        ArchetypeIntervention(
            archetype_name=r["archetype_name"],
            intervention_type=r["intervention_type"],
            description=r["description"],
            expected_roi=r["expected_roi"],
        )
        for r in archetype_intervention_rows
    ]

    return IntelligenceResponse(
        recommendations=recommendations,
        archetype_distribution=archetype_dist,
        pricing_power=pricing_power,
        archetype_interventions=archetype_interventions,
    )
