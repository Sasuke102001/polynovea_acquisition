"""
link_patterns.py
Links a manually added venue to existing behavioral_patterns based on signal overlap.
Equivalent to pattern_venues population in step_4_cluster_and_patterns.py.

Reads:  primitives_scores (venue's signals) + behavioral_patterns (existing area patterns)
Writes: pattern_venues

A venue is linked to a pattern when it has ALL of the pattern's co-occurring signals
above a minimum confidence threshold.

Usage:
    python link_patterns.py --venue-id 12066
    python link_patterns.py --venue-id 12066 --area mumbai --min-confidence 0.3
"""

import argparse
import json
import os
import sys

import psycopg2
import psycopg2.extras

sys.stdout.reconfigure(encoding='utf-8')

DB_CONFIG = {
    'host':     os.getenv('PG_HOST',     'polynovea-module2.cxeo8066g8t2.ap-south-1.rds.amazonaws.com'),
    'port':     int(os.getenv('PG_PORT', 5432)),
    'dbname':   os.getenv('PG_DB',       'polynovea_module2'),
    'user':     os.getenv('PG_USER',     'polynovea_admin'),
    'password': os.getenv('PG_PASSWORD', 'REDACTED_DB_PASSWORD'),
    'sslmode':  'require',
}

DEFAULT_MIN_CONFIDENCE = 0.30


def _get_area_key(city: str, area: str) -> str:
    """Map city/area to the area key used in behavioral_patterns."""
    city_lower = (city or "").lower()
    area_lower = (area or "").lower()

    if "navi" in city_lower or "navi" in area_lower:
        return "navi-mumbai"
    if "thane" in city_lower or "thane" in area_lower:
        return "thane"
    if "sobo" in area_lower or any(x in area_lower for x in ["colaba", "fort", "nariman", "churchgate", "bandra", "juhu", "andheri", "powai"]):
        return "mumbai-sobo"
    return "mumbai-main"


def run(venue_id: int, area_override: str | None = None, min_confidence: float = DEFAULT_MIN_CONFIDENCE) -> None:
    conn = psycopg2.connect(**DB_CONFIG)
    cur  = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)

    try:
        # Fetch venue info
        cur.execute("SELECT name, city, area FROM venues WHERE id = %s", (venue_id,))
        venue = cur.fetchone()
        if not venue:
            print(f"  Venue {venue_id} not found")
            return

        area_key = area_override or _get_area_key(venue["city"] or "", venue["area"] or "")
        print(f"  Linking {venue['name']} (venue_id={venue_id}) to patterns in area='{area_key}'")

        # Fetch venue's signals above threshold
        cur.execute(
            """
            SELECT primitive_id, MAX(confidence) AS confidence
            FROM primitives_scores WHERE venue_id = %s
            GROUP BY primitive_id
            HAVING MAX(confidence) >= %s
            """,
            (venue_id, min_confidence),
        )
        venue_signals = {r["primitive_id"] for r in cur.fetchall()}
        print(f"  Venue has {len(venue_signals)} signals above {min_confidence}: {venue_signals}")

        if not venue_signals:
            print("  No signals above threshold — cannot link patterns")
            return

        # Fetch existing patterns for this area
        cur.execute(
            """
            SELECT id, pattern_name, co_occurring_primitives, source
            FROM behavioral_patterns
            WHERE area = %s
            """,
            (area_key,),
        )
        patterns = cur.fetchall()
        print(f"  Found {len(patterns)} existing patterns for area '{area_key}'")

        linked = 0
        for pattern in patterns:
            primitives = pattern["co_occurring_primitives"]
            if isinstance(primitives, str):
                try:
                    primitives = json.loads(primitives)
                except Exception:
                    primitives = []

            if not primitives:
                continue

            # Link if venue has ALL signals in the pattern
            pattern_signals = set(primitives) if isinstance(primitives[0], str) else set()
            if not pattern_signals:
                # Handle list-of-dicts format
                pattern_signals = {p.get("signal", p) for p in primitives if isinstance(p, dict)}

            if pattern_signals and pattern_signals.issubset(venue_signals):
                try:
                    cur.execute(
                        """
                        INSERT INTO pattern_venues (venue_id, pattern_id)
                        VALUES (%s, %s)
                        ON CONFLICT (venue_id, pattern_id) DO NOTHING
                        """,
                        (venue_id, pattern["id"]),
                    )
                    linked += 1
                except Exception:
                    pass

        conn.commit()
        print(f"  Linked venue to {linked} behavioral patterns")

        if linked == 0:
            print(f"  NOTE: No pattern fully matched venue's signal set.")
            print(f"  Top venue signals: {list(venue_signals)[:8]}")
            print(f"  Consider running extract_primitives.py again or lowering --min-confidence")

    except Exception as e:
        conn.rollback()
        raise e
    finally:
        cur.close()
        conn.close()


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description="Link manual venue to existing behavioral patterns")
    parser.add_argument('--venue-id',       type=int,   required=True)
    parser.add_argument('--area',           type=str,   default=None,
                        help="Area key override (mumbai-main, navi-mumbai, thane, mumbai-sobo)")
    parser.add_argument('--min-confidence', type=float, default=DEFAULT_MIN_CONFIDENCE)
    args = parser.parse_args()
    run(args.venue_id, args.area, args.min_confidence)
