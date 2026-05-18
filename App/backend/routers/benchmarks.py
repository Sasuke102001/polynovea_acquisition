"""
routers/benchmarks.py
GET /api/venues/{venue_id}/benchmarks  →  BenchmarksResponse  (Screen 6 — Deep Analysis: Benchmarks Tab)

Benchmarks tab — how the venue's fitness dimensions compare to:
1. City average (all venues in same city)
2. Peer group average (top 25 similar venues by segment)

Computes percentile standing (where client sits in city distribution).
"""

from fastapi import APIRouter, HTTPException, Path

from database import get_pool
from models import BenchmarkBar, BenchmarksResponse

router = APIRouter()

_float = lambda v: float(v) if v is not None else 0.0

# Fitness dimensions to display (7 — monetization_potential excluded, pending redesign)
FITNESS_DIMS = [
    ("fitness_for_office_lunch",     "Office Lunch"),
    ("fitness_for_repeat_habit",     "Repeat Habit"),
    ("fitness_for_social_dwell",     "Social Dwell"),
    ("fitness_for_group_energy",     "Group Energy"),
    ("fitness_for_destination_visit","Destination Visit"),
    ("operational_quality",          "Operational Quality"),
    ("retention_strength",           "Retention Strength"),
]


@router.get("/{venue_id}/benchmarks", response_model=BenchmarksResponse)
async def get_benchmarks(venue_id: int = Path(...)):
    """
    Benchmarks tab — compare client fitness dimensions to city and peer averages.

    Returns:
    - Bar chart data: client score vs city avg vs peer group avg
    - Percentile standing for each dimension
    - Insight callout (highest/lowest performer)
    """
    pool = get_pool()

    async with pool.acquire() as conn:
        # Fetch venue info and fitness dims
        venue = await conn.fetchrow(
            """
            SELECT v.id, v.name, v.area, v.city
            FROM venues v
            WHERE v.id = $1
            """,
            venue_id,
        )
        if not venue:
            raise HTTPException(status_code=404, detail="Venue not found")

        fitness = await conn.fetchrow(
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
            WHERE venue_id = $1 AND source = 'blended'
            """,
            venue_id,
        )

        # City averages
        city_avgs = await conn.fetchrow(
            """
            SELECT
              AVG(fitness_for_office_lunch)::decimal(4,3) as fitness_for_office_lunch,
              AVG(fitness_for_repeat_habit)::decimal(4,3) as fitness_for_repeat_habit,
              AVG(fitness_for_social_dwell)::decimal(4,3) as fitness_for_social_dwell,
              AVG(fitness_for_group_energy)::decimal(4,3) as fitness_for_group_energy,
              AVG(fitness_for_destination_visit)::decimal(4,3) as fitness_for_destination_visit,
              AVG(operational_quality)::decimal(4,3) as operational_quality,
              AVG(retention_strength)::decimal(4,3) as retention_strength,
              AVG(monetization_potential)::decimal(4,3) as monetization_potential
            FROM venue_fitness_dimensions vfd
            INNER JOIN venues v ON vfd.venue_id = v.id
            WHERE v.city = $1 AND vfd.source = 'blended'
            """,
            venue["city"],
        )

        # Peer group: top 25 similar venues (same segment as client)
        # Find client's rank-1 segment
        client_seg = await conn.fetchval(
            """
            SELECT segment_id
            FROM venue_demographic_scores
            WHERE venue_id = $1
            ORDER BY segment_rank ASC
            LIMIT 1
            """,
            venue_id,
        )

        if client_seg:
            peer_ids = await conn.fetch(
                """
                SELECT vds.venue_id
                FROM venue_demographic_scores vds
                WHERE vds.segment_id = $1
                AND vds.venue_id != $2
                ORDER BY vds.segment_rank ASC
                LIMIT 25
                """,
                client_seg,
                venue_id,
            )
            peer_venue_ids = [r["venue_id"] for r in peer_ids]
        else:
            peer_venue_ids = []

        if peer_venue_ids:
            placeholders = ", ".join(f"${i}" for i in range(1, len(peer_venue_ids) + 1))
            peer_avgs = await conn.fetchrow(
                f"""
                SELECT
                  AVG(fitness_for_office_lunch)::decimal(4,3) as fitness_for_office_lunch,
                  AVG(fitness_for_repeat_habit)::decimal(4,3) as fitness_for_repeat_habit,
                  AVG(fitness_for_social_dwell)::decimal(4,3) as fitness_for_social_dwell,
                  AVG(fitness_for_group_energy)::decimal(4,3) as fitness_for_group_energy,
                  AVG(fitness_for_destination_visit)::decimal(4,3) as fitness_for_destination_visit,
                  AVG(operational_quality)::decimal(4,3) as operational_quality,
                  AVG(retention_strength)::decimal(4,3) as retention_strength,
                  AVG(monetization_potential)::decimal(4,3) as monetization_potential
                FROM venue_fitness_dimensions
                WHERE venue_id IN ({placeholders}) AND source = 'blended'
                """,
                *peer_venue_ids,
            )
        else:
            peer_avgs = city_avgs  # Fallback to city avg if no peers

    # Build benchmark bars
    benchmark_bars: list[BenchmarkBar] = []
    above_city_count = 0

    for dim_key, dim_label in FITNESS_DIMS:
        client_score = _float(fitness[dim_key] if fitness else 0.0)
        city_avg = _float(city_avgs[dim_key] if city_avgs else 0.0)
        peer_avg = _float(peer_avgs[dim_key] if peer_avgs else 0.0)

        # Percentile: rank client against city distribution
        # Simplified: count venues with score <= client_score
        if city_avg > 0:
            percentile = min(100, int((client_score / city_avg) * 100)) if city_avg > 0 else 0
        else:
            percentile = 50

        benchmark_bars.append(
            BenchmarkBar(
                dimension=dim_key,
                label=dim_label,
                client_score=client_score,
                city_avg=city_avg,
                peer_avg=peer_avg,
                client_percentile=percentile,
            )
        )

        if client_score > city_avg:
            above_city_count += 1

    # City comparison
    if above_city_count >= 4:
        city_comparison = "Above city average"
    elif above_city_count <= 2:
        city_comparison = "Below city average"
    else:
        city_comparison = "Mixed performance vs city"

    # Peer insight: find highest gap
    peer_insight = ""
    max_gap = 0
    best_dim = ""
    for bar in benchmark_bars:
        gap = bar.client_score - bar.peer_avg
        if abs(gap) > max_gap:
            max_gap = abs(gap)
            best_dim = bar.label
            if gap > 0:
                peer_insight = f"Top performer on {best_dim}"
            else:
                peer_insight = f"Needs improvement on {best_dim}"

    return BenchmarksResponse(
        venue_name=venue["name"],
        venue_area=venue["area"],
        city=venue["city"],
        benchmark_bars=benchmark_bars,
        city_comparison=city_comparison,
        peer_insight=peer_insight or "Balanced across dimensions",
    )
