"""
routers/venues.py
GET /api/venues/search  →  SearchResponse   (Screen 1 — Venue Search)
"""

from fastapi import APIRouter, Query
from fastapi.exceptions import HTTPException

from database import get_pool
from models import SearchResponse, VenueCard
from routers.utils import map_venue_types, make_archetype_chip, compute_health_score, SEGMENT_TOP_ARCHETYPES, SEGMENT_LABELS

router = APIRouter()


@router.get("/search", response_model=SearchResponse)
async def search_venues(
    q:           str = Query(default="",  description="Name or area search term"),
    city:        str = Query(default="",  description="City filter (partial match)"),
    venue_type:  str = Query(default="",  description="Venue type filter (raw Google Places key, e.g. 'cafe', 'bar')"),
    limit:       int = Query(default=20,  ge=1, le=100),
    offset:      int = Query(default=0,   ge=0),
):
    """
    Full-text search across venue name + area.
    Returns VenueCards with health score rings and top 2 archetype chips.
    Health score = composite of operational_quality + retention_strength.
    Archetypes are derived from the venue's primary demographic segment.
    """
    pool  = get_pool()
    like  = f"%{q}%"  if q    else "%"
    clike = f"%{city}%" if city else "%"

    async with pool.acquire() as conn:
        total: int = await conn.fetchval(
            """
            SELECT COUNT(*)
            FROM   venues v
            JOIN   venue_fitness_dimensions fd
                     ON fd.venue_id = v.id
                    AND fd.source = (
                        SELECT source FROM venue_fitness_dimensions
                        WHERE venue_id = v.id
                        ORDER BY CASE source WHEN 'blended' THEN 0 WHEN 'google' THEN 1 ELSE 2 END
                        LIMIT 1
                    )
            WHERE  (v.name ILIKE $1 OR v.area ILIKE $1)
              AND  v.city ILIKE $2
              AND  ($3::text = '' OR v.types @> to_jsonb($3::text))
            """,
            like, clike, venue_type,
        )

        rows = await conn.fetch(
            """
            SELECT
                v.id,
                v.place_id,
                v.name,
                v.area,
                v.city,
                v.types,
                fd.operational_quality,
                fd.fitness_for_social_dwell,
                fd.fitness_for_group_energy,
                fd.retention_strength,
                ARRAY(
                    SELECT segment_id
                    FROM   venue_demographic_scores
                    WHERE  venue_id = v.id
                    ORDER BY segment_rank
                    LIMIT  2
                ) AS top_segment_ids
            FROM   venues v
            JOIN   venue_fitness_dimensions fd
                     ON fd.venue_id = v.id
                    AND fd.source = (
                        SELECT source FROM venue_fitness_dimensions
                        WHERE venue_id = v.id
                        ORDER BY CASE source WHEN 'blended' THEN 0 WHEN 'google' THEN 1 ELSE 2 END
                        LIMIT 1
                    )
            WHERE  (v.name ILIKE $1 OR v.area ILIKE $1)
              AND  v.city ILIKE $2
              AND  ($3::text = '' OR v.types @> to_jsonb($3::text))
            ORDER BY (COALESCE(fd.operational_quality, 0) + COALESCE(fd.retention_strength, 0)) DESC
            LIMIT  $4
            OFFSET $5
            """,
            like, clike, venue_type, limit, offset,
        )

    cards = []
    for r in rows:
        seg_ids      = list(r["top_segment_ids"] or [])
        primary_seg  = seg_ids[0] if seg_ids else "office_workers"
        arc_names    = SEGMENT_TOP_ARCHETYPES.get(primary_seg, [])
        seg_labels   = [
            SEGMENT_LABELS[s]["label"]
            for s in seg_ids
            if s in SEGMENT_LABELS
        ]
        health_score = compute_health_score(
            r["operational_quality"],
            r["fitness_for_social_dwell"],
            r["fitness_for_group_energy"],
            r["retention_strength"],
        )

        cards.append(VenueCard(
            id=r["id"],
            place_id=r["place_id"],
            name=r["name"],
            area=r["area"],
            city=r["city"],
            types=map_venue_types(list(r["types"] or [])),
            top_segments=seg_labels,
            top_archetypes=[make_archetype_chip(n) for n in arc_names],
            health_score=health_score,
        ))

    return SearchResponse(venues=cards, total=total, limit=limit, offset=offset)
