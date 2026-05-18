"""
011_load_demographics.py
Populates the 4 demographic bridge tables from Phase 1 India research.

Tables:
  1. demographic_segments             — 5 target segments
  2. demographic_archetype_mapping    — archetype prevalence per segment
  3. demographic_behavioral_alignment — which primitives matter per segment
  4. demographic_archetype_interventions — intervention tactics per segment×archetype

Source: PHASE_1_INDIA_BEHAVIORAL_RESEARCH.md + survey archetype analysis
Run after: 009_load_marketing_engine.py
"""

import json
import os
import sys
import psycopg2
import psycopg2.extras

sys.stdout.reconfigure(encoding='utf-8')

DB_CONFIG = {
    'host':     os.getenv('PG_HOST',     'localhost'),
    'port':     int(os.getenv('PG_PORT', 5432)),
    'dbname':   os.getenv('PG_DB',       'polynovea_module2'),
    'user':     os.getenv('PG_USER',     'polynovea_admin'),
    'password': os.getenv('PG_PASSWORD', ''),
    'sslmode':  'require',
}

# ─── 1. DEMOGRAPHIC SEGMENTS ────────────────────────────────────────────────

SEGMENTS = [
    {
        'segment_id':          'office_workers',
        'segment_name':        'Office Workers',
        'segment_description': (
            'Working professionals aged 25-40 visiting during lunch breaks '
            'or post-work. Price-sensitive but time-crunched. Respond strongly '
            'to habit formation — same venue, same time, frictionless execution. '
            'WhatsApp reminders with first-name personalisation convert best.'
        ),
        'age_range':           '25-40',
        'company_size_range':  'SME to large corporate (10-500+)',
        'visit_when':          'Weekday lunch (12-2pm) + after-work (6-8pm)',
        'area':                'BKC, Andheri, Powai, Vashi, Thane industrial zones',
    },
    {
        'segment_id':          'college_kids',
        'segment_name':        'College Students',
        'segment_description': (
            'Students aged 18-24 visiting on weekends and evenings in groups. '
            'Budget-conscious but experience-driven — will spend on the right vibe. '
            'Respond to FOMO/scarcity and social proof (Instagram UGC). '
            'TikTok/Reels have 6.5x engagement uplift for this segment. '
            'Peer recommendation is the #1 discovery channel.'
        ),
        'age_range':           '18-24',
        'company_size_range':  'Student',
        'visit_when':          'Weekends + weekday evenings (7-11pm)',
        'area':                'Dadar, Andheri West, Vile Parle, Navi Mumbai campuses',
    },
    {
        'segment_id':          'couples',
        'segment_name':        'Couples & Date Nights',
        'segment_description': (
            'Pairs aged 23-38 visiting on weekends for special occasions or '
            'regular date nights. Quality and ambience matter more than price. '
            'Respond to identity signaling — "a venue that defines your taste". '
            'Instagram-worthy aesthetics, curated music, and table-side service '
            'are key conversion levers. Zomato Gold / Dineout table bookings dominant.'
        ),
        'age_range':           '23-38',
        'company_size_range':  'Couple (2 pax)',
        'visit_when':          'Friday-Saturday evenings (7pm-midnight)',
        'area':                'Bandra, Colaba, Lower Parel, Powai lakeside',
    },
    {
        'segment_id':          'families',
        'segment_name':        'Families',
        'segment_description': (
            'Family groups aged 30-50 (parents) visiting on weekends and holidays. '
            'Value consistency, kid-friendly options, and predictable quality. '
            'Respond to social proof (ratings + reviews) and habit formation. '
            'Google Maps and Zomato ratings are primary discovery. '
            'WhatsApp family-group recommendations are highly influential.'
        ),
        'age_range':           '30-55 (parents), any (kids)',
        'company_size_range':  'Family group (3-6 pax)',
        'visit_when':          'Sunday afternoons (12-4pm), school holidays, festivities',
        'area':                'Mulund, Thane, Navi Mumbai suburbs, Powai',
    },
    {
        'segment_id':          'solo_diners',
        'segment_name':        'Solo Diners',
        'segment_description': (
            'Individual diners visiting alone — growing post-pandemic urban segment. '
            'Four sub-types documented by research: Enjoyers (comfort-seeking), '
            'Economical Diners (price-sensitive, 36.7% of solo diners), '
            'Socialisers (open to light interaction), Relaxers (solitude-seeking). '
            'Key drivers: comfortable seating for one, no social awkwardness, '
            'staff that does not make solo dining feel odd, laptop/reading-friendly ambience, '
            'quick but not rushed service. Respond strongly to operational quality '
            'and repeat habit signals — predictability reduces the friction of solo visits. '
            'confidence: VALIDATED — solo dining archetypes from published research '
            '(Malaysia-based with Indian ethnic representation; urban India trend supported '
            'by Zomato discovery and map-view usage patterns).'
        ),
        'age_range':           '22-45',
        'company_size_range':  'Individual (1 pax)',
        'visit_when':          'Weekday lunch + weekday dinner; any time',
        'area':                'BKC, Andheri, Lower Parel, Bandra — office/transit corridors',
    },
    {
        'segment_id':          'working_women',
        'segment_name':        'Working Women',
        'segment_description': (
            'Female professionals aged 24-40 visiting during lunch, post-work, or weekend '
            'brunch. Distinct from generic office workers: higher health-consciousness, '
            'stronger emphasis on safety and ambience, higher RTE (ready-to-eat) consumption, '
            'and group composition skews toward female-only or mixed professional groups. '
            'NRAI IFSR 2024 explicitly identifies increased women workforce participation as '
            'a key demand driver. Key drivers: healthy menu options, well-lit and safe environment, '
            'good parking or cab access, staff that does not make them uncomfortable. '
            'Respond strongly to Instagram discovery and peer recommendations. '
            'confidence: INFERRED — segment existence validated by NRAI 2024 and '
            'Velocity MR (women consume more RTE than men in Indian metros); '
            'specific behavioral weights are working hypotheses.'
        ),
        'age_range':           '24-40',
        'company_size_range':  'Individual to small group (1-4 pax)',
        'visit_when':          'Weekday lunch (12-2pm) + weekday post-work (6-8pm) + weekend brunch',
        'area':                'BKC, Andheri, Powai, Lower Parel, Bandra',
    },
    {
        'segment_id':          'premium',
        'segment_name':        'Premium / High Income',
        'segment_description': (
            'High-income professionals and entrepreneurs aged 28-50. '
            'Destination dining — the venue itself is the occasion. '
            'Respond to identity signaling and environmental expectation: '
            '"a place that reflects my status and taste." '
            'Micro-influencer endorsements (50K-500K niche followers) outperform '
            'mass influencers. Word-of-mouth within premium social circles is key.'
        ),
        'age_range':           '28-50',
        'company_size_range':  'Entrepreneur / senior professional',
        'visit_when':          'Weekday dinners + weekend brunches',
        'area':                'Bandra, Colaba, Lower Parel, Worli, Juhu',
    },
]

# ─── 2. DEMOGRAPHIC → ARCHETYPE MAPPINGS ────────────────────────────────────
#
# confidence_level key:
#   VALIDATED   — behaviour pattern confirmed by published India F&B / Zomato / NRAI research
#   INFERRED    — consistent with documented behaviour but not directly measured for India dining
#   HYPOTHESIS  — working assumption; requires primary research to validate
#
# prevalence_percentage — internal model assumption; no published India source provides
# these exact splits. Treat as starting priors until venue-level data is available.

ARCHETYPE_MAPPINGS = [
    # Office Workers
    # Trusted Regular / Habit Former validated in principle by Zomato power-customer data (FY24)
    {'segment_id': 'office_workers', 'archetype_name': 'Trusted Regular',     'prevalence_percentage': 35.0, 'confidence_score': 0.82, 'confidence_level': 'VALIDATED'},
    {'segment_id': 'office_workers', 'archetype_name': 'Habit Former',        'prevalence_percentage': 28.0, 'confidence_score': 0.78, 'confidence_level': 'INFERRED'},
    {'segment_id': 'office_workers', 'archetype_name': 'Power Regular',       'prevalence_percentage': 17.0, 'confidence_score': 0.70, 'confidence_level': 'VALIDATED'},
    {'segment_id': 'office_workers', 'archetype_name': 'Calm Pairs',          'prevalence_percentage': 12.0, 'confidence_score': 0.65, 'confidence_level': 'HYPOTHESIS'},
    {'segment_id': 'office_workers', 'archetype_name': 'Discovery Explorer',  'prevalence_percentage':  8.0, 'confidence_score': 0.60, 'confidence_level': 'HYPOTHESIS'},

    # College Kids
    # Party Seeker / Scene Seeker supported by Swiggy Gen Z data (3x growth, social-led discovery)
    {'segment_id': 'college_kids', 'archetype_name': 'Party Seeker',          'prevalence_percentage': 38.0, 'confidence_score': 0.85, 'confidence_level': 'VALIDATED'},
    {'segment_id': 'college_kids', 'archetype_name': 'Scene Seeker',          'prevalence_percentage': 25.0, 'confidence_score': 0.80, 'confidence_level': 'VALIDATED'},
    {'segment_id': 'college_kids', 'archetype_name': 'Discovery Explorer',    'prevalence_percentage': 20.0, 'confidence_score': 0.72, 'confidence_level': 'INFERRED'},
    {'segment_id': 'college_kids', 'archetype_name': 'Trend Hunter',          'prevalence_percentage': 12.0, 'confidence_score': 0.68, 'confidence_level': 'INFERRED'},
    {'segment_id': 'college_kids', 'archetype_name': 'Lifestyle Regular',     'prevalence_percentage':  5.0, 'confidence_score': 0.55, 'confidence_level': 'HYPOTHESIS'},

    # Couples
    # Calm Pairs supported by fine-dining atmospherics research (PMC India); Lifestyle Regular inferred
    {'segment_id': 'couples', 'archetype_name': 'Calm Pairs',                 'prevalence_percentage': 40.0, 'confidence_score': 0.88, 'confidence_level': 'INFERRED'},
    {'segment_id': 'couples', 'archetype_name': 'Lifestyle Regular',          'prevalence_percentage': 25.0, 'confidence_score': 0.75, 'confidence_level': 'HYPOTHESIS'},
    {'segment_id': 'couples', 'archetype_name': 'Scene Seeker',               'prevalence_percentage': 20.0, 'confidence_score': 0.70, 'confidence_level': 'HYPOTHESIS'},
    {'segment_id': 'couples', 'archetype_name': 'Discovery Explorer',         'prevalence_percentage': 10.0, 'confidence_score': 0.65, 'confidence_level': 'HYPOTHESIS'},
    {'segment_id': 'couples', 'archetype_name': 'Trend Hunter',               'prevalence_percentage':  5.0, 'confidence_score': 0.55, 'confidence_level': 'HYPOTHESIS'},

    # Families
    # Trusted Regular validated (NRAI consistency / repeat-visit data); Habit Former inferred
    {'segment_id': 'families', 'archetype_name': 'Trusted Regular',           'prevalence_percentage': 45.0, 'confidence_score': 0.83, 'confidence_level': 'VALIDATED'},
    {'segment_id': 'families', 'archetype_name': 'Habit Former',              'prevalence_percentage': 30.0, 'confidence_score': 0.76, 'confidence_level': 'INFERRED'},
    {'segment_id': 'families', 'archetype_name': 'Calm Pairs',                'prevalence_percentage': 15.0, 'confidence_score': 0.65, 'confidence_level': 'HYPOTHESIS'},
    {'segment_id': 'families', 'archetype_name': 'Power Regular',             'prevalence_percentage': 10.0, 'confidence_score': 0.60, 'confidence_level': 'HYPOTHESIS'},

    # Solo Diners
    # Economical Diner validated (36.7% per solo dining research); others inferred
    {'segment_id': 'solo_diners', 'archetype_name': 'Quiet Discoverer',       'prevalence_percentage': 37.0, 'confidence_score': 0.78, 'confidence_level': 'VALIDATED'},
    {'segment_id': 'solo_diners', 'archetype_name': 'Trusted Regular',        'prevalence_percentage': 28.0, 'confidence_score': 0.72, 'confidence_level': 'INFERRED'},
    {'segment_id': 'solo_diners', 'archetype_name': 'Discovery Explorer',     'prevalence_percentage': 20.0, 'confidence_score': 0.65, 'confidence_level': 'INFERRED'},
    {'segment_id': 'solo_diners', 'archetype_name': 'Habit Former',           'prevalence_percentage': 15.0, 'confidence_score': 0.60, 'confidence_level': 'HYPOTHESIS'},

    # Working Women
    # Lifestyle Regular / Trusted Regular inferred; all prevalences are hypothesis
    {'segment_id': 'working_women', 'archetype_name': 'Lifestyle Regular',    'prevalence_percentage': 32.0, 'confidence_score': 0.68, 'confidence_level': 'INFERRED'},
    {'segment_id': 'working_women', 'archetype_name': 'Trusted Regular',      'prevalence_percentage': 28.0, 'confidence_score': 0.65, 'confidence_level': 'INFERRED'},
    {'segment_id': 'working_women', 'archetype_name': 'Discovery Explorer',   'prevalence_percentage': 22.0, 'confidence_score': 0.60, 'confidence_level': 'HYPOTHESIS'},
    {'segment_id': 'working_women', 'archetype_name': 'Calm Pairs',           'prevalence_percentage': 18.0, 'confidence_score': 0.58, 'confidence_level': 'HYPOTHESIS'},

    # Premium
    # Lifestyle Regular / Scene Seeker inferred from Zomato curated dining + identity-signal research
    {'segment_id': 'premium', 'archetype_name': 'Lifestyle Regular',          'prevalence_percentage': 35.0, 'confidence_score': 0.80, 'confidence_level': 'INFERRED'},
    {'segment_id': 'premium', 'archetype_name': 'Scene Seeker',               'prevalence_percentage': 28.0, 'confidence_score': 0.78, 'confidence_level': 'INFERRED'},
    {'segment_id': 'premium', 'archetype_name': 'Trend Hunter',               'prevalence_percentage': 22.0, 'confidence_score': 0.72, 'confidence_level': 'HYPOTHESIS'},
    {'segment_id': 'premium', 'archetype_name': 'Discovery Explorer',         'prevalence_percentage': 15.0, 'confidence_score': 0.68, 'confidence_level': 'HYPOTHESIS'},
]

# ─── 3. BEHAVIORAL ALIGNMENT (primitives that matter per segment) ────────────

BEHAVIORAL_ALIGNMENTS = [
    {
        'segment_id':    'office_workers',
        'archetype_name': 'Trusted Regular',
        'primary_primitives': json.dumps([
            'food_quality', 'service_speed', 'value_for_money',
            'consistency', 'cleanliness',
        ]),
        'secondary_primitives': json.dumps([
            'ambience', 'noise_level', 'seating_comfort',
        ]),
        'critical_fitness_dimension': 'fitness_for_office_lunch',
    },
    {
        'segment_id':    'office_workers',
        'archetype_name': 'Habit Former',
        'primary_primitives': json.dumps([
            'consistency', 'service_speed', 'value_for_money',
            'food_quality', 'familiarity',
        ]),
        'secondary_primitives': json.dumps([
            'loyalty_rewards', 'staff_recognition', 'queue_management',
        ]),
        'critical_fitness_dimension': 'fitness_for_repeat_habit',
    },
    {
        'segment_id':    'college_kids',
        'archetype_name': 'Party Seeker',
        'primary_primitives': json.dumps([
            'social_energy', 'music_quality', 'instagram_worthiness',
            'group_experience', 'event_programming',
        ]),
        'secondary_primitives': json.dumps([
            'value_for_money', 'crowd_vibe', 'bartender_skill',
        ]),
        'critical_fitness_dimension': 'fitness_for_group_energy',
    },
    {
        'segment_id':    'college_kids',
        'archetype_name': 'Scene Seeker',
        'primary_primitives': json.dumps([
            'crowd_vibe', 'instagram_worthiness', 'social_energy',
            'music_quality', 'discovery_appeal',
        ]),
        'secondary_primitives': json.dumps([
            'uniqueness', 'trend_relevance', 'staff_friendliness',
        ]),
        'critical_fitness_dimension': 'fitness_for_social_dwell',
    },
    {
        'segment_id':    'couples',
        'archetype_name': 'Calm Pairs',
        'primary_primitives': json.dumps([
            'ambience', 'noise_level', 'seating_comfort',
            'food_quality', 'service_quality',
        ]),
        'secondary_primitives': json.dumps([
            'lighting', 'music_quality', 'privacy', 'view_appeal',
        ]),
        'critical_fitness_dimension': 'fitness_for_destination_visit',
    },
    {
        'segment_id':    'couples',
        'archetype_name': 'Lifestyle Regular',
        'primary_primitives': json.dumps([
            'identity_signal', 'ambience', 'food_innovation',
            'service_quality', 'consistency',
        ]),
        'secondary_primitives': json.dumps([
            'wine_selection', 'chef_credibility', 'instagram_worthiness',
        ]),
        'critical_fitness_dimension': 'fitness_for_destination_visit',
    },
    {
        'segment_id':    'families',
        'archetype_name': 'Trusted Regular',
        'primary_primitives': json.dumps([
            'food_quality', 'consistency', 'kid_friendly',
            'cleanliness', 'value_for_money',
        ]),
        'secondary_primitives': json.dumps([
            'seating_comfort', 'service_speed', 'parking',
        ]),
        'critical_fitness_dimension': 'fitness_for_repeat_habit',
    },
    {
        'segment_id':    'premium',
        'archetype_name': 'Lifestyle Regular',
        'primary_primitives': json.dumps([
            'identity_signal', 'chef_credibility', 'food_innovation',
            'ambience', 'service_quality',
        ]),
        'secondary_primitives': json.dumps([
            'exclusivity', 'view_appeal', 'wine_selection', 'privacy',
        ]),
        'critical_fitness_dimension': 'fitness_for_destination_visit',
    },
    {
        'segment_id':    'premium',
        'archetype_name': 'Scene Seeker',
        'primary_primitives': json.dumps([
            'crowd_vibe', 'identity_signal', 'instagram_worthiness',
            'music_quality', 'exclusivity',
        ]),
        'secondary_primitives': json.dumps([
            'bartender_skill', 'event_programming', 'celebrity_factor',
        ]),
        'critical_fitness_dimension': 'fitness_for_social_dwell',
    },
]

# ─── 4. DEMOGRAPHIC × ARCHETYPE INTERVENTIONS ───────────────────────────────

INTERVENTIONS = [
    # Office Workers × Trusted Regular
    {
        'segment_id':        'office_workers',
        'archetype_name':    'Trusted Regular',
        'intervention_type': 'habit_loop_whatsapp',
        'description':       (
            'Send personalised WhatsApp reminder Tuesday–Thursday (optimal window for weekday '
            'lunch conversion; Friday evening for weekend dining). '
            '"Hey [Name], it\'s [Day] — your usual table is waiting. Quick 10-min walk from [area]." '
            'Include loyalty point balance if applicable. WhatsApp open rate: ~98% (Wapikit 2024). '
            'confidence: SEND-DAY validated (Richautomate / Dineopen 2026); '
            'personalisation uplift is a general WhatsApp engagement heuristic (~25–40% repeat '
            'purchase rate lift vs email — Wapikit 2024), not first-name-specific.'
        ),
        'expected_roi':      '25-40% repeat visit uplift over 6 weeks (general WhatsApp engagement; hypothesis for F&B-specific)',
    },
    {
        'segment_id':        'office_workers',
        'archetype_name':    'Trusted Regular',
        'intervention_type': 'loyalty_anchor',
        'description':       (
            'Introduce a simple stamp-card or digital loyalty tier. '
            'Goal: reward on visit 5 and visit 10 without discounting. '
            'Use recognition ("You\'re our Power Lunch regular") not discounts.'
        ),
        'expected_roi':      '40-50% increase in monthly visit frequency',
    },
    # College Kids × Party Seeker
    {
        'segment_id':        'college_kids',
        'archetype_name':    'Party Seeker',
        'intervention_type': 'scarcity_sms_blast',
        'description':       (
            'Friday 4pm SMS: "Tonight only — DJ [Name] + extended happy hour until 9pm. '
            'Only 40 spots. Book now: [link]" '
            'SMS 98% open rate with 2-4h conversion window. Authenticity critical — '
            'only send when genuinely limited capacity.'
        ),
        'expected_roi':      '30-45% same-day table fill on slow Fridays',
    },
    {
        'segment_id':        'college_kids',
        'archetype_name':    'Party Seeker',
        'intervention_type': 'ugc_instagram_reels',
        'description':       (
            'Partner with 3-5 micro-influencers (10K-100K, college niche). '
            'Brief: authentic Reels showing group experience, not ad-style content. '
            'Reels achieve 6.5x engagement uplift vs static posts for this segment. '
            'Amplify best-performing UGC as paid ads (lowest CPM).'
        ),
        'expected_roi':      '20-40% new customer acquisition from Instagram over 4 weeks',
    },
    # Couples × Calm Pairs
    {
        'segment_id':        'couples',
        'archetype_name':    'Calm Pairs',
        'intervention_type': 'zomato_premium_listing',
        'description':       (
            'Optimise Zomato/Swiggy listing: professional couple-ambience photos, '
            '"romantic setting" tags, 4.5+ rating maintenance. '
            'Activate Zomato Gold or Dineout table booking with exclusive 2-for-1 dessert. '
            'Platform algorithm boosts venues with high recent-review velocity.'
        ),
        'expected_roi':      '25-40% increase in weekend dinner covers via platform',
    },
    {
        'segment_id':        'couples',
        'archetype_name':    'Calm Pairs',
        'intervention_type': 'identity_email_sequence',
        'description':       (
            '3-email onboarding after first visit: '
            '1. "Welcome to [Venue] — you\'re the kind of person who..." (identity affirmation) '
            '2. Chef\'s story / sourcing narrative (aspirational signal) '
            '3. Exclusive invite to next tasting event (status reward). '
            'Email open rates 40-44% for this segment vs 85-95% WhatsApp — '
            'use email for brand-building, WhatsApp for time-sensitive offers.'
        ),
        'expected_roi':      '30-45% repeat visit rate within 60 days',
    },
    # Families × Trusted Regular
    {
        'segment_id':        'families',
        'archetype_name':    'Trusted Regular',
        'intervention_type': 'sunday_habit_whatsapp',
        'description':       (
            'Wednesday–Thursday WhatsApp to known family regulars: '
            '"This Sunday — [special] on the menu + kids eat free before 1pm. '
            'Your usual corner booth? Reply YES to reserve." '
            'Families plan 2-3 days ahead; Wednesday–Thursday window is directionally '
            'supported (Dineopen 2026) — A/B test send day by locality to confirm. '
            'confidence: HYPOTHESIS — Thursday-specifically not independently validated '
            'for India F&B; treat as starting point for experimentation.'
        ),
        'expected_roi':      '35-50% increase in Sunday family covers (hypothesis; validate with own campaign data)',
    },
    {
        'segment_id':        'families',
        'archetype_name':    'Trusted Regular',
        'intervention_type': 'rating_review_drive',
        'description':       (
            'Post-visit SMS (2h after check): '
            '"Hope the family enjoyed today! '
            'A quick Google/Zomato rating takes 30 seconds and helps us a lot: [link]" '
            'Family regulars are the highest-quality reviewers (4-5 star, detailed). '
            'Each fresh review within 7 days boosts algorithm placement.'
        ),
        'expected_roi':      '3-5 new 4.5+ star reviews per week; 15-25% discovery uplift',
    },
    # Premium × Lifestyle Regular
    {
        'segment_id':        'premium',
        'archetype_name':    'Lifestyle Regular',
        'intervention_type': 'micro_influencer_seeding',
        'description':       (
            'Host 2-3 invite-only dinners for micro-influencers (10K–100K, food/lifestyle niche). '
            'No script — authentic content only. Brief: "We want your honest experience." '
            'Micro-influencers (10K–50K) achieve 4–8% engagement rate; mid-tier (50K–500K) '
            'achieve 2–4% — both outperform macro (500K+) at 0.9–1.5% '
            '(Qoruz 2025; eMarketer 2025). One credible voice converts premium audiences '
            'better than 10 posts from mass influencers. '
            'confidence: PARTIALLY VALIDATED — engagement rate bands validated; '
            'F&B-specific CAC figure (₹85-150) is a single India case study.'
        ),
        'expected_roi':      '15-25% new premium customer acquisition over 6 weeks (hypothesis; single case study basis)',
    },
    {
        'segment_id':        'premium',
        'archetype_name':    'Lifestyle Regular',
        'intervention_type': 'exclusive_member_program',
        'description':       (
            'Create a named members table or priority reservation program. '
            '"[Venue] Insiders" — limited to 50 households. '
            'Benefits: priority booking, chef\'s table access, early event invites. '
            'No discounts. This is status, not savings. '
            'WhatsApp-only communication channel (not email — feels more personal).'
        ),
        'expected_roi':      '60-80% annual retention of premium regulars',
    },
]


# ─── LOADERS ────────────────────────────────────────────────────────────────

def load_segments(cursor) -> int:
    sql = """
        INSERT INTO demographic_segments
            (segment_id, segment_name, segment_description,
             age_range, company_size_range, visit_when, area)
        VALUES %s
        ON CONFLICT (segment_id) DO UPDATE SET
            segment_name        = EXCLUDED.segment_name,
            segment_description = EXCLUDED.segment_description,
            age_range           = EXCLUDED.age_range,
            company_size_range  = EXCLUDED.company_size_range,
            visit_when          = EXCLUDED.visit_when,
            area                = EXCLUDED.area;
    """
    rows = [
        (s['segment_id'], s['segment_name'], s['segment_description'],
         s['age_range'], s['company_size_range'], s['visit_when'], s['area'])
        for s in SEGMENTS
    ]
    psycopg2.extras.execute_values(cursor, sql, rows)
    return len(rows)


def load_archetype_mappings(cursor) -> int:
    # Add confidence_level column if it doesn't exist yet (safe to re-run)
    cursor.execute("""
        ALTER TABLE demographic_archetype_mapping
        ADD COLUMN IF NOT EXISTS confidence_level VARCHAR(20) DEFAULT 'HYPOTHESIS';
    """)
    sql = """
        INSERT INTO demographic_archetype_mapping
            (segment_id, archetype_name, prevalence_percentage, confidence_score, confidence_level)
        VALUES %s
        ON CONFLICT (segment_id, archetype_name) DO UPDATE SET
            prevalence_percentage = EXCLUDED.prevalence_percentage,
            confidence_score      = EXCLUDED.confidence_score,
            confidence_level      = EXCLUDED.confidence_level;
    """
    rows = [
        (m['segment_id'], m['archetype_name'],
         m['prevalence_percentage'], m['confidence_score'],
         m.get('confidence_level', 'HYPOTHESIS'))
        for m in ARCHETYPE_MAPPINGS
    ]
    psycopg2.extras.execute_values(cursor, sql, rows)
    return len(rows)


def load_behavioral_alignment(cursor) -> int:
    sql = """
        INSERT INTO demographic_behavioral_alignment
            (segment_id, archetype_name, primary_primitives,
             secondary_primitives, critical_fitness_dimension)
        VALUES %s
        ON CONFLICT (segment_id, archetype_name) DO UPDATE SET
            primary_primitives        = EXCLUDED.primary_primitives,
            secondary_primitives      = EXCLUDED.secondary_primitives,
            critical_fitness_dimension = EXCLUDED.critical_fitness_dimension;
    """
    rows = [
        (a['segment_id'], a['archetype_name'],
         a['primary_primitives'], a['secondary_primitives'],
         a['critical_fitness_dimension'])
        for a in BEHAVIORAL_ALIGNMENTS
    ]
    psycopg2.extras.execute_values(cursor, sql, rows)
    return len(rows)


def load_interventions(cursor) -> int:
    sql = """
        INSERT INTO demographic_archetype_interventions
            (segment_id, archetype_name, intervention_type,
             description, expected_roi)
        VALUES %s
        ON CONFLICT DO NOTHING;
    """
    rows = [
        (i['segment_id'], i['archetype_name'], i['intervention_type'],
         i['description'], i['expected_roi'])
        for i in INTERVENTIONS
    ]
    psycopg2.extras.execute_values(cursor, sql, rows)
    return len(rows)


# ─── MAIN ───────────────────────────────────────────────────────────────────

def main():
    print("\n011_load_demographics.py -- Phase 1 Demographic Segments & Archetype Mappings\n")

    conn   = psycopg2.connect(**DB_CONFIG)
    cursor = conn.cursor()

    try:
        print("  [1/4] demographic_segments ...")
        n = load_segments(cursor)
        print(f"        {n} segments loaded ({', '.join(s['segment_id'] for s in SEGMENTS)})")

        print("  [2/4] demographic_archetype_mapping ...")
        n = load_archetype_mappings(cursor)
        print(f"        {n} archetype mappings loaded")

        print("  [3/4] demographic_behavioral_alignment ...")
        n = load_behavioral_alignment(cursor)
        print(f"        {n} behavioral alignment rows loaded")

        print("  [4/4] demographic_archetype_interventions ...")
        n = load_interventions(cursor)
        print(f"        {n} intervention tactics loaded")

        conn.commit()
        print("\n" + "="*55)
        print("  DEMOGRAPHICS COMPLETE")
        print(f"  Segments     : {len(SEGMENTS)}")
        print(f"  Arc mappings : {len(ARCHETYPE_MAPPINGS)}")
        print(f"  Alignments   : {len(BEHAVIORAL_ALIGNMENTS)}")
        print(f"  Interventions: {len(INTERVENTIONS)}")
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
