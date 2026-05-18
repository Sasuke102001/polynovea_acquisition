"""
amendment_service.py
Source-specific recency weighting for primitive scores.

Phase 1: Google Places only (weight = 1.0)
Phase 2: Google 50% + MagicPin upper 30% + Google Reviews 20% (multi-source blend)

Decay formula: weight = 0.5 ^ (days_since_update / HALF_LIFE_DAYS)
Reviews older than MAX_AGE_DAYS are excluded (weight < WEIGHT_FLOOR).
"""

import math
import json
from datetime import datetime, timezone
from typing import Optional

import psycopg2
import psycopg2.extras


# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------

HALF_LIFE_DAYS  = 30     # score halves every 30 days
MAX_AGE_DAYS    = 180    # ignore scores older than 6 months
WEIGHT_FLOOR    = 0.10   # minimum usable decay weight

SOURCE_WEIGHTS = {
    1: {                          # Phase 1 — Google only
        'google':   1.0,
    },
    2: {                          # Phase 2 — multi-source blend
        'google':         0.50,
        'magicpin_upper': 0.30,
        'google_reviews': 0.20,
    },
}

ALL_SOURCES = ('google', 'zomato', 'magicpin_upper', 'google_reviews')


# ---------------------------------------------------------------------------
# Core decay logic
# ---------------------------------------------------------------------------

def compute_decay_weight(last_updated: datetime) -> float:
    """
    Exponential decay: weight = 0.5 ^ (elapsed_days / HALF_LIFE_DAYS)
    Returns 0.0 if the score is too old (> MAX_AGE_DAYS).
    """
    now          = datetime.now(timezone.utc)
    last_updated = last_updated.replace(tzinfo=timezone.utc) if last_updated.tzinfo is None else last_updated
    elapsed_days = (now - last_updated).total_seconds() / 86_400

    if elapsed_days > MAX_AGE_DAYS:
        return 0.0

    weight = math.pow(0.5, elapsed_days / HALF_LIFE_DAYS)
    return max(weight, WEIGHT_FLOOR)


# ---------------------------------------------------------------------------
# AmendmentService
# ---------------------------------------------------------------------------

class AmendmentService:
    """
    Reads from and writes to the primitives_scores table.
    Compute composite scores across sources with decay weighting.
    """

    def __init__(self, conn: psycopg2.extensions.connection, phase: int = 1):
        self.conn  = conn
        self.phase = phase
        self._weights = SOURCE_WEIGHTS.get(phase, SOURCE_WEIGHTS[1])

    # ------------------------------------------------------------------
    # Read: composite score for one primitive
    # ------------------------------------------------------------------

    def get_composite_score(self, venue_id: int, primitive_id: str) -> Optional[float]:
        """
        Returns a single decay-weighted composite score for a primitive,
        blending all active sources using phase-appropriate weights.
        Returns None if no usable data exists.
        """
        cursor = self.conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
        cursor.execute(
            """
            SELECT source, score, confidence, last_updated
            FROM primitives_scores
            WHERE venue_id = %s AND primitive_id = %s
            """,
            (venue_id, primitive_id),
        )
        rows = cursor.fetchall()
        cursor.close()

        if not rows:
            return None

        total_weighted_score  = 0.0
        total_effective_weight = 0.0

        for row in rows:
            source       = row['source']
            source_weight = self._weights.get(source, 0.0)

            if source_weight == 0.0:
                continue  # source not active in this phase

            decay        = compute_decay_weight(row['last_updated'])
            confidence   = float(row['confidence'] or 1.0)
            effective_w  = source_weight * decay * confidence

            total_weighted_score   += float(row['score']) * effective_w
            total_effective_weight += effective_w

        if total_effective_weight == 0.0:
            return None

        return round(total_weighted_score / total_effective_weight, 4)

    # ------------------------------------------------------------------
    # Read: composite vector for one venue (all primitives)
    # ------------------------------------------------------------------

    def get_composite_vector(self, venue_id: int) -> dict:
        """
        Returns {primitive_id: composite_score} for all primitives with data.
        """
        cursor = self.conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
        cursor.execute(
            """
            SELECT source, primitive_id, score, confidence, last_updated
            FROM primitives_scores
            WHERE venue_id = %s
            ORDER BY primitive_id, source
            """,
            (venue_id,),
        )
        rows = cursor.fetchall()
        cursor.close()

        # Group by primitive_id
        grouped: dict[str, list] = {}
        for row in rows:
            grouped.setdefault(row['primitive_id'], []).append(row)

        result = {}
        for primitive_id, source_rows in grouped.items():
            total_ws = 0.0
            total_w  = 0.0
            for row in source_rows:
                source_weight = self._weights.get(row['source'], 0.0)
                if source_weight == 0.0:
                    continue
                decay       = compute_decay_weight(row['last_updated'])
                confidence  = float(row['confidence'] or 1.0)
                eff_w       = source_weight * decay * confidence
                total_ws   += float(row['score']) * eff_w
                total_w    += eff_w

            if total_w > 0.0:
                result[primitive_id] = round(total_ws / total_w, 4)

        return result

    # ------------------------------------------------------------------
    # Write: apply new scores from a fresh data extraction
    # ------------------------------------------------------------------

    def apply_amendment(
        self,
        venue_id:     int,
        source:       str,
        new_scores:   dict,   # {primitive_id: score}
        confidences:  dict,   # {primitive_id: confidence}  (optional per-primitive)
        review_date:  Optional[datetime] = None,
    ) -> int:
        """
        Upserts new primitive scores for a specific source.
        Returns the number of rows upserted.
        """
        if source not in ALL_SOURCES:
            raise ValueError(f"Unknown source '{source}'. Must be one of {ALL_SOURCES}.")

        timestamp = review_date or datetime.now(timezone.utc)
        cursor    = self.conn.cursor()
        upserted  = 0

        for primitive_id, score in new_scores.items():
            score      = max(0.0, min(1.0, float(score)))
            confidence = max(0.0, min(1.0, float(confidences.get(primitive_id, 1.0))))

            cursor.execute(
                """
                INSERT INTO primitives_scores
                    (venue_id, source, primitive_id, score, confidence, last_updated)
                VALUES (%s, %s, %s, %s, %s, %s)
                ON CONFLICT (venue_id, source, primitive_id) DO UPDATE SET
                    score        = EXCLUDED.score,
                    confidence   = EXCLUDED.confidence,
                    last_updated = EXCLUDED.last_updated;
                """,
                (venue_id, source, primitive_id, score, confidence, timestamp),
            )
            upserted += cursor.rowcount

        cursor.close()
        return upserted

    # ------------------------------------------------------------------
    # Utility: source freshness report for a venue
    # ------------------------------------------------------------------

    def freshness_report(self, venue_id: int) -> dict:
        """
        Returns per-source decay weights and staleness info.
        Useful for dashboard / debugging.
        """
        cursor = self.conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
        cursor.execute(
            """
            SELECT source, MAX(last_updated) AS latest, COUNT(*) AS primitives
            FROM primitives_scores
            WHERE venue_id = %s
            GROUP BY source
            """,
            (venue_id,),
        )
        rows = cursor.fetchall()
        cursor.close()

        report = {}
        for row in rows:
            source   = row['source']
            latest   = row['latest']
            decay    = compute_decay_weight(latest) if latest else 0.0
            now      = datetime.now(timezone.utc)
            latest_  = latest.replace(tzinfo=timezone.utc) if latest and latest.tzinfo is None else latest
            age_days = round((now - latest_).total_seconds() / 86_400, 1) if latest_ else None

            report[source] = {
                'latest_update':   latest.isoformat() if latest else None,
                'age_days':        age_days,
                'decay_weight':    round(decay, 4),
                'primitive_count': row['primitives'],
                'source_weight':   self._weights.get(source, 0.0),
                'effective_weight': round(decay * self._weights.get(source, 0.0), 4),
                'usable':          decay > 0.0,
            }

        return report


# ---------------------------------------------------------------------------
# Convenience: standalone composite score (no class instance needed)
# ---------------------------------------------------------------------------

def get_score(conn, venue_id: int, primitive_id: str, phase: int = 1) -> Optional[float]:
    return AmendmentService(conn, phase).get_composite_score(venue_id, primitive_id)


def get_vector(conn, venue_id: int, phase: int = 1) -> dict:
    return AmendmentService(conn, phase).get_composite_vector(venue_id)
