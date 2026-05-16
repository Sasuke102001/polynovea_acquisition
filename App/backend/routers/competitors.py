"""
routers/competitors.py
GET /api/venues/{venue_id}/similar  →  CompetitorsResponse  (Screen 2 — Competitors Tab)

Pagination: offset=0 → similar rank 1–3, offset=3 → rank 4–6, etc.
Deltas: computed on-the-fly from venue_fitness_dimensions + fitness_delta_rules.
        No dependency on the pre-computed venue_similarity_deltas table.

Competitor type cascade (per client type, per competitor position):
  For each of the client's top-3 non-generic types (in Google's original order):
    Try competitors where that type is at position 0 (primary→primary)
    Try competitors where that type is at position 1 (primary→secondary)
    Try competitors where that type is at position 2 (primary→tertiary)
  Stop at the first combination that yields results.
  If nothing found across all 3 client types: fall back to segment-only.
  If no segment data: fall back to raw cosine similarity.
"""

from fastapi import APIRouter, HTTPException, Path, Query

from database import get_pool
from models import (
    CompetitorsResponse, ClientVenueCard, SimilarVenueCard, FitnessDimension, DeltaBar,
)
from routers.utils import (
    map_venue_types, make_archetype_chip,
    DIM_LABELS, ALL_DIMS,
    SEGMENT_LABELS, SEGMENT_TOP_ARCHETYPES,
)

router = APIRouter()

# ─── Type helpers ─────────────────────────────────────────────────────────────

_GENERIC_TYPES: frozenset[str] = frozenset({
    "food", "point_of_interest", "establishment",
    "store", "premise", "locality", "political",
    "street_address", "geocode",
    # Too broad for competitive matching — almost every F&B venue has these
    "restaurant", "bar", "cafe",
})

# Hard cap on the total competitor pool returned
_MAX_POOL = 40


def _venue_type_cascade(types: list[str]) -> list[str]:
    """
    Return up to 3 non-generic Google Places types in Google's original order.
    These are tried in sequence as the matching key for competitor selection.
    """
    result = []
    for t in (types or []):
        if t not in _GENERIC_TYPES:
            result.append(t)
            if len(result) == 3:
                break
    return result


# ─── Delta rule helpers ───────────────────────────────────────────────────────

def _lookup_rule(rules_by_dim: dict[str, list], dim: str, delta: float) -> dict:
    """Find the matching fitness_delta_rules entry for (dimension, delta value)."""
    for rule in rules_by_dim.get(dim, []):
        if float(rule["delta_min"]) <= delta <= float(rule["delta_max"]):
            return {
                "direction":        rule["direction"],
                "short_label":      rule["short_label"],
                "client_statement": rule["client_statement"],
            }
    return {
        "direction":        "neutral",
        "short_label":      "Equal",
        "client_statement": "Similar performance to your venue",
    }


# ─── Helpers ──────────────────────────────────────────────────────────────────

def _float(v) -> float:
    return float(v) if v is not None else 0.0


async def _load_delta_rules(conn) -> dict[str, list]:
    """Load all 56 fitness delta rules into memory, grouped by dimension."""
    rows = await conn.fetch(
        """
        SELECT dimension, delta_min, delta_max, direction, short_label, client_statement
        FROM   fitness_delta_rules
        ORDER  BY dimension, delta_min DESC
        """
    )
    rules: dict[str, list] = {}
    for r in rows:
        rules.setdefault(r["dimension"], []).append(dict(r))
    return rules


async def _fetch_client(conn, venue_id: int) -> ClientVenueCard:
    """Fetch full client venue card with fitness scores + archetypes + segments."""
    row = await conn.fetchrow(
        "SELECT id, name, area, city, types FROM venues WHERE id = $1",
        venue_id,
    )
    if not row:
        raise HTTPException(status_code=404, detail="Venue not found")

    fd = await conn.fetchrow(
        """
        SELECT
            fitness_for_office_lunch,  fitness_for_repeat_habit,
            fitness_for_social_dwell,  fitness_for_group_energy,
            fitness_for_destination_visit, operational_quality,
            retention_strength
        FROM venue_fitness_dimensions WHERE venue_id = $1
        """,
        venue_id,
    )

    seg_rows = await conn.fetch(
        """
        SELECT segment_id FROM venue_demographic_scores
        WHERE venue_id = $1 ORDER BY segment_rank LIMIT 3
        """,
        venue_id,
    )
    top_seg_names = [
        SEGMENT_LABELS.get(r["segment_id"], {}).get("label", r["segment_id"])
        for r in seg_rows
    ]
    primary_seg = seg_rows[0]["segment_id"] if seg_rows else "office_workers"
    arc_names   = SEGMENT_TOP_ARCHETYPES.get(primary_seg, [])

    fitness_scores = [
        FitnessDimension(key=dim, label=DIM_LABELS[dim], score=_float(fd[dim]) if fd else 0.0)
        for dim in ALL_DIMS
    ]

    return ClientVenueCard(
        id=row["id"],
        name=row["name"],
        area=row["area"],
        city=row["city"],
        types=map_venue_types(list(row["types"] or [])),
        top_archetypes=[make_archetype_chip(n) for n in arc_names],
        top_segments=top_seg_names,
        fitness_scores=fitness_scores,
    )


async def _fetch_similar_venues(
    conn,
    venue_id: int,
    limit: int,
    offset: int,
) -> tuple[list[SimilarVenueCard], int]:
    """
    Type-waterfall competitor selection.

    Walk the client's type tags in order. For each type, fill the bucket with
    venues that share that type (excluding already-found ones and the client).
    Stop as soon as the bucket is full. Paginate across the full ordered list.

    Within each type bucket, venues are ordered by operational_quality DESC so
    the strongest performers surface first.

    Deltas are computed on-the-fly from venue_fitness_dimensions.
    """
    # ── Client's type cascade (raw Google types, non-generic, in original order) ─
    raw_types = await conn.fetchval("SELECT types FROM venues WHERE id = $1", venue_id)
    cascade_types = _venue_type_cascade(list(raw_types or []))

    # ── Fitness delta rules ───────────────────────────────────────────────────
    rules_by_dim = await _load_delta_rules(conn)

    # ── Client fitness dimensions ─────────────────────────────────────────────
    client_fd = await conn.fetchrow(
        f"SELECT {', '.join(ALL_DIMS)} FROM venue_fitness_dimensions WHERE venue_id = $1",
        venue_id,
    )

    # ── Type waterfall: collect ordered venue IDs ─────────────────────────────
    # Walk the client's cascade types in order.  For each type, find competitors
    # where that type is their #1 or #2 non-generic type.  Rank by (tier, comp_pos)
    # so: client-type[0] × comp-primary > client-type[0] × comp-secondary >
    #     client-type[1] × comp-primary > …  No operational_quality involvement.
    candidates: list[tuple[int, int, int]] = []  # (tier, comp_pos, venue_id)
    seen: set[int] = {venue_id}

    for tier, type_key in enumerate(cascade_types):
        rows = await conn.fetch(
            """
            SELECT v.id, v.types
            FROM   venues v
            WHERE  v.types @> jsonb_build_array($1::text)
              AND  v.id != ALL($2::int[])
            LIMIT  300
            """,
            type_key, list(seen),
        )
        for r in rows:
            comp_cascade = _venue_type_cascade(list(r["types"] or []))
            try:
                comp_pos = comp_cascade.index(type_key)
            except ValueError:
                continue
            if comp_pos > 1:
                continue
            vid = r["id"]
            seen.add(vid)
            candidates.append((tier, comp_pos, vid))

    # Sort: tier first (client's type priority), then competitor's own cascade position
    candidates.sort(key=lambda x: (x[0], x[1]))

    ordered_ids = [vid for _, _, vid in candidates[:_MAX_POOL]]
    id_tier     = {vid: tier for tier, _, vid in candidates[:_MAX_POOL]}

    # ── Segment fallback: venue has only generic types (e.g. pure bar/restaurant) ──
    if not ordered_ids:
        primary_seg = await conn.fetchval(
            "SELECT segment_id FROM venue_demographic_scores WHERE venue_id = $1 ORDER BY segment_rank LIMIT 1",
            venue_id,
        )
        if primary_seg:
            seg_fallback = await conn.fetch(
                """
                SELECT v.id
                FROM   venues v
                JOIN   venue_demographic_scores vds ON vds.venue_id = v.id
                JOIN   venue_fitness_dimensions vfd ON vfd.venue_id = v.id
                WHERE  vds.segment_id = $1
                  AND  vds.segment_rank = 1
                  AND  v.id != ALL($2::int[])
                ORDER  BY vfd.operational_quality DESC NULLS LAST
                LIMIT  $3
                """,
                primary_seg, [venue_id], _MAX_POOL,
            )
            ordered_ids = [r["id"] for r in seg_fallback]
            id_tier     = {r["id"]: 2 for r in seg_fallback}

    total = len(ordered_ids)
    page_ids = ordered_ids[offset: offset + limit]

    if not page_ids:
        return [], total

    sim_ids = page_ids

    # ── Venue details ─────────────────────────────────────────────────────────
    venue_rows = await conn.fetch(
        "SELECT id, name, area, city, types FROM venues WHERE id = ANY($1::int[])",
        sim_ids,
    )
    venue_map = {r["id"]: r for r in venue_rows}

    # ── Primary segment + top-3 segments per similar venue ────────────────────
    seg_rows = await conn.fetch(
        """
        SELECT venue_id, segment_id
        FROM   venue_demographic_scores
        WHERE  venue_id = ANY($1::int[]) AND segment_rank = 1
        """,
        sim_ids,
    )
    primary_seg_map = {r["venue_id"]: r["segment_id"] for r in seg_rows}

    top3_seg_rows = await conn.fetch(
        """
        SELECT venue_id, segment_id, segment_rank
        FROM   venue_demographic_scores
        WHERE  venue_id = ANY($1::int[]) AND segment_rank <= 3
        ORDER  BY venue_id, segment_rank
        """,
        sim_ids,
    )
    top3_seg_map: dict[int, list[str]] = {}
    for r in top3_seg_rows:
        label = SEGMENT_LABELS.get(r["segment_id"], {}).get("label", r["segment_id"])
        top3_seg_map.setdefault(r["venue_id"], []).append(label)

    # ── Similar venue fitness dimensions (for on-the-fly delta computation) ───
    sim_fd_rows = await conn.fetch(
        f"SELECT venue_id, {', '.join(ALL_DIMS)} FROM venue_fitness_dimensions WHERE venue_id = ANY($1::int[])",
        sim_ids,
    )
    sim_fd_map = {r["venue_id"]: r for r in sim_fd_rows}

    # ── Assemble SimilarVenueCard list ────────────────────────────────────────
    cards: list[SimilarVenueCard] = []
    rank_offset = offset + 1

    for idx, sim_id in enumerate(sim_ids):
        v = venue_map.get(sim_id)
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

        # similarity_score reflects cascade tier: type[0]=1.0, type[1]=0.9, type[2]=0.8
        tier      = id_tier.get(sim_id, 0)
        sim_score = max(0.5, 1.0 - tier * 0.1)

        cards.append(SimilarVenueCard(
            id=sim_id,
            name=v["name"],
            area=v["area"],
            city=v["city"],
            types=map_venue_types(list(v["types"] or [])),
            top_archetypes=[make_archetype_chip(n) for n in arc_names],
            top_segments=top3_seg_map.get(sim_id, []),
            delta_bars=delta_bars,
            similarity_score=sim_score,
            rank=rank_offset + idx,
        ))

    return cards, total or 0


def _build_insight_callout(similar_venues: list[SimilarVenueCard]) -> str:
    """Generate the gold callout card text from the largest absolute delta across all venues."""
    if not similar_venues:
        return ""

    best_bar: DeltaBar | None = None
    best_abs = 0.0

    for venue in similar_venues:
        for bar in venue.delta_bars:
            if abs(bar.delta) > best_abs:
                best_abs = abs(bar.delta)
                best_bar = bar

    if not best_bar or best_abs < 0.05:
        return "These venues are closely matched across all fitness dimensions."

    if best_bar.delta > 0:
        return (
            f"Largest gap: {best_bar.label} — similar venues score "
            f"{round(best_abs * 100)}pts higher. {best_bar.client_statement}"
        )
    else:
        return (
            f"Your edge: {best_bar.label} — you score "
            f"{round(best_abs * 100)}pts higher than similar venues. "
            "Lean into this in your marketing."
        )


# ─── Route ────────────────────────────────────────────────────────────────────

@router.get("/{venue_id}/similar", response_model=CompetitorsResponse)
async def get_similar_venues(
    venue_id: int = Path(...),
    limit:    int = Query(default=3, ge=1, le=25),
    offset:   int = Query(default=0, ge=0),
):
    pool = get_pool()

    async with pool.acquire() as conn:
        await conn.execute("SET statement_timeout = '15s'")
        client_card    = await _fetch_client(conn, venue_id)
        similar, total = await _fetch_similar_venues(conn, venue_id, limit, offset)

    callout = _build_insight_callout(similar)

    return CompetitorsResponse(
        client_venue=client_card,
        similar_venues=similar,
        total_similar=total,
        offset=offset,
        limit=limit,
        insight_callout=callout,
    )
