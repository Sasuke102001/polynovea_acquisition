"""
routers/overview.py
GET /api/venues/{venue_id}/overview  →  OverviewResponse  (Screen 5 — Overview Tab)
"""

from fastapi import APIRouter, HTTPException, Path

from database import get_pool
from models import (
    OverviewResponse, VenueHeader, FitnessRadar, FitnessDimension,
    CustomerProfile, SegmentRow, ArchetypeBar, HealthScore, InsightCard,
)
from routers.utils import (
    map_venue_types, make_archetype_chip,
    compute_health_score, data_confidence_label, health_label,
    DIM_LABELS, RADAR_DIMS,
    SEGMENT_LABELS, intervention_title,
)

router = APIRouter()


@router.get("/{venue_id}/overview", response_model=OverviewResponse)
async def get_overview(venue_id: int = Path(...)):
    """
    Overview tab — the anchor screen shown to clients first.
    Returns fitness radar, customer profile, health score, and
    top 3 working signals + top 3 gaps from intervention_triggers.

    Recommendations scope: ONLY behavioral signals from intervention_triggers.
    Never includes menu / pricing / delivery / staffing.
    """
    pool = get_pool()

    async with pool.acquire() as conn:
        # ── Venue header ──────────────────────────────────────────────────────
        venue = await conn.fetchrow(
            "SELECT id, name, area, city, types FROM venues WHERE id = $1",
            venue_id,
        )
        if not venue:
            raise HTTPException(status_code=404, detail="Venue not found")

        # ── Fitness dimensions ────────────────────────────────────────────────
        fd = await conn.fetchrow(
            """
            SELECT
                fitness_for_office_lunch,
                fitness_for_repeat_habit,
                fitness_for_social_dwell,
                fitness_for_group_energy,
                fitness_for_destination_visit,
                operational_quality,
                retention_strength,
                monetization_potential
            FROM venue_fitness_dimensions
            WHERE venue_id = $1
            """,
            venue_id,
        )
        if not fd:
            raise HTTPException(status_code=404, detail="Fitness data not found for venue")

        # ── Top 3 demographic segments ────────────────────────────────────────
        seg_rows = await conn.fetch(
            """
            SELECT segment_id, alignment_score, segment_rank
            FROM   venue_demographic_scores
            WHERE  venue_id = $1
            ORDER  BY segment_rank
            LIMIT  3
            """,
            venue_id,
        )

        # ── Archetypes for each top segment (up to 3 per segment) ────────────
        seg_ids = [r["segment_id"] for r in seg_rows]
        arc_by_seg: dict[str, list] = {}
        if seg_ids:
            arc_rows = await conn.fetch(
                """
                SELECT segment_id, archetype_name, prevalence_percentage
                FROM   demographic_archetype_mapping
                WHERE  segment_id = ANY($1::text[])
                ORDER  BY segment_id, prevalence_percentage DESC
                """,
                seg_ids,
            )
            for r in arc_rows:
                arc_by_seg.setdefault(r["segment_id"], []).append(r)

        # ── Archetype distribution (top 5 across primary segment) ─────────────
        primary_seg = seg_ids[0] if seg_ids else "office_workers"
        dist_rows = await conn.fetch(
            """
            SELECT archetype_name, prevalence_percentage
            FROM   demographic_archetype_mapping
            WHERE  segment_id = $1
            ORDER  BY prevalence_percentage DESC
            LIMIT  5
            """,
            primary_seg,
        )

        # ── Intervention triggers (working + gaps) ────────────────────────────
        intervention_rows = await conn.fetch(
            """
            SELECT intervention_type, description, priority_tier, recommended
            FROM   intervention_triggers
            WHERE  venue_id = $1
            ORDER  BY
                CASE recommended WHEN true THEN 0 ELSE 1 END,
                fit_score DESC
            """,
            venue_id,
        )

        # ── Primitives fallback (for working_for_you waterfall tier 2) ────────
        # Only needed if recommended=true interventions are sparse.
        primitives_rows = await conn.fetch(
            """
            SELECT primitive_id, score
            FROM   primitives_scores
            WHERE  venue_id = $1 AND score >= 0.55
            ORDER  BY score DESC
            LIMIT  5
            """,
            venue_id,
        )

    # ── Build radar ───────────────────────────────────────────────────────────
    radar = FitnessRadar(dimensions=[
        FitnessDimension(
            key=dim,
            label=DIM_LABELS[dim],
            score=float(fd[dim] or 0.0),
        )
        for dim in RADAR_DIMS
    ])

    # ── Build customer profile ─────────────────────────────────────────────────
    top_segments: list[SegmentRow] = []
    for sr in seg_rows:
        meta = SEGMENT_LABELS.get(sr["segment_id"], {})
        arcs = arc_by_seg.get(sr["segment_id"], [])[:2]
        top_segments.append(SegmentRow(
            segment_id=sr["segment_id"],
            segment_name=meta.get("label", sr["segment_id"]),
            demographic_label=meta.get("demographic", ""),
            alignment_score=float(sr["alignment_score"]),
            alignment_pct=round(float(sr["alignment_score"]) * 100),
            archetypes=[make_archetype_chip(a["archetype_name"]) for a in arcs],
        ))

    archetype_dist: list[ArchetypeBar] = [
        ArchetypeBar(
            name=r["archetype_name"],
            demographic_label=make_archetype_chip(r["archetype_name"]).demographic_label,
            prevalence_pct=round(float(r["prevalence_percentage"])),
        )
        for r in dist_rows
    ]

    # ── Health score ──────────────────────────────────────────────────────────
    score = compute_health_score(
        fd["operational_quality"],
        fd["fitness_for_social_dwell"],
        fd["fitness_for_group_energy"],
        fd["retention_strength"],
    )
    health = HealthScore(
        score=score,
        label=health_label(score),
        operational_quality=float(fd["operational_quality"] or 0.0),
        retention_strength=float(fd["retention_strength"] or 0.0),
        data_confidence=data_confidence_label(fd),
    )

    # ── Working for you — 3-tier waterfall ────────────────────────────────────
    # Tier 1: recommended=True rows from intervention_triggers
    # Tier 2: high-scoring primitives if tier 1 is sparse
    # Tier 3: strong fitness dimensions (>= 0.35) if still sparse
    working: list[InsightCard] = []

    for r in intervention_rows:
        if r["recommended"] and len(working) < 3:
            working.append(InsightCard(
                title=intervention_title(r["intervention_type"]),
                subtitle=r["description"],
                priority_tier="",
            ))

    # Tier 2 fallback — high-scoring primitives
    if len(working) < 3 and primitives_rows:
        for p in primitives_rows:
            if len(working) >= 3:
                break
            pname     = str(p["primitive_id"]).replace("_", " ").title()
            score_pct = round(float(p["score"]) * 100)
            working.append(InsightCard(
                title=f"Strong {pname}",
                subtitle=f"Score {score_pct}/100 — this signal is performing well for your venue.",
                priority_tier="",
            ))

    # Tier 3 fallback — fitness dimensions
    if len(working) < 3:
        for dim in RADAR_DIMS:
            if len(working) >= 3:
                break
            dim_score = float(fd[dim] or 0)
            if dim_score >= 0.35:
                working.append(InsightCard(
                    title=f"Strong {DIM_LABELS[dim]}",
                    subtitle=(
                        f"Score {round(dim_score * 100)}/100 — "
                        "solid performance in this dimension."
                    ),
                    priority_tier="",
                ))

    # ── Gaps to close — CRITICAL / HIGH / MEDIUM only (drop EXPLORE/LOW noise) ─
    # Fallback to bottom fitness dimensions if no qualifying trigger rows exist.
    gaps: list[InsightCard] = []

    for r in intervention_rows:
        if (
            not r["recommended"]
            and r["priority_tier"] in ("CRITICAL", "HIGH", "MEDIUM")
            and len(gaps) < 3
        ):
            gaps.append(InsightCard(
                title=intervention_title(r["intervention_type"]),
                subtitle=r["description"],
                priority_tier=r["priority_tier"] or "",
            ))

    # Fallback: bottom-2 fitness dimensions
    if not gaps:
        scored_dims = sorted(
            [(dim, float(fd[dim] or 0)) for dim in RADAR_DIMS],
            key=lambda x: x[1],
        )
        for dim, dim_score in scored_dims[:2]:
            gaps.append(InsightCard(
                title=f"Weak {DIM_LABELS[dim]}",
                subtitle=(
                    f"Score {round(dim_score * 100)}/100 — "
                    "strengthening this dimension will improve venue performance."
                ),
                priority_tier="LOW",
            ))

    return OverviewResponse(
        venue=VenueHeader(
            id=venue["id"],
            name=venue["name"],
            area=venue["area"],
            city=venue["city"],
            types=map_venue_types(list(venue["types"] or [])),
        ),
        fitness_radar=radar,
        customer_profile=CustomerProfile(
            top_segments=top_segments,
            archetype_distribution=archetype_dist,
        ),
        health_score=health,
        working_for_you=working,
        gaps_to_close=gaps,
    )
