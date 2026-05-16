"""
008_load_surveys.py
Loads form_v1_responses.csv + form_v2_responses.csv into:
  - survey_responses_canonical  (one row per respondent)
  - user_archetypes             (one archetype per respondent, derived)
Run after 001_init_schema.sql (independent of venue loaders)
"""

import csv
import json
import os
import sys
import psycopg2
import psycopg2.extras

sys.stdout.reconfigure(encoding='utf-8')

SURVEY_PATH = os.path.join(os.path.dirname(__file__), '..', 'data', 'raw', 'surveys')
V1_FILE     = os.path.join(SURVEY_PATH, 'form_v1_responses.csv')
V2_FILE     = os.path.join(SURVEY_PATH, 'form_v2_responses.csv')

DB_CONFIG = {
    'host':     os.getenv('PG_HOST',     'your-db-instance.xxxxxxxxxxxx.ap-south-1.rds.amazonaws.com'),
    'port':     int(os.getenv('PG_PORT', 5432)),
    'dbname':   os.getenv('PG_DB',       'polynovea_module2'),
    'user':     os.getenv('PG_USER',     'your_user'),
    'password': os.getenv('PG_PASSWORD', 'your_password'),
    'sslmode':  'require',
}

SURVEY_SQL = """
    INSERT INTO survey_responses_canonical
        (response_id, form_version, age_group, city, company_size,
         visit_frequency, energy_preference, place_preference, social_personality,
         fomo_tendency, discovery_tendency, group_influence,
         email, newsletter_consent, raw_responses)
    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
    ON CONFLICT (response_id) DO UPDATE SET
        form_version        = EXCLUDED.form_version,
        age_group           = EXCLUDED.age_group,
        city                = EXCLUDED.city,
        company_size        = EXCLUDED.company_size,
        visit_frequency     = EXCLUDED.visit_frequency,
        energy_preference   = EXCLUDED.energy_preference,
        place_preference    = EXCLUDED.place_preference,
        social_personality  = EXCLUDED.social_personality,
        fomo_tendency       = EXCLUDED.fomo_tendency,
        discovery_tendency  = EXCLUDED.discovery_tendency,
        group_influence     = EXCLUDED.group_influence,
        email               = EXCLUDED.email,
        newsletter_consent  = EXCLUDED.newsletter_consent,
        raw_responses       = EXCLUDED.raw_responses;
"""

ARCHETYPE_SQL = """
    INSERT INTO user_archetypes
        (response_id, archetype_name, confidence_score, primary_traits, secondary_traits)
    VALUES (%s, %s, %s, %s, %s)
    ON CONFLICT DO NOTHING;
"""

# ---------------------------------------------------------------------------
# Normalisation helpers
# ---------------------------------------------------------------------------

_CITY_MAP = {
    'vashi':           'navi-mumbai',
    'navi mumbai':     'navi-mumbai',
    'navi-mumbai':     'navi-mumbai',
    'cbd belapur':     'navi-mumbai',
    'nerul':           'navi-mumbai',
    'kharghar':        'navi-mumbai',
    'panvel':          'navi-mumbai',
    'airoli':          'navi-mumbai',
    'thane':           'thane',
    'thane west':      'thane',
    'thane east':      'thane',
    'mulund':          'thane',
    'sobo':            'mumbai-sobo',
    'south mumbai':    'mumbai-sobo',
    'south-mumbai':    'mumbai-sobo',
    'lower parel':     'mumbai-sobo',
    'worli':           'mumbai-sobo',
    'bandra':          'mumbai-sobo',
    'juhu':            'mumbai-sobo',
    'andheri':         'mumbai-main',
    'powai':           'mumbai-main',
    'goregaon':        'mumbai-main',
    'malad':           'mumbai-main',
    'borivali':        'mumbai-main',
    'kandivali':       'mumbai-main',
    'dahisar':         'mumbai-main',
    'kurla':           'mumbai-main',
    'ghatkopar':       'mumbai-main',
    'chembur':         'mumbai-main',
    'mumbai':          'mumbai-main',   # generic fallback
}


def normalize_city(raw: str) -> str:
    raw = (raw or '').strip().lower()
    for key, slug in _CITY_MAP.items():
        if key in raw:
            return slug
    return raw or 'unknown'


def normalize_company(raw: str) -> str:
    raw = (raw or '').lower()
    if 'alone' in raw or 'solo' in raw:
        return 'solo'
    if 'partner' in raw or '1' in raw:
        return 'duo'
    if '2' in raw or '3' in raw or '4' in raw or 'small' in raw:
        return 'small_group'
    if '5' in raw or 'large' in raw or 'gang' in raw or 'team' in raw:
        return 'large_group'
    return 'mixed'


def normalize_energy(raw: str) -> str:
    raw = (raw or '').lower()
    if 'high' in raw or 'exciting' in raw:
        return 'high_energy'
    if 'calm' in raw or 'comfortable' in raw or 'quiet' in raw:
        return 'calm'
    return 'balanced'


def normalize_social(raw: str) -> str:
    raw = (raw or '').lower()
    if 'new' in raw or 'trying' in raw or 'explorer' in raw or 'discover' in raw:
        return 'explorer'
    if 'familiar' in raw or 'stick' in raw or 'prefer' in raw:
        return 'loyalist'
    return 'balanced'


def normalize_scale(raw: str) -> float:
    """'A lot' → 0.9, 'Somewhat' → 0.5, 'Very little' / 'Not much' → 0.2"""
    raw = (raw or '').lower()
    if 'a lot' in raw or 'very much' in raw:
        return 0.9
    if 'somewhat' in raw or 'some' in raw or 'moderate' in raw:
        return 0.5
    if 'little' in raw or 'not much' in raw or 'barely' in raw:
        return 0.2
    return 0.5


# ---------------------------------------------------------------------------
# Archetype derivation
# ---------------------------------------------------------------------------

_ARCHETYPE_MATRIX = {
    ('explorer', 'high_energy'): ('Trend Hunter',    0.90),
    ('explorer', 'balanced'):    ('Scene Seeker',     0.82),
    ('explorer', 'calm'):        ('Quiet Discoverer', 0.78),
    ('balanced', 'high_energy'): ('Social Butterfly', 0.80),
    ('balanced', 'balanced'):    ('Lifestyle Regular',0.75),
    ('balanced', 'calm'):        ('Comfort Dweller',  0.72),
    ('loyalist', 'high_energy'): ('Power Regular',    0.80),
    ('loyalist', 'balanced'):    ('Trusted Regular',  0.78),
    ('loyalist', 'calm'):        ('Habit Former',     0.85),
}


def derive_archetype(social: str, energy: str, fomo: float) -> tuple:
    social = social or 'balanced'
    energy = energy or 'balanced'
    name, base_conf = _ARCHETYPE_MATRIX.get(
        (social, energy), ('Lifestyle Regular', 0.70)
    )
    # Adjust confidence slightly by fomo signal availability
    confidence = round(base_conf * (0.95 if fomo is None else 1.0), 3)
    primary_traits = {
        'social_personality': social,
        'energy_preference':  energy,
    }
    secondary_traits = {
        'fomo_tendency': fomo,
    }
    return name, confidence, primary_traits, secondary_traits


# ---------------------------------------------------------------------------
# V1 loader
# ---------------------------------------------------------------------------

def load_v1(cursor) -> dict:
    loaded = 0
    skipped = 0

    with open(V1_FILE, 'r', encoding='utf-8-sig') as f:
        reader = csv.reader(f)
        headers = next(reader)  # consume header row

        for i, row in enumerate(reader):
            if len(row) < 18:
                skipped += 1
                continue

            # Last column (index 18) is the response_id
            response_id = row[18].strip() if len(row) > 18 else f'v1_row_{i}'
            if not response_id:
                response_id = f'v1_row_{i}'

            raw_dict = dict(zip(headers, row))

            age_group       = row[1].strip()
            city            = normalize_city(row[2])
            frequency       = row[3].strip()
            company         = normalize_company(row[6])
            energy          = normalize_energy(row[13])
            crowd_raw       = row[11].strip()
            email           = row[17].strip() if len(row) > 17 else ''

            group_influence = normalize_scale(crowd_raw)
            social          = 'balanced'  # v1 has no direct social_personality question
            discovery       = 0.5

            cursor.execute(SURVEY_SQL, (
                response_id, 'v1',
                age_group, city, company,
                frequency, energy, None, social,
                None, discovery, group_influence,
                email or None, False,
                json.dumps(raw_dict),
            ))

            arch_name, arch_conf, primary, secondary = derive_archetype(social, energy, None)
            cursor.execute(ARCHETYPE_SQL, (
                response_id, arch_name, arch_conf,
                json.dumps(primary), json.dumps(secondary),
            ))
            loaded += 1

    return {'version': 'v1', 'loaded': loaded, 'skipped': skipped}


# ---------------------------------------------------------------------------
# V2 loader
# ---------------------------------------------------------------------------

def load_v2(cursor) -> dict:
    loaded = 0
    skipped = 0

    with open(V2_FILE, 'r', encoding='utf-8-sig') as f:
        reader = csv.DictReader(f)

        for i, row in enumerate(reader):
            response_id = (row.get('Submission ID') or '').strip()
            if not response_id:
                skipped += 1
                continue

            age_group  = (row.get('Age Group') or '').strip()
            city       = normalize_city(row.get('City / Area') or '')
            frequency  = (row.get('How often do you go out in a month?') or '').strip()
            company    = normalize_company(row.get('Who do you usually go with?') or '')
            energy_raw = row.get('Which do you usually prefer?') or ''
            social_raw = row.get('Which feels more like you?') or ''
            fomo_raw   = row.get('How much do reviews / recommendations affect your decision?') or ''
            crowd_raw  = row.get('How much does the crowd at a place affect your decision?') or ''
            email      = (row.get('Email ID') or '').strip()
            newsletter_raw = (row.get('Would you like to join our Newsletter?') or '').strip()

            energy          = normalize_energy(energy_raw)
            social          = normalize_social(social_raw)
            fomo            = normalize_scale(fomo_raw)
            group_influence = normalize_scale(crowd_raw)
            newsletter      = newsletter_raw.lower() in ('yes', 'true', '1')

            discovery = {
                'explorer': 0.85,
                'balanced': 0.50,
                'loyalist': 0.20,
            }.get(social, 0.50)

            cursor.execute(SURVEY_SQL, (
                response_id, 'v2',
                age_group, city, company,
                frequency, energy, None, social,
                fomo, discovery, group_influence,
                email or None, newsletter,
                json.dumps(dict(row)),
            ))

            arch_name, arch_conf, primary, secondary = derive_archetype(social, energy, fomo)
            cursor.execute(ARCHETYPE_SQL, (
                response_id, arch_name, arch_conf,
                json.dumps(primary), json.dumps(secondary),
            ))
            loaded += 1

    return {'version': 'v2', 'loaded': loaded, 'skipped': skipped}


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main():
    print("\n008_load_surveys.py -- Loading survey responses & user archetypes\n")

    conn   = psycopg2.connect(**DB_CONFIG)
    cursor = conn.cursor()

    results = []
    try:
        print("  Loading form_v1_responses.csv ...")
        r1 = load_v1(cursor)
        results.append(r1)
        print(f"  Loaded : {r1['loaded']}  |  Skipped : {r1['skipped']}")

        print("\n  Loading form_v2_responses.csv ...")
        r2 = load_v2(cursor)
        results.append(r2)
        print(f"  Loaded : {r2['loaded']}  |  Skipped : {r2['skipped']}")

        conn.commit()
        total = sum(r['loaded'] for r in results)
        print("\n" + "="*55)
        print("  COMPLETE")
        print(f"  Total responses loaded : {total}")
        print(f"  Archetypes computed    : {total}")
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

