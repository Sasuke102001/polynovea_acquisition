"""
compute_similarity_manual.py
Computes venue similarity for a manually added venue using cosine similarity
across the 5 fitness dimensions. Populates venue_similarity and venue_vectors
so the Competitors and Transform tabs work correctly.

Usage:
    python compute_similarity_manual.py --venue-id 12066

How it works:
    1. Reads the target venue's blended fitness vector
    2. Reads all other venues' blended fitness vectors from venue_fitness_dimensions
    3. Computes cosine similarity between target and every other venue
    4. Inserts top 25 most similar into venue_similarity (source='manual_reviews')
    5. Inserts the target's vector into venue_vectors
"""

import argparse
import json
import math
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

# The 5 dimensions used for the fitness vector
DIMS = [
    'fitness_for_office_lunch',
    'fitness_for_repeat_habit',
    'fitness_for_social_dwell',
    'fitness_for_group_energy',
    'fitness_for_destination_visit',
]

TOP_N = 25


def cosine_similarity(a: list[float], b: list[float]) -> float:
    dot   = sum(x * y for x, y in zip(a, b))
    mag_a = math.sqrt(sum(x * x for x in a))
    mag_b = math.sqrt(sum(x * x for x in b))
    if mag_a == 0 or mag_b == 0:
        return 0.0
    return dot / (mag_a * mag_b)


def run(venue_id: int):
    conn = psycopg2.connect(**DB_CONFIG)
    cur  = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)

    # ── Step 1: Fetch target venue's blended fitness vector ─────────────────
    cur.execute(
        f"""
        SELECT {', '.join(DIMS)}
        FROM venue_fitness_dimensions
        WHERE venue_id = %s
        ORDER BY CASE source WHEN 'blended' THEN 0 WHEN 'manual_reviews' THEN 1 ELSE 2 END
        LIMIT 1
        """,
        (venue_id,)
    )
    target_row = cur.fetchone()
    if not target_row:
        print(f"ERROR: No fitness data found for venue_id={venue_id}")
        sys.exit(1)

    target_vec = [float(target_row[d] or 0.0) for d in DIMS]
    print(f"Target venue_id={venue_id} fitness vector: {[round(v, 3) for v in target_vec]}")

    # ── Step 2: Fetch all other venues' blended fitness vectors ─────────────
    cur.execute(
        f"""
        SELECT DISTINCT ON (venue_id)
            venue_id,
            {', '.join(DIMS)}
        FROM venue_fitness_dimensions
        WHERE venue_id != %s
        ORDER BY venue_id,
                 CASE source WHEN 'blended' THEN 0 WHEN 'google' THEN 1 ELSE 2 END
        """,
        (venue_id,)
    )
    all_rows = cur.fetchall()
    print(f"Computing similarity against {len(all_rows)} venues...")

    # ── Step 3: Compute cosine similarity ────────────────────────────────────
    scored = []
    for row in all_rows:
        vec   = [float(row[d] or 0.0) for d in DIMS]
        score = cosine_similarity(target_vec, vec)
        scored.append((row['venue_id'], round(score, 6)))

    # Sort descending, take top N
    scored.sort(key=lambda x: x[1], reverse=True)
    top = scored[:TOP_N]

    print(f"Top {TOP_N} similar venues (sample): {top[:5]}")

    # ── Step 4: Insert into venue_similarity ─────────────────────────────────
    sim_rows = [
        (venue_id, 'manual_reviews', sim_venue_id, score, json.dumps([]), 0)
        for sim_venue_id, score in top
    ]
    psycopg2.extras.execute_values(
        cur,
        """
        INSERT INTO venue_similarity
            (venue_id, source, similar_venue_id, similarity_score, shared_primitives, shared_primitive_count)
        VALUES %s
        ON CONFLICT (venue_id, source, similar_venue_id) DO UPDATE SET
            similarity_score = EXCLUDED.similarity_score
        """,
        sim_rows,
    )
    print(f"Inserted {len(sim_rows)} similarity rows into venue_similarity")

    # ── Step 5: Insert into venue_vectors ────────────────────────────────────
    cur.execute(
        """
        INSERT INTO venue_vectors (venue_id, source, fitness_vector, vector_source)
        VALUES (%s, %s, %s, %s)
        ON CONFLICT (venue_id, source) DO UPDATE SET
            fitness_vector = EXCLUDED.fitness_vector,
            vector_source  = EXCLUDED.vector_source,
            last_computed  = CURRENT_TIMESTAMP
        """,
        (venue_id, 'manual_reviews', target_vec, 'manual_review_analysis')
    )
    print("Inserted venue vector into venue_vectors")

    conn.commit()
    cur.close()
    conn.close()

    print(f"\nDone. Competitors tab for venue_id={venue_id} should now show results.")


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description="Compute similarity for a manually added venue")
    parser.add_argument('--venue-id', type=int, required=True, help="venue_id of the manual venue")
    args = parser.parse_args()
    run(args.venue_id)
