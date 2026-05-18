"""
routers/transform.py
GET /api/venues/{venue_id}/transform  →  TransformResponse  (Screen 3 — Transform Tab)

Purpose: client selects a target demographic to attract.
System returns venues that already attract that segment, categorised by tier:

  ROLE MODEL   — target=rank-1 AND client's primary segment=rank-2 in that venue
                 Best case: venue already bridges both audiences.
  TRANSITION   — target=rank-1 AND client's primary segment=rank-3.
                 Has pivoted somewhat but client's base is still present.
  PURE TARGET  — target=rank-1, client's primary segment absent from top-3.
                 Fully pivoted; most distant from client's current identity.

If no ROLE MODEL venues exist, TRANSITION venues are shown first (fall-through).
"""

from fastapi import APIRouter, HTTPException, Path, Query

from database import get_pool
from models import (
    TransformResponse, SegmentOption,
    SimilarVenueCard, DeltaBar,
)
from routers.competitors import _fetch_client, _load_delta_rules, _lookup_rule
from routers.utils import (
    map_venue_types, make_archetype_chip,
    SEGMENT_LABELS, SEGMENT_TOP_ARCHETYPES,
    DIM_LABELS, RADAR_DIMS, ALL_DIMS,
)

router = APIRouter()


def _float(v) -> float:
    return float(v) if v is not None else 0.0


# ─── Current segment options ──────────────────────────────────────────────────

async def _get_current_segments(conn, venue_id: int) -> list[SegmentOption]:
    """Return all 5 segments with alignment scores; flag which the venue already attracts."""
    rows = await conn.fetch(
        """
        SELECT segment_id, alignment_score, segment_rank
        FROM   venue_demographic_scores
        WHERE  venue_id = $1
        ORDER  BY segment_rank
        """,
        venue_id,
    )
    options: list[SegmentOption] = []
    for r in rows:
        meta  = SEGMENT_LABELS.get(r["segment_id"], {})
        score = float(r["alignment_score"])
        # A venue "currently attracts" a segment if it ranks in top 2
        is_current = (r["segment_rank"] <= 2)
        options.append(SegmentOption(
            segment_id=r["segment_id"],
            segment_name=meta.get("label", r["segment_id"]),
            demographic_label=meta.get("demographic", ""),
            is_current=is_current,
            current_alignment_pct=round(score * 100),
        ))
    return options


# ─── Segment Ladder venue fetch ───────────────────────────────────────────────

async def _fetch_segment_ladder_venues(
    conn,
    venue_id: int,
    client_primary_seg: str,
    target_segment: str,
    limit: int,
    offset: int,
) -> tuple[list[SimilarVenueCard], int]:
    """
    Find venues where target_segment is rank-1, classify by tier, paginate.
    Within each tier sorted by target segment alignment_score DESC.
    Delta bars use pre-computed venue_similarity_deltas when available.
    """
    # Total venues with target as rank-1 (excluding client), capped at 40
    raw_total = await conn.fetchval(
        """
        SELECT COUNT(DISTINCT vds_t.venue_id)
        FROM   venue_demographic_scores vds_t
        WHERE  vds_t.segment_id  = $1
          AND  vds_t.segment_rank = 1
          AND  vds_t.venue_id    != $2
        """,
        target_segment, venue_id,
    )
    total = min(int(raw_total or 0), 40)

    # Tier classification + diversity sort:
    # diversity_score = sum of abs fitness differences from client.
    # Within each tier, most-distinct-from-client venues surface first so
    # every card the user sees is instructive and visually different.
    tier_rows = await conn.fetch(
        """
        SELECT
            vds_t.venue_id,
            vds_t.alignment_score AS target_alignment,
            CASE
                WHEN vds_c.segment_rank = 2 THEN 'role_model'
                WHEN vds_c.segment_rank = 3 THEN 'transition'
                ELSE                              'pure_target'
            END AS tier,
            (
                ABS(COALESCE(vfd_s.fitness_for_group_energy,      0) - COALESCE(vfd_c.fitness_for_group_energy,      0)) +
                ABS(COALESCE(vfd_s.fitness_for_social_dwell,      0) - COALESCE(vfd_c.fitness_for_social_dwell,      0)) +
                ABS(COALESCE(vfd_s.fitness_for_destination_visit, 0) - COALESCE(vfd_c.fitness_for_destination_visit, 0)) +
                ABS(COALESCE(vfd_s.fitness_for_repeat_habit,      0) - COALESCE(vfd_c.fitness_for_repeat_habit,      0)) +
                ABS(COALESCE(vfd_s.fitness_for_office_lunch,      0) - COALESCE(vfd_c.fitness_for_office_lunch,      0)) +
                ABS(COALESCE(vfd_s.operational_quality,           0) - COALESCE(vfd_c.operational_quality,           0)) +
                ABS(COALESCE(vfd_s.retention_strength,            0) - COALESCE(vfd_c.retention_strength,            0))
            ) AS diversity_score
        FROM   venue_demographic_scores vds_t
        LEFT JOIN venue_demographic_scores vds_c
               ON vds_c.venue_id   = vds_t.venue_id
              AND vds_c.segment_id = $1
        LEFT JOIN venue_fitness_dimensions vfd_s ON vfd_s.venue_id = vds_t.venue_id AND vfd_s.source = 'blended'
        LEFT JOIN venue_fitness_dimensions vfd_c ON vfd_c.venue_id = $3 AND vfd_c.source = 'blended'
        WHERE  vds_t.segment_id   = $2
          AND  vds_t.segment_rank = 1
          AND  vds_t.venue_id    != $3
        ORDER BY
            CASE
                WHEN vds_c.segment_rank = 2 THEN 1
                WHEN vds_c.segment_rank = 3 THEN 2
                ELSE                              3
            END,
            diversity_score DESC,
            vds_t.alignment_score DESC
        LIMIT  $4 OFFSET $5
        """,
        client_primary_seg, target_segment, venue_id, limit, offset,
    )

    if not tier_rows:
        return [], total

    sim_ids  = [r["venue_id"] for r in tier_rows]
    tier_map = {r["venue_id"]: r["tier"] for r in tier_rows}

    # ── Venue details ─────────────────────────────────────────────────────────
    venue_rows = await conn.fetch(
        "SELECT id, name, area, city, types FROM venues WHERE id = ANY($1::int[])",
        sim_ids,
    )
    venue_map = {r["id"]: r for r in venue_rows}

    # ── Primary segment → archetypes for each similar venue ───────────────────
    pseg_rows = await conn.fetch(
        """
        SELECT venue_id, segment_id
        FROM   venue_demographic_scores
        WHERE  venue_id = ANY($1::int[]) AND segment_rank = 1
        """,
        sim_ids,
    )
    primary_seg_map = {r["venue_id"]: r["segment_id"] for r in pseg_rows}

    # ── Top 3 segment display names ───────────────────────────────────────────
    top3_rows = await conn.fetch(
        """
        SELECT venue_id, segment_id, segment_rank
        FROM   venue_demographic_scores
        WHERE  venue_id = ANY($1::int[]) AND segment_rank <= 3
        ORDER  BY venue_id, segment_rank
        """,
        sim_ids,
    )
    top_seg_map: dict[int, list[str]] = {}
    for r in top3_rows:
        label = SEGMENT_LABELS.get(r["segment_id"], {}).get("label", r["segment_id"])
        top_seg_map.setdefault(r["venue_id"], []).append(label)

    # ── Fitness dimensions: client + all similar venues (on-the-fly deltas) ─────
    client_fd = await conn.fetchrow(
        f"SELECT {', '.join(ALL_DIMS)} FROM venue_fitness_dimensions WHERE venue_id = $1 AND source = 'blended'",
        venue_id,
    )
    sim_fd_rows = await conn.fetch(
        f"SELECT venue_id, {', '.join(ALL_DIMS)} FROM venue_fitness_dimensions WHERE venue_id = ANY($1::int[]) AND source = 'blended'",
        sim_ids,
    )
    sim_fd_map = {r["venue_id"]: r for r in sim_fd_rows}

    rules_by_dim = await _load_delta_rules(conn)

    # ── Assemble cards ────────────────────────────────────────────────────────
    cards: list[SimilarVenueCard] = []
    rank_offset = offset + 1

    for idx, tr in enumerate(tier_rows):
        sim_id = tr["venue_id"]
        v      = venue_map.get(sim_id)
        if not v:
            continue

        p_seg     = primary_seg_map.get(sim_id, "office_workers")
        arc_names = SEGMENT_TOP_ARCHETYPES.get(p_seg, [])
        sim_fd    = sim_fd_map.get(sim_id)

        delta_bars: list[DeltaBar] = []
        for dim in ALL_DIMS:
            c_score   = _float(client_fd[dim]) if client_fd else 0.0
            s_score   = _float(sim_fd[dim])    if sim_fd   else 0.0
            delta_val = round(s_score - c_score, 4)
            rule      = _lookup_rule(rules_by_dim, dim, delta_val)

            delta_bars.append(DeltaBar(
                dimension=dim,
                label=DIM_LABELS[dim],
                client_score=c_score,
                similar_score=max(0.0, min(1.0, s_score)),
                delta=delta_val,
                direction=rule["direction"],
                short_label=rule["short_label"],
                client_statement=rule["client_statement"],
            ))

        cards.append(SimilarVenueCard(
            id=sim_id,
            name=v["name"],
            area=v["area"],
            city=v["city"],
            types=map_venue_types(list(v["types"] or [])),
            top_archetypes=[make_archetype_chip(n) for n in arc_names],
            top_segments=top_seg_map.get(sim_id, []),
            delta_bars=delta_bars,
            similarity_score=_float(tr["target_alignment"]),
            rank=rank_offset + idx,
            tier=tier_map.get(sim_id, "pure_target"),
        ))

    return cards, total


# ─── Gap callout ──────────────────────────────────────────────────────────────

def _build_gap_callout(
    venue_id: int,
    target_segment_id: str,
    segment_options: list[SegmentOption],
    similar_venues: list[SimilarVenueCard],
) -> str:
    """Amber callout text: biggest gap + tier fall-through notice if needed."""
    SEGMENT_CRITICAL_DIM: dict[str, str] = {
        "office_workers": "fitness_for_office_lunch",
        "college_kids":   "fitness_for_group_energy",
        "couples":        "fitness_for_destination_visit",
        "families":       "fitness_for_repeat_habit",
        "premium":        "fitness_for_destination_visit",
    }
    critical_dim = SEGMENT_CRITICAL_DIM.get(target_segment_id)
    dim_label    = DIM_LABELS.get(critical_dim, "venue fitness") if critical_dim else "venue fitness"

    target_meta  = SEGMENT_LABELS.get(target_segment_id, {})
    target_name  = target_meta.get("label", target_segment_id)
    visit_time   = target_meta.get("visit_time", "their preferred time")

    target_opt = next((o for o in segment_options if o.segment_id == target_segment_id), None)
    current_pct = target_opt.current_alignment_pct if target_opt else 0

    callout = (
        f"To attract {target_name} ({visit_time}), focus on strengthening "
        f"{dim_label}. "
        f"Your current alignment is {current_pct}% — "
        "see how similar venues below have closed this gap."
    )

    # Tier fall-through notice
    if similar_venues:
        has_role_model  = any(s.tier == "role_model"  for s in similar_venues)
        has_transition  = any(s.tier == "transition"  for s in similar_venues)
        has_pure_target = any(s.tier == "pure_target" for s in similar_venues)

        if not has_role_model and has_transition:
            callout += (
                f" No ROLE MODEL venues found (no venues that serve both "
                f"{target_name} and your current audience). "
                "Showing TRANSITION venues — they have partially pivoted."
            )
        elif not has_role_model and not has_transition and has_pure_target:
            callout += (
                f" No overlap found with your current audience. "
                "Showing PURE TARGET venues — these have fully committed to "
                f"the {target_name} segment."
            )

    return callout


# ─── Route ───────────────────────────────────────────────────────────────────

@router.get("/{venue_id}/transform", response_model=TransformResponse)
async def get_transform(
    venue_id:       int  = Path(...),
    target_segment: str  = Query(default=None, description="Target demographic segment ID"),
    limit:          int  = Query(default=40, ge=1, le=40),
    offset:         int  = Query(default=0, ge=0),
):
    """
    Transform tab.
    - Without target_segment: returns all segment options + current alignment.
    - With target_segment: returns segment-ladder venues categorised by tier,
      with the same 4-column delta comparison as the Competitors tab.

    Recommendations scope: ONLY fitness gap analysis — no menu / pricing / staffing.
    """
    pool = get_pool()

    async with pool.acquire() as conn:
        # Validate venue exists
        exists = await conn.fetchval("SELECT id FROM venues WHERE id = $1", venue_id)
        if not exists:
            raise HTTPException(status_code=404, detail="Venue not found")

        client_card     = await _fetch_client(conn, venue_id)
        segment_options = await _get_current_segments(conn, venue_id)

        target_opt: SegmentOption | None = None
        similar: list[SimilarVenueCard] = []
        total = 0

        if target_segment:
            target_opt = next(
                (o for o in segment_options if o.segment_id == target_segment), None
            )
            if not target_opt:
                raise HTTPException(
                    status_code=400,
                    detail=(
                        f"Unknown segment '{target_segment}'. "
                        "Valid: office_workers, college_kids, couples, families, premium, solo_diners, working_women"
                    ),
                )

            # Client's rank-1 segment drives tier classification
            client_primary_seg = await conn.fetchval(
                """
                SELECT segment_id FROM venue_demographic_scores
                WHERE  venue_id = $1 AND segment_rank = 1
                """,
                venue_id,
            ) or "office_workers"

            similar, total = await _fetch_segment_ladder_venues(
                conn,
                venue_id,
                client_primary_seg,
                target_segment,
                limit,
                offset,
            )

    gap_callout = ""
    if target_segment:
        gap_callout = _build_gap_callout(venue_id, target_segment, segment_options, similar)

    return TransformResponse(
        current_segments=segment_options,
        target_segment=target_opt,
        similar_venues=similar,
        total_similar=total,
        offset=offset,
        limit=limit,
        gap_callout=gap_callout,
    )
