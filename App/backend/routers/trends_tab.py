"""
routers/trends_tab.py
GET /api/venues/{venue_id}/trends  →  TrendsResponse  (Screen 6 — Deep Analysis: Trends Tab)

Trends tab — temporal patterns and emerging/declining signals in the market.
Shows drift_signals by trend_direction and pattern_scores top rising patterns.
"""

from fastapi import APIRouter, HTTPException, Path

from database import get_pool
from models import TrendSignal, RisingPattern, TrendsResponse

router = APIRouter()

_float = lambda v: float(v) if v is not None else 0.0


@router.get("/{venue_id}/trends", response_model=TrendsResponse)
async def get_trends(venue_id: int = Path(...)):
    """
    Trends tab — emerging/declining behavioral patterns in the market.

    Returns:
    - Trend signals: EMERGING and DECLINING patterns from drift_signals
    - Rising patterns: top 5 patterns by confidence score
    - Insight callout based on strongest trend
    """
    pool = get_pool()

    async with pool.acquire() as conn:
        # Fetch venue info
        venue = await conn.fetchrow(
            """
            SELECT id, name, area, city
            FROM venues
            WHERE id = $1
            """,
            venue_id,
        )
        if not venue:
            raise HTTPException(status_code=404, detail="Venue not found")

        # Fetch drift signals grouped by trend direction
        # Get top emerging and top declining for the venue's area
        trend_signals_rows = await conn.fetch(
            """
            SELECT
              pattern_description,
              confidence_score,
              trend_direction
            FROM drift_signals
            WHERE area = $1
            ORDER BY
              CASE
                WHEN trend_direction = 'emerging' THEN 1
                WHEN trend_direction = 'declining' THEN 2
                ELSE 3
              END,
              confidence_score DESC
            LIMIT 6
            """,
            venue["area"],
        )

        # Fetch rising patterns (top 5 by confidence from pattern_scores)
        rising_patterns_rows = await conn.fetch(
            """
            SELECT
              bp.pattern_name,
              ps.confidence_score,
              ps.prevalence
            FROM pattern_scores ps
            INNER JOIN behavioral_patterns bp ON ps.pattern_id = bp.id
            WHERE bp.area = $1
            ORDER BY ps.confidence_score DESC
            LIMIT 5
            """,
            venue["area"],
        )

    # Build trend signals
    trend_signals: list[TrendSignal] = []
    for row in trend_signals_rows:
        direction = row["trend_direction"] or "emerging"
        signal_label = "Emerging" if direction == "emerging" else (
            "Declining" if direction == "declining" else "Stable"
        )
        trend_signals.append(
            TrendSignal(
                pattern_description=row["pattern_description"],
                confidence=_float(row["confidence_score"]),
                trend_direction=direction,
                signal_label=signal_label,
            )
        )

    # Build rising patterns
    rising_patterns: list[RisingPattern] = []
    for row in rising_patterns_rows:
        confidence = _float(row["confidence_score"])
        prevalence = _float(row["prevalence"])

        # Determine status based on confidence trajectory
        if confidence >= 0.75:
            status = "Rising"
        elif confidence >= 0.5:
            status = "Stable"
        else:
            status = "Declining"

        rising_patterns.append(
            RisingPattern(
                pattern_name=row["pattern_name"],
                confidence=confidence,
                prevalence_pct=prevalence * 100,
                status=status,
            )
        )

    # Insight callout
    insight_callout = ""
    if trend_signals:
        strongest = trend_signals[0]
        if strongest.signal_label == "Emerging":
            insight_callout = f"Emerging pattern: {strongest.pattern_description}"
        else:
            insight_callout = f"Declining pattern: {strongest.pattern_description}"
    else:
        insight_callout = "No significant trend signals detected"

    return TrendsResponse(
        venue_name=venue["name"],
        venue_area=venue["area"],
        trend_signals=trend_signals,
        rising_patterns=rising_patterns,
        insight_callout=insight_callout,
    )
