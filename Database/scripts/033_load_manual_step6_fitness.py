"""
033_load_manual_step6_fitness.py
Loads BIF pipeline output for manually added venues into:
  - venue_fitness_dimensions  (source='manual_reviews')
  - intervention_triggers     (source='manual_reviews')

Run AFTER:
  1. format_manual_for_pipeline.py
  2. BIF steps 3–6 --city manual
Run BEFORE:
  3. 027_blend_fitness.py
"""

import json
import os
import sys
from pathlib import Path

import psycopg2

sys.stdout.reconfigure(encoding='utf-8')

STEP6_PATH = Path(
    r"D:\PolyNovea\Module 2\Magic Pin and Zomato\Magic Pin\pipelines"
    r"\Behavioural_Intelligence_Framework\Data\manual\step_6_output.json"
)

SOURCE           = "manual_reviews"
PIPELINE_VERSION = "manual-bif-1.0"

DB_CONFIG = {
    'host':     os.getenv('PG_HOST',     'polynovea-module2.cxeo8066g8t2.ap-south-1.rds.amazonaws.com'),
    'port':     int(os.getenv('PG_PORT', 5432)),
    'dbname':   os.getenv('PG_DB',       'polynovea_module2'),
    'user':     os.getenv('PG_USER',     'polynovea_admin'),
    'password': os.getenv('PG_PASSWORD', '07586277012Luna'),
    'sslmode':  'require',
}

FITNESS_SQL = """
    INSERT INTO venue_fitness_dimensions
        (venue_id, source,
         fitness_for_office_lunch, fitness_for_repeat_habit,
         fitness_for_social_dwell, fitness_for_group_energy,
         fitness_for_destination_visit,
         operational_quality, retention_strength, monetization_potential,
         fitness_details, pipeline_version, schema_version)
    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, 1)
    ON CONFLICT (venue_id, source) DO UPDATE SET
        fitness_for_office_lunch      = EXCLUDED.fitness_for_office_lunch,
        fitness_for_repeat_habit      = EXCLUDED.fitness_for_repeat_habit,
        fitness_for_social_dwell      = EXCLUDED.fitness_for_social_dwell,
        fitness_for_group_energy      = EXCLUDED.fitness_for_group_energy,
        fitness_for_destination_visit = EXCLUDED.fitness_for_destination_visit,
        operational_quality           = EXCLUDED.operational_quality,
        retention_strength            = EXCLUDED.retention_strength,
        monetization_potential        = EXCLUDED.monetization_potential,
        fitness_details               = EXCLUDED.fitness_details,
        pipeline_version              = EXCLUDED.pipeline_version,
        computed_at                   = NOW();
"""

INTERVENTION_SQL = """
    INSERT INTO intervention_triggers
        (venue_id, source, intervention_type, description, fit_score,
         priority_tier, recommended, matched_signals, missing_signals,
         matched_signal_count)
    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
    ON CONFLICT (venue_id, source, intervention_type) DO UPDATE SET
        description          = EXCLUDED.description,
        fit_score            = EXCLUDED.fit_score,
        priority_tier        = EXCLUDED.priority_tier,
        recommended          = EXCLUDED.recommended,
        matched_signals      = EXCLUDED.matched_signals,
        missing_signals      = EXCLUDED.missing_signals,
        matched_signal_count = EXCLUDED.matched_signal_count;
"""


def fd_score(fd, key):
    return float(fd.get(key, {}).get("score", 0.0))


def fd_details(fd):
    dims = (
        "fitness_for_office_lunch", "fitness_for_repeat_habit",
        "fitness_for_social_dwell", "fitness_for_group_energy",
        "fitness_for_destination_visit",
    )
    return json.dumps({
        d: {
            "match_ratio":      fd.get(d, {}).get("match_ratio", 0.0),
            "confidence_basis": fd.get(d, {}).get("confidence_basis", 0.0),
            "matched_signals":  fd.get(d, {}).get("matched_signals", []),
            "strength_tier":    fd.get(d, {}).get("strength_tier", ""),
        }
        for d in dims
    })


def main():
    print(f"\n033_load_manual_step6_fitness.py — source='{SOURCE}'\n")

    if not STEP6_PATH.exists():
        print(f"[ERROR] Not found: {STEP6_PATH}")
        print("Run BIF steps 3–6 --city manual first.")
        sys.exit(1)

    with open(STEP6_PATH, "r", encoding="utf-8") as f:
        data = json.load(f)

    venues = data.get("venues", [])
    print(f"  Venues in step_6_output: {len(venues)}")

    conn   = psycopg2.connect(**DB_CONFIG)
    cursor = conn.cursor()

    try:
        cursor.execute("SELECT place_id, id FROM venues WHERE place_id IS NOT NULL")
        lookup = {row[0]: row[1] for row in cursor.fetchall()}
        print(f"  DB lookup: {len(lookup):,} venues\n")

        loaded = skipped = interventions = 0

        for v in venues:
            place_id = v.get("place_id")
            venue_id = lookup.get(place_id)
            if not venue_id:
                print(f"  SKIP (place_id not in DB): {place_id} — {v.get('venue')}")
                skipped += 1
                continue

            fd = v.get("fitness_dimensions", {})
            bs = v.get("behavioral_summary", {})

            cursor.execute(FITNESS_SQL, (
                venue_id, SOURCE,
                fd_score(fd, "fitness_for_office_lunch"),
                fd_score(fd, "fitness_for_repeat_habit"),
                fd_score(fd, "fitness_for_social_dwell"),
                fd_score(fd, "fitness_for_group_energy"),
                fd_score(fd, "fitness_for_destination_visit"),
                float(bs.get("operational_quality",    0.0)),
                float(bs.get("retention_strength",     0.0)),
                float(bs.get("monetization_potential", 0.0)),
                fd_details(fd),
                PIPELINE_VERSION,
            ))

            for lev in v.get("operational_leverage", []):
                cursor.execute(INTERVENTION_SQL, (
                    venue_id, SOURCE,
                    lev.get("intervention", ""),
                    lev.get("operational_lever", ""),
                    float(lev.get("fit_score", 0.0)),
                    lev.get("priority_tier", "EXPLORE"),
                    bool(lev.get("recommended", False)),
                    json.dumps(lev.get("matched_signals", [])),
                    json.dumps(lev.get("missing_signals", [])),
                    str(lev.get("matched_signal_count", "")),
                ))
                interventions += 1

            loaded += 1
            print(f"  Loaded: {v.get('venue')} (venue_id={venue_id})")

        conn.commit()
        print(f"\n{'='*50}")
        print(f"  Venues loaded  : {loaded}")
        print(f"  Interventions  : {interventions}")
        if skipped:
            print(f"  Skipped        : {skipped}")
        print(f"{'='*50}")
        print("\nNext: python 027_blend_fitness.py")

    except Exception as e:
        conn.rollback()
        raise e
    finally:
        cursor.close()
        conn.close()


if __name__ == "__main__":
    main()
