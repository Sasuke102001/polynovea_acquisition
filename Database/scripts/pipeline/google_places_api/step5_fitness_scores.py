"""
004_load_scores.py
Loads step_5_behavioral_scores.json for all 4 cities into:
  - venue_fitness_dimensions  (5 fitness scores per venue)
  - behavioral_summary        (3 quality scores per venue)
Joins on venues.name_normalized + city.
Run after 002_load_venues.py
"""

import json
import os
import sys
import psycopg2
import psycopg2.extras

sys.stdout.reconfigure(encoding='utf-8')

BASE_PATH  = os.path.join(os.path.dirname(__file__), '..', '..', '..', 'data', 'raw', 'google_places')
CITIES     = ['navi-mumbai', 'mumbai-sobo', 'mumbai-main', 'thane']
BATCH_SIZE = 500

CITY_LABEL = {
    'mumbai-main': 'Mumbai',
    'mumbai-sobo': 'Mumbai',
    'navi-mumbai':  'Navi Mumbai',
    'thane':        'Thane',
}

DB_CONFIG = {
    'host':     os.getenv('PG_HOST',     'your-db-instance.xxxxxxxxxxxx.ap-south-1.rds.amazonaws.com'),
    'port':     int(os.getenv('PG_PORT', 5432)),
    'dbname':   os.getenv('PG_DB',       'polynovea_module2'),
    'user':     os.getenv('PG_USER',     'your_user'),
    'password': os.getenv('PG_PASSWORD', 'your_password'),
    'sslmode':  'require',
}

FITNESS_SQL = """
    INSERT INTO venue_fitness_dimensions
        (venue_id, source, fitness_for_office_lunch, fitness_for_repeat_habit,
         fitness_for_social_dwell, fitness_for_group_energy, fitness_for_destination_visit,
         operational_quality, retention_strength, monetization_potential,
         fitness_details)
    SELECT v.id, 'google', %s, %s, %s, %s, %s, %s, %s, %s, %s
    FROM venues v
    WHERE v.name_normalized = LOWER(TRIM(%s)) AND v.city = %s
    ON CONFLICT (venue_id, source) DO UPDATE SET
        fitness_for_office_lunch      = EXCLUDED.fitness_for_office_lunch,
        fitness_for_repeat_habit      = EXCLUDED.fitness_for_repeat_habit,
        fitness_for_social_dwell      = EXCLUDED.fitness_for_social_dwell,
        fitness_for_group_energy      = EXCLUDED.fitness_for_group_energy,
        fitness_for_destination_visit = EXCLUDED.fitness_for_destination_visit,
        operational_quality           = EXCLUDED.operational_quality,
        retention_strength            = EXCLUDED.retention_strength,
        monetization_potential        = EXCLUDED.monetization_potential,
        fitness_details               = EXCLUDED.fitness_details;
"""

INTERVENTION_SQL = """
    INSERT INTO intervention_triggers
        (venue_id, source, intervention_type, description, fit_score, priority_tier,
         recommended, tier_description, matched_signals, missing_signals,
         matched_signal_count, match_ratio, confidence_basis)
    SELECT v.id, 'google', %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s
    FROM venues v
    WHERE v.name_normalized = LOWER(TRIM(%s)) AND v.city = %s
    ON CONFLICT (venue_id, source, intervention_type) DO UPDATE SET
        description          = EXCLUDED.description,
        fit_score            = EXCLUDED.fit_score,
        priority_tier        = EXCLUDED.priority_tier,
        recommended          = EXCLUDED.recommended,
        tier_description     = EXCLUDED.tier_description,
        matched_signals      = EXCLUDED.matched_signals,
        missing_signals      = EXCLUDED.missing_signals,
        matched_signal_count = EXCLUDED.matched_signal_count,
        match_ratio          = EXCLUDED.match_ratio,
        confidence_basis     = EXCLUDED.confidence_basis;
"""

SUMMARY_SQL = """
    INSERT INTO behavioral_summary
        (venue_id, source, operational_quality, retention_strength, monetization_potential)
    SELECT v.id, 'google', %s, %s, %s
    FROM venues v
    WHERE v.name_normalized = LOWER(TRIM(%s)) AND v.city = %s
    ON CONFLICT (venue_id, source) DO UPDATE SET
        operational_quality    = EXCLUDED.operational_quality,
        retention_strength     = EXCLUDED.retention_strength,
        monetization_potential = EXCLUDED.monetization_potential;
"""


def get_fitness(fd: dict, key: str) -> float:
    return fd.get(key, {}).get('score', 0.0)


def build_fitness_details(fd: dict) -> dict:
    """Extract match_ratio, confidence_basis, matched_signals per dimension."""
    details = {}
    for dim in ('fitness_for_office_lunch', 'fitness_for_repeat_habit',
                'fitness_for_social_dwell', 'fitness_for_group_energy',
                'fitness_for_destination_visit'):
        dim_data = fd.get(dim, {})
        details[dim] = {
            'match_ratio':      dim_data.get('match_ratio', 0.0),
            'confidence_basis': dim_data.get('confidence_basis', 0.0),
            'matched_signals':  dim_data.get('matched_signals', []),
        }
    return details


def load_city(cursor, city: str) -> dict:
    path = os.path.join(BASE_PATH, city, 'step_5_behavioral_scores.json')

    with open(path, 'r', encoding='utf-8') as f:
        data = json.load(f)

    venues           = data.get('venue_scores', [])
    city_label       = CITY_LABEL[city]
    loaded           = 0
    missed           = 0
    interventions_in = 0

    for i, venue in enumerate(venues):
        name = venue.get('venue_name', '')
        fd   = venue.get('fitness_dimensions', {})
        bs   = venue.get('behavioral_summary', {})

        ol = get_fitness(fd, 'fitness_for_office_lunch')
        rh = get_fitness(fd, 'fitness_for_repeat_habit')
        sd = get_fitness(fd, 'fitness_for_social_dwell')
        ge = get_fitness(fd, 'fitness_for_group_energy')
        dv = get_fitness(fd, 'fitness_for_destination_visit')
        oq = bs.get('operational_quality', 0.0)
        rs = bs.get('retention_strength', 0.0)
        mp = bs.get('monetization_potential', 0.0)
        details = json.dumps(build_fitness_details(fd))

        cursor.execute(FITNESS_SQL, (ol, rh, sd, ge, dv, oq, rs, mp, details, name, city_label))
        cursor.execute(SUMMARY_SQL, (oq, rs, mp, name, city_label))

        if cursor.rowcount > 0:
            loaded += 1
        else:
            missed += 1

        # Load intervention_opportunities per venue
        for opp in venue.get('intervention_opportunities', []):
            cursor.execute(INTERVENTION_SQL, (
                opp.get('intervention', ''),
                opp.get('description', ''),
                opp.get('fit_score', 0.0),
                opp.get('priority_tier', ''),
                bool(opp.get('recommended', False)),
                opp.get('tier_description', ''),
                json.dumps(opp.get('matched_signals', [])),
                json.dumps(opp.get('missing_signals', [])),
                str(opp.get('matched_signal_count', '')),
                opp.get('match_ratio', 0.0),
                opp.get('confidence_basis', 0.0),
                name, city_label,
            ))
            if cursor.rowcount > 0:
                interventions_in += 1

        if (i + 1) % BATCH_SIZE == 0:
            print(f"  [{city}] {i+1}/{len(venues)} processed...")

    return {
        'city':          city,
        'total':         len(venues),
        'loaded':        loaded,
        'missed':        missed,
        'interventions': interventions_in,
    }


def main():
    print("\n004_load_scores.py -- Loading fitness dimensions & behavioral summary\n")

    conn   = psycopg2.connect(**DB_CONFIG)
    cursor = conn.cursor()

    summary = []
    try:
        for city in CITIES:
            print(f"\n  City: {city}")
            result = load_city(cursor, city)
            summary.append(result)
            print(f"  Loaded        : {result['loaded']}/{result['total']}")
            print(f"  Interventions : {result['interventions']}")
            if result['missed']:
                print(f"  [WARN] Not matched: {result['missed']}")

        conn.commit()
        print("\n" + "="*55)
        print("  COMPLETE")
        print(f"  Total loaded        : {sum(r['loaded'] for r in summary)}")
        print(f"  Total interventions : {sum(r['interventions'] for r in summary)}")
        print(f"  Total missed        : {sum(r['missed'] for r in summary)}")
        print("="*55 + "\n")

    except Exception as e:
        conn.rollback()
        print(f"\n[ERROR] {e}")
        raise
    finally:
        cursor.close()
        conn.close()


if __name__ == '__main__':
    main()

