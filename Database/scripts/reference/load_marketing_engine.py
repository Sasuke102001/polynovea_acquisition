"""
009_load_marketing_engine.py
Populates Phase 1 marketing engine lookup tables from India-specific research.

Tables populated (in dependency order):
  1. behavioral_mechanism_catalog  — 5 mechanisms (habit_formation, fomo, etc.)
  2. channel_mechanism_mapping     — channel × mechanism effectiveness matrix
  3. campaign_templates            — archetype × channel × message templates

Source: PHASE_1_INDIA_BEHAVIORAL_RESEARCH.md
Run after: 001_init_schema.sql
Run before: venue_marketing_recommendations (generated per-venue by the app)
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

# ---------------------------------------------------------------------------
# 1. BEHAVIORAL MECHANISM CATALOG
# ---------------------------------------------------------------------------

MECHANISMS = [
    {
        'mechanism_id': 'habit_formation',
        'name': 'Habit Formation',
        'description': (
            'Regular, timed reminders reinforce routine and anchor repeat visits. '
            'The mechanism works by pairing a contextual cue (day, time, occasion) '
            'with the venue — so over 4–8 weeks the cue alone triggers the visit. '
            'Most effective for office lunch regulars and weekend staples.'
        ),
        'psychological_basis': (
            'Habit loop theory (Duhigg): cue → routine → reward. '
            'Temporal self-appraisal theory supports time-anchored messaging. '
            'WhatsApp preferred over email in India due to ~98% vs 18-38% open rates '
            '(Wapikit 2024; Campaign Monitor / Constant Contact F&B benchmarks 2024). '
            'confidence: INFERRED — direction validated, exact open-rate gap is India-proxied.'
        ),
        'key_triggers': json.dumps([
            'Day-of-week reminder (e.g., "It\'s Friday — your usual spot is ready")',
            'Time-window message (sent 2–3 days before typical visit)',
            'Loyalty point redemption (reward the habit without discounting)',
            'Personalized name + dish reference (strengthens cue)',
        ]),
        'best_channels': json.dumps(['whatsapp', 'email', 'sms']),
        'best_archetypes': json.dumps(['Repeat Regulars', 'Trusted Regular', 'Habit Former', 'Power Regular']),
        'timeline_weeks': '4–8 weeks to establish; ongoing',
        'research_citations': (
            'Waakif WhatsApp Marketing Playbook for India Restaurants; '
            'Elephants Deli + Thanx case study (43% weekend brunch increase); '
            'SevenRooms email marketing guide'
        ),
    },
    {
        'mechanism_id': 'fomo_scarcity',
        'name': 'FOMO / Scarcity',
        'description': (
            'Time-limited or supply-limited signals create urgency that converts '
            'consideration into immediate booking. SMS delivers the fastest window '
            '(2–4 hours); WhatsApp event announcements work at 24–48 hours. '
            'Authenticity is critical — false scarcity erodes trust after 2–3 uses.'
        ),
        'psychological_basis': (
            'Scarcity heuristic (Cialdini): perceived rarity increases value. '
            'Loss aversion (Kahneman): framing as loss ("only 5 tables left") '
            'outperforms gain ("book now"). Countdown timers amplify urgency visually.'
        ),
        'key_triggers': json.dumps([
            'Real supply scarcity ("Only 5 tables left tonight")',
            'Time countdown ("Guest DJ in 2 hours")',
            'Event exclusivity ("Limited to 40 guests — first come first served")',
            'Flash offer ("Happy hour extended 30 min for this list only")',
        ]),
        'best_channels': json.dumps(['sms', 'whatsapp', 'instagram_stories']),
        'best_archetypes': json.dumps(['Party Seekers', 'Trend Hunter', 'Scene Seeker', 'Discovery Explorers']),
        'timeline_weeks': 'Immediate (2–4h SMS); 24–48h WhatsApp events',
        'research_citations': (
            'NOTE: SMS open rate is ~20% in India — WhatsApp outperforms SMS significantly '
            '(Wapikit 2024). The 98% figure was incorrect; removed. '
            '2–4h conversion window for SMS is unvalidated — treat as hypothesis. '
            'Spice Advisors Zomato/Swiggy ad campaign analysis; '
            'Punchh Cinco de Mayo case study (43% YoY lift). '
            'confidence: HYPOTHESIS for SMS timing; VALIDATED for WhatsApp superiority.'
        ),
    },
    {
        'mechanism_id': 'social_proof',
        'name': 'Social Proof',
        'description': (
            'Visible peer adoption reduces perceived risk and increases decision '
            'confidence. In India, Zomato/Swiggy platform ratings dominate discovery '
            'for casual dining. Instagram UGC (user-generated content) drives nightlife '
            'and social venue discovery. A 4.5+ star rating with recent photos '
            'materially lifts platform ranking.'
        ),
        'psychological_basis': (
            'Social proof heuristic (Cialdini): people follow others in uncertain situations. '
            'Review recency effect: last-7-days reviews weighted more by algorithms. '
            'Quantified social proof ("340 guests last week") amplifies effect.'
        ),
        'key_triggers': json.dumps([
            '4.5+ star rating on Zomato/Swiggy (algorithm ranking boost)',
            'Fresh reviews (within last 7 days)',
            'High-quality food/ambience photos on listing',
            'UGC carousel on Instagram (customer photos > brand photos)',
            '"X guests visited this week" count badge',
        ]),
        'best_channels': json.dumps(['zomato_swiggy', 'instagram_organic', 'google', 'facebook']),
        'best_archetypes': json.dumps(['Discovery Explorers', 'Calm Pairs', 'Scene Seeker', 'Lifestyle Regular']),
        'timeline_weeks': 'Ongoing; new reviews visible in 24–48h',
        'research_citations': (
            'Spice Advisors: Zomato/Swiggy ads (25–60% uplift with featured placement); '
            'Restromark Zomato algorithm analysis; '
            'Cuebiq location data (28.5% visit uplift from platform social proof); '
            'Reelo India retention benchmarks'
        ),
    },
    {
        'mechanism_id': 'identity_signaling',
        'name': 'Identity Signaling / Exclusivity',
        'description': (
            'Premium positioning attracts status-conscious customers who choose venues '
            'as a form of self-expression. Micro-influencers (5K–50K followers) '
            'outperform macro in trust; VIP WhatsApp lists convert at 12–18% for '
            'premium segments. Visual consistency across Instagram is the foundation.'
        ),
        'psychological_basis': (
            'Self-concept theory: people choose products/places that align with their '
            'desired identity. Aspirational social comparison: seeing desired-group '
            'members at a venue signals "this is where people like me go". '
            'Exclusivity framing ("VIP preview") outperforms discount framing.'
        ),
        'key_triggers': json.dumps([
            'Curated Instagram aesthetic (high-end photography, consistent palette)',
            'Micro-influencer authentic endorsement (5K–50K followers)',
            'VIP WhatsApp list ("exclusive previews for our guests")',
            'Exclusivity framing ("curated", "by invitation", "limited access")',
            'Status-signal positioning ("Mumbai\'s most Instagrammed venue")',
        ]),
        'best_channels': json.dumps(['instagram_organic', 'instagram_ads', 'micro_influencer', 'whatsapp']),
        'best_archetypes': json.dumps(['Premium Prioritizers', 'Calm Pairs', 'Trend Hunter']),
        'timeline_weeks': '2–4 weeks for influencer content; 4–16 weeks for full brand build',
        'research_citations': (
            'Level Up case study: micro-influencer CAC ₹85–150 per booking; '
            'BizzExpose case study (Bangalore bars); '
            'Meta/Instagram premium brand positioning guides'
        ),
    },
    {
        'mechanism_id': 'environmental_expectation',
        'name': 'Environmental Expectation',
        'description': (
            'Pre-visit imagery sets expectation and reduces the gap between imagined '
            'and actual experience. Instagram Reels reach 10–50x more accounts than static '
            'posts and generate ~2x the engagement rate (Meta 2025; Colorlib 2026) — '
            'note: the previously stated 6.5x figure was incorrect and has been removed. '
            'Zomato/Swiggy photo optimization overlaps with social proof and boosts '
            'algorithm ranking. YouTube Shorts is most effective for nightlife venues '
            'targeting 18–28 demographics in India (TikTok is banned).'
        ),
        'psychological_basis': (
            'Expectancy theory: motivation increases when outcome is clearly visualised. '
            'Pre-experience imagery (Pine & Gilmore experiential economy): customers '
            'buy the expected experience before arriving. '
            'Reduces post-visit cognitive dissonance — fewer negative reviews.'
        ),
        'key_triggers': json.dumps([
            'Instagram Reels showing ambience, food quality, crowd energy (Reels reach 10–50x more accounts than static; ~2x engagement rate — Meta 2025)',
            'Professional food + interior photography (updated within 30 days of menu changes)',
            'Zomato/Swiggy listing photos (fresh, high quality)',
            'YouTube Shorts behind-the-scenes (nightlife, DJ sets, kitchen tours) — TikTok banned in India',
            'User-generated photo aggregation on Instagram',
        ]),
        'best_channels': json.dumps(['instagram_organic', 'zomato_swiggy', 'youtube_shorts', 'instagram_ads']),
        'best_archetypes': json.dumps(['Calm Pairs', 'Discovery Explorers', 'Premium Prioritizers', 'Quiet Discoverer']),
        'timeline_weeks': '2–6 weeks for content accumulation and algorithm pickup',
        'research_citations': (
            'Meta/Instagram: Reels reach 10–50x more accounts than static; ~2x engagement rate '
            '(Colorlib 2026, Bill Feeds 2026) — the 6.5x engagement claim was incorrect and removed; '
            'YouTube Shorts (30% weekend walk-in uplift case study, India-applicable); '
            'Spice Advisors: Zomato photo optimisation drives algorithm ranking. '
            'confidence: PARTIALLY VALIDATED — reach multiplier validated, engagement multiplier proxied.'
        ),
    },
]

# ---------------------------------------------------------------------------
# 2. CHANNEL × MECHANISM MAPPING
# ---------------------------------------------------------------------------
# effectiveness_score: 1–10
# baseline_roi_lift: percentage points (e.g. 35 = +35%)
# primary_use_case: 'acquisition' | 'retention' | 'both'
# research_confidence: 'HIGH' | 'MEDIUM' | 'LOW'

CHANNEL_MAPPINGS = [
    # ── WhatsApp ─────────────────────────────────────────────
    {
        'channel': 'whatsapp',
        'behavioral_mechanism': 'habit_formation',
        'effectiveness_score': 10,
        'best_archetypes': json.dumps(['Repeat Regulars', 'Trusted Regular', 'Habit Former']),
        'baseline_roi_lift_min': 30.0,
        'baseline_roi_lift_max': 40.0,
        'primary_use_case': 'retention',
        'research_confidence': 'MEDIUM',
    },
    {
        'channel': 'whatsapp',
        'behavioral_mechanism': 'fomo_scarcity',
        'effectiveness_score': 8,
        'best_archetypes': json.dumps(['Party Seekers', 'Trend Hunter', 'Scene Seeker']),
        'baseline_roi_lift_min': 12.0,
        'baseline_roi_lift_max': 20.0,
        'primary_use_case': 'both',
        'research_confidence': 'MEDIUM',
    },
    {
        'channel': 'whatsapp',
        'behavioral_mechanism': 'identity_signaling',
        'effectiveness_score': 7,
        'best_archetypes': json.dumps(['Premium Prioritizers']),
        'baseline_roi_lift_min': 12.0,
        'baseline_roi_lift_max': 18.0,
        'primary_use_case': 'retention',
        'research_confidence': 'LOW',
    },
    # ── SMS ──────────────────────────────────────────────────
    {
        'channel': 'sms',
        'behavioral_mechanism': 'fomo_scarcity',
        'effectiveness_score': 9,
        'best_archetypes': json.dumps(['Party Seekers', 'Trend Hunter', 'Discovery Explorers']),
        'baseline_roi_lift_min': 15.0,
        'baseline_roi_lift_max': 25.0,
        'primary_use_case': 'both',
        'research_confidence': 'MEDIUM',
    },
    {
        'channel': 'sms',
        'behavioral_mechanism': 'habit_formation',
        'effectiveness_score': 5,
        'best_archetypes': json.dumps(['Repeat Regulars']),
        'baseline_roi_lift_min': 10.0,
        'baseline_roi_lift_max': 15.0,
        'primary_use_case': 'retention',
        'research_confidence': 'MEDIUM',
    },
    # ── Email ────────────────────────────────────────────────
    {
        'channel': 'email',
        'behavioral_mechanism': 'habit_formation',
        'effectiveness_score': 7,
        'best_archetypes': json.dumps(['Repeat Regulars', 'Trusted Regular', 'Habit Former']),
        'baseline_roi_lift_min': 15.0,
        'baseline_roi_lift_max': 25.0,
        'primary_use_case': 'retention',
        'research_confidence': 'LOW',
    },
    {
        'channel': 'email',
        'behavioral_mechanism': 'environmental_expectation',
        'effectiveness_score': 5,
        'best_archetypes': json.dumps(['Calm Pairs', 'Premium Prioritizers']),
        'baseline_roi_lift_min': 8.0,
        'baseline_roi_lift_max': 12.0,
        'primary_use_case': 'acquisition',
        'research_confidence': 'LOW',
    },
    {
        'channel': 'email',
        'behavioral_mechanism': 'social_proof',
        'effectiveness_score': 5,
        'best_archetypes': json.dumps(['Repeat Regulars', 'Discovery Explorers']),
        'baseline_roi_lift_min': 6.0,
        'baseline_roi_lift_max': 10.0,
        'primary_use_case': 'acquisition',
        'research_confidence': 'LOW',
    },
    # ── Instagram Organic ────────────────────────────────────
    {
        'channel': 'instagram_organic',
        'behavioral_mechanism': 'environmental_expectation',
        'effectiveness_score': 9,
        'best_archetypes': json.dumps(['Calm Pairs', 'Discovery Explorers', 'Quiet Discoverer']),
        'baseline_roi_lift_min': 15.0,
        'baseline_roi_lift_max': 25.0,
        'primary_use_case': 'acquisition',
        'research_confidence': 'MEDIUM',
    },
    {
        'channel': 'instagram_organic',
        'behavioral_mechanism': 'identity_signaling',
        'effectiveness_score': 8,
        'best_archetypes': json.dumps(['Premium Prioritizers', 'Trend Hunter', 'Calm Pairs']),
        'baseline_roi_lift_min': 10.0,
        'baseline_roi_lift_max': 15.0,
        'primary_use_case': 'acquisition',
        'research_confidence': 'MEDIUM',
    },
    {
        'channel': 'instagram_organic',
        'behavioral_mechanism': 'fomo_scarcity',
        'effectiveness_score': 7,
        'best_archetypes': json.dumps(['Party Seekers', 'Scene Seeker', 'Trend Hunter']),
        'baseline_roi_lift_min': 8.0,
        'baseline_roi_lift_max': 15.0,
        'primary_use_case': 'acquisition',
        'research_confidence': 'MEDIUM',
    },
    {
        'channel': 'instagram_organic',
        'behavioral_mechanism': 'social_proof',
        'effectiveness_score': 7,
        'best_archetypes': json.dumps(['Discovery Explorers', 'Calm Pairs']),
        'baseline_roi_lift_min': 8.0,
        'baseline_roi_lift_max': 12.0,
        'primary_use_case': 'acquisition',
        'research_confidence': 'MEDIUM',
    },
    # ── Instagram Ads ────────────────────────────────────────
    {
        'channel': 'instagram_ads',
        'behavioral_mechanism': 'environmental_expectation',
        'effectiveness_score': 8,
        'best_archetypes': json.dumps(['Calm Pairs', 'Premium Prioritizers', 'Discovery Explorers']),
        'baseline_roi_lift_min': 12.0,
        'baseline_roi_lift_max': 20.0,
        'primary_use_case': 'acquisition',
        'research_confidence': 'MEDIUM',
    },
    {
        'channel': 'instagram_ads',
        'behavioral_mechanism': 'identity_signaling',
        'effectiveness_score': 7,
        'best_archetypes': json.dumps(['Premium Prioritizers', 'Trend Hunter']),
        'baseline_roi_lift_min': 10.0,
        'baseline_roi_lift_max': 18.0,
        'primary_use_case': 'acquisition',
        'research_confidence': 'LOW',
    },
    # ── Zomato / Swiggy ──────────────────────────────────────
    {
        'channel': 'zomato_swiggy',
        'behavioral_mechanism': 'social_proof',
        'effectiveness_score': 9,
        'best_archetypes': json.dumps(['Discovery Explorers', 'Calm Pairs', 'Lifestyle Regular', 'Office Workers']),
        'baseline_roi_lift_min': 25.0,
        'baseline_roi_lift_max': 60.0,
        'primary_use_case': 'acquisition',
        'research_confidence': 'MEDIUM',
    },
    {
        'channel': 'zomato_swiggy',
        'behavioral_mechanism': 'environmental_expectation',
        'effectiveness_score': 8,
        'best_archetypes': json.dumps(['Discovery Explorers', 'Calm Pairs']),
        'baseline_roi_lift_min': 20.0,
        'baseline_roi_lift_max': 45.0,
        'primary_use_case': 'acquisition',
        'research_confidence': 'MEDIUM',
    },
    {
        'channel': 'zomato_swiggy',
        'behavioral_mechanism': 'fomo_scarcity',
        'effectiveness_score': 7,
        'best_archetypes': json.dumps(['Discovery Explorers', 'Party Seekers']),
        'baseline_roi_lift_min': 25.0,
        'baseline_roi_lift_max': 35.0,
        'primary_use_case': 'acquisition',
        'research_confidence': 'MEDIUM',
    },
    # ── YouTube Shorts (TikTok banned in India) ─────────────
    {
        'channel': 'tiktok',
        'behavioral_mechanism': 'environmental_expectation',
        'effectiveness_score': 7,
        'best_archetypes': json.dumps(['Party Seekers', 'Trend Hunter', 'Scene Seeker']),
        'baseline_roi_lift_min': 8.0,
        'baseline_roi_lift_max': 30.0,
        'primary_use_case': 'acquisition',
        'research_confidence': 'LOW',
    },
    {
        'channel': 'tiktok',
        'behavioral_mechanism': 'fomo_scarcity',
        'effectiveness_score': 6,
        'best_archetypes': json.dumps(['Party Seekers', 'Trend Hunter']),
        'baseline_roi_lift_min': 8.0,
        'baseline_roi_lift_max': 20.0,
        'primary_use_case': 'acquisition',
        'research_confidence': 'LOW',
    },
    {
        'channel': 'tiktok',
        'behavioral_mechanism': 'social_proof',
        'effectiveness_score': 6,
        'best_archetypes': json.dumps(['Party Seekers', 'Scene Seeker', 'Trend Hunter']),
        'baseline_roi_lift_min': 10.0,
        'baseline_roi_lift_max': 25.0,
        'primary_use_case': 'acquisition',
        'research_confidence': 'LOW',
    },
    # ── Facebook ──────────────────────────────────────────────
    {
        'channel': 'facebook',
        'behavioral_mechanism': 'social_proof',
        'effectiveness_score': 6,
        'best_archetypes': json.dumps(['Lifestyle Regular', 'Calm Pairs', 'Habit Former']),
        'baseline_roi_lift_min': 6.0,
        'baseline_roi_lift_max': 10.0,
        'primary_use_case': 'acquisition',
        'research_confidence': 'MEDIUM',
    },
    {
        'channel': 'facebook',
        'behavioral_mechanism': 'environmental_expectation',
        'effectiveness_score': 5,
        'best_archetypes': json.dumps(['Calm Pairs', 'Lifestyle Regular']),
        'baseline_roi_lift_min': 5.0,
        'baseline_roi_lift_max': 8.0,
        'primary_use_case': 'acquisition',
        'research_confidence': 'MEDIUM',
    },
    # ── Micro-influencer ─────────────────────────────────────
    {
        'channel': 'micro_influencer',
        'behavioral_mechanism': 'identity_signaling',
        'effectiveness_score': 8,
        'best_archetypes': json.dumps(['Premium Prioritizers', 'Trend Hunter', 'Calm Pairs']),
        'baseline_roi_lift_min': 20.0,
        'baseline_roi_lift_max': 40.0,
        'primary_use_case': 'acquisition',
        'research_confidence': 'LOW',
    },
    {
        'channel': 'micro_influencer',
        'behavioral_mechanism': 'social_proof',
        'effectiveness_score': 7,
        'best_archetypes': json.dumps(['Discovery Explorers', 'Scene Seeker']),
        'baseline_roi_lift_min': 15.0,
        'baseline_roi_lift_max': 30.0,
        'primary_use_case': 'acquisition',
        'research_confidence': 'LOW',
    },
    {
        'channel': 'micro_influencer',
        'behavioral_mechanism': 'environmental_expectation',
        'effectiveness_score': 7,
        'best_archetypes': json.dumps(['Calm Pairs', 'Premium Prioritizers', 'Discovery Explorers']),
        'baseline_roi_lift_min': 15.0,
        'baseline_roi_lift_max': 35.0,
        'primary_use_case': 'acquisition',
        'research_confidence': 'LOW',
    },
]

# ---------------------------------------------------------------------------
# 3. CAMPAIGN TEMPLATES
# ---------------------------------------------------------------------------

TEMPLATES = [
    # ── Office Workers (Lunch) → Repeat Regulars ─────────────
    {
        'demographic_segment': 'office_workers_lunch',
        'target_archetype': 'Repeat Regulars',
        'behavioral_mechanism': 'habit_formation',
        'channel': 'whatsapp',
        'message_template': (
            "Hi {{first_name}} 👋 It's {{day_of_week}} — your usual spot is ready.\n\n"
            "{{venue_name}} | {{area}}\n"
            "Book your table for lunch → {{booking_link}}\n\n"
            "See you at {{usual_time}}! 🍽️"
        ),
        'suggested_roi_lift_percentage': 35.0,
        'confidence_level': 'MEDIUM',
        'implementation_guide': (
            '1. Build WhatsApp broadcast list from repeat customer contacts (opt-in only).\n'
            '2. Segment by typical visit day (Mon-Fri lunch).\n'
            '3. Send Tuesday or Wednesday for Friday lunch bookings.\n'
            '4. Personalise with first name + typical visit time.\n'
            '5. Link directly to booking page — reduce friction.\n'
            '6. Cadence: weekly. Pause if customer books to avoid over-messaging.\n'
            'Expected: +30–40% repeat frequency within 90 days.'
        ),
    },
    {
        'demographic_segment': 'office_workers_lunch',
        'target_archetype': 'Repeat Regulars',
        'behavioral_mechanism': 'habit_formation',
        'channel': 'email',
        'message_template': (
            "Subject: Your Friday lunch table is waiting, {{first_name}}\n\n"
            "Hi {{first_name}},\n\n"
            "You've been coming to {{venue_name}} every {{visit_day}} — we wanted "
            "to make sure your favourite spot is ready for you this week.\n\n"
            "📍 {{venue_name}}, {{area}}\n"
            "🕐 {{usual_time}} | {{visit_day}}\n\n"
            "[Reserve My Table] → {{booking_link}}\n\n"
            "P.S. Your usual — {{favourite_item}} — is on today.\n\n"
            "See you soon,\nThe {{venue_name}} team"
        ),
        'suggested_roi_lift_percentage': 20.0,
        'confidence_level': 'LOW',
        'implementation_guide': (
            '1. Export repeat customer emails from POS or booking system.\n'
            '2. Segment customers who visited 3+ times in last 60 days.\n'
            '3. Send Thursday for following-week bookings.\n'
            '4. Subject line: personalise with name + day.\n'
            '5. Include favourite dish if available from order history.\n'
            'Expected: +15–25% repeat visits (slower build than WhatsApp).'
        ),
    },
    # ── Office Workers (Lunch) → Premium Prioritizers ─────────
    {
        'demographic_segment': 'office_workers_lunch',
        'target_archetype': 'Premium Prioritizers',
        'behavioral_mechanism': 'identity_signaling',
        'channel': 'whatsapp',
        'message_template': (
            "{{first_name}}, you're on our VIP lunch list 🥂\n\n"
            "This week at {{venue_name}}:\n"
            "✨ {{special_item}} — chef's limited preparation\n"
            "🪑 Reserved seating available for lunch until 1pm\n\n"
            "Confirm your table → {{booking_link}}\n\n"
            "Complimentary welcome drink on arrival."
        ),
        'suggested_roi_lift_percentage': 15.0,
        'confidence_level': 'LOW',
        'implementation_guide': (
            '1. Build VIP WhatsApp list separately from general broadcast.\n'
            '2. Invite customers who spend 30%+ above average ticket.\n'
            '3. Message 2x per week maximum — exclusivity requires restraint.\n'
            '4. Always include a tangible VIP benefit (priority seating, welcome item).\n'
            '5. Never use discount framing — use "curated" and "reserved" language.\n'
            'Expected: +12–18% conversion on VIP offers.'
        ),
    },
    # ── College Kids (Weekend) → Party Seekers ────────────────
    {
        'demographic_segment': 'college_kids_weekend',
        'target_archetype': 'Party Seekers',
        'behavioral_mechanism': 'fomo_scarcity',
        'channel': 'sms',
        'message_template': (
            "{{venue_name}}: Only 12 tables left for Saturday night 🔥 "
            "Guest DJ {{dj_name}} from 9pm. Book now before it sells out → {{booking_link}}"
        ),
        'suggested_roi_lift_percentage': 20.0,
        'confidence_level': 'MEDIUM',
        'implementation_guide': (
            '1. SMS must be 160 chars max — keep it tight.\n'
            '2. Send Thursday or Friday evening (6–9pm) for Saturday.\n'
            '3. Scarcity MUST be real — false table counts erode trust fast.\n'
            '4. Include specific event (DJ name, theme) not generic "special event".\n'
            '5. One CTA only: booking link. No social links.\n'
            '6. Max 2 SMS per week — any more triggers opt-outs.\n'
            'Expected: +15–25% same-weekend bookings.'
        ),
    },
    {
        'demographic_segment': 'college_kids_weekend',
        'target_archetype': 'Party Seekers',
        'behavioral_mechanism': 'fomo_scarcity',
        'channel': 'whatsapp',
        'message_template': (
            "🚨 THIS WEEKEND @ {{venue_name}}\n\n"
            "🎵 Live DJ — {{dj_name}}\n"
            "📅 {{event_date}} | Doors 9pm\n"
            "🪑 Only {{tables_left}} tables left — book in the next 24 hrs\n\n"
            "👉 {{booking_link}}\n\n"
            "⏰ Last year this sold out 6 hours before. Don't miss it."
        ),
        'suggested_roi_lift_percentage': 18.0,
        'confidence_level': 'MEDIUM',
        'implementation_guide': (
            '1. Send 48 hours before event (WhatsApp has 24–48h conversion window).\n'
            '2. Use real event details — specific DJ, real table count.\n'
            '3. Add social proof element ("last year sold out") if true.\n'
            '4. Follow up 12 hours before with final scarcity message to non-bookers.\n'
            'Expected: +12–20% event attendance.'
        ),
    },
    # ── College Kids (Weekend) → Discovery Explorers ──────────
    {
        'demographic_segment': 'college_kids_weekend',
        'target_archetype': 'Discovery Explorers',
        'behavioral_mechanism': 'environmental_expectation',
        'channel': 'instagram_organic',
        'message_template': (
            "We changed the menu. Again. 🌿\n\n"
            "{{new_item_1}}, {{new_item_2}}, and a dessert we're not ready to name yet.\n\n"
            "Come find out what's new this weekend → link in bio 🔗\n\n"
            "#{{venue_hashtag}} #NewMenu #{{area_hashtag}} #MumbaiEats"
        ),
        'suggested_roi_lift_percentage': 18.0,
        'confidence_level': 'MEDIUM',
        'implementation_guide': (
            '1. Post as Reel (not static) — 6.5x higher engagement on Reels.\n'
            '2. Show the actual dish being prepared or plated (process > product shot).\n'
            '3. Post Friday 6–9pm for peak discovery window.\n'
            '4. Use 3–5 local area hashtags + 2–3 food/mood hashtags.\n'
            '5. Booking link in bio — mention "link in bio" in caption.\n'
            '6. Post 3–4 Reels per week for sustained algorithm pickup.\n'
            'Expected: +15–25% new discovery engagement.'
        ),
    },
    # ── Couples / Date Nights → Calm Pairs ────────────────────
    {
        'demographic_segment': 'couples_date_nights',
        'target_archetype': 'Calm Pairs',
        'behavioral_mechanism': 'environmental_expectation',
        'channel': 'instagram_organic',
        'message_template': (
            "Some evenings deserve the right setting 🕯️\n\n"
            "Intimate tables, soft lighting, and food made to slow down for.\n\n"
            "{{venue_name}}, {{area}} — because not every dinner needs to be loud.\n\n"
            "Reserve your evening → link in bio\n\n"
            "#IntimateDate #MumbaiDate #{{venue_hashtag}} #QuietDining #{{area_hashtag}}"
        ),
        'suggested_roi_lift_percentage': 22.0,
        'confidence_level': 'MEDIUM',
        'implementation_guide': (
            '1. Reel format: show the atmosphere — candles, soft light, plated food.\n'
            '2. Avoid loud music in video — calm, ambient sound fits the archetype.\n'
            '3. Post Tuesday–Thursday (couple plans ahead, not impulse).\n'
            '4. Consistently portray the intimate, unhurried aesthetic — no crowd shots.\n'
            '5. UGC bonus: encourage couples to tag → reshare their photos (social proof).\n'
            'Expected: +20–35% new couple bookings over 4–12 weeks.'
        ),
    },
    {
        'demographic_segment': 'couples_date_nights',
        'target_archetype': 'Calm Pairs',
        'behavioral_mechanism': 'social_proof',
        'channel': 'zomato_swiggy',
        'message_template': (
            "Photo captions for listing: "
            "'Date night done right — intimate setting, exceptional food, zero rush. "
            "Our couples consistently rate us 4.8/5 for ambience. "
            "Book a table for two → {{booking_link}}'"
        ),
        'suggested_roi_lift_percentage': 30.0,
        'confidence_level': 'MEDIUM',
        'implementation_guide': (
            '1. Maintain 4.5+ star rating — respond to all reviews within 24 hours.\n'
            '2. Upload 5–8 professional photos: food, ambience, intimate table settings.\n'
            '3. Update photos within 30 days of any menu or decor change.\n'
            '4. Request reviews from satisfied couples (WhatsApp message post-visit).\n'
            '5. Tag "couple-friendly" and "good for dates" in listing attributes.\n'
            'Expected: +25–60% platform visibility uplift when featured.'
        ),
    },
    # ── Families (Casual) → Calm Pairs ────────────────────────
    {
        'demographic_segment': 'families_casual_dining',
        'target_archetype': 'Calm Pairs',
        'behavioral_mechanism': 'social_proof',
        'channel': 'facebook',
        'message_template': (
            "Where does {{area}} go for a relaxed family lunch? 🏠\n\n"
            "{{venue_name}} — comfortable seating, a menu for everyone, "
            "and a team that genuinely looks after you.\n\n"
            "📍 {{area}} | ⭐ {{rating}}/5 from {{review_count}} families\n\n"
            "Book this weekend → {{booking_link}}"
        ),
        'suggested_roi_lift_percentage': 8.0,
        'confidence_level': 'MEDIUM',
        'implementation_guide': (
            '1. Facebook targets 35+ demographic well — right fit for family segment.\n'
            '2. Boost posts with neighbourhood targeting (2–5km radius).\n'
            '3. Include real ratings and review counts in copy.\n'
            '4. Post Saturday morning (families plan weekend lunch same-day).\n'
            '5. Use family-friendly imagery — groups at table, not couples or solo.\n'
            'Expected: +6–10% awareness in family segment.'
        ),
    },
    # ── Families → Discovery Explorers ────────────────────────
    {
        'demographic_segment': 'families_casual_dining',
        'target_archetype': 'Discovery Explorers',
        'behavioral_mechanism': 'environmental_expectation',
        'channel': 'instagram_organic',
        'message_template': (
            "Introducing: {{new_menu_item}} 🍜\n\n"
            "Our chef's latest addition — inspired by {{ingredient_origin}}. "
            "Available this weekend only to start.\n\n"
            "Come try something genuinely new at {{venue_name}}, {{area}}.\n\n"
            "#NewDish #{{area_hashtag}} #MumbaiFood #FamilyDining #{{venue_hashtag}}"
        ),
        'suggested_roi_lift_percentage': 15.0,
        'confidence_level': 'MEDIUM',
        'implementation_guide': (
            '1. Discovery Explorers respond to novelty — always lead with what\'s new.\n'
            '2. Authenticity matters: show real ingredients, real prep process.\n'
            '3. "Available this weekend only" creates soft scarcity without hard FOMO.\n'
            '4. Reel format: show preparation process (not just final dish).\n'
            'Expected: +12–18% new customer discovery engagement.'
        ),
    },
    # ── Premium High-Income → Premium Prioritizers ────────────
    {
        'demographic_segment': 'premium_high_income',
        'target_archetype': 'Premium Prioritizers',
        'behavioral_mechanism': 'identity_signaling',
        'channel': 'micro_influencer',
        'message_template': (
            "Creator brief (5K–50K followers, food/lifestyle niche):\n\n"
            "We'd love to host you at {{venue_name}} for a private dining experience.\n"
            "No script — just visit, eat, and share what you genuinely experience.\n\n"
            "We're looking for authentic creators who appreciate: {{venue_key_strength_1}}, "
            "{{venue_key_strength_2}}, and unhurried hospitality.\n\n"
            "DM us to arrange your evening. Table for two, on us."
        ),
        'suggested_roi_lift_percentage': 30.0,
        'confidence_level': 'LOW',
        'implementation_guide': (
            '1. Target micro-creators (5K–50K followers) — higher trust than macro.\n'
            '2. Match audience: their followers should overlap with 28–40 premium segment.\n'
            '3. Never script the content — ask for genuine experience.\n'
            '4. Budget: ₹85–150 CAC per booking (food cost + creator fee if any).\n'
            '5. Start with 5 creators; measure bookings attributed before scaling.\n'
            '6. Track: follower → profile visit → DM/booking within 7 days.\n'
            'Expected: +20–40% bookings for 4-week pilot (case study range).'
        ),
    },
    {
        'demographic_segment': 'premium_high_income',
        'target_archetype': 'Premium Prioritizers',
        'behavioral_mechanism': 'identity_signaling',
        'channel': 'instagram_organic',
        'message_template': (
            "Not everything on our menu is listed. 🖤\n\n"
            "Chef's table — 6 courses, 8 guests, one evening a week.\n"
            "Enquire via DM or {{booking_link}}\n\n"
            "#ChefTable #{{venue_hashtag}} #MumbaiFineFood #ExclusiveDining"
        ),
        'suggested_roi_lift_percentage': 15.0,
        'confidence_level': 'LOW',
        'implementation_guide': (
            '1. Premium aesthetic: dark background, minimal text, high-contrast food photography.\n'
            '2. Post at 7–9pm when premium demographic is most active.\n'
            '3. Exclusivity framing: "not listed", "enquire via DM", "limited seats".\n'
            '4. Maintain consistent aesthetic — no inconsistent casual posts on this account.\n'
            'Expected: +10–15% premium customer awareness.'
        ),
    },
    # ── Generic: Any venue → Discovery Explorers (new menu) ───
    {
        'demographic_segment': None,
        'target_archetype': 'Discovery Explorers',
        'behavioral_mechanism': 'environmental_expectation',
        'channel': 'zomato_swiggy',
        'message_template': (
            "Listing update copy:\n"
            "'New this season: {{seasonal_items}}. "
            "We update our menu every 6–8 weeks — there\'s always something to discover. "
            "Photos updated {{photo_date}}. Book a table → {{booking_link}}'"
        ),
        'suggested_roi_lift_percentage': 20.0,
        'confidence_level': 'MEDIUM',
        'implementation_guide': (
            '1. Update Zomato/Swiggy listing every time menu changes (within 24 hours).\n'
            '2. Add 2–3 new photos with each menu update.\n'
            '3. Keep listing description current — stale descriptions hurt ranking.\n'
            '4. Tag "new menu" and "seasonal" keywords where available on platform.\n'
            'Expected: +20–40% platform ranking improvement for discovery searches.'
        ),
    },
]

# ---------------------------------------------------------------------------
# SQL Statements
# ---------------------------------------------------------------------------

MECHANISM_SQL = """
    INSERT INTO behavioral_mechanism_catalog
        (mechanism_id, name, description, psychological_basis,
         key_triggers, best_channels, best_archetypes, timeline_weeks, research_citations)
    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
    ON CONFLICT (mechanism_id) DO UPDATE SET
        name                = EXCLUDED.name,
        description         = EXCLUDED.description,
        psychological_basis = EXCLUDED.psychological_basis,
        key_triggers        = EXCLUDED.key_triggers,
        best_channels       = EXCLUDED.best_channels,
        best_archetypes     = EXCLUDED.best_archetypes,
        timeline_weeks      = EXCLUDED.timeline_weeks,
        research_citations  = EXCLUDED.research_citations;
"""

CHANNEL_SQL = """
    INSERT INTO channel_mechanism_mapping
        (channel, behavioral_mechanism, effectiveness_score, best_archetypes,
         baseline_roi_lift_min, baseline_roi_lift_max, primary_use_case, research_confidence)
    VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
    ON CONFLICT (channel, behavioral_mechanism) DO UPDATE SET
        effectiveness_score   = EXCLUDED.effectiveness_score,
        best_archetypes       = EXCLUDED.best_archetypes,
        baseline_roi_lift_min = EXCLUDED.baseline_roi_lift_min,
        baseline_roi_lift_max = EXCLUDED.baseline_roi_lift_max,
        primary_use_case      = EXCLUDED.primary_use_case,
        research_confidence   = EXCLUDED.research_confidence;
"""

TEMPLATE_SQL = """
    INSERT INTO campaign_templates
        (demographic_segment, target_archetype, behavioral_mechanism, channel,
         message_template, suggested_roi_lift_percentage, confidence_level, implementation_guide)
    VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
    ON CONFLICT DO NOTHING;
"""


# ---------------------------------------------------------------------------
# Loaders
# ---------------------------------------------------------------------------

def load_mechanisms(cursor) -> int:
    for m in MECHANISMS:
        cursor.execute(MECHANISM_SQL, (
            m['mechanism_id'], m['name'], m['description'],
            m['psychological_basis'], m['key_triggers'],
            m['best_channels'], m['best_archetypes'],
            m['timeline_weeks'], m['research_citations'],
        ))
    return len(MECHANISMS)


def load_channel_mappings(cursor) -> int:
    for cm in CHANNEL_MAPPINGS:
        cursor.execute(CHANNEL_SQL, (
            cm['channel'], cm['behavioral_mechanism'], cm['effectiveness_score'],
            cm['best_archetypes'], cm['baseline_roi_lift_min'], cm['baseline_roi_lift_max'],
            cm['primary_use_case'], cm['research_confidence'],
        ))
    return len(CHANNEL_MAPPINGS)


def load_templates(cursor) -> int:
    for t in TEMPLATES:
        cursor.execute(TEMPLATE_SQL, (
            t['demographic_segment'], t['target_archetype'], t['behavioral_mechanism'],
            t['channel'], t['message_template'], t['suggested_roi_lift_percentage'],
            t['confidence_level'], t['implementation_guide'],
        ))
    return len(TEMPLATES)


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main():
    print("\n009_load_marketing_engine.py -- Phase 1 Marketing Engine Lookup Tables\n")

    conn   = psycopg2.connect(**DB_CONFIG)
    cursor = conn.cursor()

    try:
        print("  [1/3] behavioral_mechanism_catalog ...")
        n_mech = load_mechanisms(cursor)
        print(f"        {n_mech} mechanisms loaded (habit_formation, fomo_scarcity, social_proof, "
              f"identity_signaling, environmental_expectation)")

        print("  [2/3] channel_mechanism_mapping ...")
        n_ch = load_channel_mappings(cursor)
        print(f"        {n_ch} channel × mechanism pairs loaded "
              f"(whatsapp, sms, email, instagram, zomato_swiggy, youtube_shorts, facebook, micro_influencer)")

        print("  [3/3] campaign_templates ...")
        n_tmpl = load_templates(cursor)
        print(f"        {n_tmpl} campaign templates loaded "
              f"(office workers, college kids, couples, families, premium segments)")

        conn.commit()
        print("\n" + "=" * 55)
        print("  MARKETING ENGINE COMPLETE")
        print(f"  Mechanisms     : {n_mech}")
        print(f"  Channel mappings: {n_ch}")
        print(f"  Templates      : {n_tmpl}")
        print("=" * 55)
        print("  Next step: Generate per-venue recommendations via")
        print("  GET /api/marketing/recommendations/{venue_id}")
        print("=" * 55 + "\n")

    except Exception as e:
        conn.rollback()
        print(f"\n[ERROR] {e}")
        raise
    finally:
        cursor.close()
        conn.close()


if __name__ == '__main__':
    main()
