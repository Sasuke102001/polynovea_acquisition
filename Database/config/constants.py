"""
Constants Configuration for Polynovea Module 2
Links to primitives.json and defines API masks, keywords, and thresholds
"""

import json
import os

# Load primitives registry at runtime
PRIMITIVES_PATH = os.path.join(os.path.dirname(__file__), 'primitives.json')

def load_primitives():
    """Load primitives from JSON configuration"""
    try:
        with open(PRIMITIVES_PATH, 'r') as f:
            return json.load(f)
    except FileNotFoundError:
        raise FileNotFoundError(f"Primitives registry not found at {PRIMITIVES_PATH}")

# API Configuration
API_CONFIG = {
    'google_places': {
        'max_results': 100,
        'fields': ['name', 'types', 'place_id', 'geometry', 'formatted_address', 'rating', 'reviews'],
        'review_batch_size': 50
    },
    'zomato': {
        'max_results': 50,
        'fields': ['name', 'id', 'cuisines', 'rating', 'reviews']
    },
    'magicpin': {
        'max_results': 30,
        'fields': ['name', 'id', 'checkins', 'energy_level']
    }
}

# Primitive Signal Extraction Keywords (from primitives.json)
# These are example masks - actual values loaded from primitives.json
PRIMITIVE_KEYWORDS = {
    'food_quality': ['fresh', 'delicious', 'taste', 'flavor', 'quality', 'authentic'],
    'social_energy': ['lively', 'vibrant', 'energetic', 'buzzing', 'alive'],
    'service_speed': ['fast', 'quick', 'slow', 'wait', 'speedy', 'prompt'],
    'staff_warmth': ['friendly', 'warm', 'welcoming', 'hospitable', 'nice'],
    'ambience_comfortable': ['comfortable', 'cozy', 'relaxed', 'ease', 'cushy'],
    'cleanliness': ['clean', 'dirty', 'hygiene', 'spotless', 'neat'],
    'repeat_visits': ['again', 'repeat', 'came back', 'frequent', 'regular'],
    'sharing_moments': ['photo', 'instagram', 'share', 'pictures', 'capture'],
    'overall_satisfaction': ['satisfied', 'happy', 'pleased', 'content', 'rating']
}

# Confidence Score Thresholds (Source Quality)
CONFIDENCE_THRESHOLDS = {
    'google_places': {
        'min_confidence': 0.55,
        'avg_confidence': 0.664,
        'extraction_confidence_range': [0.4, 1.0]
    },
    'zomato': {
        'min_confidence': 0.50,
        'avg_confidence': 0.60,
        'extraction_confidence_range': [0.35, 1.0]
    },
    'magicpin': {
        'min_confidence': 0.45,
        'avg_confidence': 0.55,
        'extraction_confidence_range': [0.3, 1.0]
    }
}

# Data Quality Metrics Baseline (from governance report)
QUALITY_METRICS_BASELINE = {
    'avg_confidence_baseline': 0.664,
    'avg_reliability_baseline': 0.79,
    'reliability_score_baseline': 0.734,
    'high_reliability_threshold': 0.70,
    'min_venues_for_pattern': 3,
    'min_pattern_prevalence': 0.05  # 5% of market
}

# Recency Weighting (Amendment Logic - Phase 2 Ready)
TEMPORAL_FILTERS = {
    'half_life_days': 30,
    'exponential_decay_formula': 'weight = 0.5^(days_since_update / 30)',
    'max_age_days': 180,
    'weight_threshold': 0.1  # Don't use reviews older than this weight
}

# Fitness Dimensions Definition
FITNESS_DIMENSIONS = {
    'office_lunch': {
        'name': 'Office Lunch Fitness',
        'description': 'Quick meal convenience for business lunch',
        'key_factors': ['service_speed', 'value_for_money', 'location_accessibility']
    },
    'repeat_habit': {
        'name': 'Repeat Habit Fitness',
        'description': 'Loyalty and repeat visit potential',
        'key_factors': ['repeat_visits', 'loyalty', 'consistency']
    },
    'social_dwell': {
        'name': 'Social Dwell Fitness',
        'description': 'Group hanging out for extended periods',
        'key_factors': ['seating_comfort', 'seating_spacing', 'ambience_comfortable', 'dwell_time']
    },
    'group_energy': {
        'name': 'Group Energy Fitness',
        'description': 'Party and high-energy group events',
        'key_factors': ['social_energy', 'music_quality', 'ambience_energy', 'group_friendly']
    },
    'destination_visit': {
        'name': 'Destination Visit Fitness',
        'description': 'Venue as a planned destination experience',
        'key_factors': ['experience_memorable', 'experience_unique', 'view_appeal', 'special_occasions']
    }
}

# Surface Categories (from surface_categories.json)
VENUE_CATEGORIES = {
    'casual_dining': 'Casual dining - relaxed, informal',
    'premium_dining': 'Premium dining - high-end refined',
    'quick_service': 'Quick service - fast-casual, QSR',
    'cafe': 'Cafe - coffee, beverages, light snacks',
    'bar_lounge': 'Bar & Lounge - alcohol-focused',
    'buffet': 'Buffet - all-you-can-eat spread',
    'specialty': 'Specialty/Themed - niche experiences'
}

# Pattern Detection Thresholds
PATTERN_THRESHOLDS = {
    'min_cooccurrence_count': 3,  # Minimum venues showing pattern
    'min_confidence_score': 50,  # Confidence 50-100 scale
    'prevalence_threshold': 0.05,  # 5% of market minimum
    'drift_signal_threshold': 0.60  # 60% confidence for drift signals
}

# Behavioral Mechanism Catalog (Phase 1 Marketing)
BEHAVIORAL_MECHANISMS = {
    'habit_formation': {
        'description': 'Regular reminders reinforcing routine behavior',
        'best_channels': ['whatsapp', 'email', 'sms'],
        'expected_lift_min': 0.30,
        'expected_lift_max': 0.40,
        'timeline_weeks': '4-8'
    },
    'fomo': {
        'description': 'Fear of missing out / scarcity messaging',
        'best_channels': ['sms', 'whatsapp', 'push'],
        'expected_lift_min': 0.15,
        'expected_lift_max': 0.25,
        'timeline_weeks': '0.3-2'
    },
    'social_proof': {
        'description': 'Platform visibility, ratings, reviews',
        'best_channels': ['zomata', 'swiggy', 'google'],
        'expected_lift_min': 0.25,
        'expected_lift_max': 0.60,
        'timeline_weeks': '2-4'
    },
    'identity_signaling': {
        'description': 'Premium aesthetic, brand identity alignment',
        'best_channels': ['instagram', 'influencer'],
        'expected_lift_min': 0.12,
        'expected_lift_max': 0.18,
        'timeline_weeks': '4-16'
    },
    'environmental_expectation': {
        'description': 'Pre-visit imagery shaping visit expectations',
        'best_channels': ['instagram_reels', 'video'],
        'expected_lift_min': 0.15,
        'expected_lift_max': 0.25,
        'timeline_weeks': '4-12'
    }
}

# Channel Effectiveness Rankings (India-Specific Benchmarks)
CHANNEL_EFFECTIVENESS = {
    'whatsapp': {
        'open_rate': 0.90,  # 85-95%
        'primary_use': 'retention',
        'best_mechanisms': ['habit_formation'],
        'effectiveness_score': 9
    },
    'sms': {
        'open_rate': 0.98,  # 98%
        'primary_use': 'acquisition',
        'best_mechanisms': ['fomo'],
        'effectiveness_score': 8
    },
    'email': {
        'open_rate': 0.42,  # 40-44%
        'primary_use': 'retention',
        'best_mechanisms': ['habit_formation', 'content'],
        'effectiveness_score': 6
    },
    'instagram': {
        'open_rate': 0.35,
        'primary_use': 'acquisition',
        'best_mechanisms': ['identity_signaling', 'environmental_expectation'],
        'effectiveness_score': 7
    },
    'zomata_swiggy': {
        'open_rate': 0.60,
        'primary_use': 'acquisition',
        'best_mechanisms': ['social_proof'],
        'effectiveness_score': 8
    },
    'google_maps': {
        'open_rate': 0.50,
        'primary_use': 'acquisition',
        'best_mechanisms': ['social_proof'],
        'effectiveness_score': 7
    }
}

# Archetype Confidence Thresholds
ARCHETYPE_THRESHOLDS = {
    'min_confidence_assignment': 0.60,
    'high_confidence': 0.80,
    'total_archetypes': 35,
    'archetype_categories': [
        'Party Seeker', 'Discovery Explorer', 'Repeat Regular',
        'Premium Prioritizer', 'Calm Pairs', 'Convenience Seeker',
        'Social Butterfly', 'Family Focused', 'Experience Hunter',
        'Budget Conscious'  # And 25 more
    ]
}

# Demographic Segment Mapping
DEMOGRAPHIC_SEGMENTS = {
    'college_kids_weekend': {
        'age': '22-25',
        'company_size': '2-4',
        'when': 'weekends',
        'primary_archetype': 'Party Seeker'
    },
    'office_workers_lunch': {
        'age': '26-35',
        'company_size': '1-2',
        'when': 'weekdays_lunch',
        'primary_archetype': 'Repeat Regular'
    },
    'families_casual': {
        'age': 'all',
        'company_size': '2-6',
        'when': 'weekends',
        'primary_archetype': 'Calm Pairs'
    },
    'young_professionals': {
        'age': '26-35',
        'company_size': '1-4',
        'when': 'evenings',
        'primary_archetype': 'Premium Prioritizer'
    },
    'couples_dating': {
        'age': '22-40',
        'company_size': '2',
        'when': 'weekends_evenings',
        'primary_archetype': 'Experience Hunter'
    }
}

# Data Loading Batch Sizes
BATCH_SIZES = {
    'venue_load': 100,
    'primitive_scores_load': 500,
    'pattern_load': 50,
    'similarity_load': 200,
    'survey_load': 45
}

# Response Validation Constraints
VALIDATION_RULES = {
    'primitive_score_range': (0, 1),
    'confidence_range': (0, 1),
    'fitness_range': (0, 1),
    'max_primitives_per_venue': 54,
    'required_fields_venue': ['place_id', 'name', 'area', 'latitude', 'longitude'],
    'required_fields_primitive': ['venue_id', 'primitive_id', 'score', 'confidence'],
    'max_response_length': 10000
}

def get_primitive_keywords(primitive_id):
    """
    Get extraction keywords for a specific primitive.
    Falls back to primitives.json if not in PRIMITIVE_KEYWORDS
    """
    if primitive_id in PRIMITIVE_KEYWORDS:
        return PRIMITIVE_KEYWORDS[primitive_id]

    try:
        primitives = load_primitives()
        if primitive_id in primitives.get('primitives', {}):
            return primitives['primitives'][primitive_id].get('extraction_keywords', [])
    except Exception:
        pass

    return []

def validate_score(score, score_type='primitive'):
    """Validate score is within expected range"""
    min_val, max_val = VALIDATION_RULES['primitive_score_range']
    return min_val <= score <= max_val

def get_channel_roi_estimate(channel, mechanism):
    """Get ROI estimate for a channel-mechanism combination"""
    mechanism_data = BEHAVIORAL_MECHANISMS.get(mechanism, {})
    return {
        'channel': channel,
        'mechanism': mechanism,
        'lift_min': mechanism_data.get('expected_lift_min', 0),
        'lift_max': mechanism_data.get('expected_lift_max', 0),
        'timeline': mechanism_data.get('timeline_weeks', 'TBD')
    }
