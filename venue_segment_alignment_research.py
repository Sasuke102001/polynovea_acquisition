
# RESEARCH BRIEF: Venue-Segment Alignment Scoring for Urban India F&B
# Validated Methodology & Dictionaries
# Generated: 2026-05-15

# =============================================================================
# SEGMENT_FITNESS_WEIGHTS
# =============================================================================

SEGMENT_FITNESS_WEIGHTS = {
    "solo_diners": {
        "operational_quality": (0.45, "HIGH"),   # SoDF scale: Inconspicuousness, Proper Service
        "repeat_habit": (0.20, "MED"),           # Habits form around convenience + low friction
        "retention_strength": (0.15, "MED"),       # Lower than group diners (social bonding weaker)
        "friction_tolerance": (0.10, "HIGH"),    # Solo diners are MORE friction-sensitive
        "social_dwell": (0.05, "LOW"),             # Negative predictor - solo diners avoid high social density
        "destination_visit": (0.05, "LOW"),        # Weak - solo dining is utilitarian, not destination-driven
    },
    "working_women": {
        "operational_quality": (0.30, "HIGH"),     # Safety, comfort, proper service
        "office_lunch": (0.25, "HIGH"),            # Temporal + location constraint
        "retention_strength": (0.15, "MED"),         # Habit loop: weekday routine
        "friction_tolerance": (0.15, "HIGH"),      # Low friction tolerance (time-constrained)
        "social_dwell": (0.10, "MED"),             # Peer social proof matters
        "destination_visit": (0.05, "LOW"),          # Less destination-driven than couples
    },
    "couples": {
        "destination_visit": (0.40, "HIGH"),         # Date night = planned, occasion-driven
        "social_dwell": (0.20, "HIGH"),              # Intimacy requires privacy + ambiance
        "operational_quality": (0.15, "MED"),        # Service quality matters for experience
        "repeat_habit": (0.10, "MED"),               # Some habitual date spots, but less than solo/office
        "retention_strength": (0.10, "MED"),           # Emotional bonding (Mattila 2001)
        "friction_tolerance": (0.05, "LOW"),           # Will tolerate some friction for special occasion
    },
    "premium": {
        "destination_visit": (0.35, "HIGH"),          # Status signaling, Veblen effect
        "social_dwell": (0.25, "HIGH"),               # Social belonging + identity display
        "operational_quality": (0.20, "HIGH"),        # Exceptional service expected
        "retention_strength": (0.10, "MED"),          # Lower repeat - occasion-driven
        "repeat_habit": (0.05, "LOW"),                # Not habitual - special occasions
        "friction_tolerance": (0.05, "LOW"),            # Zero friction tolerance at premium price
    },
    "college_kids": {
        "group_energy": (0.35, "HIGH"),                # 90% enjoy communal formats (Gen Z research)
        "social_dwell": (0.25, "HIGH"),                 # Social proof + group dynamics
        "friction_tolerance": (0.15, "MED"),            # Price-sensitive but tolerate some friction
        "repeat_habit": (0.10, "MED"),                  # Habit formation around hangout spots
        "operational_quality": (0.10, "MED"),             # Less sensitive than solo diners
        "destination_visit": (0.05, "LOW"),               # Proximity > destination
    },
    "office_workers": {
        "office_lunch": (0.35, "HIGH"),                 # Temporal + location + speed constraints
        "repeat_habit": (0.25, "HIGH"),                 # Duhigg habit loop: weekday routine
        "operational_quality": (0.20, "HIGH"),          # Speed, consistency, reliability
        "friction_tolerance": (0.10, "HIGH"),             # Very low - time is scarce
        "retention_strength": (0.05, "MED"),              # Some loyalty to convenient spots
        "social_dwell": (0.05, "LOW"),                      # Anti-predictor - want fast, not lingering
    },
    "families": {
        "repeat_habit": (0.30, "HIGH"),                   # Strong habit + routine (weekend ritual)
        "operational_quality": (0.25, "HIGH"),            # Cleanliness, safety, kid-friendly
        "retention_strength": (0.20, "MED"),                # Reliability-seeking
        "friction_tolerance": (0.15, "HIGH"),             # Low - children amplify friction sensitivity
        "social_dwell": (0.05, "LOW"),                        # Anti-predictor - avoid dense social environments
        "destination_visit": (0.05, "LOW"),                     # Proximity + convenience > destination
    }
}

# =============================================================================
# VENUE_TYPE_SEGMENT_PRIORS
# =============================================================================

VENUE_TYPE_SEGMENT_PRIORS = {
    "fine_dining_restaurant": {
        "premium": (0.45, "HIGH", "Veblen effect + status signaling; 70% prioritize food quality/ambiance"),
        "couples": (0.30, "HIGH", "Date night + special occasion; intimacy + ambiance drivers"),
        "families": (0.10, "MED", "Celebration meals; some family fine dining but structurally less fit"),
        "office_workers": (0.05, "LOW", "Business lunch only; time + price mismatch"),
        "college_kids": (0.05, "LOW", "Price mismatch; aspirational but not primary"),
        "solo_diners": (0.03, "LOW", "Possible but stigmatized in India; inconspicuousness hard"),
        "working_women": (0.02, "LOW", "Safety + comfort concerns in upscale solo dining"),
    },
    "fast_food_restaurant": {
        "college_kids": (0.30, "HIGH", "Price-sensitive + group energy; QSR 65% Gen Z/millennial"),
        "office_workers": (0.25, "HIGH", "Speed + convenience; tiffin alternative"),
        "families": (0.20, "MED", "Quick weekend meals; kid-friendly"),
        "solo_diners": (0.15, "MED", "Low friction + inconspicuousness"),
        "working_women": (0.05, "LOW", "Possible but less preferred than healthier options"),
        "couples": (0.03, "LOW", "Anti-fit; lacks ambiance + intimacy"),
        "premium": (0.02, "LOW", "Status mismatch"),
    },
    "bar": {
        "college_kids": (0.30, "HIGH", "Social energy + group dynamics; evening/weekend"),
        "couples": (0.20, "MED", "Some date nights; but noise + crowd can conflict with intimacy"),
        "office_workers": (0.15, "MED", "After-work social; but temporal mismatch for lunch"),
        "solo_diners": (0.10, "MED", "Bar counter solo dining normalized"),
        "premium": (0.10, "MED", "Cocktail culture + status signaling"),
        "working_women": (0.08, "LOW", "Safety concerns in India bar culture"),
        "families": (0.07, "LOW", "Structurally anti-fit; children not allowed"),
    },
    "cafe": {
        "college_kids": (0.25, "HIGH", "Study + hangout; 72% go with friends"),
        "working_women": (0.20, "HIGH", "Safety + comfort; all-women staff cafes emerging"),
        "solo_diners": (0.20, "HIGH", "Inconspicuousness + proper service; cafe = safe solo space"),
        "office_workers": (0.15, "MED", "Coffee meetings + quick lunch"),
        "couples": (0.10, "MED", "Casual dates; but less intimate than fine dining"),
        "families": (0.07, "LOW", "Possible but less preferred than full-service"),
        "premium": (0.03, "LOW", "Status mismatch; cafe = accessible, not exclusive"),
    },
    "night_club": {
        "college_kids": (0.45, "HIGH", "Peak social energy; 90% Gen Z communal formats"),
        "couples": (0.20, "MED", "Some date nights; but intimacy destroyed by noise"),
        "premium": (0.15, "MED", "Bottle service + status display"),
        "office_workers": (0.10, "LOW", "After-work Friday; but temporal mismatch"),
        "solo_diners": (0.05, "LOW", "Possible but socially stigmatized"),
        "working_women": (0.03, "LOW", "Safety concerns high"),
        "families": (0.02, "LOW", "Structurally anti-fit; children not allowed"),
    },
    "gastropub": {
        "couples": (0.25, "HIGH", "Casual date + food + drinks; ambiance balance"),
        "college_kids": (0.20, "HIGH", "Social energy + food + drinks"),
        "office_workers": (0.15, "MED", "After-work social + dinner"),
        "premium": (0.15, "MED", "Craft beer + culinary experience = status signal"),
        "solo_diners": (0.10, "MED", "Bar counter + food = acceptable solo"),
        "families": (0.08, "LOW", "Possible early evening; alcohol focus anti-fit"),
        "working_women": (0.07, "LOW", "Safety + comfort variable"),
    },
    "lounge_bar": {
        "premium": (0.35, "HIGH", "Exclusivity + ambiance + status"),
        "couples": (0.25, "HIGH", "Intimacy + privacy + soft lighting"),
        "office_workers": (0.15, "MED", "Business entertaining"),
        "college_kids": (0.10, "MED", "Aspirational but price-sensitive"),
        "solo_diners": (0.08, "LOW", "Possible but lounge = social space"),
        "working_women": (0.05, "LOW", "Safety + comfort depends on management"),
        "families": (0.02, "LOW", "Structurally anti-fit"),
    },
    "cocktail_bar": {
        "premium": (0.40, "HIGH", "Craft cocktail = cultural capital + distinction"),
        "couples": (0.25, "HIGH", "Date night + sophistication"),
        "office_workers": (0.15, "MED", "After-work; business entertaining"),
        "college_kids": (0.10, "MED", "Aspirational; some penetration"),
        "solo_diners": (0.05, "LOW", "Possible but specialized"),
        "working_women": (0.03, "LOW", "Safety concerns"),
        "families": (0.02, "LOW", "Structurally anti-fit"),
    },
    "family_restaurant": {
        "families": (0.50, "HIGH", "Explicit positioning; kid-friendly + reliable"),
        "office_workers": (0.15, "MED", "Lunch thali; value + speed"),
        "couples": (0.10, "MED", "Possible but lacks intimacy"),
        "college_kids": (0.10, "MED", "Group meals; value for money"),
        "solo_diners": (0.08, "LOW", "Possible but family atmosphere = conspicuous"),
        "working_women": (0.05, "LOW", "Possible but not optimized"),
        "premium": (0.02, "LOW", "Status mismatch"),
    },
    "bistro": {
        "couples": (0.30, "HIGH", "Casual intimacy + European ambiance"),
        "office_workers": (0.20, "HIGH", "Business lunch + casual meetings"),
        "solo_diners": (0.15, "MED", "Counter seating + casual = acceptable solo"),
        "college_kids": (0.12, "MED", "Aspirational + affordable"),
        "premium": (0.10, "MED", "Culinary experience + cultural capital"),
        "families": (0.08, "LOW", "Possible but less kid-optimized"),
        "working_women": (0.05, "LOW", "Possible but variable safety"),
    },
    "brewpub": {
        "college_kids": (0.30, "HIGH", "Social energy + craft beer culture"),
        "couples": (0.20, "MED", "Casual dates + shared experience"),
        "office_workers": (0.15, "MED", "After-work social"),
        "premium": (0.15, "MED", "Craft = cultural capital"),
        "solo_diners": (0.10, "MED", "Bar counter solo normalized"),
        "families": (0.05, "LOW", "Possible daytime; alcohol focus anti-fit evening"),
        "working_women": (0.05, "LOW", "Safety variable"),
    },
    "coffee_shop": {
        "office_workers": (0.25, "HIGH", "Coffee meetings + remote work + quick lunch"),
        "solo_diners": (0.20, "HIGH", "Safe solo space; inconspicuousness"),
        "working_women": (0.20, "HIGH", "Comfort + safety; all-women staff emerging"),
        "college_kids": (0.15, "MED", "Study + hangout"),
        "couples": (0.10, "MED", "Casual coffee dates"),
        "families": (0.07, "LOW", "Possible but less preferred"),
        "premium": (0.03, "LOW", "Accessible, not exclusive"),
    },
    "restaurant": {
        "families": (0.25, "MED", "Generic = broad appeal; weekend meals"),
        "couples": (0.20, "MED", "Date nights + casual dining"),
        "office_workers": (0.15, "MED", "Lunch + business meals"),
        "college_kids": (0.12, "MED", "Group meals"),
        "solo_diners": (0.10, "MED", "Possible but variable"),
        "premium": (0.10, "MED", "Some upscale generic restaurants"),
        "working_women": (0.08, "LOW", "Variable fit"),
    },
    "sports_bar": {
        "college_kids": (0.30, "HIGH", "Social energy + group viewing"),
        "office_workers": (0.20, "HIGH", "After-work sports viewing"),
        "couples": (0.10, "MED", "Some shared sports interest"),
        "solo_diners": (0.10, "MED", "Bar counter solo normalized"),
        "premium": (0.10, "MED", "Premium sports bar = status"),
        "families": (0.10, "LOW", "Possible daytime; evening anti-fit"),
        "working_women": (0.10, "LOW", "Safety + interest variable"),
    },
    "hookah_bar": {
        "college_kids": (0.40, "HIGH", "Social energy + group ritual"),
        "couples": (0.15, "MED", "Some casual dates"),
        "office_workers": (0.15, "MED", "After-work social"),
        "solo_diners": (0.10, "LOW", "Possible but group-oriented"),
        "premium": (0.10, "LOW", "Variable positioning"),
        "families": (0.05, "LOW", "Anti-fit; health concerns"),
        "working_women": (0.05, "LOW", "Safety + health concerns"),
    },
    "bakery": {
        "solo_diners": (0.25, "HIGH", "Quick + inconspicuous + proper service"),
        "office_workers": (0.20, "HIGH", "Quick snack + coffee"),
        "families": (0.15, "MED", "Weekend treats + celebrations"),
        "college_kids": (0.15, "MED", "Affordable treats"),
        "working_women": (0.10, "MED", "Safe + comfortable"),
        "couples": (0.10, "LOW", "Casual but less intimate"),
        "premium": (0.05, "LOW", "Accessible, not exclusive"),
    },
    "dessert_shop": {
        "couples": (0.30, "HIGH", "Date night + shared indulgence"),
        "college_kids": (0.25, "HIGH", "Social treat + affordable"),
        "families": (0.15, "MED", "Weekend treats"),
        "solo_diners": (0.10, "MED", "Possible but indulgence = social"),
        "office_workers": (0.10, "MED", "Quick treat"),
        "working_women": (0.05, "LOW", "Possible"),
        "premium": (0.05, "LOW", "Accessible"),
    },
    "brunch_restaurant": {
        "couples": (0.30, "HIGH", "Leisurely date + weekend ritual"),
        "families": (0.25, "HIGH", "Weekend family ritual"),
        "premium": (0.15, "MED", "Brunch = cultural capital"),
        "college_kids": (0.10, "MED", "Weekend social"),
        "office_workers": (0.10, "MED", "Weekend leisure"),
        "working_women": (0.05, "LOW", "Possible"),
        "solo_diners": (0.05, "LOW", "Possible but social ritual"),
    },
    "buffet_restaurant": {
        "families": (0.35, "HIGH", "Value + variety + kid-friendly"),
        "office_workers": (0.20, "HIGH", "Lunch buffet = speed + value"),
        "college_kids": (0.15, "MED", "Group meals + value"),
        "couples": (0.10, "MED", "Some casual dates"),
        "solo_diners": (0.10, "MED", "Possible but conspicuous"),
        "premium": (0.05, "LOW", "Status mismatch; buffet = abundance, not exclusivity"),
        "working_women": (0.05, "LOW", "Possible but not optimized"),
    },
    "bar_and_grill": {
        "couples": (0.25, "HIGH", "Casual date + food + drinks"),
        "college_kids": (0.20, "HIGH", "Social energy + food + drinks"),
        "office_workers": (0.15, "MED", "After-work social + dinner"),
        "families": (0.12, "MED", "Early evening possible"),
        "solo_diners": (0.10, "MED", "Bar counter acceptable"),
        "premium": (0.10, "LOW", "Casual, not exclusive"),
        "working_women": (0.08, "LOW", "Variable"),
    }
}
