"""
012_compute_venue_demographics.py

Two operations in one pass:

  1. Adds `rank` column to venue_similarity (ordered by similarity_score DESC per venue_id)
     Enables: paginated carousel browsing

  2. Creates + populates venue_demographic_scores
     Two-layer Bayesian scoring for each venue × 7 segments:

       Layer 1 — Venue-type prior: derived from Google Places type, validated against
                 India F&B research (NRAI, Swiggy/Zomato demographics, SoDF scale).
       Layer 2 — Fitness-dimension evidence: review-signal weights with per-dimension
                 confidence discounts (HIGH=1.0, MED=0.80, LOW=0.60).

       Formula: score = prior × (1 + Σ(evidence_i × weight_i × confidence_discount_i))
       Then normalized across segments per venue.

Run after: 011_load_demographics.py
"""

import os
import sys
import psycopg2
import psycopg2.extras

sys.stdout.reconfigure(encoding='utf-8')

DB_CONFIG = {
    'host':     os.getenv('PG_HOST',     'your-db-instance.xxxxxxxxxxxx.ap-south-1.rds.amazonaws.com'),
    'port':     int(os.getenv('PG_PORT', 5432)),
    'dbname':   os.getenv('PG_DB',       'polynovea_module2'),
    'user':     os.getenv('PG_USER',     'your_user'),
    'password': os.getenv('PG_PASSWORD', 'your_password'),
    'sslmode':  'require',
}

# ─── Dimension name → DB column mapping ──────────────────────────────────────
# Research uses short names; DB uses fitness_for_* prefix for some.
# friction_tolerance: not yet a pipeline output — always 0 until added.
DIM_MAP: dict[str, str | None] = {
    "operational_quality":  "operational_quality",
    "repeat_habit":         "fitness_for_repeat_habit",
    "retention_strength":   "retention_strength",
    "friction_tolerance":   None,                        # pipeline gap — skipped
    "social_dwell":         "fitness_for_social_dwell",
    "destination_visit":    "fitness_for_destination_visit",
    "office_lunch":         "fitness_for_office_lunch",
    "group_energy":         "fitness_for_group_energy",
}

CONFIDENCE_DISCOUNT: dict[str, float] = {"HIGH": 1.0, "MED": 0.80, "LOW": 0.60}

# ─── Segment fitness weights (validated — Kimi research 2026-05-15) ────────────
# Sources: Cialdini social proof, Kahneman System 1, Bitner servicescape,
#          Mehrabian-Russell S-O-R, Mattila emotional bonding, SoDF scale,
#          NRAI 2019/2023, Swiggy/Zomato demographic data.
# Format: {segment_id: {dim_name: (weight, confidence_tag)}}
SEGMENT_FITNESS_WEIGHTS: dict[str, dict[str, tuple[float, str]]] = {
    "solo_diners": {
        "operational_quality":  (0.45, "HIGH"),
        "repeat_habit":         (0.20, "MED"),
        "retention_strength":   (0.15, "MED"),
        "friction_tolerance":   (0.10, "HIGH"),  # skipped — no pipeline value yet
        "social_dwell":         (0.05, "LOW"),   # negative predictor; LOW weight limits damage
        "destination_visit":    (0.05, "LOW"),
    },
    "working_women": {
        "operational_quality":  (0.30, "HIGH"),
        "office_lunch":         (0.25, "HIGH"),
        "retention_strength":   (0.15, "MED"),
        "friction_tolerance":   (0.15, "HIGH"),  # skipped — no pipeline value yet
        "social_dwell":         (0.10, "MED"),
        "destination_visit":    (0.05, "LOW"),
    },
    "couples": {
        "destination_visit":    (0.40, "HIGH"),
        "social_dwell":         (0.20, "HIGH"),
        "operational_quality":  (0.15, "MED"),
        "repeat_habit":         (0.10, "MED"),
        "retention_strength":   (0.10, "MED"),
        "friction_tolerance":   (0.05, "LOW"),   # skipped
    },
    "premium": {
        "destination_visit":    (0.35, "HIGH"),
        "social_dwell":         (0.25, "HIGH"),
        "operational_quality":  (0.20, "HIGH"),
        "retention_strength":   (0.10, "MED"),
        "repeat_habit":         (0.05, "LOW"),
        "friction_tolerance":   (0.05, "LOW"),   # skipped
    },
    "college_kids": {
        "group_energy":         (0.35, "HIGH"),
        "social_dwell":         (0.25, "HIGH"),
        "friction_tolerance":   (0.15, "MED"),   # skipped
        "repeat_habit":         (0.10, "MED"),
        "operational_quality":  (0.10, "MED"),
        "destination_visit":    (0.05, "LOW"),
    },
    "office_workers": {
        "office_lunch":         (0.35, "HIGH"),
        "repeat_habit":         (0.25, "HIGH"),
        "operational_quality":  (0.20, "HIGH"),
        "friction_tolerance":   (0.10, "HIGH"),  # skipped
        "retention_strength":   (0.05, "MED"),
        "social_dwell":         (0.05, "LOW"),   # anti-predictor; LOW weight limits damage
    },
    "families": {
        "repeat_habit":         (0.30, "HIGH"),
        "operational_quality":  (0.25, "HIGH"),
        "retention_strength":   (0.20, "MED"),
        "friction_tolerance":   (0.15, "HIGH"),  # skipped
        "social_dwell":         (0.05, "LOW"),   # anti-predictor
        "destination_visit":    (0.05, "LOW"),
    },
}

ALL_SEGMENTS = list(SEGMENT_FITNESS_WEIGHTS.keys())

# ─── Venue-type segment priors (validated — Kimi research 2026-05-15) ─────────
# Format: {type_key: {segment_id: (prior_weight, confidence, rationale)}}
# Priors sum to ~1.0 per venue type. Applied before fitness evidence.
VENUE_TYPE_SEGMENT_PRIORS: dict[str, dict[str, tuple[float, str, str]]] = {
    "fine_dining_restaurant": {
        "premium":        (0.45, "HIGH", "Veblen effect + status signaling"),
        "couples":        (0.30, "HIGH", "Date night + special occasion"),
        "families":       (0.10, "MED",  "Celebration meals"),
        "office_workers": (0.05, "LOW",  "Business lunch only"),
        "college_kids":   (0.05, "LOW",  "Price mismatch; aspirational"),
        "solo_diners":    (0.03, "LOW",  "Stigmatized in India"),
        "working_women":  (0.02, "LOW",  "Safety + comfort concerns"),
    },
    "fast_food_restaurant": {
        "college_kids":   (0.30, "HIGH", "Price-sensitive + group energy"),
        "office_workers": (0.25, "HIGH", "Speed + convenience"),
        "families":       (0.20, "MED",  "Quick weekend meals"),
        "solo_diners":    (0.15, "MED",  "Low friction + inconspicuousness"),
        "working_women":  (0.05, "LOW",  "Less preferred than healthier options"),
        "couples":        (0.03, "LOW",  "Anti-fit; lacks ambiance"),
        "premium":        (0.02, "LOW",  "Status mismatch"),
    },
    "bar": {
        "college_kids":   (0.30, "HIGH", "Social energy + group dynamics"),
        "couples":        (0.20, "MED",  "Some date nights"),
        "office_workers": (0.15, "MED",  "After-work social"),
        "solo_diners":    (0.10, "MED",  "Bar counter solo normalized"),
        "premium":        (0.10, "MED",  "Cocktail culture + status signaling"),
        "working_women":  (0.08, "LOW",  "Safety concerns in India bar culture"),
        "families":       (0.07, "LOW",  "Structurally anti-fit"),
    },
    "cafe": {
        "college_kids":   (0.25, "HIGH", "Study + hangout; 72% go with friends"),
        "working_women":  (0.20, "HIGH", "Safety + comfort; all-women staff cafes emerging"),
        "solo_diners":    (0.20, "HIGH", "Inconspicuousness + proper service"),
        "office_workers": (0.15, "MED",  "Coffee meetings + quick lunch"),
        "couples":        (0.10, "MED",  "Casual dates"),
        "families":       (0.07, "LOW",  "Possible but less preferred"),
        "premium":        (0.03, "LOW",  "Status mismatch"),
    },
    "night_club": {
        "college_kids":   (0.45, "HIGH", "Peak social energy; 90% Gen Z communal formats"),
        "couples":        (0.20, "MED",  "Some date nights"),
        "premium":        (0.15, "MED",  "Bottle service + status display"),
        "office_workers": (0.10, "LOW",  "After-work Friday; temporal mismatch"),
        "solo_diners":    (0.05, "LOW",  "Socially stigmatized"),
        "working_women":  (0.03, "LOW",  "Safety concerns high"),
        "families":       (0.02, "LOW",  "Structurally anti-fit"),
    },
    "gastropub": {
        "couples":        (0.25, "HIGH", "Casual date + food + drinks"),
        "college_kids":   (0.20, "HIGH", "Social energy + food + drinks"),
        "office_workers": (0.15, "MED",  "After-work social + dinner"),
        "premium":        (0.15, "MED",  "Craft beer + culinary experience"),
        "solo_diners":    (0.10, "MED",  "Bar counter + food = acceptable solo"),
        "families":       (0.08, "LOW",  "Possible early evening"),
        "working_women":  (0.07, "LOW",  "Safety + comfort variable"),
    },
    "lounge_bar": {
        "premium":        (0.35, "HIGH", "Exclusivity + ambiance + status"),
        "couples":        (0.25, "HIGH", "Intimacy + privacy + soft lighting"),
        "office_workers": (0.15, "MED",  "Business entertaining"),
        "college_kids":   (0.10, "MED",  "Aspirational but price-sensitive"),
        "solo_diners":    (0.08, "LOW",  "Lounge = social space"),
        "working_women":  (0.05, "LOW",  "Safety depends on management"),
        "families":       (0.02, "LOW",  "Structurally anti-fit"),
    },
    "cocktail_bar": {
        "premium":        (0.40, "HIGH", "Craft cocktail = cultural capital"),
        "couples":        (0.25, "HIGH", "Date night + sophistication"),
        "office_workers": (0.15, "MED",  "After-work; business entertaining"),
        "college_kids":   (0.10, "MED",  "Aspirational; some penetration"),
        "solo_diners":    (0.05, "LOW",  "Possible but specialized"),
        "working_women":  (0.03, "LOW",  "Safety concerns"),
        "families":       (0.02, "LOW",  "Structurally anti-fit"),
    },
    "family_restaurant": {
        "families":       (0.50, "HIGH", "Explicit positioning; kid-friendly + reliable"),
        "office_workers": (0.15, "MED",  "Lunch thali; value + speed"),
        "couples":        (0.10, "MED",  "Possible but lacks intimacy"),
        "college_kids":   (0.10, "MED",  "Group meals; value for money"),
        "solo_diners":    (0.08, "LOW",  "Family atmosphere = conspicuous"),
        "working_women":  (0.05, "LOW",  "Possible but not optimized"),
        "premium":        (0.02, "LOW",  "Status mismatch"),
    },
    "bistro": {
        "couples":        (0.30, "HIGH", "Casual intimacy + European ambiance"),
        "office_workers": (0.20, "HIGH", "Business lunch + casual meetings"),
        "solo_diners":    (0.15, "MED",  "Counter seating + casual"),
        "college_kids":   (0.12, "MED",  "Aspirational + affordable"),
        "premium":        (0.10, "MED",  "Culinary experience + cultural capital"),
        "families":       (0.08, "LOW",  "Less kid-optimized"),
        "working_women":  (0.05, "LOW",  "Variable safety"),
    },
    "brewpub": {
        "college_kids":   (0.30, "HIGH", "Social energy + craft beer culture"),
        "couples":        (0.20, "MED",  "Casual dates + shared experience"),
        "office_workers": (0.15, "MED",  "After-work social"),
        "premium":        (0.15, "MED",  "Craft = cultural capital"),
        "solo_diners":    (0.10, "MED",  "Bar counter solo normalized"),
        "families":       (0.05, "LOW",  "Daytime possible; alcohol focus anti-fit"),
        "working_women":  (0.05, "LOW",  "Safety variable"),
    },
    "coffee_shop": {
        "office_workers": (0.25, "HIGH", "Coffee meetings + remote work"),
        "solo_diners":    (0.20, "HIGH", "Safe solo space; inconspicuousness"),
        "working_women":  (0.20, "HIGH", "Comfort + safety"),
        "college_kids":   (0.15, "MED",  "Study + hangout"),
        "couples":        (0.10, "MED",  "Casual coffee dates"),
        "families":       (0.07, "LOW",  "Possible but less preferred"),
        "premium":        (0.03, "LOW",  "Accessible, not exclusive"),
    },
    "restaurant": {
        "families":       (0.25, "MED",  "Generic = broad appeal; weekend meals"),
        "couples":        (0.20, "MED",  "Date nights + casual dining"),
        "office_workers": (0.15, "MED",  "Lunch + business meals"),
        "college_kids":   (0.12, "MED",  "Group meals"),
        "solo_diners":    (0.10, "MED",  "Possible but variable"),
        "premium":        (0.10, "MED",  "Some upscale generic restaurants"),
        "working_women":  (0.08, "LOW",  "Variable fit"),
    },
    "sports_bar": {
        "college_kids":   (0.30, "HIGH", "Social energy + group viewing"),
        "office_workers": (0.20, "HIGH", "After-work sports viewing"),
        "couples":        (0.10, "MED",  "Some shared sports interest"),
        "solo_diners":    (0.10, "MED",  "Bar counter solo normalized"),
        "premium":        (0.10, "MED",  "Premium sports bar = status"),
        "families":       (0.10, "LOW",  "Possible daytime; evening anti-fit"),
        "working_women":  (0.10, "LOW",  "Safety + interest variable"),
    },
    "hookah_bar": {
        "college_kids":   (0.40, "HIGH", "Social energy + group ritual"),
        "couples":        (0.15, "MED",  "Some casual dates"),
        "office_workers": (0.15, "MED",  "After-work social"),
        "solo_diners":    (0.10, "LOW",  "Possible but group-oriented"),
        "premium":        (0.10, "LOW",  "Variable positioning"),
        "families":       (0.05, "LOW",  "Anti-fit; health concerns"),
        "working_women":  (0.05, "LOW",  "Safety + health concerns"),
    },
    "bakery": {
        "solo_diners":    (0.25, "HIGH", "Quick + inconspicuous + proper service"),
        "office_workers": (0.20, "HIGH", "Quick snack + coffee"),
        "families":       (0.15, "MED",  "Weekend treats + celebrations"),
        "college_kids":   (0.15, "MED",  "Affordable treats"),
        "working_women":  (0.10, "MED",  "Safe + comfortable"),
        "couples":        (0.10, "LOW",  "Casual but less intimate"),
        "premium":        (0.05, "LOW",  "Accessible, not exclusive"),
    },
    "dessert_shop": {
        "couples":        (0.30, "HIGH", "Date night + shared indulgence"),
        "college_kids":   (0.25, "HIGH", "Social treat + affordable"),
        "families":       (0.15, "MED",  "Weekend treats"),
        "solo_diners":    (0.10, "MED",  "Possible but indulgence = social"),
        "office_workers": (0.10, "MED",  "Quick treat"),
        "working_women":  (0.05, "LOW",  "Possible"),
        "premium":        (0.05, "LOW",  "Accessible"),
    },
    "brunch_restaurant": {
        "couples":        (0.30, "HIGH", "Leisurely date + weekend ritual"),
        "families":       (0.25, "HIGH", "Weekend family ritual"),
        "premium":        (0.15, "MED",  "Brunch = cultural capital"),
        "college_kids":   (0.10, "MED",  "Weekend social"),
        "office_workers": (0.10, "MED",  "Weekend leisure"),
        "working_women":  (0.05, "LOW",  "Possible"),
        "solo_diners":    (0.05, "LOW",  "Possible but social ritual"),
    },
    "buffet_restaurant": {
        "families":       (0.35, "HIGH", "Value + variety + kid-friendly"),
        "office_workers": (0.20, "HIGH", "Lunch buffet = speed + value"),
        "college_kids":   (0.15, "MED",  "Group meals + value"),
        "couples":        (0.10, "MED",  "Some casual dates"),
        "solo_diners":    (0.10, "MED",  "Possible but conspicuous"),
        "premium":        (0.05, "LOW",  "Status mismatch"),
        "working_women":  (0.05, "LOW",  "Possible but not optimized"),
    },
    "bar_and_grill": {
        "couples":        (0.25, "HIGH", "Casual date + food + drinks"),
        "college_kids":   (0.20, "HIGH", "Social energy + food + drinks"),
        "office_workers": (0.15, "MED",  "After-work social + dinner"),
        "families":       (0.12, "MED",  "Early evening possible"),
        "solo_diners":    (0.10, "MED",  "Bar counter acceptable"),
        "premium":        (0.10, "LOW",  "Casual, not exclusive"),
        "working_women":  (0.08, "LOW",  "Variable"),
    },
    # ── Cuisine-type priors (Google Places cuisine tags) ─────────────────────
    # Kimi research 2026-05-15. All 34 types validated against NRAI IFSR 2024,
    # Swiggy/Zomato 2024-2025, Ipsos India 2026, Mordor Intelligence 2026.
    # Venues fall back to the generic 'restaurant' prior when no match is found.
    # Indian-origin cuisine types ─────────────────────────────────────────────
    "indian_restaurant": {
        "families":       (0.28, "HIGH", "Family dining 45% of casual dining revenue; avg group 4.2; generic Indian is the most democratic format"),
        "office_workers": (0.22, "HIGH", "Business people rank #1 customer group in Mumbai surveys; weekday lunch dominant in commercial districts"),
        "college_kids":   (0.15, "MED",  "Cheap thali joints + street-adjacent Indian are group hangout staples near campuses"),
        "couples":        (0.12, "MED",  "Mid-casual Indian serves as budget date-night when continental is too expensive"),
        "solo_diners":    (0.10, "HIGH", "Counter-service Udupi/Maharashtrian places explicitly designed for solo dining — low friction, fast, inconspicuous"),
        "premium":        (0.06, "MED",  "Premium diners avoid generic Indian in favor of chef-driven or regional specialty"),
        "working_women":  (0.07, "MED",  "Well-lit, family-friendly Indian formats are safe for solo women diners, especially Udupi and thali"),
    },
    "north_indian_restaurant": {
        "families":       (0.30, "HIGH", "North Indian is India's most popular cuisine (34% of diners); family-style mid-casual dominates MMR suburbs"),
        "office_workers": (0.18, "HIGH", "Dhaba-style and thali joints dominate weekday lunch in commercial districts"),
        "couples":        (0.16, "MED",  "Mid-casual North Indian (Punjab Grill tier) is standard date-night choice; occasion-driven, weekend evenings"),
        "college_kids":   (0.12, "MED",  "Value dhaba-style North Indian is budget-friendly group food near campuses"),
        "premium":        (0.10, "MED",  "Premium North Indian (Bukhara-style, chef-driven) attracts HNW families and status diners"),
        "solo_diners":    (0.08, "MED",  "Quick thali/counter service attracts solo office workers and commuters; low friction preference"),
        "working_women":  (0.06, "MED",  "Family-style North Indian is safe for women but less so than South Indian/Udupi"),
    },
    "south_indian_restaurant": {
        "office_workers": (0.28, "HIGH", "Breakfast idli-vada + lunch meals anchor office workers in Matunga, Dadar, Chembur; speed + value perfect"),
        "families":       (0.24, "HIGH", "Weekend family breakfast at Udupi chains is a strong Mumbai cultural ritual"),
        "solo_diners":    (0.18, "HIGH", "Counter seating, fast service, low social pressure — most solo-friendly cuisine format in Mumbai"),
        "college_kids":   (0.12, "MED",  "Cheap South Indian near campuses (Vidyavihar, Matunga) is group hangout food; budget-friendly"),
        "working_women":  (0.10, "MED",  "Perceived as clean, well-lit, family-friendly — strong safety signal; Udupi culture explicitly welcoming"),
        "couples":        (0.05, "LOW",  "Underrepresented unless modern South Indian fine dining (Rameshwaram Café tier)"),
        "premium":        (0.03, "LOW",  "Premium South Indian is rare in MMR unless explicitly fine-dining tagged"),
    },
    "vegetarian_restaurant": {
        "families":       (0.32, "HIGH", "Jain/Hindu veg families (92% Jain, 44% Hindu veg) drive core demand; Gujarati/Marwari communities; family thali is anchor"),
        "working_women":  (0.18, "HIGH", "Guaranteed meat-free environment is strong safety/comfort signal; perceived as cleaner and more family-appropriate"),
        "solo_diners":    (0.14, "MED",  "Solo vegetarians (Jain, Hindu religious) seek guaranteed veg environments; counter thali format"),
        "office_workers": (0.12, "MED",  "Vegetarian office workers prefer pure-veg to avoid cross-contamination; especially strong in Jain business communities"),
        "couples":        (0.10, "MED",  "Health-conscious couples (millennial/Gen Z) actively seek vegetarian for lifestyle reasons"),
        "college_kids":   (0.08, "MED",  "Budget vegetarian common near campuses but not as 'cool' as Indo-Chinese or burgers"),
        "premium":        (0.06, "MED",  "Premium vegetarian attracts HNW health-conscious diners; growing but still niche"),
    },
    "vegan_restaurant": {
        "college_kids":   (0.25, "HIGH", "Gen Z drives vegan demand — 65% tried plant-based, 78% health-conscious, 57% influenced by social media"),
        "working_women":  (0.20, "HIGH", "Vegan cafés in Bandra/Khar/Juhu attract women-centric groups; safety + health + community alignment"),
        "couples":        (0.18, "MED",  "Health-conscious couples use vegan as 'conscious dating' — shared values signal; growing millennial trend"),
        "solo_diners":    (0.15, "MED",  "Laptop-friendly vegan cafés with WiFi attract solo remote workers; all-day format, low pressure"),
        "premium":        (0.12, "MED",  "Vegan is often priced at premium due to ingredient costs; attracts affluent health-conscious diners"),
        "families":       (0.06, "LOW",  "Families find vegan too restrictive for multi-generational groups; weak unless family is explicitly vegan"),
        "office_workers": (0.04, "LOW",  "Too expensive and niche for regular office lunch; occasional wellness-driven visit only"),
    },
    # Western cuisine types ───────────────────────────────────────────────────
    "american_restaurant": {
        "college_kids":   (0.28, "MED",  "Sit-down American (wings, ribs, milkshakes) perceived as 'cool' and social-media friendly; group-appropriate"),
        "families":       (0.22, "MED",  "Families with teenage children use American as compromise cuisine — familiar, non-spicy, kid-friendly; mall locations"),
        "couples":        (0.18, "MED",  "Casual date-night in mall locations; American is 'safe' and unchallenging for early-stage dating"),
        "office_workers": (0.14, "MED",  "Occasional team lunch outing; too heavy/slow for regular weekday lunch"),
        "premium":        (0.08, "LOW",  "Standard American casual is not status-signaling unless it is a high-end smokehouse"),
        "solo_diners":    (0.06, "LOW",  "Solo dining possible at mall food courts but not the primary format"),
        "working_women":  (0.04, "LOW",  "Weak — American casual is male-skewed in perception (wings, ribs, beer)"),
    },
    "hamburger_restaurant": {
        "college_kids":   (0.32, "HIGH", "Burger is the quintessential youth QSR format; student pricing, digital campaigns, Hallyu collabs"),
        "office_workers": (0.20, "HIGH", "Quick lunch, delivery-heavy, low friction; standard office-lunch option in BKC/Andheri"),
        "solo_diners":    (0.18, "MED",  "Single-burger combos perfect for solo consumption; counter service, minimal social pressure"),
        "families":       (0.14, "MED",  "Mall-based burger joints attract families with young children; kid-friendly, familiar"),
        "couples":        (0.08, "LOW",  "Not a date-night format unless it is a premium burger bar; most hamburger joints too casual"),
        "premium":        (0.04, "LOW",  "Hamburger is QSR-adjacent — not premium-positioned; premium burger bars rare in MMR"),
        "working_women":  (0.04, "LOW",  "Weak — burger joints perceived as male-skewed, heavy, and less healthy"),
    },
    "italian_restaurant": {
        "couples":        (0.26, "HIGH", "Italian is the default 'safe' date-night cuisine in Mumbai — romantic positioning, wine, familiar menu"),
        "families":       (0.24, "HIGH", "Perceived as kid-friendly (pasta, pizza); top family weekend choice for affluent suburbs"),
        "premium":        (0.16, "MED",  "Higher-end Italian (Olive, Celini, CinCin) attracts status-conscious and HNW families"),
        "office_workers": (0.16, "MED",  "Team lunches at mid-casual Italian in BKC/Andheri; safe corporate choice, broad appeal"),
        "college_kids":   (0.08, "LOW",  "Italian full-service too expensive for regular college visits unless it is a budget pasta place"),
        "solo_diners":    (0.06, "LOW",  "Possible at counter-service pasta bars but weak at full-service Italian"),
        "working_women":  (0.04, "LOW",  "Moderate — Italian is safe for women but not explicitly women-targeted"),
    },
    "pizza_restaurant": {
        "families":       (0.26, "HIGH", "QSR pizza (62% of market) is weekend home-delivery staple, kid-driven; family bucket orders dominant"),
        "college_kids":   (0.22, "HIGH", "Late-night delivery, group orders, price-sensitive; pizza is the #2 ordered cuisine after biryani"),
        "couples":        (0.16, "MED",  "Artisan/wood-fired pizza (22.6% gourmet segment) is date-night format; QSR pizza weak for couples"),
        "office_workers": (0.14, "MED",  "Team lunch orders, bulk deals; QSR pizza is standard office food"),
        "solo_diners":    (0.12, "MED",  "Single pizza meals, especially delivery; low friction, complete meal"),
        "premium":        (0.06, "LOW",  "Artisan wood-fired attracts premium but is minority; most pizza in MMR is QSR-adjacent"),
        "working_women":  (0.04, "LOW",  "Weak — pizza is not women-targeted unless health-conscious thin-crust format"),
    },
    "steak_house": {
        "premium":        (0.35, "MED",  "Steakhouse is premium by necessity — high ingredient cost, niche demand, imported cuts, wine pairing; status signal"),
        "couples":        (0.28, "MED",  "Special-occasion dining — anniversary, birthday, proposal; romantic positioning"),
        "office_workers": (0.14, "LOW",  "Corporate entertaining at premium steakhouses in South Mumbai/BKC; occasional, high-check"),
        "families":       (0.10, "LOW",  "Too expensive and culturally narrow; beef taboo limits family appeal (72% Hindus link beef-eating to Hindu identity)"),
        "college_kids":   (0.08, "LOW",  "Price-prohibitive; very weak unless it is a budget pork/lamb steak place"),
        "solo_diners":    (0.03, "LOW",  "Extremely rare — steakhouse is social/occasion format"),
        "working_women":  (0.02, "LOW",  "Very weak — steakhouse is male-skewed in perception"),
    },
    "barbecue_restaurant": {
        "college_kids":   (0.26, "MED",  "Shareable meats, craft beer adjacencies, social energy; American BBQ appeals to youth experimentation"),
        "families":       (0.22, "MED",  "Weekend indulgence — all-you-can-eat formats appeal to Indian family psychology; Barbeque Nation model"),
        "office_workers": (0.18, "MED",  "Team outings, Friday night gatherings; social format suits corporate groups"),
        "couples":        (0.16, "MED",  "Casual date-night in Bandra/Khar hipster zones; craft beer + BBQ pairing"),
        "premium":        (0.08, "LOW",  "American BBQ in India is mid-premium, not luxury; premium segment weak"),
        "solo_diners":    (0.06, "LOW",  "Possible at counter-service BBQ but weak at full-service"),
        "working_women":  (0.04, "LOW",  "Weak — BBQ is male-skewed in perception (meat-heavy, beer-centric)"),
    },
    # Asian cuisine types ─────────────────────────────────────────────────────
    "chinese_restaurant": {
        "college_kids":   (0.24, "HIGH", "Indo-Chinese (Hakka, Manchurian, Schezwan) is the default 'cool cheap food' for Indian youth; group hangouts"),
        "families":       (0.22, "HIGH", "Weekend lunch/dinner staple in suburban Mumbai; reliable, spicy, kid-friendly adaptations"),
        "couples":        (0.16, "MED",  "Casual date-night at Indo-Chinese; dim sum brunch for authentic Chinese is couple ritual"),
        "office_workers": (0.14, "MED",  "Quick lunch, delivery; business lunch at authentic Chinese in BKC/South Mumbai"),
        "premium":        (0.12, "MED",  "Authentic Chinese (dim sum, Sichuan) signals cosmopolitan sophistication in South Mumbai/BKC"),
        "solo_diners":    (0.08, "MED",  "Quick bowls, low friction; especially strong at Indo-Chinese counters"),
        "working_women":  (0.04, "LOW",  "Moderate — Chinese is safe but not explicitly women-targeted"),
    },
    "japanese_restaurant": {
        "premium":        (0.28, "HIGH", "Japanese is premium-positioned by default — omakase, sake, Taj/ITC-level; status cuisine in Mumbai"),
        "couples":        (0.26, "HIGH", "Sushi is a date-night staple for affluent millennials; romantic, experiential, shareable"),
        "office_workers": (0.16, "MED",  "Business entertaining in BKC/South Mumbai; safe corporate choice for impressing clients"),
        "working_women":  (0.12, "MED",  "Perceived as safe, clean, sophisticated — attractive for women-centric groups"),
        "families":       (0.08, "LOW",  "Too expensive and 'adventurous' for most Indian families with young children"),
        "college_kids":   (0.06, "LOW",  "Price-prohibitive unless it is a budget ramen joint; weak at full-service Japanese"),
        "solo_diners":    (0.04, "LOW",  "Possible at sushi bar or ramen counter but weak at full-service"),
    },
    "thai_restaurant": {
        "couples":        (0.30, "MED",  "Thai perceived as romantic, aromatic, 'different but not scary' — ideal date-night"),
        "premium":        (0.18, "MED",  "Higher-end Thai (Thai Pavilion, Mekong) attracts status-conscious diners"),
        "families":       (0.16, "MED",  "Families with older children or travel-exposed parents; weekend lunch/dinner"),
        "working_women":  (0.14, "MED",  "Thai cafés in Bandra/Khar attract women for lunch; perceived as healthy, light, safe"),
        "office_workers": (0.10, "LOW",  "Not a common business-lunch cuisine; occasional team lunch"),
        "college_kids":   (0.08, "LOW",  "Too expensive and unfamiliar for regular visits"),
        "solo_diners":    (0.04, "LOW",  "Weak — Thai is social/occasion format"),
    },
    "korean_restaurant": {
        "college_kids":   (0.32, "HIGH", "K-wave (K-pop, K-dramas) drives demand; Gen Z = 27% of Korean orders; BBQ-at-table, Soju nights, group hangouts"),
        "couples":        (0.22, "HIGH", "Korean BBQ is a trendy date-night format; experiential, shareable, Instagram-worthy"),
        "office_workers": (0.14, "MED",  "Occasional team outing; K-culture is conversation starter"),
        "families":       (0.12, "LOW",  "Too unfamiliar and spicy for most Indian families unless K-culture exposed"),
        "premium":        (0.10, "LOW",  "Korean in Mumbai is mid-premium, not luxury; premium segment weak"),
        "solo_diners":    (0.06, "LOW",  "Possible at quick Korean counters but weak at BBQ format"),
        "working_women":  (0.04, "LOW",  "Weak — Korean BBQ is male-skewed in perception (meat-heavy, alcohol-centric)"),
    },
    "sushi_restaurant": {
        "premium":        (0.38, "HIGH", "Standalone sushi is the most premium-skewed category; omakase, chef's counter, imported fish"),
        "couples":        (0.28, "HIGH", "Special-occasion — anniversary, proposal, celebration; romantic, exclusive"),
        "office_workers": (0.16, "MED",  "High-end business entertaining; sushi = 'serious culinary interest' or 'expense account dining'"),
        "working_women":  (0.08, "MED",  "Women-centric groups at mid-range sushi; perceived as sophisticated, safe"),
        "families":       (0.04, "LOW",  "Not a family format — too expensive, too niche, raw fish concerns"),
        "college_kids":   (0.04, "LOW",  "Price-prohibitive; very weak"),
        "solo_diners":    (0.02, "LOW",  "Possible at sushi bar but extremely rare as primary format"),
    },
    "ramen_restaurant": {
        "college_kids":   (0.28, "MED",  "Affordable Japanese, Instagram-worthy, K-culture adjacent; strong near campuses"),
        "solo_diners":    (0.26, "MED",  "Ramen counter culture is perfect for solo dining — quick, warm, low social pressure; comfort food + solitude"),
        "office_workers": (0.18, "MED",  "Quick solo lunch in business districts; warm, filling, fast"),
        "couples":        (0.16, "MED",  "Casual date-night in Bandra/Khar; novelty + affordability"),
        "premium":        (0.06, "LOW",  "Ramen is not status-signaling in Mumbai; premium segment very weak"),
        "families":       (0.04, "LOW",  "Too niche for family outings"),
        "working_women":  (0.02, "LOW",  "Weak — ramen is not explicitly women-targeted"),
    },
    "asian_restaurant": {
        "families":       (0.28, "HIGH", "Pan-Asian solves the 'everyone wants something different' problem; strong weekend family choice"),
        "office_workers": (0.20, "MED",  "Team lunches, safe corporate choice; broad menu = broad appeal"),
        "couples":        (0.18, "MED",  "Casual date-night when neither wants Indian; safe, familiar"),
        "college_kids":   (0.16, "MED",  "Group hangouts in mall food courts; budget-friendly, variety"),
        "premium":        (0.08, "LOW",  "Generic Asian is not premium-positioned; premium segment weak"),
        "solo_diners":    (0.06, "LOW",  "Possible at food courts but weak at full-service"),
        "working_women":  (0.04, "LOW",  "Moderate — safe but not explicitly women-targeted"),
    },
    "asian_fusion_restaurant": {
        "couples":        (0.26, "MED",  "Fusion is experiential, Instagram-driven, signals cultural capital; strong date-night appeal"),
        "college_kids":   (0.24, "MED",  "Gen Z favorite — 90% enjoy communal formats, 58% choose independent restaurants; discovery-driven"),
        "premium":        (0.16, "MED",  "Higher check than generic Asian, chef-driven; attracts affluent experimenters"),
        "working_women":  (0.14, "MED",  "Safe, trendy, women-friendly spaces in Bandra/Khar/Juhu"),
        "office_workers": (0.12, "MED",  "After-work drinks + small plates in Lower Parel/Bandra"),
        "families":       (0.06, "LOW",  "Too experimental for conservative family palates; weak"),
        "solo_diners":    (0.02, "LOW",  "Very weak — fusion is social/discovery format"),
    },
    "middle_eastern_restaurant": {
        "couples":        (0.24, "MED",  "Hummus, mezze, shisha-adjacent ambience = romantic/casual date-night; strong in Bandra/BKC"),
        "office_workers": (0.18, "MED",  "Business lunch in BKC — Mediterranean/Middle Eastern perceived as healthy, light"),
        "families":       (0.16, "MED",  "Mezze sharing format works for families with older children; weekend lunch/dinner"),
        "premium":        (0.14, "MED",  "Lebanese fine-dining (Souk, Taj properties) attracts status-conscious diners"),
        "working_women":  (0.14, "MED",  "Perceived as healthy, safe, sophisticated; strong women presence in Bandra/BKC"),
        "college_kids":   (0.10, "LOW",  "Shawarma/falafel joints near campuses attract budget-conscious students; weak at full-service"),
        "solo_diners":    (0.04, "LOW",  "Weak at full-service; stronger at quick shawarma counters"),
    },
    # Quick-service / protein types ───────────────────────────────────────────
    "chicken_restaurant": {
        "families":       (0.28, "HIGH", "Chicken is the most accepted meat across Indian demographics; family bucket meals are a strong format; KFC and clones dominate"),
        "college_kids":   (0.26, "HIGH", "Fried chicken is a youth staple — shareable, indulgent, social-media friendly"),
        "office_workers": (0.16, "MED",  "Quick lunch, delivery; chicken QSR is standard office food"),
        "solo_diners":    (0.14, "MED",  "Single-combo meals, low friction"),
        "couples":        (0.08, "LOW",  "Not a date-night format; weak"),
        "premium":        (0.04, "LOW",  "Chicken QSR is not premium-positioned"),
        "working_women":  (0.04, "LOW",  "Weak — fried chicken is male-skewed in perception"),
    },
    "chicken_wings_restaurant": {
        "college_kids":   (0.38, "HIGH", "Wings + beer is the quintessential college male hangout; sports-bar adjacent, social energy"),
        "office_workers": (0.24, "MED",  "After-work sports viewing in BKC/Andheri; male-skewed team gatherings"),
        "couples":        (0.14, "LOW",  "Weak unless both are sports fans; not a date format"),
        "families":       (0.10, "LOW",  "Not family-appropriate; weak"),
        "premium":        (0.06, "LOW",  "Wings are casual, not premium"),
        "solo_diners":    (0.04, "LOW",  "Possible at sports bars but weak as primary format"),
        "working_women":  (0.04, "LOW",  "Very weak — wings + sports bar is male-skewed"),
    },
    "kebab_shop": {
        "solo_diners":    (0.24, "MED",  "Quick kebab roll, eat-while-walking or stand-and-eat; low friction, high convenience"),
        "office_workers": (0.22, "MED",  "Quick lunch/dinner grab near railway stations and commercial areas"),
        "college_kids":   (0.20, "MED",  "Cheap, filling, flavorful — perfect for student budgets"),
        "families":       (0.16, "MED",  "Sit-down Mughlai-style kebab shops for weekend family meals"),
        "couples":        (0.10, "LOW",  "Casual date-night at mid-range kebab joints; weak at street stalls"),
        "premium":        (0.04, "LOW",  "Kebab is street-food heritage, not luxury"),
        "working_women":  (0.04, "LOW",  "Weak at street-adjacent; moderate at sit-down Mughlai"),
    },
    "shawarma_restaurant": {
        "college_kids":   (0.32, "HIGH", "Post-party food, late-night cravings, budget-friendly; shawarma is the default late-night college food in Mumbai"),
        "solo_diners":    (0.28, "HIGH", "Single shawarma roll is the perfect solo meal; delivery-first, low friction"),
        "office_workers": (0.18, "MED",  "Late-shift workers, delivery to office; quick, filling"),
        "couples":        (0.10, "LOW",  "Not a date format; weak"),
        "families":       (0.06, "LOW",  "Not a family dining format; weak"),
        "premium":        (0.04, "LOW",  "Shawarma is street food, not premium"),
        "working_women":  (0.02, "LOW",  "Very weak — late-night shawarma is male-skewed in perception"),
    },
    "sandwich_shop": {
        "office_workers": (0.32, "HIGH", "Subway and clones positioned as 'healthier than burger' lunch; BKC, Andheri, Nariman Point strongholds"),
        "working_women":  (0.24, "HIGH", "Perceived as light, healthy, safe — strong women customer base; health-focused meals 2.3x growth"),
        "solo_diners":    (0.20, "MED",  "Single sandwich meals, eat-at-desk or quick counter"),
        "college_kids":   (0.14, "MED",  "Budget-friendly near campuses"),
        "families":       (0.04, "LOW",  "Not a family format; weak"),
        "couples":        (0.04, "LOW",  "Not a date format; weak"),
        "premium":        (0.02, "LOW",  "Sandwich is utilitarian, not status"),
    },
    # Seafood ─────────────────────────────────────────────────────────────────
    "seafood_restaurant": {
        "families":       (0.26, "HIGH", "Weekend family seafood lunch is a deep cultural ritual for Maharashtrian, Goan, Mangalorean communities; fish thali is anchor"),
        "premium":        (0.22, "HIGH", "South Mumbai seafood (Trishna, Mahesh Lunch Home) is status ritual — fresh catch, high check, wine"),
        "couples":        (0.18, "MED",  "Romantic seaside/outdoor seating in Colaba, Worli, Bandra; special-occasion"),
        "office_workers": (0.14, "MED",  "Business lunch at premium seafood in Fort/BKC; quick fish thali at mid-casual near industrial zones"),
        "solo_diners":    (0.12, "MED",  "Quick fish fry + sol kadhi at lunch counters; low friction, filling"),
        "college_kids":   (0.04, "LOW",  "Too expensive for regular visits unless budget joint; weak"),
        "working_women":  (0.04, "LOW",  "Moderate at mid-casual thali places; weak at premium"),
    },
    "fish_and_chips_restaurant": {
        "premium":        (0.28, "LOW",  "If it exists, it is in South Mumbai targeting tourists and expats; premium positioning by default"),
        "couples":        (0.22, "LOW",  "Curious Indian couples might try once for novelty; weak repeat potential"),
        "families":       (0.16, "LOW",  "Indian families prefer coastal Indian seafood over British-style fried fish; weak"),
        "solo_diners":    (0.14, "LOW",  "Solo tourists in Colaba/Fort area; very niche"),
        "office_workers": (0.10, "LOW",  "Occasional expat office workers in BKC; very weak"),
        "college_kids":   (0.06, "LOW",  "Too expensive and unfamiliar; very weak"),
        "working_women":  (0.04, "LOW",  "Very weak — not women-targeted"),
    },
    # International / long-tail cuisine ──────────────────────────────────────
    "mexican_restaurant": {
        "couples":        (0.28, "LOW",  "Casual date-night in Bandra/Khar; tacos, nachos, margaritas — social, shareable"),
        "college_kids":   (0.26, "LOW",  "Tacos and nachos are Instagram-friendly, group-appropriate; Gen Z discovery-driven"),
        "office_workers": (0.16, "LOW",  "Team lunches at mid-casual Mexican in BKC; occasional"),
        "families":       (0.12, "LOW",  "Too spicy/unfamiliar for conservative family palates; weak"),
        "premium":        (0.08, "LOW",  "Mexican is not premium-positioned in Mumbai"),
        "solo_diners":    (0.06, "LOW",  "Possible at quick-taco counters but weak at full-service"),
        "working_women":  (0.04, "LOW",  "Weak — Mexican is not explicitly women-targeted"),
    },
    "french_restaurant": {
        "premium":        (0.40, "LOW",  "French is the apex of Western culinary status in India; ultra-premium, rare"),
        "couples":        (0.30, "LOW",  "Special-occasion — anniversary, proposal; romantic, exclusive"),
        "office_workers": (0.14, "LOW",  "Corporate entertaining at 5-star hotel French outlets; occasional, high-check"),
        "families":       (0.08, "LOW",  "Not a family format; weak"),
        "college_kids":   (0.04, "LOW",  "Price-prohibitive; very weak"),
        "solo_diners":    (0.02, "LOW",  "Extremely rare"),
        "working_women":  (0.02, "LOW",  "Very weak"),
    },
    "mediterranean_restaurant": {
        "couples":        (0.26, "LOW",  "Healthy, light, romantic — date-night appeal; Bandra/Khar geography"),
        "working_women":  (0.22, "LOW",  "Perceived as healthy, safe, sophisticated; strong women presence"),
        "premium":        (0.16, "LOW",  "Higher check than generic, but not fine-dining"),
        "office_workers": (0.16, "LOW",  "Healthy lunch option in BKC/Bandra"),
        "families":       (0.12, "LOW",  "Families with health-conscious parents; weekend lunch"),
        "college_kids":   (0.04, "LOW",  "Too expensive for regular visits"),
        "solo_diners":    (0.04, "LOW",  "Possible at Mediterranean cafés but weak"),
    },
    "lebanese_restaurant": {
        "couples":        (0.24, "LOW",  "Mezze sharing is romantic, casual; strong in Bandra/BKC"),
        "office_workers": (0.20, "LOW",  "Business lunch in BKC — healthy, light"),
        "families":       (0.18, "LOW",  "Sharing format works for families; weekend lunch"),
        "working_women":  (0.16, "LOW",  "Safe, healthy, women-friendly"),
        "college_kids":   (0.12, "LOW",  "Budget falafel/shawarma joints near campuses"),
        "premium":        (0.06, "LOW",  "Lebanese fine-dining is rare but attracts curious affluent diners"),
        "solo_diners":    (0.04, "LOW",  "Weak at full-service; stronger at quick falafel counters"),
    },
    "turkish_restaurant": {
        "couples":        (0.28, "LOW",  "Novelty date-night; Turkish is rare in Mumbai — curiosity-driven"),
        "premium":        (0.24, "LOW",  "Turkish fine-dining is rare but attracts curious affluent diners"),
        "families":       (0.16, "LOW",  "Not a family format; weak"),
        "office_workers": (0.14, "LOW",  "Occasional business lunch if near BKC"),
        "college_kids":   (0.10, "LOW",  "Too unfamiliar for regular visits"),
        "solo_diners":    (0.04, "LOW",  "Very weak"),
        "working_women":  (0.04, "LOW",  "Very weak"),
    },
    "fusion_restaurant": {
        "couples":        (0.28, "MED",  "Fusion is the ultimate date-night 'discovery' cuisine; experiential, Instagram-driven (Farzi Café model)"),
        "premium":        (0.24, "MED",  "High check, chef reputation, exclusivity; attracts HNW experimenters; Godrej Food Trends (provenance + innovation)"),
        "office_workers": (0.18, "MED",  "Corporate entertaining at chef-driven fusion; impress-client format"),
        "college_kids":   (0.14, "LOW",  "Instagram-driven visits to viral fusion spots; one-time, not repeat"),
        "families":       (0.10, "LOW",  "Too experimental for conservative palates; weak"),
        "solo_diners":    (0.04, "LOW",  "Very weak — fusion is social/discovery format"),
        "working_women":  (0.02, "LOW",  "Very weak"),
    },
    "european_restaurant": {
        "premium":        (0.34, "LOW",  "Generic European = 'continental fine dining' in India; hotel-based or fine-dining"),
        "couples":        (0.26, "LOW",  "Special-occasion dining; romantic, formal"),
        "office_workers": (0.20, "LOW",  "Business dining at 5-star European outlets"),
        "families":       (0.10, "LOW",  "Not a family format unless hotel buffet"),
        "college_kids":   (0.04, "LOW",  "Price-prohibitive"),
        "solo_diners":    (0.04, "LOW",  "Very weak"),
        "working_women":  (0.02, "LOW",  "Very weak"),
    },
}

# Types that are too generic to use as a prior lookup key
_PRIOR_GENERIC: frozenset[str] = frozenset({
    "food", "point_of_interest", "establishment", "store",
    "premise", "locality", "political", "street_address", "geocode",
})

FLAT_PRIOR = 1.0 / len(ALL_SEGMENTS)  # used when venue type has no matched prior

FITNESS_COLS = [
    'fitness_for_office_lunch', 'fitness_for_repeat_habit', 'fitness_for_social_dwell',
    'fitness_for_group_energy', 'fitness_for_destination_visit', 'operational_quality',
    'retention_strength',
]

# ─── SQL ────────────────────────────────────────────────────────────────────

CREATE_TABLE_SQL = """
CREATE TABLE IF NOT EXISTS venue_demographic_scores (
    id              SERIAL PRIMARY KEY,
    venue_id        INTEGER NOT NULL REFERENCES venues(id) ON DELETE CASCADE,
    segment_id      VARCHAR(50) NOT NULL,
    alignment_score FLOAT NOT NULL DEFAULT 0.0,
    segment_rank    INTEGER,
    created_at      TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(venue_id, segment_id)
);
"""

CREATE_INDEXES_SQL = [
    "CREATE INDEX IF NOT EXISTS idx_vds_venue_id   ON venue_demographic_scores(venue_id);",
    "CREATE INDEX IF NOT EXISTS idx_vds_venue_rank ON venue_demographic_scores(venue_id, segment_rank);",
    "CREATE INDEX IF NOT EXISTS idx_vds_segment    ON venue_demographic_scores(segment_id, alignment_score DESC);",
]

ADD_RANK_COL_SQL = "ALTER TABLE venue_similarity ADD COLUMN IF NOT EXISTS rank INTEGER;"

UPDATE_RANK_SQL = """
UPDATE venue_similarity vs
SET rank = sub.rn
FROM (
    SELECT venue_id, similar_venue_id,
           ROW_NUMBER() OVER (
               PARTITION BY venue_id
               ORDER BY similarity_score DESC
           ) AS rn
    FROM venue_similarity
) sub
WHERE vs.venue_id         = sub.venue_id
  AND vs.similar_venue_id = sub.similar_venue_id;
"""

CREATE_RANK_INDEX_SQL = "CREATE INDEX IF NOT EXISTS idx_vs_venue_rank ON venue_similarity(venue_id, rank);"

INSERT_SCORES_SQL = """
    INSERT INTO venue_demographic_scores
        (venue_id, segment_id, alignment_score, segment_rank)
    VALUES %s
    ON CONFLICT (venue_id, segment_id) DO UPDATE SET
        alignment_score = EXCLUDED.alignment_score,
        segment_rank    = EXCLUDED.segment_rank;
"""

BATCH_SIZE = 500


# ─── Scoring logic ────────────────────────────────────────────────────────────

def _get_prior(raw_types: list[str]) -> dict[str, float]:
    """
    Walk the venue's raw Google types in order; return the first matching
    VENUE_TYPE_SEGMENT_PRIORS entry as a dict {segment_id: prior_weight}.
    Falls back to a flat prior if no match is found.
    """
    for t in (raw_types or []):
        if t in _PRIOR_GENERIC:
            continue
        if t in VENUE_TYPE_SEGMENT_PRIORS:
            return {seg: entry[0] for seg, entry in VENUE_TYPE_SEGMENT_PRIORS[t].items()}
    return {seg: FLAT_PRIOR for seg in ALL_SEGMENTS}


def _compute_scores(prior: dict[str, float], fitness: dict[str, float]) -> dict[str, float]:
    """
    For each segment: score = prior × (1 + Σ(evidence × weight × confidence_discount))
    Then normalize so scores sum to 1.0.
    """
    raw: dict[str, float] = {}
    for segment_id, weights in SEGMENT_FITNESS_WEIGHTS.items():
        evidence_sum = 0.0
        for dim, (weight, conf) in weights.items():
            col = DIM_MAP.get(dim)
            if col is None:
                continue  # friction_tolerance not yet in pipeline
            evidence_sum += fitness.get(col, 0.0) * weight * CONFIDENCE_DISCOUNT[conf]
        seg_prior = prior.get(segment_id, FLAT_PRIOR)
        raw[segment_id] = seg_prior * (1.0 + evidence_sum)

    total = sum(raw.values()) or 1.0
    return {seg: round(v / total, 6) for seg, v in raw.items()}


# ─── Operations ─────────────────────────────────────────────────────────────

def create_tables(cursor) -> None:
    cursor.execute(CREATE_TABLE_SQL)
    for sql in CREATE_INDEXES_SQL:
        cursor.execute(sql)
    print("  venue_demographic_scores table + indexes ready")


def add_similarity_rank(cursor) -> int:
    cursor.execute(ADD_RANK_COL_SQL)
    cursor.execute(UPDATE_RANK_SQL)
    updated = cursor.rowcount
    cursor.execute(CREATE_RANK_INDEX_SQL)
    print(f"  Rank populated for {updated:,} similarity pairs")
    return updated


def compute_demographic_scores(cursor) -> int:
    # Load fitness profiles
    cols_sql = ', '.join(FITNESS_COLS)
    cursor.execute(f"SELECT venue_id, {cols_sql} FROM venue_fitness_dimensions")
    fitness_rows = cursor.fetchall()
    fitness_map: dict[int, dict[str, float]] = {
        row[0]: dict(zip(FITNESS_COLS, [float(v or 0.0) for v in row[1:]]))
        for row in fitness_rows
    }
    print(f"  Loaded fitness profiles for {len(fitness_map):,} venues")

    # Load venue types for prior lookup
    cursor.execute("SELECT id, types FROM venues WHERE id = ANY(%s)", (list(fitness_map.keys()),))
    types_map: dict[int, list[str]] = {row[0]: list(row[1] or []) for row in cursor.fetchall()}
    print(f"  Loaded venue types for {len(types_map):,} venues")

    insert_rows = []
    prior_hits = 0

    for venue_id, fitness in fitness_map.items():
        raw_types = types_map.get(venue_id, [])
        prior = _get_prior(raw_types)
        if any(v != FLAT_PRIOR for v in prior.values()):
            prior_hits += 1

        scores = _compute_scores(prior, fitness)
        ranked = sorted(scores.items(), key=lambda x: x[1], reverse=True)
        for rank, (segment_id, score) in enumerate(ranked, 1):
            insert_rows.append((venue_id, segment_id, score, rank))

    for i in range(0, len(insert_rows), BATCH_SIZE):
        psycopg2.extras.execute_values(
            cursor, INSERT_SCORES_SQL, insert_rows[i:i + BATCH_SIZE]
        )

    print(f"  Venues with type-matched prior : {prior_hits:,} / {len(fitness_map):,}")
    return len(insert_rows)


# ─── Main ────────────────────────────────────────────────────────────────────

def main():
    print("\n012_compute_venue_demographics.py -- Demographic scores + similarity rank\n")

    conn   = psycopg2.connect(**DB_CONFIG)
    cursor = conn.cursor()

    try:
        print("  [1/3] Creating venue_demographic_scores table...")
        create_tables(cursor)

        print("\n  [2/3] Adding rank to venue_similarity (for carousel pagination)...")
        sim_ranked = add_similarity_rank(cursor)

        print("\n  [3/3] Computing venue → segment alignment scores (Bayesian prior + fitness evidence)...")
        score_rows = compute_demographic_scores(cursor)

        conn.commit()

        print("\n" + "=" * 60)
        print("  COMPLETE")
        print(f"  Similarity pairs ranked    : {sim_ranked:,}")
        print(f"  Demographic score rows     : {score_rows:,}")
        print(f"  Segments per venue         : {len(ALL_SEGMENTS)}")
        print(f"  Venues scored              : {score_rows // len(ALL_SEGMENTS):,}")
        print("=" * 60 + "\n")
        print("  NOTE: friction_tolerance dimension is not yet in the pipeline.")
        print("        Add it to step_5 output and update DIM_MAP to activate.")

    except Exception as e:
        conn.rollback()
        print(f"\n[ERROR] {e}")
        raise
    finally:
        cursor.close()
        conn.close()


if __name__ == '__main__':
    main()
