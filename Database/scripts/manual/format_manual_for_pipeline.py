"""
format_manual_for_pipeline.py
Reads manual reviews from raw_venue_data and writes reviews_grouped.json
so the BIF pipeline (steps 3–6) can consume them under --city manual.

Usage:
    python format_manual_for_pipeline.py               # all manual-review venues
    python format_manual_for_pipeline.py --venue-id 12066

Output:
    D:\\PolyNovea\\Module 2\\...\\Output_upper\\manual\\reviews_grouped.json

After running this, execute:
    cd .../Scripts_upper
    python step_3_extract.py --city manual
    python step_4_pattern.py --city manual
    python step_4b_governance_validate.py --city manual
    python step_5_score.py --city manual
    python step_5b_similarity.py --city manual
    python step_6_output.py --city manual
Then run 033_load_manual_step6_fitness.py and 027_blend_fitness.py.
"""

import argparse
import json
import os
import sys
from pathlib import Path

import psycopg2
import psycopg2.extras

sys.stdout.reconfigure(encoding='utf-8')

DB_CONFIG = {
    'host':     os.getenv('PG_HOST',     'polynovea-module2.cxeo8066g8t2.ap-south-1.rds.amazonaws.com'),
    'port':     int(os.getenv('PG_PORT', 5432)),
    'dbname':   os.getenv('PG_DB',       'polynovea_module2'),
    'user':     os.getenv('PG_USER',     'polynovea_admin'),
    'password': os.getenv('PG_PASSWORD', '07586277012Luna'),
    'sslmode':  'require',
}

OUTPUT_DIR = Path(
    r"D:\PolyNovea\Module 2\Magic Pin and Zomato\Magic Pin\pipelines\Output_upper\manual"
)


def run(venue_id: int | None = None):
    conn = psycopg2.connect(**DB_CONFIG)
    cur  = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)

    try:
        if venue_id:
            cur.execute(
                "SELECT id, name, place_id, area, city, types FROM venues WHERE id = %s",
                (venue_id,),
            )
        else:
            cur.execute(
                """
                SELECT DISTINCT v.id, v.name, v.place_id, v.area, v.city, v.types
                FROM   venues v
                JOIN   raw_venue_data rvd ON rvd.venue_id = v.id
                WHERE  rvd.platform = 'manual_reviews'
                  AND  rvd.data_type = 'review_batch'
                ORDER  BY v.id
                """
            )
        venues = cur.fetchall()

        if not venues:
            print("No venues with manual_reviews found in raw_venue_data.")
            return

        print(f"Exporting {len(venues)} venue(s) for BIF pipeline...")

        output = []
        for v in venues:
            cur.execute(
                """
                SELECT raw_payload FROM raw_venue_data
                WHERE  venue_id   = %s
                  AND  platform   = 'manual_reviews'
                  AND  data_type  = 'review_batch'
                ORDER  BY collected_at DESC
                LIMIT  1
                """,
                (v["id"],),
            )
            row = cur.fetchone()
            if not row:
                print(f"  SKIP {v['name']} — no review_batch found")
                continue

            payload = row["raw_payload"]
            if isinstance(payload, str):
                payload = json.loads(payload)

            reviews_raw = payload.get("reviews", [])
            reviews = [
                {
                    "text":            r.get("text", ""),
                    "rating":          r.get("rating", 3),
                    "review_age_days": r.get("review_age_days", 30),
                    "source":          "manual_reviews",
                    "author_name":     r.get("author_name", "anonymous"),
                }
                for r in reviews_raw
                if r.get("text", "").strip()
            ]

            output.append({
                "name":     v["name"],
                "place_id": v["place_id"] or f"manual_{v['id']}",
                "area":     v["area"] or "",
                "city":     v["city"] or "",
                "types":    list(v["types"] or []),
                "reviews":  reviews,
            })
            print(f"  {v['name']} (venue_id={v['id']}) — {len(reviews)} reviews")

    finally:
        cur.close()
        conn.close()

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    out_file = OUTPUT_DIR / "reviews_grouped.json"
    with open(out_file, "w", encoding="utf-8") as f:
        json.dump(output, f, indent=2, ensure_ascii=False)

    print(f"\nWrote {len(output)} venue(s) → {out_file}")
    print("\nNext steps:")
    print("  cd 'D:\\PolyNovea\\Module 2\\...\\Scripts_upper'")
    print("  python step_3_extract.py --city manual")
    print("  python step_4_pattern.py --city manual")
    print("  python step_4b_governance_validate.py --city manual")
    print("  python step_5_score.py --city manual")
    print("  python step_5b_similarity.py --city manual")
    print("  python step_6_output.py --city manual")
    print("  python 033_load_manual_step6_fitness.py")
    print("  python 027_blend_fitness.py")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Format manual reviews for BIF pipeline")
    parser.add_argument("--venue-id", type=int, default=None,
                        help="Export a single venue (omit for all manual venues)")
    args = parser.parse_args()
    run(args.venue_id)
