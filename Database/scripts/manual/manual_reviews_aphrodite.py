"""
030_load_manual_reviews_aphrodite.py
Loads manually curated review signals for Aphrodite Bar & Cafe (venue_id=223)
into venue_fitness_dimensions with source='manual_reviews'.

Reviews analyzed: 28 reviews from Google/aggregators (May 2026)
Run blend (027) after this to include in source='blended'.

────────────────────────────────────────────────────────────────
SCORING RATIONALE — Aphrodite Bar & Cafe, CBD Belapur, Navi Mumbai
────────────────────────────────────────────────────────────────

POSITIVE SIGNALS (reviews 17–28):
  - Ambiance/vibe praised consistently ("great vibe", "aesthetically designed")
  - Two floors: ground-floor restaurant + first-floor lounge — physical asset
  - Friday/Saturday live singer events — group energy driver
  - Specific dishes repeatedly praised: Paneer Bhurji Cigar, biryani, soya tandoori chaap
  - Espresso martini + cocktails (Head Banger) specifically called out
  - Some staff interactions described as polite, humble, non-pushy
  - Weekday 40% discount — draws office/daytime crowd
  - People pre-book (EasyDinner, Dine Out), showing destination intent

NEGATIVE SIGNALS (reviews 1–16):
  - Menu availability is a chronic, severe problem (Indian/Chinese/Japanese all unavailable on
    separate visits) — the single biggest operational failure
  - Staff attitude deeply inconsistent (reception described as rude + arrogant in multiple reviews)
  - Staple pin found in food (hygiene/safety breach)
  - Events attract 16–19 year old crowd openly consuming alcohol, fighting — no crowd control
  - Service speed failures: 25 min wait for water, 50 min for fries
  - Price-value gap perceived as high: ₹5009 for incomplete meal, ₹5000/head NYE not disclosed
  - Food execution inconsistent: frozen paratha, chilli powder on plain fries
  - No valet

DIMENSION SCORES (0.0–1.0 scale):

operational_quality = 0.34
  Severe inconsistency. Menu unavailability on multiple visits + rude reception staff + food
  safety incident (staple pin) drag this down significantly. Positive staff reviews exist but
  are outweighed. Core operations unreliable.

retention_strength = 0.30
  Most critical/mid-range reviews explicitly say "will not return" / "not recommended".
  A minority say "will go again" (review 27) or "highly recommend" (review 18). The
  polarisation itself signals poor retention — only enthusiasts return, majority one-and-done.

fitness_for_office_lunch = 0.32
  Review 2 confirms an explicit office lunch booking with colleagues — use case exists.
  Weekday 40% off (review 18) attracts daytime. But: menu unavailability, slow service,
  loud music, and price-value mismatch all undermine office-lunch repeatability.

fitness_for_repeat_habit = 0.28
  Low. Few reviewers signal repeat intent. The inconsistency in food and service makes
  habit formation difficult — you can't rely on the experience being the same each visit.

fitness_for_social_dwell = 0.56
  Moderate-high. Lounge area, events, vibe, non-pushy staff (review 27) all support
  longer dwell. People arrive in groups and stay for drinks + multiple courses when
  service works. Espresso martini / cocktail culture present.

fitness_for_group_energy = 0.62
  The venue naturally attracts high-energy group occasions despite management issues.
  Events (Friday/Saturday), college crowd, pre-booked group tables, two-floor format,
  shooter/cocktail culture all drive group energy. Highest-scoring dimension.

fitness_for_destination_visit = 0.42
  People explicitly come from afar and pre-book (review 5: "came a long way").
  Booking via apps (EasyDinner, Dine Out) signals destination intent. But majority of
  first-time destination visits end in disappointment — destination pull without conversion.

monetization_potential = 0.54
  Strong events monetisation capability: ₹5000/head NYE cover charges, live music events,
  lounge premium positioning, premium cocktail menu. Weekday discount model operational.
  Price point is high; ability to charge is present even if value delivery is inconsistent.
────────────────────────────────────────────────────────────────
"""

import json
import os
import sys
import psycopg2

sys.path.insert(0, os.path.dirname(__file__))
import compute_manual_pipeline

sys.stdout.reconfigure(encoding='utf-8')

DB_CONFIG = {
    'host':     os.getenv('PG_HOST',     'polynovea-module2.cxeo8066g8t2.ap-south-1.rds.amazonaws.com'),
    'port':     int(os.getenv('PG_PORT', 5432)),
    'dbname':   os.getenv('PG_DB',       'polynovea_module2'),
    'user':     os.getenv('PG_USER',     'polynovea_admin'),
    'password': os.getenv('PG_PASSWORD', 'REDACTED_DB_PASSWORD'),
    'sslmode':  'require',
}

VENUE_ID = 223   # Aphrodite Bar & Cafe — CBD Belapur, Navi Mumbai
SOURCE   = 'manual_reviews'

FITNESS = {
    'fitness_for_office_lunch':      0.32,
    'fitness_for_repeat_habit':      0.28,
    'fitness_for_social_dwell':      0.56,
    'fitness_for_group_energy':      0.62,
    'fitness_for_destination_visit': 0.42,
    'operational_quality':           0.34,
    'retention_strength':            0.30,
    'monetization_potential':        0.54,
}

FITNESS_DETAILS = {
    "source_type":       "manual_review_analysis",
    "review_count":      28,
    "collection_date":   "2026-05-18",
    "platform_mix":      ["google", "zomato", "dineout", "easydinner"],
    "analyst_notes":     (
        "High variance venue. Group energy and social dwell are genuine strengths "
        "anchored in the lounge format, live events, and cocktail culture. "
        "Operational inconsistency (menu availability, staff attitude) suppresses "
        "office lunch and retention scores. Monetisation ceiling is high — "
        "events and cover charges demonstrate premium positioning capability."
    ),
    "key_positives": [
        "Two-floor format with dedicated lounge",
        "Friday/Saturday live music events",
        "Paneer Bhurji Cigar, biryani, soya chaap — consistently praised dishes",
        "Cocktail culture: espresso martini, Head Banger, shooters",
        "Non-pushy staff in multiple reviews",
        "Weekday 40% off — daytime pull"
    ],
    "key_negatives": [
        "Chronic menu unavailability (multiple separate visits)",
        "Rude reception staff (multiple independent reviews)",
        "Staple pin found in food",
        "Underage crowd at events, no crowd control",
        "Price-value mismatch perceived across majority of reviews",
        "Service speed failures"
    ]
}

FITNESS_SQL = """
    INSERT INTO venue_fitness_dimensions
        (venue_id, source,
         fitness_for_office_lunch, fitness_for_repeat_habit,
         fitness_for_social_dwell, fitness_for_group_energy,
         fitness_for_destination_visit,
         operational_quality, retention_strength, monetization_potential,
         fitness_details, pipeline_version, schema_version)
    VALUES (%(venue_id)s, %(source)s,
            %(fitness_for_office_lunch)s, %(fitness_for_repeat_habit)s,
            %(fitness_for_social_dwell)s, %(fitness_for_group_energy)s,
            %(fitness_for_destination_visit)s,
            %(operational_quality)s, %(retention_strength)s, %(monetization_potential)s,
            %(fitness_details)s, %(pipeline_version)s, 1)
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

SUMMARY_SQL = """
    INSERT INTO behavioral_summary
        (venue_id, source, operational_quality, retention_strength, monetization_potential)
    VALUES (%(venue_id)s, %(source)s, %(operational_quality)s, %(retention_strength)s, %(monetization_potential)s)
    ON CONFLICT (venue_id, source) DO UPDATE SET
        operational_quality    = EXCLUDED.operational_quality,
        retention_strength     = EXCLUDED.retention_strength,
        monetization_potential = EXCLUDED.monetization_potential;
"""


def run():
    conn = psycopg2.connect(**DB_CONFIG)
    cur  = conn.cursor()

    params = {
        'venue_id': VENUE_ID,
        'source':   SOURCE,
        **FITNESS,
        'fitness_details':   json.dumps(FITNESS_DETAILS),
        'pipeline_version':  'manual-review-1.0',
    }

    print(f"Loading manual review fitness for venue_id={VENUE_ID} (source='{SOURCE}')...")
    cur.execute(FITNESS_SQL, params)

    print("Loading behavioral summary...")
    cur.execute(SUMMARY_SQL, params)

    conn.commit()
    print(f"Done loading venue data for venue_id={VENUE_ID}")
    print("Running pipeline (blend → similarity → demographics)...")
    compute_manual_pipeline.run(VENUE_ID)

    # Verify
    cur.execute(
        "SELECT source, operational_quality, retention_strength, fitness_for_group_energy, "
        "fitness_for_social_dwell, fitness_for_destination_visit FROM venue_fitness_dimensions "
        "WHERE venue_id = %s ORDER BY source",
        (VENUE_ID,)
    )
    print("\nAll fitness rows for venue 223:")
    for row in cur.fetchall():
        print(" ", row)

    cur.close()
    conn.close()


if __name__ == '__main__':
    run()
