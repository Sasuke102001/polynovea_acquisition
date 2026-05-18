"""
013_compute_fitness_deltas.py
Two operations:

  1. Creates + populates fitness_delta_rules
     56 rules (7 threshold bands × 8 fitness dimensions) mapping a delta value
     to a short_label + client_statement in plain English.
     Consultants can edit these rows directly in the DB to tune language.

  2. Creates + populates venue_similarity_deltas
     Pre-computes all 8 fitness dimension deltas for every similarity pair.
     146,426 pairs × 8 dimensions = ~1.17M rows.
     delta = similar_venue.score − client_venue.score (positive = similar is better)

Enables:
  - Feature 1 (Competitors Tab): number + plain-English statement per fitness bar
  - Feature 2 (Transform Tab):   same, filtered by target demographic
  - Feature 10 (Benchmarking):   dimension-level comparison at scale

Run after: 012_compute_venue_demographics.py
"""

import os
import sys
import psycopg2
import psycopg2.extras

sys.stdout.reconfigure(encoding='utf-8')

DB_CONFIG = {
    'host':     os.getenv('PG_HOST',     'your-db-instance.ap-south-1.rds.amazonaws.com'),
    'port':     int(os.getenv('PG_PORT', 5432)),
    'dbname':   os.getenv('PG_DB',       'polynovea_module2'),
    'user':     os.getenv('PG_USER',     'your_user'),
    'password': os.getenv('PG_PASSWORD', 'your_password'),
    'sslmode':  'require',
}

# ─── Dimension display names (for UI labels) ────────────────────────────────

DIMENSION_LABELS = {
    'fitness_for_office_lunch':    'Office Lunch',
    'fitness_for_repeat_habit':    'Repeat Habit',
    'fitness_for_social_dwell':    'Social Dwell',
    'fitness_for_group_energy':    'Group Energy',
    'fitness_for_destination_visit': 'Destination Visit',
    'operational_quality':         'Operational Quality',
    'retention_strength':          'Retention Strength',
    'monetization_potential':      'Monetization Potential',
}

FITNESS_DIMS = list(DIMENSION_LABELS.keys())

# ─── Delta interpretation rules ─────────────────────────────────────────────
# 7 bands per dimension, ordered from strongest positive to strongest negative.
# client_statement is written from the CLIENT'S perspective:
#   "They" = the similar venue being compared
#   Positive delta → similar venue scores higher than client venue

DELTA_RULES = []

def add_rules(dimension, bands):
    for (delta_min, delta_max, direction, short_label, client_statement) in bands:
        DELTA_RULES.append({
            'dimension':        dimension,
            'delta_min':        delta_min,
            'delta_max':        delta_max,
            'direction':        direction,   # 'higher' | 'lower' | 'neutral'
            'short_label':      short_label,
            'client_statement': client_statement,
        })

add_rules('fitness_for_office_lunch', [
    ( 0.25,  1.00, 'higher',  'Far stronger',    'Far better set up for the office lunch crowd — faster, more reliable, closer to how corporates think'),
    ( 0.10,  0.25, 'higher',  'Stronger',         'Better optimised for weekday office visits — service speed and consistency'),
    ( 0.05,  0.10, 'higher',  'Slightly ahead',   'Marginally better at attracting the office lunch segment'),
    (-0.05,  0.05, 'neutral', 'Equal',            'Similar weekday office appeal to your venue'),
    (-0.10, -0.05, 'lower',   'Slightly behind',  'Slightly less suited for the office lunch crowd'),
    (-0.25, -0.10, 'lower',   'Weaker',           'Less optimised for midday office visits — you have an edge here'),
    (-1.00, -0.25, 'lower',   'Far weaker',       'Significantly less office lunch appeal — this is a clear strength of yours'),
])

add_rules('fitness_for_repeat_habit', [
    ( 0.25,  1.00, 'higher',  'Far stronger',    'Much stronger at building regular customer habits — their customers return on autopilot'),
    ( 0.10,  0.25, 'higher',  'Stronger',         'Better at bringing customers back repeatedly over time'),
    ( 0.05,  0.10, 'higher',  'Slightly ahead',   'Marginally better at encouraging repeat visits'),
    (-0.05,  0.05, 'neutral', 'Equal',            'Similar habit-forming potential to your venue'),
    (-0.10, -0.05, 'lower',   'Slightly behind',  'Slightly weaker at locking in repeat behaviour'),
    (-0.25, -0.10, 'lower',   'Weaker',           'Less effective at building a loyal repeating customer base — you retain better'),
    (-1.00, -0.25, 'lower',   'Far weaker',       'Significantly weaker at generating repeat visits — strong advantage for you here'),
])

add_rules('fitness_for_social_dwell', [
    ( 0.25,  1.00, 'higher',  'Far stronger',    'Creates a noticeably stronger social atmosphere — customers linger, groups stay longer'),
    ( 0.10,  0.25, 'higher',  'Stronger',         'Better at encouraging group dwell time and social energy'),
    ( 0.05,  0.10, 'higher',  'Slightly ahead',   'Marginally more socially engaging environment'),
    (-0.05,  0.05, 'neutral', 'Equal',            'Roughly the same social energy as your venue'),
    (-0.10, -0.05, 'lower',   'Slightly behind',  'Slightly less socially engaging than your venue'),
    (-0.25, -0.10, 'lower',   'Weaker',           'Less effective at creating a social dwell environment — your space does this better'),
    (-1.00, -0.25, 'lower',   'Far weaker',       'Significantly less social atmosphere — customers visit and leave faster there'),
])

add_rules('fitness_for_group_energy', [
    ( 0.25,  1.00, 'higher',  'Far stronger',    'Much better suited for large groups, events, and high-energy occasions'),
    ( 0.10,  0.25, 'higher',  'Stronger',         'Better at energising groups — more suited for celebrations and outings'),
    ( 0.05,  0.10, 'higher',  'Slightly ahead',   'Marginally stronger for group visits and high-energy moments'),
    (-0.05,  0.05, 'neutral', 'Equal',            'Similar group energy appeal to your venue'),
    (-0.10, -0.05, 'lower',   'Slightly behind',  'Slightly less suited for large group outings'),
    (-0.25, -0.10, 'lower',   'Weaker',           'Less suited for group experiences — your venue does groups better'),
    (-1.00, -0.25, 'lower',   'Far weaker',       'Significantly weaker for group energy — they draw solo or pair visits more than groups'),
])

add_rules('fitness_for_destination_visit', [
    ( 0.25,  1.00, 'higher',  'Far stronger',    'A much stronger destination — people plan trips specifically to go there'),
    ( 0.10,  0.25, 'higher',  'Stronger',         'More of a destination venue — customers travel further and visit with purpose'),
    ( 0.05,  0.10, 'higher',  'Slightly ahead',   'Marginally stronger destination pull than your venue'),
    (-0.05,  0.05, 'neutral', 'Equal',            'Similar destination appeal to your venue'),
    (-0.10, -0.05, 'lower',   'Slightly behind',  'Slightly less of a destination draw than yours'),
    (-0.25, -0.10, 'lower',   'Weaker',           'Less of a destination — customers discover it by proximity, not by reputation'),
    (-1.00, -0.25, 'lower',   'Far weaker',       'Significantly less destination appeal — you have a clear edge in drawing intentional visits'),
])

add_rules('operational_quality', [
    ( 0.25,  1.00, 'higher',  'Far stronger',    'Runs noticeably smoother — faster service, better consistency, fewer complaints'),
    ( 0.10,  0.25, 'higher',  'Stronger',         'Better overall operational execution — service, speed, and consistency'),
    ( 0.05,  0.10, 'higher',  'Slightly ahead',   'Marginally sharper day-to-day operations'),
    (-0.05,  0.05, 'neutral', 'Equal',            'Similar operational quality to your venue'),
    (-0.10, -0.05, 'lower',   'Slightly behind',  'Slightly weaker on service consistency'),
    (-0.25, -0.10, 'lower',   'Weaker',           'Weaker operational execution — your service and consistency score better'),
    (-1.00, -0.25, 'lower',   'Far weaker',       'Noticeably weaker operations — clear service quality advantage for your venue'),
])

add_rules('retention_strength', [
    ( 0.25,  1.00, 'higher',  'Far stronger',    'Much stronger at keeping customers — they build loyalty faster'),
    ( 0.10,  0.25, 'higher',  'Stronger',         'Better customer retention signals — their regulars stick around longer'),
    ( 0.05,  0.10, 'higher',  'Slightly ahead',   'Marginally better at retaining customers over time'),
    (-0.05,  0.05, 'neutral', 'Equal',            'Similar retention strength to your venue'),
    (-0.10, -0.05, 'lower',   'Slightly behind',  'Slightly weaker at retaining customers long-term'),
    (-0.25, -0.10, 'lower',   'Weaker',           'Weaker retention — customers drift away faster there than at your venue'),
    (-1.00, -0.25, 'lower',   'Far weaker',       'Significantly weaker at retaining customers — your loyalty signals are stronger'),
])

add_rules('monetization_potential', [
    ( 0.25,  1.00, 'higher',  'Far stronger',    'Much higher revenue potential — customers spend more and upsell better'),
    ( 0.10,  0.25, 'higher',  'Stronger',         'Better positioned to monetise their customer base'),
    ( 0.05,  0.10, 'higher',  'Slightly ahead',   'Marginally stronger monetisation signals'),
    (-0.05,  0.05, 'neutral', 'Equal',            'Similar monetisation potential to your venue'),
    (-0.10, -0.05, 'lower',   'Slightly behind',  'Slightly lower revenue signals per customer'),
    (-0.25, -0.10, 'lower',   'Weaker',           'Lower monetisation potential — your customers spend and upsell better'),
    (-1.00, -0.25, 'lower',   'Far weaker',       'Significantly lower revenue potential — clear monetisation advantage for your venue'),
])


# ─── SQL ─────────────────────────────────────────────────────────────────────

CREATE_RULES_TABLE = """
CREATE TABLE IF NOT EXISTS fitness_delta_rules (
    id               SERIAL PRIMARY KEY,
    dimension        VARCHAR(60) NOT NULL,
    delta_min        FLOAT NOT NULL,
    delta_max        FLOAT NOT NULL,
    direction        VARCHAR(10) NOT NULL,   -- 'higher' | 'lower' | 'neutral'
    short_label      VARCHAR(30) NOT NULL,
    client_statement TEXT NOT NULL,
    created_at       TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
CREATE INDEX IF NOT EXISTS idx_fdr_dim_range
    ON fitness_delta_rules(dimension, delta_min, delta_max);
"""

INSERT_RULES_SQL = """
    INSERT INTO fitness_delta_rules
        (dimension, delta_min, delta_max, direction, short_label, client_statement)
    VALUES %s
    ON CONFLICT DO NOTHING;
"""

CREATE_DELTAS_TABLE = """
CREATE TABLE IF NOT EXISTS venue_similarity_deltas (
    id               SERIAL PRIMARY KEY,
    venue_id         INTEGER NOT NULL REFERENCES venues(id) ON DELETE CASCADE,
    similar_venue_id INTEGER NOT NULL REFERENCES venues(id) ON DELETE CASCADE,
    similarity_rank  INTEGER,
    dimension        VARCHAR(60) NOT NULL,
    delta            FLOAT NOT NULL,
    UNIQUE(venue_id, similar_venue_id, dimension)
);
CREATE INDEX IF NOT EXISTS idx_vsd_venue_dim
    ON venue_similarity_deltas(venue_id, dimension);
CREATE INDEX IF NOT EXISTS idx_vsd_venue_rank
    ON venue_similarity_deltas(venue_id, similarity_rank, dimension);
"""

INSERT_DELTAS_SQL = """
    INSERT INTO venue_similarity_deltas
        (venue_id, similar_venue_id, similarity_rank, dimension, delta)
    VALUES %s
    ON CONFLICT (venue_id, similar_venue_id, dimension) DO UPDATE SET
        delta           = EXCLUDED.delta,
        similarity_rank = EXCLUDED.similarity_rank;
"""

BATCH_SIZE = 1000


# ─── Operations ──────────────────────────────────────────────────────────────

def load_delta_rules(cursor) -> int:
    rows = [
        (r['dimension'], r['delta_min'], r['delta_max'],
         r['direction'], r['short_label'], r['client_statement'])
        for r in DELTA_RULES
    ]
    psycopg2.extras.execute_values(cursor, INSERT_RULES_SQL, rows)
    return len(rows)


def compute_similarity_deltas(cursor) -> int:
    """
    For every (venue_id, similar_venue_id) pair in venue_similarity,
    compute delta = similar.score − venue.score for all 8 fitness dimensions.
    Processes in batches to avoid loading 1.17M rows into memory at once.
    """
    # Load all fitness profiles into memory (6,007 venues × 8 cols = small)
    dim_cols = ', '.join(FITNESS_DIMS)
    cursor.execute(f"SELECT venue_id, {dim_cols} FROM venue_fitness_dimensions")
    fitness_map = {}
    for row in cursor.fetchall():
        fitness_map[row[0]] = dict(zip(FITNESS_DIMS, row[1:]))
    print(f"  Loaded fitness profiles for {len(fitness_map):,} venues into memory")

    # Load all similarity pairs with rank
    cursor.execute("SELECT venue_id, similar_venue_id, rank FROM venue_similarity ORDER BY venue_id, rank")
    pairs = cursor.fetchall()
    print(f"  Processing {len(pairs):,} similarity pairs × {len(FITNESS_DIMS)} dimensions...")

    insert_rows = []
    skipped     = 0
    total       = 0

    for venue_id, similar_id, rank in pairs:
        a = fitness_map.get(venue_id)
        b = fitness_map.get(similar_id)
        if not a or not b:
            skipped += 1
            continue
        for dim in FITNESS_DIMS:
            delta = round(float(b.get(dim) or 0.0) - float(a.get(dim) or 0.0), 4)
            insert_rows.append((venue_id, similar_id, rank, dim, delta))

        # Flush batch
        if len(insert_rows) >= BATCH_SIZE * len(FITNESS_DIMS):
            psycopg2.extras.execute_values(cursor, INSERT_DELTAS_SQL, insert_rows)
            total += len(insert_rows)
            insert_rows = []

    # Flush remaining
    if insert_rows:
        psycopg2.extras.execute_values(cursor, INSERT_DELTAS_SQL, insert_rows)
        total += len(insert_rows)

    if skipped:
        print(f"  [WARN] Skipped {skipped:,} pairs (missing fitness data)")

    return total


# ─── Main ─────────────────────────────────────────────────────────────────────

def main():
    print("\n013_compute_fitness_deltas.py -- Delta rules + pre-computed similarity deltas\n")

    conn   = psycopg2.connect(**DB_CONFIG)
    cursor = conn.cursor()

    try:
        print("  [1/3] Creating tables...")
        cursor.execute(CREATE_RULES_TABLE)
        cursor.execute(CREATE_DELTAS_TABLE)
        print("  fitness_delta_rules + venue_similarity_deltas ready")

        print("\n  [2/3] Loading delta interpretation rules...")
        n_rules = load_delta_rules(cursor)
        print(f"  {n_rules} rules loaded ({len(FITNESS_DIMS)} dimensions × 7 bands)")

        print("\n  [3/3] Pre-computing fitness deltas for all similarity pairs...")
        n_deltas = compute_similarity_deltas(cursor)

        conn.commit()

        print("\n  [4/4] Running ANALYZE on delta tables...")
        cursor.execute("ANALYZE venue_similarity_deltas")
        cursor.execute("ANALYZE fitness_delta_rules")
        cursor.execute("ANALYZE venue_similarity")
        conn.commit()
        print("  ANALYZE complete — query planner stats refreshed")

        print("\n" + "=" * 55)
        print("  COMPLETE")
        print(f"  Delta rules loaded         : {n_rules}")
        print(f"  Similarity delta rows      : {n_deltas:,}")
        print(f"  Pairs covered              : {n_deltas // len(FITNESS_DIMS):,}")
        print("=" * 55 + "\n")

    except Exception as e:
        conn.rollback()
        print(f"\n[ERROR] {e}")
        raise
    finally:
        cursor.close()
        conn.close()


if __name__ == '__main__':
    main()
