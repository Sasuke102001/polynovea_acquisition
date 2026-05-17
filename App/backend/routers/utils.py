"""
utils.py
Shared helpers used across all routers.
"""

from models import ArchetypeChip

# ─── Venue type taxonomy ──────────────────────────────────────────────────────
#
# Display logic (up to 5 tags per venue):
#   Slot 1      : First food type in Google's original array — owner's primary identity,
#                 exactly how it appears on Google / Zomato / Swiggy. Always kept first.
#   Slots 2–4   : Remaining food types the venue actually has, filled in tier priority
#                 order (Tier 1 broad → Tier 2 style → Tier 3 cuisine/detail).
#   Slot 5      : One valid non-food descriptor that adds customer-facing context
#                 (e.g. Live Music, Karaoke, Hookah Bar). Excluded: infra tags, housing,
#                 schools, medical, and anything with zero F&B relevance.

# Google Places infra tags — never display
_INFRA_TYPES: frozenset[str] = frozenset({
    "food", "point_of_interest", "establishment", "store", "premise",
    "locality", "political", "street_address", "geocode", "route",
    "sublocality", "sublocality_level_1", "sublocality_level_2",
    "neighborhood", "administrative_area_level_1",
    "administrative_area_level_2", "administrative_area_level_3",
    "country", "postal_code", "natural_feature", "colloquial_area",
})

# Tier 1: Broad venue category — what kind of place is this?
_TIER_1: list[str] = [
    "restaurant", "bar", "cafe", "night_club", "pub", "bakery",
    "food_court", "lounge_bar", "cocktail_bar", "hookah_bar", "brewpub",
    "brewery", "wine_bar", "coffee_shop", "coffee_roastery", "coffee_stand",
    "tea_house", "tea_store", "dessert_shop", "confectionery",
    "snack_bar", "juice_shop",
]

# Tier 2: Style / format — how does it operate?
_TIER_2: list[str] = [
    "fine_dining_restaurant", "fast_food_restaurant", "family_restaurant",
    "buffet_restaurant", "brunch_restaurant", "breakfast_restaurant",
    "diner", "bistro", "gastropub", "bar_and_grill", "sports_bar",
    "dessert_restaurant", "pastry_shop", "cake_shop", "ice_cream_shop",
    "food_delivery", "health_food_store", "catering_service", "cafeteria",
]

# Tier 3: Cuisine / specific descriptor — what do they serve?
_TIER_3: list[str] = [
    "indian_restaurant", "north_indian_restaurant", "south_indian_restaurant",
    "chinese_restaurant", "italian_restaurant", "seafood_restaurant",
    "pizza_restaurant", "mexican_restaurant", "japanese_restaurant",
    "thai_restaurant", "middle_eastern_restaurant", "american_restaurant",
    "asian_restaurant", "vegetarian_restaurant", "vegan_restaurant",
    "hamburger_restaurant", "chicken_restaurant", "chicken_wings_restaurant",
    "kebab_shop", "shawarma_restaurant", "sandwich_shop",
    "european_restaurant", "mediterranean_restaurant", "lebanese_restaurant",
    "turkish_restaurant", "persian_restaurant", "cantonese_restaurant",
    "korean_restaurant", "ramen_restaurant", "sushi_restaurant",
    "french_restaurant", "british_restaurant", "barbecue_restaurant",
    "fusion_restaurant", "asian_fusion_restaurant",
    "dim_sum_restaurant", "chinese_noodle_restaurant", "noodle_shop",
    "dumpling_restaurant", "steak_house", "tapas_restaurant",
    "tex_mex_restaurant", "taco_restaurant", "burrito_restaurant",
    "hot_dog_restaurant", "hot_dog_stand", "fish_and_chips_restaurant",
    "portuguese_restaurant", "burmese_restaurant", "eastern_european_restaurant",
    "afghani_restaurant", "bagel_shop", "deli", "salad_shop",
    "soup_restaurant", "western_restaurant", "irish_pub",
    "german_restaurant", "australian_restaurant", "malaysian_restaurant",
    "latin_american_restaurant", "vietnamese_restaurant", "tibetan_restaurant",
    "brazilian_restaurant", "african_restaurant", "falafel_restaurant",
    "southwestern_us_restaurant",
]

# Non-food descriptors — slot 5 only, adds customer-facing venue identity context
_NON_FOOD_DESCRIPTORS: list[str] = [
    "live_music_venue", "comedy_club", "wedding_venue", "banquet_hall",
    "event_venue", "karaoke", "beer_garden", "coworking_space",
    "performing_arts_theater", "dance_hall", "wellness_center",
    "sports_complex", "indoor_playground", "amusement_park",
    "video_arcade", "bowling_alley", "internet_cafe", "dog_cafe", "cat_cafe",
]

# Derived sets for O(1) lookup
_ALL_FOOD_TYPES: list[str] = _TIER_1 + _TIER_2 + _TIER_3
_FOOD_TYPES_SET: frozenset[str] = frozenset(_ALL_FOOD_TYPES)
_NON_FOOD_SET:   frozenset[str] = frozenset(_NON_FOOD_DESCRIPTORS)

# Human-readable display labels for every approved type
_TYPE_LABELS: dict[str, str] = {
    # Tier 1
    "restaurant":                   "Restaurant",
    "bar":                          "Bar",
    "cafe":                         "Café",
    "night_club":                   "Night Club",
    "pub":                          "Pub",
    "bakery":                       "Bakery",
    "food_court":                   "Food Court",
    "lounge_bar":                   "Lounge Bar",
    "cocktail_bar":                 "Cocktail Bar",
    "hookah_bar":                   "Hookah Bar",
    "brewpub":                      "Brewpub",
    "brewery":                      "Brewery",
    "wine_bar":                     "Wine Bar",
    "coffee_shop":                  "Coffee Shop",
    "coffee_roastery":              "Coffee Roastery",
    "coffee_stand":                 "Coffee Stand",
    "tea_house":                    "Tea House",
    "tea_store":                    "Tea Store",
    "dessert_shop":                 "Dessert Shop",
    "confectionery":                "Confectionery",
    "snack_bar":                    "Snack Bar",
    "juice_shop":                   "Juice Shop",
    # Tier 2
    "fine_dining_restaurant":       "Fine Dining",
    "fast_food_restaurant":         "Fast Food",
    "family_restaurant":            "Family Restaurant",
    "buffet_restaurant":            "Buffet",
    "brunch_restaurant":            "Brunch",
    "breakfast_restaurant":         "Breakfast",
    "diner":                        "Diner",
    "bistro":                       "Bistro",
    "gastropub":                    "Gastropub",
    "bar_and_grill":                "Bar & Grill",
    "sports_bar":                   "Sports Bar",
    "dessert_restaurant":           "Dessert",
    "pastry_shop":                  "Pastry Shop",
    "cake_shop":                    "Cake Shop",
    "ice_cream_shop":               "Ice Cream",
    "food_delivery":                "Delivery",
    "health_food_store":            "Health Food",
    "catering_service":             "Catering",
    "cafeteria":                    "Cafeteria",
    # Tier 3
    "indian_restaurant":            "Indian",
    "north_indian_restaurant":      "North Indian",
    "south_indian_restaurant":      "South Indian",
    "chinese_restaurant":           "Chinese",
    "italian_restaurant":           "Italian",
    "seafood_restaurant":           "Seafood",
    "pizza_restaurant":             "Pizza",
    "mexican_restaurant":           "Mexican",
    "japanese_restaurant":          "Japanese",
    "thai_restaurant":              "Thai",
    "middle_eastern_restaurant":    "Middle Eastern",
    "american_restaurant":          "American",
    "asian_restaurant":             "Asian",
    "vegetarian_restaurant":        "Vegetarian",
    "vegan_restaurant":             "Vegan",
    "hamburger_restaurant":         "Burgers",
    "chicken_restaurant":           "Chicken",
    "chicken_wings_restaurant":     "Wings",
    "kebab_shop":                   "Kebab",
    "shawarma_restaurant":          "Shawarma",
    "sandwich_shop":                "Sandwiches",
    "european_restaurant":          "European",
    "mediterranean_restaurant":     "Mediterranean",
    "lebanese_restaurant":          "Lebanese",
    "turkish_restaurant":           "Turkish",
    "persian_restaurant":           "Persian",
    "cantonese_restaurant":         "Cantonese",
    "korean_restaurant":            "Korean",
    "ramen_restaurant":             "Ramen",
    "sushi_restaurant":             "Sushi",
    "french_restaurant":            "French",
    "british_restaurant":           "British",
    "barbecue_restaurant":          "BBQ",
    "fusion_restaurant":            "Fusion",
    "asian_fusion_restaurant":      "Asian Fusion",
    "dim_sum_restaurant":           "Dim Sum",
    "chinese_noodle_restaurant":    "Chinese Noodles",
    "noodle_shop":                  "Noodles",
    "dumpling_restaurant":          "Dumplings",
    "steak_house":                  "Steakhouse",
    "tapas_restaurant":             "Tapas",
    "tex_mex_restaurant":           "Tex-Mex",
    "taco_restaurant":              "Tacos",
    "burrito_restaurant":           "Burritos",
    "hot_dog_restaurant":           "Hot Dogs",
    "hot_dog_stand":                "Hot Dogs",
    "fish_and_chips_restaurant":    "Fish & Chips",
    "portuguese_restaurant":        "Portuguese",
    "burmese_restaurant":           "Burmese",
    "eastern_european_restaurant":  "Eastern European",
    "afghani_restaurant":           "Afghani",
    "bagel_shop":                   "Bagels",
    "deli":                         "Deli",
    "salad_shop":                   "Salads",
    "soup_restaurant":              "Soups",
    "western_restaurant":           "Western",
    "irish_pub":                    "Irish Pub",
    "german_restaurant":            "German",
    "australian_restaurant":        "Australian",
    "malaysian_restaurant":         "Malaysian",
    "latin_american_restaurant":    "Latin American",
    "vietnamese_restaurant":        "Vietnamese",
    "tibetan_restaurant":           "Tibetan",
    "brazilian_restaurant":         "Brazilian",
    "african_restaurant":           "African",
    "falafel_restaurant":           "Falafel",
    "southwestern_us_restaurant":   "Southwestern",
    # Non-food descriptors
    "live_music_venue":             "Live Music",
    "comedy_club":                  "Comedy Club",
    "wedding_venue":                "Wedding Venue",
    "banquet_hall":                 "Banquet Hall",
    "event_venue":                  "Event Venue",
    "karaoke":                      "Karaoke",
    "beer_garden":                  "Beer Garden",
    "coworking_space":              "Coworking",
    "performing_arts_theater":      "Performing Arts",
    "dance_hall":                   "Dance Hall",
    "wellness_center":              "Wellness",
    "sports_complex":               "Sports Complex",
    "indoor_playground":            "Indoor Play",
    "amusement_park":               "Amusement Park",
    "video_arcade":                 "Arcade",
    "bowling_alley":                "Bowling",
    "internet_cafe":                "Internet Café",
    "dog_cafe":                     "Dog Café",
    "cat_cafe":                     "Cat Café",
}


def map_venue_types(raw_types: list[str]) -> list[str]:
    """
    Convert Google Place types to up to 5 display-friendly labels.

    Slot 1:   First food type in Google's original order — the venue's primary identity
              as Google / Zomato / Swiggy surface it. Always kept first.
    Slots 2–4: Remaining food types the venue has, filled in tier-priority order
              (Tier 1 broad category → Tier 2 style/format → Tier 3 cuisine/detail).
    Slot 5:   One valid non-food descriptor if present, adds contextual identity value
              (e.g. "Live Music", "Karaoke"). Schools, apartments, hospitals excluded.
    """
    if not raw_types:
        return ["Venue"]

    food_in_order = [t for t in raw_types if t in _FOOD_TYPES_SET]
    non_food_in_order = [t for t in raw_types if t in _NON_FOOD_SET]

    if not food_in_order and not non_food_in_order:
        return ["Venue"]

    result_keys: list[str] = []

    # Slot 1: Google's first food type in the raw array — venue's primary identity
    if food_in_order:
        result_keys.append(food_in_order[0])

    # Slots 2–4: remaining food types in Google's original order (no tier reordering)
    for t in food_in_order[1:]:
        if len(result_keys) >= 4:
            break
        result_keys.append(t)

    # Slot 5: first valid non-food descriptor (context only)
    if non_food_in_order and len(result_keys) < 5:
        result_keys.append(non_food_in_order[0])

    labels = [_TYPE_LABELS.get(k, k.replace("_", " ").title()) for k in result_keys]
    return labels or ["Venue"]


# ─── Archetype demographic descriptors ───────────────────────────────────────
# Never show an archetype label alone — always paired with demographic context.

ARCHETYPE_DESCRIPTORS: dict[str, str] = {
    "Trusted Regular":      "Loyal weekday diners · 26–35 · office crowd",
    "Habit Former":         "Routine-driven · return on schedule",
    "Power Regular":        "High-frequency visitors · discipline-driven",
    "Calm Pairs":           "Couples · weekend & occasion dining",
    "Discovery Explorer":   "First-time visitors · curiosity-driven",
    "Premium Prioritizer":  "High spend · status-conscious",
    "Party Seeker":         "Weekend groups · 18–24 · high energy",
    "Scene Seeker":         "Trend-conscious · Instagram-active",
    "Lifestyle Regular":    "Premium regulars · experience-driven",
    "Trend Hunter":         "Early adopters · novelty-seeking · 20–30",
    "Quiet Discoverer":     "Solo explorers · low-key · discovery-driven",
    "Social Butterfly":     "Group-first · social-occasion-driven · WOM amplifier",
    "Comfort Dweller":      "Familiarity-seeking · long dwell · safety-conscious",
}

def make_archetype_chip(name: str) -> ArchetypeChip:
    return ArchetypeChip(
        name=name,
        demographic_label=ARCHETYPE_DESCRIPTORS.get(name, name),
    )


# ─── Health score ─────────────────────────────────────────────────────────────

def compute_health_score(
    operational_quality,
    social_dwell,
    group_energy,
    retention_strength,
) -> int:
    """
    Venue Signal Score — weighted formula:
      0.40 × operational_quality
      0.30 × fitness_for_social_dwell
      0.20 × fitness_for_group_energy
      0.10 × retention_strength

    asyncpg may return Decimal for NUMERIC columns — always cast to float first.
    Replacing the old (ops + retention) / 2 formula which let retention=0 drag the
    score down unfairly for venues with no repeat-visit signals in reviews.
    """
    ops   = float(operational_quality or 0)
    dwell = float(social_dwell        or 0)
    group = float(group_energy        or 0)
    ret   = float(retention_strength  or 0)
    raw   = 0.40 * ops + 0.30 * dwell + 0.20 * group + 0.10 * ret
    return round(raw * 100)


def data_confidence_label(fd) -> str:
    """
    Rates how much radar signal exists for this venue.
    Counts fitness dimensions with score > 0.01 (truly non-zero).
    HIGH (>=4 dims), MED (2-3), LOW (0-1).
    """
    radar_keys = [
        "fitness_for_office_lunch",
        "fitness_for_repeat_habit",
        "fitness_for_social_dwell",
        "fitness_for_group_energy",
        "fitness_for_destination_visit",
    ]
    non_zero = sum(1 for k in radar_keys if float(fd[k] or 0) > 0.01)
    if non_zero >= 4:
        return "HIGH"
    if non_zero >= 2:
        return "MED"
    return "LOW"


def health_label(score: int) -> str:
    if score >= 80: return "STRONG"
    if score >= 65: return "GOOD"
    if score >= 45: return "NEEDS WORK"
    return "AT RISK"


# ─── Fitness dimension display labels ────────────────────────────────────────

DIM_LABELS: dict[str, str] = {
    "fitness_for_office_lunch":      "Office Lunch",
    "fitness_for_repeat_habit":      "Repeat Habit",
    "fitness_for_social_dwell":      "Social Dwell",
    "fitness_for_group_energy":      "Group Energy",
    "fitness_for_destination_visit": "Destination Visit",
    "operational_quality":           "Operational Quality",
    "retention_strength":            "Retention Strength",
    # monetization_potential excluded — incoherent composite, pending redesign
}

RADAR_DIMS = [
    "fitness_for_office_lunch",
    "fitness_for_repeat_habit",
    "fitness_for_social_dwell",
    "fitness_for_group_energy",
    "fitness_for_destination_visit",
]

ALL_DIMS = list(DIM_LABELS.keys())


# ─── Segment demographic labels ──────────────────────────────────────────────

SEGMENT_LABELS: dict[str, dict] = {
    "office_workers": {
        "label": "Office Workers",
        "demographic": "26–35 · Weekday lunch · Solo or pairs",
        "visit_time": "Weekday lunch",
    },
    "college_kids": {
        "label": "Social Crowd",
        "demographic": "18–30 · Weekends & evenings · Groups 3+",
        "visit_time": "Weekend evenings",
    },
    "couples": {
        "label": "Couples",
        "demographic": "23–38 · Weekend evenings · Destination dining",
        "visit_time": "Weekend evening",
    },
    "families": {
        "label": "Families",
        "demographic": "All ages · Weekends · 3–6 people",
        "visit_time": "Weekend lunch & dinner",
    },
    "premium": {
        "label": "Premium Diners",
        "demographic": "30–50 · Any day · High spend",
        "visit_time": "Weekend & special occasions",
    },
    "solo_diners": {
        "label": "Solo Diners",
        "demographic": "22–40 · Weekday lunch & evening · Solo",
        "visit_time": "Weekday lunch & evening",
    },
    "working_women": {
        "label": "Working Women",
        "demographic": "24–38 · Weekday lunch · Safe, comfortable spaces",
        "visit_time": "Weekday lunch",
    },
}


# ─── Intervention type → human title ─────────────────────────────────────────
# Maps raw intervention_type strings from DB to display titles.
# Scope: behavioral signals ONLY — never menu, pricing, delivery, staffing.

INTERVENTION_TITLES: dict[str, str] = {
    "operational_optimization": "Reduce service friction",
    "premium_justification":    "Strengthen premium positioning",
    "dwell_monetization":       "Improve dwell-time conversion",
    "friction_reduction":       "Remove repeat visit barriers",
    "social_proof_gap":         "Close platform visibility gap",
    "retention_gap":            "Build re-engagement mechanism",
    "group_energy_gap":         "Address group experience friction",
    "destination_gap":          "Build destination narrative",
    "ambience_signal":          "Improve atmosphere signals",
    "segment_capture":          "Capture underserved segment",
}

def intervention_title(intervention_type: str) -> str:
    return INTERVENTION_TITLES.get(intervention_type, intervention_type.replace("_", " ").title())


# ─── Segment → top 2 archetypes (static, matches demographic_archetype_mapping) ─
# Avoids per-venue DB round-trips on list screens.

SEGMENT_TOP_ARCHETYPES: dict[str, list[str]] = {
    "office_workers": ["Trusted Regular",   "Habit Former"],
    "college_kids":   ["Party Seeker",      "Scene Seeker"],
    "couples":        ["Calm Pairs",        "Lifestyle Regular"],
    "families":       ["Trusted Regular",   "Habit Former"],
    "premium":        ["Lifestyle Regular", "Scene Seeker"],
    "solo_diners":    ["Quiet Discoverer",  "Trusted Regular"],
    "working_women":  ["Lifestyle Regular", "Trusted Regular"],
}


# ─── Channel & mechanism display labels ──────────────────────────────────────

CHANNEL_LABELS: dict[str, str] = {
    "whatsapp":               "WhatsApp Broadcast",
    "sms":                    "SMS Blast",
    "email":                  "Email Campaign",
    "instagram_organic":      "Instagram Content",
    "instagram_reels":        "Instagram Reels",
    "instagram_ads":          "Meta & Instagram Ads",
    "google_ads":             "Google Ads",
    "instagram_consulting":   "Instagram (Advisory)",
    "zomato_swiggy":          "Zomato / Swiggy",
    "youtube_shorts":         "YouTube Shorts",
    "tiktok":                 "YouTube Shorts",   # TikTok banned in India → display as YT Shorts
    "facebook":               "Facebook Ads",
    "micro_influencer":       "Micro-Influencer",
}

MECHANISM_LABELS: dict[str, str] = {
    "habit_formation":           "Habit Formation",
    "fomo_scarcity":             "FOMO / Scarcity",
    "social_proof":              "Social Proof",
    "identity_signaling":        "Identity Signaling",
    "environmental_expectation": "Environmental Expectation",
    "intent_capture":            "Search Intent Capture",
}


# ─── Priority tier ordering ───────────────────────────────────────────────────

TIER_ORDER = {"CRITICAL": 1, "HIGH": 2, "MEDIUM": 3, "LOW": 4}

def tier_sort_key(tier: str) -> int:
    return TIER_ORDER.get(tier, 5)
