"""
routers/primitives_tab.py
GET /api/venues/{venue_id}/primitives  →  PrimitivesResponse  (Screen 6 — Primitives Tab)

Primitives tab — behavioral signal heatmap.
Shows all 21 scored primitives grouped by category, with top/bottom summary
and automated conflict detection for contradictory high-scoring signals.

primitive_id is a varchar in primitives_scores (e.g. 'live_music', 'social_energy').
No separate primitives lookup table — the id IS the name.
"""

from fastapi import APIRouter, HTTPException, Path

from database import get_pool
from models import PrimitiveScore, PrimitiveGroup, PrimitiveConflict, PrimitivesResponse

router = APIRouter()

_float = lambda v: float(v) if v is not None else 0.0


# ─── Category map ─────────────────────────────────────────────────────────────
# Maps every known primitive_id to a display category.
# "Other" is the fallback for any unknown primitives that appear in future data.

PRIMITIVE_CATEGORIES: dict[str, str] = {
    # Atmosphere
    "comfort":             "Atmosphere",
    "crowding":            "Atmosphere",
    "excitement":          "Atmosphere",
    "great_view":          "Atmosphere",
    "live_music":          "Atmosphere",
    "scenic_value":        "Atmosphere",
    "wonder_ambience":     "Atmosphere",
    # Social
    "long_dwell":          "Social",
    "social_company":      "Social",
    "social_energy":       "Social",
    # Food
    "authentic_taste":     "Food",
    "food_quality":        "Food",
    # Service
    "service_quality":     "Service",
    "staff_warmth":        "Service",
    # Emotional signals
    "disappointment":      "Signals",
    "experience_memories": "Signals",
    "nostalgia":           "Signals",
    "nostalgia_emotion":   "Signals",
    "pride":               "Signals",
    "relief":              "Signals",
    "satisfaction":        "Signals",
}

CATEGORY_ORDER = ["Atmosphere", "Social", "Food", "Service", "Signals"]


# ─── Conflict rules ───────────────────────────────────────────────────────────
# (primitive_a, primitive_b, reason)
# Both must score >= 0.55 for the conflict to be flagged.

CONFLICT_RULES: list[tuple[str, str, str]] = [
    (
        "crowding",
        "comfort",
        "High crowding and high comfort are typically contradictory — "
        "a crowded venue struggles to deliver comfort.",
    ),
    (
        "disappointment",
        "satisfaction",
        "Simultaneous high disappointment and satisfaction signals are contradictory — "
        "review sentiment is deeply split.",
    ),
    (
        "crowding",
        "long_dwell",
        "Crowded venues generally deter extended dwell time — "
        "customers leave sooner when space is tight.",
    ),
]


def _label(primitive_id: str) -> str:
    """Convert snake_case primitive_id to Title Case display label."""
    return primitive_id.replace("_", " ").title()


# ─── Route ───────────────────────────────────────────────────────────────────

@router.get("/{venue_id}/primitives", response_model=PrimitivesResponse)
async def get_primitives(venue_id: int = Path(...)):
    """
    Primitives tab — behavioral signal heatmap.

    Returns:
    - All scored primitives grouped by category (Atmosphere, Social, Food, Service, Signals)
    - Top 5 highest-scoring signals
    - Bottom 5 lowest-scoring signals (among those with data)
    - Conflict pairs where two contradictory signals both score ≥ 0.55
    - Total count of primitives with signal data

    Primitives not in the DB for this venue are included in groups with
    score=0 and has_signal=False to show the full signal landscape.
    """
    pool = get_pool()

    async with pool.acquire() as conn:
        venue = await conn.fetchrow(
            "SELECT id, name, area FROM venues WHERE id = $1",
            venue_id,
        )
        if not venue:
            raise HTTPException(status_code=404, detail="Venue not found")

        rows = await conn.fetch(
            """
            SELECT primitive_id, score
            FROM   primitives_scores
            WHERE  venue_id = $1
            ORDER  BY score DESC
            """,
            venue_id,
        )

    # ── Build score lookup ────────────────────────────────────────────────────
    scored_map: dict[str, float] = {r["primitive_id"]: _float(r["score"]) for r in rows}

    # ── Build full primitive list ─────────────────────────────────────────────
    # Include ALL known primitives — scored ones get actual values,
    # unscored ones get score=0 / has_signal=False.
    all_primitives: list[PrimitiveScore] = [
        PrimitiveScore(
            primitive_id=pid,
            label=_label(pid),
            score=scored_map.get(pid, 0.0),
            category=PRIMITIVE_CATEGORIES.get(pid, "Other"),
            has_signal=pid in scored_map,
        )
        for pid in PRIMITIVE_CATEGORIES
    ]

    # ── Groups by category ────────────────────────────────────────────────────
    groups: list[PrimitiveGroup] = []
    for cat in CATEGORY_ORDER:
        members = sorted(
            [p for p in all_primitives if p.category == cat],
            key=lambda p: p.score,
            reverse=True,
        )
        if members:
            groups.append(PrimitiveGroup(category=cat, primitives=members))

    # ── Top 5 / Bottom 5 (only among primitives with actual signal data) ──────
    has_signal = [p for p in all_primitives if p.has_signal]
    by_score_desc = sorted(has_signal, key=lambda p: p.score, reverse=True)
    top_5    = by_score_desc[:5]
    bottom_5 = list(reversed(by_score_desc))[:5]

    # ── Conflict detection ────────────────────────────────────────────────────
    conflicts: list[PrimitiveConflict] = [
        PrimitiveConflict(primitive_a=a, primitive_b=b, reason=reason)
        for a, b, reason in CONFLICT_RULES
        if scored_map.get(a, 0.0) >= 0.55 and scored_map.get(b, 0.0) >= 0.55
    ]

    return PrimitivesResponse(
        venue_name=venue["name"],
        venue_area=venue["area"],
        groups=groups,
        top_5=top_5,
        bottom_5=bottom_5,
        conflicts=conflicts,
        total_scored=len(has_signal),
    )
