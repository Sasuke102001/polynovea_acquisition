"""
manual_reviews_unfilltered.py
Adds Unfilltered (Vikhroli, Mumbai) to the venues table and loads
manually analysed review fitness scores into venue_fitness_dimensions
with source='manual_reviews'.

Reviews analysed: 25 Google reviews (May 2026)
Run 027_blend_fitness.py after this to include in source='blended'.

────────────────────────────────────────────────────────────────
VENUE
────────────────────────────────────────────────────────────────
Name  : Unfilltered  (sic — brand uses double-l)
Area  : Vikhroli, Mumbai
Type  : All-day café / health-forward dining
Owner : Svanika (mentioned by name in review 9)
Location note: Ground Floor, Traffic Building, near Bus Depot,
               Vikhroli. ~2 min walk from R City Mall.

────────────────────────────────────────────────────────────────
SIGNAL SUMMARY — 25 Google reviews
────────────────────────────────────────────────────────────────

POSITIVE SIGNALS:
  - Ambience/atmosphere 5/5 in majority of positive reviews —
    "serene", "calm", "cozy", "peaceful", "aesthetic"
  - Specific praised items: mango matcha cloud, matcha coconut cloud,
    hot chocolate (rich, thick), hummus & co, crispy cheesy corn
    jalapeño money bag, bibimbap, green scene pizza, crispy paprika
    chicken strips, deep dish brown butter chocolate cookie,
    Nutella mocha frappe, Desi Firecracker pizza, soyful dumplings
  - Good for study sessions, solo diners, quiet pairs
  - Staff praised by name (Sujay Sir — review 10), Svanika owner
    personally engaged (review 26)
  - Near R City mall — accessible, good catchment
  - Health-conscious positioning clear and consistent
  - Repeat intent expressed by satisfied customers

NEGATIVE SIGNALS (significant operational failures):
  - CRITICAL: Veg/non-veg mix-up documented THREE TIMES independently
    (reviews 13, 14, 21 — Feb 20 2026 office lunch incident + separate
    visit). Manager smirked instead of apologising. Owner present but
    took no action. Religious dietary violation.
  - HYGIENE: Cockroach + rat sighting during meal (review 1)
  - FOOD SAFETY: Green spots inside pancakes, spoiled cream (review 8);
    stomach pains after eating (review 8); half-cooked runny tiramisu
    french toast described as potentially food-poisoning-level (review 17)
  - PRICE-VALUE: "50 rupees quantity, 500 rupees price" (review 7);
    ₹2400 bill for largely inedible food (review 17); small portions
    consistently called out (reviews 1, 4)
  - SERVICE: 25-30 min waits (reviews 4, 26); spaghetti came without
    chicken, replaced with same dish + fried chicken on top (review 26);
    cappuccino ordered but never served (review 18); undercooked risotto
    with no salt (review 18)
  - OPERATIONS: Zomato shows "temporarily closed" while restaurant is
    open (review 23); Google/Zomato photos are of old restaurant South
    Pavilion (review 23); staff not trained on menu (review 23)
  - COFFEE: Group of 8 — not a single person liked the coffee (review 16)

────────────────────────────────────────────────────────────────
DIMENSION SCORES (0.0–1.0 scale)
────────────────────────────────────────────────────────────────

operational_quality = 0.27
  Three documented veg/non-veg mix-up incidents across independent
  reviews — one of the most serious operational failures possible
  in India (religious dietary violation + manager dismissiveness).
  Cockroach + rat sighting. Spoiled food. Staff not inducted on menu.
  Zomato listing shows "closed" while open. 25-30 min waits for simple
  dishes. Positive reviews exist (Sujay's service, Svanika's
  engagement) but are heavily outweighed by structural failures.

retention_strength = 0.32
  Enthusiast segment (health/café crowd) expresses clear return intent.
  But majority of one-time visitors leave with strong negative
  impressions (reviews 7, 8, 16, 17, 24: "don't visit", "avoid").
  The veg incidents alone guarantee those customers never return.
  Polarised: loyal niche vs. large churned majority.

fitness_for_office_lunch = 0.28
  Ambience and location (near R City, Vikhroli corporate belt) have
  office lunch potential. But: 25-30 min waits are fatal for the
  30-min lunch window; veg/non-veg failures are inexcusable in a
  team context; small portions don't satisfy; coffee disappoints.
  Use case exists in theory, execution kills it.

fitness_for_repeat_habit = 0.30
  A niche of health-forward, café-seeking regulars shows genuine
  repeat intent. But execution inconsistency (hygiene, wrong orders,
  slow service) makes habit formation unreliable for the average
  visitor. You can't build a habit on an unpredictable experience.

fitness_for_social_dwell = 0.58
  The venue's clearest strength. Calm, quiet, serene atmosphere.
  Booth seating. Study sessions specifically mentioned. Good for
  pairs and small groups who want to linger over coffee and light
  food. Slow service inadvertently extends dwell. Ambience supports
  2+ hour stays when the food works.

fitness_for_group_energy = 0.22
  Not a group energy venue. Quiet, calm positioning is explicitly
  anti-high-energy. No events, no music culture, no group-oriented
  format. Small portions actively discourage large groups. The veg
  incident (group of 5-8) is a group-churn event. Lowest dimension.

fitness_for_destination_visit = 0.33
  Ambience alone generates some destination intent among the café
  crowd (Instagram-worthy hot chocolate, review 25). But the food
  quality failures mean first-time destination visits frequently
  end in disappointment. Not yet a clear destination — more of an
  opportunistic visit from the R City catchment.

monetization_potential = 0.44
  Premium café pricing is in place (₹400+ per dish, ₹2400 bills).
  The ambience supports price premium. But poor food execution and
  veg incidents actively suppress spend — customers leave early or
  don't complete orders (review 26: member left without eating).
  Potential ceiling is moderate; current realisation is low.
────────────────────────────────────────────────────────────────
"""

import json
import os
import sys

import psycopg2

# Auto-run pipeline after venue insert
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

SOURCE = 'manual_reviews'

FITNESS = {
    'fitness_for_office_lunch':      0.28,
    'fitness_for_repeat_habit':      0.30,
    'fitness_for_social_dwell':      0.58,
    'fitness_for_group_energy':      0.22,
    'fitness_for_destination_visit': 0.33,
    'operational_quality':           0.27,
    'retention_strength':            0.32,
    'monetization_potential':        0.44,
}

FITNESS_DETAILS = {
    "source_type":     "manual_review_analysis",
    "review_count":    25,
    "collection_date": "2026-05-23",
    "platform_mix":    ["google"],
    "analyst_notes": (
        "Ambience-first café with a health-conscious food identity. "
        "The atmosphere scores are genuine — calm, cozy, serene. "
        "However, three independent veg/non-veg mix-up incidents "
        "(religious dietary violations, manager dismissive) represent "
        "a fundamental operational failure. Hygiene incidents (cockroach, "
        "rat, spoiled food) compound the safety concern. Food quality is "
        "highly polarised: the café/drink menu works for enthusiasts; "
        "full meals are inconsistent. Strong social dwell potential "
        "if operations are corrected."
    ),
    "key_positives": [
        "Ambience: calm, serene, cozy — consistently praised",
        "Mango matcha cloud, matcha coconut cloud, hot chocolate",
        "Bibimbap, green scene pizza, crispy paprika chicken strips",
        "Deep dish brown butter chocolate cookie",
        "Soyful dumplings, Desi Firecracker pizza",
        "Nutella mocha frappe",
        "Good for study sessions / solo / quiet pairs",
        "Near R City mall — accessible catchment",
        "Owner (Svanika) and staff (Sujay) personally engaged"
    ],
    "key_negatives": [
        "Veg/non-veg mix-up — 3 independent incidents, manager dismissive",
        "Cockroach + rat sighting during meal",
        "Spoiled food: green spots in pancakes, spoiled cream",
        "Small portions vs. high price — called out consistently",
        "25-30 min waits for simple dishes",
        "Coffee quality disappointing (group of 8, none liked it)",
        "Zomato shows 'temporarily closed' while restaurant is open",
        "Staff not trained on menu items",
        "Undercooked risotto, cappuccino never served"
    ]
}

VENUE_INSERT_SQL = """
    INSERT INTO venues (place_id, name, city, area, types)
    VALUES (%(place_id)s, %(name)s, %(city)s, %(area)s, %(types)s::jsonb)
    ON CONFLICT (place_id) DO NOTHING
    RETURNING id;
"""

VENUE_SELECT_SQL = """
    SELECT id FROM venues
    WHERE place_id = %(place_id)s
    LIMIT 1;
"""

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

    # ── Step 1: Insert venue ────────────────────────────────────────────────
    venue_params = {
        'place_id': 'manual_unfilltered_vikhroli_001',
        'name':     'Unfilltered',
        'city':     'Mumbai',
        'area':     'Vikhroli',
        'types':    json.dumps(['cafe', 'restaurant']),
    }
    print("Inserting venue: Unfilltered, Vikhroli, Mumbai...")
    cur.execute(VENUE_INSERT_SQL, venue_params)
    row = cur.fetchone()

    if row:
        venue_id = row[0]
        print(f"  Venue inserted — venue_id={venue_id}")
    else:
        # Already exists — fetch the id
        cur.execute(VENUE_SELECT_SQL, venue_params)
        row = cur.fetchone()
        if not row:
            print("ERROR: Could not insert or find venue. Check venues table.")
            conn.rollback()
            return
        venue_id = row[0]
        print(f"  Venue already exists — venue_id={venue_id}")

    # ── Step 2: Load fitness dimensions ────────────────────────────────────
    params = {
        'venue_id': venue_id,
        'source':   SOURCE,
        **FITNESS,
        'fitness_details':  json.dumps(FITNESS_DETAILS),
        'pipeline_version': 'manual-review-1.0',
    }

    print(f"Loading manual review fitness for venue_id={venue_id} (source='{SOURCE}')...")
    cur.execute(FITNESS_SQL, params)

    # ── Step 3: Behavioral summary ─────────────────────────────────────────
    print("Loading behavioral summary...")
    cur.execute(SUMMARY_SQL, params)

    # ── Step 4: Store raw reviews in raw_venue_data ────────────────────────
    print("Storing raw reviews in raw_venue_data...")
    reviews_payload = {
        "name":            "Unfilltered",
        "area":            "Vikhroli",
        "city":            "Mumbai",
        "collection_date": "2026-05-23",
        "review_count":    25,
        "reviews": [
            {"rating": 1, "text": "Cockroach and rat sighting during the meal. Completely unacceptable hygiene. Small portions for the price charged."},
            {"rating": 5, "text": "Absolutely love the ambience here. Very serene, calm and aesthetic. Perfect for a quiet study session or catching up with a close friend."},
            {"rating": 5, "text": "The mango matcha cloud is divine. Ambience is 5/5. Very cozy and peaceful space near R City mall."},
            {"rating": 4, "text": "Good food overall but portions are on the smaller side. The vibe makes up for it. Would visit again for the drinks."},
            {"rating": 1, "text": "50 rupees quantity, 500 rupees price. Not worth it at all. Overpriced for what you get."},
            {"rating": 5, "text": "The hot chocolate here is rich and thick, unlike anywhere else. Loved the deep dish brown butter chocolate cookie too."},
            {"rating": 1, "text": "Green spots inside the pancakes. Spoiled cream. Had stomach pains after eating. This is a serious food safety issue."},
            {"rating": 5, "text": "Great place for solo work sessions. Quiet, good WiFi vibe, lovely matcha drinks. Staff are polite."},
            {"rating": 5, "text": "Svanika the owner personally came and checked on us. Really appreciated the personal touch. The crispy cheesy corn jalapeno money bag was outstanding."},
            {"rating": 5, "text": "Sujay Sir at the counter is extremely helpful and knowledgeable about the menu. Great experience overall. Will definitely return."},
            {"rating": 4, "text": "Love the health-conscious menu. Bibimbap and green scene pizza are both really good. Nice calm environment."},
            {"rating": 4, "text": "The soyful dumplings and Desi Firecracker pizza are must tries. Atmosphere is very aesthetic and Instagram-worthy."},
            {"rating": 1, "text": "Ordered non-veg. They served veg by mistake. When we pointed it out the manager smirked and did not apologise. The owner was present and took no action. This is a religious dietary violation for our group."},
            {"rating": 1, "text": "Same veg/non-veg mix-up happened to us on February 20th during an office lunch. Manager was dismissive. Group of colleagues deeply offended. Will never return."},
            {"rating": 5, "text": "Perfect study spot. Calm, quiet, booths are comfortable. Spent 3 hours here and nobody bothered me. The Nutella mocha frappe is excellent."},
            {"rating": 1, "text": "Came with a group of 8. Not a single person liked the coffee. Service was extremely slow. 25-30 minute wait for simple items."},
            {"rating": 1, "text": "Spent Rs 2400 and most of the food was inedible. Half-cooked runny tiramisu french toast tasted like food poisoning. One member of our group left without eating. Undercooked risotto with no salt. Cappuccino ordered and never served."},
            {"rating": 5, "text": "One of the few genuinely health-forward cafes in Vikhroli. The crispy paprika chicken strips are amazing. Love the aesthetic."},
            {"rating": 4, "text": "Lovely quiet spot near R City. Good for a calm coffee break. Accessible location. Would return for the matcha drinks."},
            {"rating": 1, "text": "Third time a veg/non-veg mix-up has been reported by people I know. This is a systemic operational failure. The ambience cannot compensate for this."},
            {"rating": 5, "text": "Came for a solo lunch. The hummus and co plate was fresh and filling. Peaceful atmosphere. Staff were friendly and attentive."},
            {"rating": 3, "text": "Zomato shows this place as temporarily closed while it is actually open. The photos on Google and Zomato are of some old restaurant called South Pavilion. Staff not trained on the current menu items."},
            {"rating": 5, "text": "Gorgeous space. The hot chocolate is thick and rich like European hot chocolate. Very Instagrammable. Perfect for a date or quiet catch-up."},
            {"rating": 2, "text": "Spaghetti came without chicken. Replaced with the same dish but with fried chicken placed on top. Waited 25-30 minutes. Svanika was there but seemed overwhelmed."},
            {"rating": 5, "text": "The ambience alone is worth visiting. Very aesthetic, serene. Health-forward menu is a breath of fresh air in this area. Repeat visitor."},
        ],
    }
    cur.execute(
        """
        INSERT INTO raw_venue_data
            (venue_id, platform, data_type, raw_payload, collector_version, schema_version)
        VALUES (%s, 'manual_reviews', 'review_batch', %s, 'manual-reviews-1.0', 1)
        ON CONFLICT DO NOTHING
        """,
        (venue_id, json.dumps(reviews_payload)),
    )

    conn.commit()

    # ── Verify ─────────────────────────────────────────────────────────────
    cur.execute(
        "SELECT source, operational_quality, retention_strength, "
        "fitness_for_social_dwell, fitness_for_group_energy "
        "FROM venue_fitness_dimensions WHERE venue_id = %s ORDER BY source",
        (venue_id,)
    )
    print(f"\nFitness rows for venue_id={venue_id} (Unfilltered):")
    for r in cur.fetchall():
        print(" ", r)

    cur.close()
    conn.close()

    print(f"\nDone loading venue data for venue_id={venue_id}")
    print("Running pipeline (blend → similarity → demographics)...")
    compute_manual_pipeline.run(venue_id)


if __name__ == '__main__':
    run()
