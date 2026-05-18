"""
routers/transform.py
GET /api/venues/{venue_id}/transform  →  TransformResponse  (Screen 3 — Transform Tab)

Purpose: client selects a target demographic to attract.
System returns venues already attracting that segment, classified by four tiers:

  ROLE MODEL   — target=rank-1, ATA ≥ 0.50
                 Client's primary segment is meaningfully present (best to learn from).
  BRIDGE       — target=rank-2 or rank-3 (mid-pivot), alignment ≥ 0.30
                 Venue hasn't fully committed but target is growing — mid-pivot.
  TRANSITION   — target=rank-1, ATA 0.20–0.50
                 Some client-like audience present; venue is in transition.
  PURE TARGET  — target=rank-1, ATA < 0.20
                 Fully committed to target segment; most distant from client identity.

ATA (Audience Transition Affinity) = client_alignment_at_venue / target_alignment_at_venue
Composite sort = target_alignment × (1 − effort) × (0.70 + 0.30 × geo_multiplier)
Quota: role_model=10, bridge=8, transition=14, pure_target=8
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


# ─── Effort scoring ────────────────────────────────────────────────────────────

# Dimension weights for effort — upward-only gaps (venue > client) only
_DIM_EFFORT_WEIGHTS: dict[str, float] = {
    "operational_quality":           1.0,
    "retention_strength":            0.9,
    "fitness_for_office_lunch":      0.8,
    "fitness_for_repeat_habit":      0.7,
    "fitness_for_destination_visit": 0.5,
    "fitness_for_social_dwell":      0.4,
    "fitness_for_group_energy":      0.4,
}
_TOTAL_EFFORT_WEIGHT = sum(_DIM_EFFORT_WEIGHTS.values())

# Tier quotas
_QUOTA: dict[str, int] = {
    "role_model":  10,
    "bridge":       8,
    "transition":  14,
    "pure_target":  8,
}

_TIER_ORDER = ["role_model", "bridge", "transition", "pure_target"]


def _compute_effort(client_fd, sim_fd) -> float:
    """Weighted upward-only effort: sum(max(0, venue − client) × weight) / total_weight."""
    total = 0.0
    for dim, w in _DIM_EFFORT_WEIGHTS.items():
        c = _float(client_fd[dim]) if client_fd else 0.0
        s = _float(sim_fd[dim])    if sim_fd    else 0.0
        total += max(0.0, s - c) * w
    return total / _TOTAL_EFFORT_WEIGHT


def _effort_label(effort: float) -> str:
    if effort < 0.12:
        return "Quick Win"
    if effort < 0.25:
        return "Major Initiative"
    return "Strategic Pivot"


def _geo_mult(client_area: str, client_city: str, v_area: str, v_city: str) -> float:
    if v_area and v_area == client_area:
        return 1.0
    if v_city and v_city == client_city:
        return 0.70
    return 0.15


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
    Find venues for the target segment, classify by ATA-based tier, apply quotas.

    Tier assignment:
      rank-1 pool  — target is rank-1 at that venue
        ATA ≥ 0.50  → role_model
        ATA ≥ 0.20  → transition
        ATA < 0.20  → pure_target
      bridge pool  — target is rank-2/3, alignment ≥ 0.30, not in rank-1 pool

    Composite sort within each tier:
      target_alignment × (1 − effort) × (0.70 + 0.30 × geo_multiplier)

    Quotas: role_model=10, bridge=8, transition=14, pure_target=8
    """
    # ── 1. Rank-1 candidate pool (up to 80) ──────────────────────────────────
    rank1_rows = await conn.fetch(
        """
        SELECT venue_id, alignment_score AS target_alignment
        FROM   venue_demographic_scores
        WHERE  segment_id   = $1
          AND  segment_rank = 1
          AND  venue_id    != $2
        ORDER BY alignment_score DESC
        LIMIT  80
        """,
        target_segment, venue_id,
    )
    rank1_ids: set[int] = {r["venue_id"] for r in rank1_rows}
    target_align_map: dict[int, float] = {
        r["venue_id"]: float(r["target_alignment"]) for r in rank1_rows
    }

    # ── 2. Bridge candidate pool (target rank-2/3, alignment ≥ 0.30) ─────────
    bridge_rows = await conn.fetch(
        """
        SELECT venue_id, alignment_score AS target_alignment
        FROM   venue_demographic_scores
        WHERE  segment_id        = $1
          AND  segment_rank     IN (2, 3)
          AND  alignment_score  >= 0.30
          AND  venue_id         != $2
        ORDER BY alignment_score DESC
        LIMIT  80
        """,
        target_segment, venue_id,
    )
    for r in bridge_rows:
        vid = r["venue_id"]
        if vid not in rank1_ids:
            target_align_map[vid] = float(r["target_alignment"])

    all_ids = list(target_align_map.keys())
    if not all_ids:
        return [], 0

    # ── 3. Client primary-segment alignment at each candidate ─────────────────
    c_align_rows = await conn.fetch(
        """
        SELECT venue_id, alignment_score
        FROM   venue_demographic_scores
        WHERE  venue_id    = ANY($1::int[])
          AND  segment_id  = $2
        """,
        all_ids, client_primary_seg,
    )
    client_align_map: dict[int, float] = {
        r["venue_id"]: float(r["alignment_score"]) for r in c_align_rows
    }

    # ── 4. Client area/city for geo multiplier ────────────────────────────────
    client_vrow = await conn.fetchrow(
        "SELECT area, city FROM venues WHERE id = $1", venue_id
    )
    client_area = (client_vrow["area"] or "") if client_vrow else ""
    client_city = (client_vrow["city"] or "") if client_vrow else ""

    # ── 5. Fitness dimensions (client + all candidates) ───────────────────────
    client_fd = await conn.fetchrow(
        f"SELECT {', '.join(ALL_DIMS)} FROM venue_fitness_dimensions "
        "WHERE venue_id = $1 AND source = 'blended'",
        venue_id,
    )
    sim_fd_rows = await conn.fetch(
        f"SELECT venue_id, {', '.join(ALL_DIMS)} FROM venue_fitness_dimensions "
        "WHERE venue_id = ANY($1::int[]) AND source = 'blended'",
        all_ids,
    )
    sim_fd_map = {r["venue_id"]: r for r in sim_fd_rows}

    # ── 6. Venue details ──────────────────────────────────────────────────────
    venue_rows = await conn.fetch(
        "SELECT id, name, area, city, types FROM venues WHERE id = ANY($1::int[])",
        all_ids,
    )
    venue_map = {r["id"]: r for r in venue_rows}

    # ── 7. Primary segment + top-3 segments per candidate ─────────────────────
    pseg_rows = await conn.fetch(
        """
        SELECT venue_id, segment_id
        FROM   venue_demographic_scores
        WHERE  venue_id = ANY($1::int[]) AND segment_rank = 1
        """,
        all_ids,
    )
    primary_seg_map = {r["venue_id"]: r["segment_id"] for r in pseg_rows}

    top3_rows = await conn.fetch(
        """
        SELECT venue_id, segment_id, segment_rank
        FROM   venue_demographic_scores
        WHERE  venue_id = ANY($1::int[]) AND segment_rank <= 3
        ORDER  BY venue_id, segment_rank
        """,
        all_ids,
    )
    top_seg_map: dict[int, list[str]] = {}
    for r in top3_rows:
        lbl = SEGMENT_LABELS.get(r["segment_id"], {}).get("label", r["segment_id"])
        top_seg_map.setdefault(r["venue_id"], []).append(lbl)

    rules_by_dim = await _load_delta_rules(conn)

    # ── 8. Score and tier each candidate ─────────────────────────────────────
    scored: list[dict] = []
    for vid in all_ids:
        v = venue_map.get(vid)
        if not v:
            continue

        target_align = target_align_map[vid]
        client_align = client_align_map.get(vid, 0.0)

        # ATA: how much of the client audience is present here vs the target audience
        ata = (client_align / target_align) if target_align > 0 else 0.0

        # Tier
        if vid in rank1_ids:
            if ata >= 0.50:
                tier = "role_model"
            elif ata >= 0.20:
                tier = "transition"
            else:
                tier = "pure_target"
        else:
            tier = "bridge"

        # Effort (upward-only gaps — how hard to get from client's level to this venue's level)
        sim_fd = sim_fd_map.get(vid)
        effort = _compute_effort(client_fd, sim_fd) if (client_fd and sim_fd) else 0.5
        effort_lbl = _effort_label(effort)

        # Geo multiplier
        v_area = v["area"] or ""
        v_city = v["city"] or ""
        geo = _geo_mult(client_area, client_city, v_area, v_city)

        # Composite sort score
        composite = target_align * (1.0 - effort) * (0.70 + 0.30 * geo)

        scored.append({
            "venue_id":       vid,
            "tier":           tier,
            "target_align":   target_align,
            "effort":         effort,
            "effort_label":   effort_lbl,
            "composite":      composite,
        })

    # ── 9. Apply tier quotas with composite sort ──────────────────────────────
    tier_buckets: dict[str, list[dict]] = {t: [] for t in _TIER_ORDER}
    for s in scored:
        tier_buckets[s["tier"]].append(s)

    for t in _TIER_ORDER:
        tier_buckets[t].sort(key=lambda x: x["composite"], reverse=True)

    flat: list[dict] = []
    for t in _TIER_ORDER:
        flat.extend(tier_buckets[t][: _QUOTA[t]])

    total = len(flat)
    page  = flat[offset: offset + limit]
    if not page:
        return [], total

    # ── 10. Assemble SimilarVenueCard objects ─────────────────────────────────
    cards: list[SimilarVenueCard] = []
    for idx, item in enumerate(page):
        vid = item["venue_id"]
        v   = venue_map.get(vid)
        if not v:
            continue

        p_seg     = primary_seg_map.get(vid, "office_workers")
        arc_names = SEGMENT_TOP_ARCHETYPES.get(p_seg, [])
        sim_fd    = sim_fd_map.get(vid)

        delta_bars: list[DeltaBar] = []
        for dim in ALL_DIMS:
            c_score   = _float(client_fd[dim]) if client_fd else 0.0
            s_score   = _float(sim_fd[dim])    if sim_fd    else 0.0
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
            id=vid,
            name=v["name"],
            area=v["area"],
            city=v["city"],
            types=map_venue_types(list(v["types"] or [])),
            top_archetypes=[make_archetype_chip(n) for n in arc_names],
            top_segments=top_seg_map.get(vid, []),
            delta_bars=delta_bars,
            similarity_score=item["target_align"],
            rank=offset + idx + 1,
            tier=item["tier"],
            effort_label=item["effort_label"],
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

    # Tier composition notice
    if similar_venues:
        has_role_model  = any(s.tier == "role_model"  for s in similar_venues)
        has_bridge      = any(s.tier == "bridge"      for s in similar_venues)
        has_transition  = any(s.tier == "transition"  for s in similar_venues)
        has_pure_target = any(s.tier == "pure_target" for s in similar_venues)

        if has_bridge:
            callout += (
                " BRIDGE venues (mid-pivot) are shown alongside — these venues have "
                f"{target_name} as a growing secondary audience and represent the "
                "earliest, lowest-effort entry point."
            )

        if not has_role_model and has_transition:
            callout += (
                f" No ROLE MODEL venues found (no venues that serve both "
                f"{target_name} and your current audience). "
                "Showing TRANSITION venues — they have partially pivoted."
            )
        elif not has_role_model and not has_transition and has_pure_target:
            callout += (
                " No overlap found with your current audience. "
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
