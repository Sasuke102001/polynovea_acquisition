"""
routers/risk.py
GET /api/venues/{venue_id}/risk  →  RiskResponse  (Screen 6 — Deep Analysis: Risk Tab)

Risk tab — churn risk ring derived from retention_strength, critical interventions,
and friction funnel from intervention_triggers.

Scope: behavioral signals ONLY. Never: menu, pricing, delivery, staffing.
"""

from fastapi import APIRouter, HTTPException, Path

from database import get_pool
from models import ChurnRisk, RecommendationRow, RiskResponse
from routers.utils import intervention_title

router = APIRouter()

_float = lambda v: float(v) if v is not None else 0.0

# Intervention types that represent friction or repeat-visit barriers
FRICTION_TYPES = {
    "friction_reduction",
    "operational_optimization",
    "retention_gap",
}

# Priority tier sort order (CRITICAL first, unknown last)
_TIER_ORDER = {
    "CRITICAL":  1,
    "HIGH":      2,
    "MEDIUM":    3,
    "CANDIDATE": 4,
    "LOW":       5,
    "EXPLORE":   6,
}


def _churn_level(retention: float) -> tuple[str, str]:
    """Derive churn risk level and explanation from retention_strength."""
    if retention >= 0.60:
        return (
            "LOW",
            f"Strong repeat-visit signals (score {round(retention * 100)}/100) — "
            "low churn risk. Customers are returning regularly.",
        )
    if retention >= 0.30:
        return (
            "MED",
            f"Moderate retention signals (score {round(retention * 100)}/100) — "
            "some repeat-visit gap. Targeted re-engagement can improve loyalty.",
        )
    return (
        "HIGH",
        f"Weak or absent repeat-visit signals (score {round(retention * 100)}/100) — "
        "high churn risk. Most customers visit once and don't return.",
    )


def _build_rec_row(r: dict) -> RecommendationRow:
    return RecommendationRow(
        intervention_type=r["intervention_type"],
        title=intervention_title(r["intervention_type"]),
        description=r["description"] or "",
        priority_tier=r["priority_tier"] or "LOW",
        fit_score=_float(r["fit_score"]),
        expected_impact=r["tier_description"] or "",
        recommended=bool(r["recommended"]),
    )


# ─── Route ───────────────────────────────────────────────────────────────────

@router.get("/{venue_id}/risk", response_model=RiskResponse)
async def get_risk(venue_id: int = Path(...)):
    """
    Risk tab — churn risk, critical interventions, friction funnel.

    Churn risk: derived from retention_strength in venue_fitness_dimensions.
    Critical interventions: CRITICAL/HIGH priority triggers. Falls back to
    best-available (MEDIUM/CANDIDATE) if no critical/high rows exist.
    Friction funnel: triggers whose intervention_type is friction/barrier related.
    """
    pool = get_pool()

    async with pool.acquire() as conn:
        venue = await conn.fetchrow(
            "SELECT id, name, area FROM venues WHERE id = $1",
            venue_id,
        )
        if not venue:
            raise HTTPException(status_code=404, detail="Venue not found")

        fd = await conn.fetchrow(
            "SELECT retention_strength FROM venue_fitness_dimensions WHERE venue_id = $1",
            venue_id,
        )
        retention = _float(fd["retention_strength"]) if fd else 0.0

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
                    WHEN 'CRITICAL'  THEN 1
                    WHEN 'HIGH'      THEN 2
                    WHEN 'MEDIUM'    THEN 3
                    WHEN 'CANDIDATE' THEN 4
                    WHEN 'LOW'       THEN 5
                    ELSE 6
                END,
                fit_score DESC
            """,
            venue_id,
        )

    # ── Churn risk ────────────────────────────────────────────────────────────
    level, label = _churn_level(retention)
    churn = ChurnRisk(level=level, score=retention, label=label)

    # ── Critical interventions ────────────────────────────────────────────────
    # Prefer CRITICAL/HIGH. Fall back to best-available if none exist.
    critical: list[RecommendationRow] = [
        _build_rec_row(r)
        for r in trigger_rows
        if r["priority_tier"] in ("CRITICAL", "HIGH")
    ][:6]

    if not critical:
        # Fallback: show top 3 by tier order (whatever exists)
        critical = [_build_rec_row(r) for r in trigger_rows[:3]]

    # ── Friction funnel ───────────────────────────────────────────────────────
    friction: list[RecommendationRow] = [
        _build_rec_row(r)
        for r in trigger_rows
        if r["intervention_type"] in FRICTION_TYPES
    ]

    return RiskResponse(
        venue_name=venue["name"],
        venue_area=venue["area"],
        churn_risk=churn,
        critical_interventions=critical,
        friction_items=friction,
    )
