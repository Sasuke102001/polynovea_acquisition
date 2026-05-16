-- =============================================================================
-- SEED: BEHAVIORAL MECHANISMS, CHANNEL BENCHMARKS, TRAIT→FITNESS WEIGHTS
-- Sources:
--   behavioral_acquisition_mechanisms_hospitality.md (academic backbone)
--   Behavioral Mechanisms and Channel Effectiveness in Hospitality Marketing.md
--   Indian_FB_Consumer_Segmentation_Validation_Report.md (corrections)
-- =============================================================================


-- ---------------------------------------------------------------------------
-- BEHAVIORAL MECHANISMS
-- ---------------------------------------------------------------------------

INSERT INTO behavioral_mechanisms (slug, label, category, psychological_logic, hospitality_context, operational_implication) VALUES

('social_proof',
 'Social Proof & Crowd Psychology',
 'social_influence',
 'Operates via two pathways: normative social influence (conforming to fit in) and informational social influence (assuming the crowd has superior quality information). Creates rational herding — crowd density is used as a proxy quality signal, especially under uncertainty. Cognitively efficient: observing density reduces search costs and deliberation effort.',
 'Visible queue formation functions as public quality signal. Window/crowd visibility allows crowd density to serve as ambient advertising. A bustling interior visible from the street triggers approach behavior. Table scarcity signaling increases perceived social value.',
 'Optimize for street-facing visibility and occupancy perception. Never seat all guests at back tables early in service. Stagger reservations to maintain apparent density. Consider crowd planting at soft openings.'),

('fomo',
 'FOMO & Anticipation Psychology',
 'scarcity_urgency',
 'Fear of Missing Out compresses decision timelines and bypasses rational deliberation. Mechanism: anticipated regret — individuals fear the emotional pain of missing an experience more than they anticipate the pleasure of attending. Aligns with loss aversion — missed experiences weighted ~2x more heavily than equivalent gains. Anticipation loops form when temporal distance creates progressive emotional buildup (weekday build toward Friday/Saturday peak).',
 'Flash reservation behavior from scarcity-perception triggers. Panic-driven attendance to avoid social exclusion. Last-minute table booking surge as capacity limits approach. Weekday emotional buildup toward weekend venue experiences.',
 'Scarcity messaging ("Only X spots left") converts at measurable rates (FOMO correlation index r=0.35 with purchase frequency). Weekend-specific FOMO campaigns outperform weekday. Time-limited offers exploit anticipation loops.'),

('identity_signaling',
 'Identity Signaling & Social Identity',
 'identity_status',
 'Venue selection functions as conspicuous consumption — performed publicly to signal social position, taste, and group affiliation. Veblen: individuals emulate consumption of higher-status groups. Bourdieu habitus: signals are often unconscious, generated through learned dispositions. Modern shift toward "inconspicuous consumption" (Currid-Halkett): cultural knowledge and experiential taste signal capital as much as economic capital.',
 '"Seen at" behavior: selecting venues where visibility to the right audience is maximized. Venue hierarchy navigation as social/financial capital changes. Aesthetic matching — choosing venues whose design, music, and clientele match self-concept. Premium identity behavior: paying above-market prices because the price filters the clientele.',
 'Positioning language should activate identity alignment, not just food quality. Segment-appropriate clientele mix is itself a marketing signal. Interior aesthetic and price point communicate who belongs here.'),

('habit_formation',
 'Habit Formation & Automaticity',
 'habit_automaticity',
 'Duhigg cue-routine-reward loop: habitual behavior is triggered by environmental cues, executed automatically, and reinforced by reward. Wood & Neal automaticity research: once habit is formed, deliberation is bypassed — behavior occurs without conscious decision. Path dependency: the first few experiences heavily determine future behavior patterns. Environmental stability is critical — changes to environment break habits.',
 'Regular patrons operate on cue-routine-reward: proximity (cue) → enter venue (routine) → satisfaction/familiarity (reward). Menu changes break habit loops. Same table, same server, same order are all habit-reinforcing signals.',
 'Retention strategy for habit-driven archetypes (Habit Former, Trusted Regular): minimize disruption, maximize environmental consistency. Loyalty programs that reinforce the cue-routine-reward loop outperform transactional discounts.'),

('environmental_expectation',
 'Environmental Expectation & Servicescape',
 'environmental',
 'Mehrabian & Russell SOR model: Stimulus (environment) → Organism (internal state: pleasure/arousal/dominance) → Response (approach/avoidance behavior). Bitner Servicescape: physical environment (ambient conditions, spatial layout, signs/symbols) shapes cognitive and emotional states, which drive behavior. Kotler Atmospherics: the designed sensory environment is a product in itself — atmosphere triggers purchase intent independently of food.',
 'Ambient conditions (music BPM, temperature, lighting) directly modulate dwell time and spend rate. High arousal environments (loud music, bright lighting) accelerate throughput but reduce per-cover spend quality. Low arousal environments (quiet, dim) increase dwell and premium ordering. Servicescape mismatch (premium food in low-quality environment) creates cognitive dissonance that depresses satisfaction scores.',
 'Circadian stimulus design: transition from high-energy lunch environment to lower-BPM intimate dinner atmosphere increases revenue per cover across dayparts. Match environmental expectations of primary segment to physical design.'),

('scarcity',
 'Scarcity & Commodity Theory',
 'scarcity_urgency',
 'Brock Commodity Theory (1968): items become more desirable as they become less available. Scarcity operates through two mechanisms — quantity scarcity ("only X left") and time scarcity ("only until Friday"). Combined with FOMO, creates urgency-pressure cascade. Social scarcity (visible competition for same resource: queue, waitlist) amplifies the effect because it adds social proof validation.',
 'Limited cocktail availability increases order rate. Waitlist signals elevate venue desirability perception. "Chef''s table" exclusivity commands premium pricing. Flash reservation windows create booking urgency. Limited-time menu items drive trial at higher price points.',
 'Ethical use: scarcity signals must be credible to maintain trust. Manufactured scarcity (claiming sold-out when not) damages long-term loyalty. Time-limited seasonal items are the highest-trust scarcity format.'),

('loss_aversion',
 'Loss Aversion & Prospect Theory',
 'loss_aversion',
 'Kahneman & Tversky Prospect Theory: losses are weighted approximately 2x more heavily than equivalent gains. This asymmetry means framing a message as "what you''ll lose by not coming" is more powerful than "what you''ll gain by coming." Regret theory (Loomes & Sugden): anticipated regret drives preventive action — buying insurance, booking early, attending events they''re unsure about.',
 'Membership/loyalty program framing as "don''t lose your points" outperforms "earn points." "Limited availability" messaging activates loss frame (seat you''ll lose) not gain frame (seat you''ll get). Re-engagement campaigns for lapsed guests: "We''ve missed you — your [loyalty tier] status expires soon" exploits loss aversion.',
 'Frame all retention messaging in loss terms: losing status, losing streak, losing access. Frame all acquisition messaging in gain terms: discovery, newness, first access. Test both framings systematically.'),

('cultural_capital',
 'Cultural Capital & Bourdieu Distinction',
 'cultural_capital',
 'Bourdieu: cultural capital (knowledge, skills, education, tastes) is accumulated and displayed through consumption choices. "Distinction" — individuals use consumption to differentiate from undesired social groups while affiliating with desired ones. Trickle-round effect: upper classes may adopt working-class aesthetics to outflank middle-class pretension. Food knowledge, wine literacy, and venue familiarity are all forms of cultural capital display.',
 'Premium segment and Lifestyle Regulars use venue choice to signal cultural capital (knowing the right chef, ordering correctly, navigating the menu with expertise). Staff who recognize and affirm cultural capital display generate significantly higher satisfaction and spend. "Insider knowledge" framing ("this is what the kitchen team drinks") activates cultural capital reward.',
 'Train staff to affirm guest expertise without being patronizing. "What you already know" framing beats "let me educate you." Menus with provenance stories and tasting notes provide cultural capital scaffolding for aspirational segments.');


-- ---------------------------------------------------------------------------
-- MECHANISM CITATIONS
-- ---------------------------------------------------------------------------

INSERT INTO mechanism_citations (mechanism_id, author, year, framework_name, core_claim, relevance) VALUES

-- Social Proof
((SELECT id FROM behavioral_mechanisms WHERE slug = 'social_proof'), 'Cialdini', 1984, 'Social Proof Theory', 'Individuals assume an action is correct if others are performing it, especially under ambiguity', 'Foundation of venue crowd-as-signal behavior'),
((SELECT id FROM behavioral_mechanisms WHERE slug = 'social_proof'), 'Deutsch & Gerard', 1955, 'Informational vs Normative Social Influence', 'Two distinct pathways: informational (crowd knows better) and normative (fit in)', 'Explains why both quality-seeking and belonging-seeking customers respond to crowd density'),
((SELECT id FROM behavioral_mechanisms WHERE slug = 'social_proof'), 'Banerjee', 1992, 'Rational Herding Theory', 'Individuals rationally ignore private information and follow the crowd when crowd signal is strong', 'Models venue selection under uncertainty in unfamiliar neighborhoods'),

-- FOMO
((SELECT id FROM behavioral_mechanisms WHERE slug = 'fomo'), 'Kahneman & Tversky', 1979, 'Prospect Theory / Loss Aversion', 'Losses weighted ~2x more than equivalent gains; missed experiences activate loss frame', 'FOMO is a loss-aversion manifestation applied to experiences'),
((SELECT id FROM behavioral_mechanisms WHERE slug = 'fomo'), 'Loomes & Sugden', 1982, 'Regret Theory', 'Anticipated regret drives preventive action even when expected utility is uncertain', 'Explains booking behavior driven by "don''t miss out" rather than "I really want to go"'),
((SELECT id FROM behavioral_mechanisms WHERE slug = 'fomo'), 'Holbrook & Hirschman', 1982, 'Hedonic Consumption Theory', 'Consumers seek emotional fulfillment and sensation; FOMO fuels sentimental urgency', 'Connects FOMO to hedonic motivation in nightlife/dining context'),

-- Identity Signaling
((SELECT id FROM behavioral_mechanisms WHERE slug = 'identity_signaling'), 'Veblen', 1899, 'Conspicuous Consumption', 'Consumption performed publicly to signal social position and pecuniary ability', 'Venue selection as social status signaling for Premium and Social Crowd segments'),
((SELECT id FROM behavioral_mechanisms WHERE slug = 'identity_signaling'), 'Bourdieu', 1984, 'Habitus & Cultural Capital', 'Learned dispositions generate identity signals unconsciously through taste and practice', 'Explains why identity signaling in venue selection feels natural, not performative'),
((SELECT id FROM behavioral_mechanisms WHERE slug = 'identity_signaling'), 'Currid-Halkett', 2017, 'Inconspicuous Consumption', 'Upper-income groups shift toward subtle signals (cultural knowledge, experiential taste) over overt luxury', 'Relevant for Premium Prioritizer and Lifestyle Regular archetypes'),

-- Habit Formation
((SELECT id FROM behavioral_mechanisms WHERE slug = 'habit_formation'), 'Duhigg', 2012, 'Cue-Routine-Reward Loop', 'Habits are triggered by environmental cues, executed automatically, and reinforced by reward; changing one element disrupts the loop', 'Models repeat-visit behavior for Habit Former and Trusted Regular archetypes'),
((SELECT id FROM behavioral_mechanisms WHERE slug = 'habit_formation'), 'Wood & Neal', 2007, 'Habit Automaticity', 'Once habit is formed, behavior occurs without conscious decision-making; environmental stability is critical', 'Explains why Habit Formers resist menu changes and venue redesigns'),

-- Environmental Expectation
((SELECT id FROM behavioral_mechanisms WHERE slug = 'environmental_expectation'), 'Mehrabian & Russell', 1974, 'Stimulus-Organism-Response (SOR) Model', 'Environment (S) triggers internal organism states (O: pleasure/arousal/dominance) that drive approach/avoidance behavior (R)', 'Foundation for environmental design as revenue lever'),
((SELECT id FROM behavioral_mechanisms WHERE slug = 'environmental_expectation'), 'Bitner', 1992, 'Servicescape', 'Physical environment shapes cognitive and emotional states; ambient conditions, spatial layout, and symbols all modulate behavior', 'Direct application to venue design for fitness_for_social_dwell and operational_quality scoring'),
((SELECT id FROM behavioral_mechanisms WHERE slug = 'environmental_expectation'), 'Kotler', 1973, 'Atmospherics', 'The designed sensory environment is a product; atmosphere triggers purchase intent independently of core product', 'Justifies investment in ambiance as a revenue-generating asset, not a cost center'),

-- Scarcity
((SELECT id FROM behavioral_mechanisms WHERE slug = 'scarcity'), 'Brock', 1968, 'Commodity Theory', 'Items become more desirable as they become less available; scarcity increases perceived value', 'Foundation for limited-menu items, chef''s table exclusivity, flash reservation windows'),
((SELECT id FROM behavioral_mechanisms WHERE slug = 'scarcity'), 'Cialdini', 1984, 'Scarcity Principle', 'Opportunities appear more valuable when their availability is limited; combines with social proof for maximum effect', 'Staff scripts for "only X left" upsell patterns'),

-- Loss Aversion
((SELECT id FROM behavioral_mechanisms WHERE slug = 'loss_aversion'), 'Kahneman & Tversky', 1979, 'Prospect Theory', 'The value function is steeper for losses than gains; framing effects are powerful and predictable', 'Retention messaging should use loss framing; acquisition messaging should use gain framing'),
((SELECT id FROM behavioral_mechanisms WHERE slug = 'loss_aversion'), 'Loomes & Sugden', 1982, 'Regret Theory', 'Anticipated regret drives preventive action; people will pay to avoid regret even at low expected utility', 'Loyalty program "expiry" messaging exploits loss aversion for re-engagement'),

-- Cultural Capital
((SELECT id FROM behavioral_mechanisms WHERE slug = 'cultural_capital'), 'Bourdieu', 1984, 'Distinction & Cultural Capital', 'Cultural knowledge and taste are accumulated as capital and displayed through consumption to signal class position', 'Menus with provenance stories, sommeliers, and staff expertise provide cultural capital scaffolding');


-- ---------------------------------------------------------------------------
-- MECHANISM SIGNALS
-- ---------------------------------------------------------------------------

INSERT INTO mechanism_signals (mechanism_id, signal_type, signal_text) VALUES
-- Social Proof — observable
((SELECT id FROM behavioral_mechanisms WHERE slug = 'social_proof'), 'observable', 'Pedestrian slowing or stopping when observing crowd density through windows'),
((SELECT id FROM behavioral_mechanisms WHERE slug = 'social_proof'), 'observable', 'Group members pointing toward crowded venues ("That place looks busy")'),
((SELECT id FROM behavioral_mechanisms WHERE slug = 'social_proof'), 'observable', 'Review language: "packed", "full", "crowded", "line out the door"'),
-- Social Proof — measurable
((SELECT id FROM behavioral_mechanisms WHERE slug = 'social_proof'), 'measurable', 'Passerby-to-entry conversion rate correlated with visible interior occupancy'),
((SELECT id FROM behavioral_mechanisms WHERE slug = 'social_proof'), 'measurable', 'Review frequency mentioning crowd density as quality signal'),

-- FOMO — observable
((SELECT id FROM behavioral_mechanisms WHERE slug = 'fomo'), 'observable', 'Rapid response to event/availability announcements (within minutes/hours)'),
((SELECT id FROM behavioral_mechanisms WHERE slug = 'fomo'), 'observable', 'Review language: "went before it closed", "finally got a table", "worth the wait"'),
((SELECT id FROM behavioral_mechanisms WHERE slug = 'fomo'), 'observable', 'Social media pre-posting of venue location to signal attendance intent'),
-- FOMO — measurable
((SELECT id FROM behavioral_mechanisms WHERE slug = 'fomo'), 'measurable', 'Announcement-to-booking latency: time between event announcement and first reservation'),
((SELECT id FROM behavioral_mechanisms WHERE slug = 'fomo'), 'measurable', 'Scarcity messaging urgency response rate (conversion from "Only X spots left")'),
((SELECT id FROM behavioral_mechanisms WHERE slug = 'fomo'), 'measurable', 'FOMO correlation index: r=0.35 between perceived scarcity and purchase frequency'),

-- Identity Signaling — observable
((SELECT id FROM behavioral_mechanisms WHERE slug = 'identity_signaling'), 'observable', 'Review language: "vibe", "crowd", "who goes here", "felt like I belonged"'),
((SELECT id FROM behavioral_mechanisms WHERE slug = 'identity_signaling'), 'observable', 'Outfit coordination with venue aesthetic before arrival'),
((SELECT id FROM behavioral_mechanisms WHERE slug = 'identity_signaling'), 'observable', 'Social media venue tagging with personal identity caption ("This is my kind of place")'),
-- Identity Signaling — measurable
((SELECT id FROM behavioral_mechanisms WHERE slug = 'identity_signaling'), 'measurable', 'Repeat visit rate segmented by clientele-mix congruence with guest self-concept'),
((SELECT id FROM behavioral_mechanisms WHERE slug = 'identity_signaling'), 'measurable', 'Price premium acceptance rate when venue is positioned as identity marker'),

-- Habit Formation — observable
((SELECT id FROM behavioral_mechanisms WHERE slug = 'habit_formation'), 'observable', 'Same order pattern across visits (trackable via POS history)'),
((SELECT id FROM behavioral_mechanisms WHERE slug = 'habit_formation'), 'observable', 'Review language: "my regular spot", "always come here for lunch", "never disappoints"'),
((SELECT id FROM behavioral_mechanisms WHERE slug = 'habit_formation'), 'observable', 'Time-of-day and day-of-week clustering in repeat visit patterns'),
-- Habit Formation — measurable
((SELECT id FROM behavioral_mechanisms WHERE slug = 'habit_formation'), 'measurable', 'Visit frequency and inter-visit interval consistency (coefficient of variation)'),
((SELECT id FROM behavioral_mechanisms WHERE slug = 'habit_formation'), 'measurable', 'Same-order rate across visits for identified repeat customers'),

-- Environmental Expectation — observable
((SELECT id FROM behavioral_mechanisms WHERE slug = 'environmental_expectation'), 'observable', 'Review language: "ambiance", "vibe", "atmosphere", "felt cozy/romantic/energetic"'),
((SELECT id FROM behavioral_mechanisms WHERE slug = 'environmental_expectation'), 'observable', 'Dwell time extension beyond food consumption (music, lighting driving stay)'),
-- Environmental Expectation — measurable
((SELECT id FROM behavioral_mechanisms WHERE slug = 'environmental_expectation'), 'measurable', 'Satisfaction score correlation with ambiance-related review terms'),
((SELECT id FROM behavioral_mechanisms WHERE slug = 'environmental_expectation'), 'measurable', 'Dwell time by table location (window vs interior, loud vs quiet zone)');


-- ---------------------------------------------------------------------------
-- CHANNEL BENCHMARKS
-- (Source: "Behavioral Mechanisms and Channel Effectiveness in Hospitality Marketing.md"
--  + Validation Report corrections applied)
-- ---------------------------------------------------------------------------

INSERT INTO channel_benchmarks (
    channel_key, label,
    open_rate_pct_min, open_rate_pct_max,
    repeat_visit_lift_pct,
    roi_multiplier_min, roi_multiplier_max,
    order_uplift_pct_min, order_uplift_pct_max,
    primary_effect,
    geographic_context, source_citation,
    is_validated, validation_notes
) VALUES

('whatsapp',
 'WhatsApp (Business Messaging)',
 85, 95,   -- 85-95% open rate — VALIDATED for India
 40,       -- 40% higher repeat visits
 3.0, 5.0, -- 3-5x ROI
 NULL, NULL,
 'Highest open rate of any digital channel in India; drives repeat visit behavior via personal framing',
 'india', 'Multiple India hospitality benchmarks 2024-25',
 TRUE, 'Validated: India WhatsApp open rate 85-95%. Original SMS 98% claim in system is WRONG — SMS open rate ~20%'),

('sms',
 'SMS',
 18, 22,   -- ~20% open rate — corrected from system claim of 98%
 NULL,
 1.0, 2.0,
 NULL, NULL,
 'Low open rate in India; overshadowed by WhatsApp for restaurant marketing',
 'india', 'Indian_FB_Consumer_Segmentation_Validation_Report.md — correction of system error',
 TRUE, 'CORRECTED: System claimed 98% SMS open rate. Validated value is ~20%. Do not use 98% in any marketing copy.'),

('zomato_swiggy_sponsored',
 'Zomato / Swiggy Sponsored Listings',
 NULL, NULL,
 NULL,
 NULL, NULL,
 25, 60,   -- 25-60% order uplift
 'Direct order volume uplift; highest intent-to-purchase channel (users already in purchase mode)',
 'india', 'Behavioral Mechanisms and Channel Effectiveness in Hospitality Marketing.md',
 TRUE, NULL),

('instagram_reels',
 'Instagram Reels',
 NULL, NULL,
 NULL,
 NULL, NULL,
 NULL, NULL,
 'Discovery channel; 2x engagement lift vs static posts; 10-50x reach vs feed; strong for Social Crowd and Working Women',
 'india', 'Indian_FB_Consumer_Segmentation_Validation_Report.md — corrected from 6.5x claim',
 TRUE, 'CORRECTED: System claimed 6.5x engagement. Validated: 2x engagement, 10-50x reach (reach ≠ engagement). Update all marketing copy.'),

('instagram_static',
 'Instagram Static / Carousel Posts',
 NULL, NULL,
 NULL,
 NULL, NULL,
 NULL, NULL,
 'Brand building and aesthetic signaling; lower reach than Reels but higher intent audience',
 'global', NULL,
 FALSE, NULL),

('email',
 'Email Marketing',
 20, 35,
 NULL,
 NULL, NULL,
 NULL, NULL,
 'Moderate open rate; useful for premium segments who check email; low India penetration for casual dining',
 'india', 'Behavioral Segmentation and Targeted Marketing for Hospitality Venues.md',
 FALSE, 'CAC ~$24 per acquisition (SevenRooms benchmark)'),

('micro_influencer',
 'Micro-Influencer (10K-50K followers)',
 NULL, NULL,
 NULL,
 NULL, NULL,
 NULL, NULL,
 'Highest engagement rate in influencer tier; strongest for niche identity segments',
 'india', 'Indian_FB_Consumer_Segmentation_Validation_Report.md — corrected range',
 TRUE, 'Engagement rate 4-8% for 10K-50K. CORRECTED: System used 4-7% for 50K-500K range which is WRONG (that range is 2-4%).'),

('macro_influencer',
 'Macro-Influencer (500K+ followers)',
 NULL, NULL,
 NULL,
 NULL, NULL,
 NULL, NULL,
 'High reach but low engagement; useful for launch/awareness; low for conversion',
 'india', NULL,
 FALSE, 'CAC ~$85 per acquisition (SevenRooms benchmark). Engagement rate 1-2%.'),

('google_search_ads',
 'Google Search Ads (Intent-based)',
 NULL, NULL,
 NULL,
 NULL, NULL,
 NULL, NULL,
 'High intent; captures "restaurants near me" queries; strong for Families and Office Workers (proximity-driven)',
 'india', NULL,
 FALSE, NULL),

('loyalty_program',
 'In-venue Loyalty Program',
 NULL, NULL,
 NULL,
 NULL, NULL,
 NULL, NULL,
 'Repeat guest worth 26x more than first-time guest over lifetime; 60% of revenue from repeat guests (industry average)',
 'india', 'Behavioral Mechanisms and Channel Effectiveness in Hospitality Marketing.md',
 TRUE, '77% of first-time guests never return. Repeat guests average 6.93 visits. India retention target: 60-70%, top performers 75-80%.');


-- ---------------------------------------------------------------------------
-- CHANNEL × SEGMENT EFFECTIVENESS
-- ---------------------------------------------------------------------------

INSERT INTO channel_segment_effectiveness (channel_id, segment_id, effectiveness_score, primary_use_case) VALUES

-- WhatsApp
((SELECT id FROM channel_benchmarks WHERE channel_key = 'whatsapp'),
 (SELECT id FROM segment_behavioral_profiles WHERE segment_key = 'office_workers'), 5, 'Lunch deals, weekday promos — high open rate converts to repeat lunch visits'),
((SELECT id FROM channel_benchmarks WHERE channel_key = 'whatsapp'),
 (SELECT id FROM segment_behavioral_profiles WHERE segment_key = 'families'), 5, 'Weekend family outing nudges, birthday reservation prompts'),
((SELECT id FROM channel_benchmarks WHERE channel_key = 'whatsapp'),
 (SELECT id FROM segment_behavioral_profiles WHERE segment_key = 'couples'), 4, 'Anniversary reminder, date night special promotions'),
((SELECT id FROM channel_benchmarks WHERE channel_key = 'whatsapp'),
 (SELECT id FROM segment_behavioral_profiles WHERE segment_key = 'college_kids'), 3, 'Event announcements; competes with Instagram for attention'),
((SELECT id FROM channel_benchmarks WHERE channel_key = 'whatsapp'),
 (SELECT id FROM segment_behavioral_profiles WHERE segment_key = 'working_women'), 4, 'After-work promos, girls-night announcements'),

-- Instagram Reels
((SELECT id FROM channel_benchmarks WHERE channel_key = 'instagram_reels'),
 (SELECT id FROM segment_behavioral_profiles WHERE segment_key = 'college_kids'), 5, 'Primary discovery channel; FOMO + social proof cascade'),
((SELECT id FROM channel_benchmarks WHERE channel_key = 'instagram_reels'),
 (SELECT id FROM segment_behavioral_profiles WHERE segment_key = 'working_women'), 5, 'Discovery; safety and ambiance signals via visual content'),
((SELECT id FROM channel_benchmarks WHERE channel_key = 'instagram_reels'),
 (SELECT id FROM segment_behavioral_profiles WHERE segment_key = 'couples'), 4, 'Date spot discovery; romantic ambiance showcasing'),
((SELECT id FROM channel_benchmarks WHERE channel_key = 'instagram_reels'),
 (SELECT id FROM segment_behavioral_profiles WHERE segment_key = 'office_workers'), 2, 'Low priority — office workers discover via Google Maps and colleagues'),

-- Zomato/Swiggy Sponsored
((SELECT id FROM channel_benchmarks WHERE channel_key = 'zomato_swiggy_sponsored'),
 (SELECT id FROM segment_behavioral_profiles WHERE segment_key = 'office_workers'), 5, 'Lunch ordering — highest intent channel for proximity-driven segment'),
((SELECT id FROM channel_benchmarks WHERE channel_key = 'zomato_swiggy_sponsored'),
 (SELECT id FROM segment_behavioral_profiles WHERE segment_key = 'families'), 4, 'Weekend discovery; families filter by kid-friendly on platform'),
((SELECT id FROM channel_benchmarks WHERE channel_key = 'zomato_swiggy_sponsored'),
 (SELECT id FROM segment_behavioral_profiles WHERE segment_key = 'solo_diners'), 5, 'Solo diners use Zomato as primary discovery + validation + booking'),

-- Loyalty Program
((SELECT id FROM channel_benchmarks WHERE channel_key = 'loyalty_program'),
 (SELECT id FROM segment_behavioral_profiles WHERE segment_key = 'office_workers'), 5, 'Habit reinforcement — cue-routine-reward loop amplification'),
((SELECT id FROM channel_benchmarks WHERE channel_key = 'loyalty_program'),
 (SELECT id FROM segment_behavioral_profiles WHERE segment_key = 'families'), 5, 'Sunday lunch tradition — loyalty program cements the habit'),
((SELECT id FROM channel_benchmarks WHERE channel_key = 'loyalty_program'),
 (SELECT id FROM segment_behavioral_profiles WHERE segment_key = 'college_kids'), 2, 'Low effectiveness — occasion-driven, venue loyalty is to the group not venue');


-- ---------------------------------------------------------------------------
-- TRAIT → FITNESS DIMENSION WEIGHTS
-- (Maps behavioral signals extracted from reviews to fitness dimensions)
-- ---------------------------------------------------------------------------

INSERT INTO trait_fitness_weights (trait_key, fitness_dimension, weight, rationale) VALUES

-- Social Proof signals → Social Dwell fitness
('crowd_density_signal',     'fitness_for_social_dwell',    0.800, 'Crowd density directly validates venue as social gathering space'),
('group_energy_signal',      'fitness_for_social_dwell',    0.750, 'Energetic group atmosphere is the primary social dwell indicator'),
('fomo_signal',              'fitness_for_social_dwell',    0.600, 'FOMO-generating venues attract occasion-driven social crowd'),
('identity_signal',          'fitness_for_social_dwell',    0.500, 'Status-signaling venues draw social groups using venue for identity expression'),

-- Habit signals → Repeat Habit fitness
('habit_signal',             'fitness_for_repeat_habit',    0.900, 'Explicit habit language in reviews is the strongest repeat predictor'),
('consistency_signal',       'fitness_for_repeat_habit',    0.750, 'Consistency of experience reduces switching cost'),
('proximity_signal',         'fitness_for_repeat_habit',    0.650, 'Office proximity drives 60-70% repeat rate within 30 days for office workers'),
('familiarity_signal',       'fitness_for_repeat_habit',    0.600, 'Staff recognition and "usual order" acknowledgment reinforce habit loop'),

-- Group energy signals → Group Energy fitness
('group_energy_signal',      'fitness_for_group_energy',    0.850, 'Group ordering patterns and energy level directly measure group fitness'),
('social_proof_signal',      'fitness_for_group_energy',    0.600, 'High social proof venues attract groups seeking validation from presence'),
('music_energy_signal',      'fitness_for_group_energy',    0.700, 'High BPM / energetic music environment drives group engagement'),

-- Destination signals → Destination Visit fitness
('fomo_signal',              'fitness_for_destination_visit', 0.800, 'FOMO content (waitlists, limited availability) marks venue as destination'),
('identity_signal',          'fitness_for_destination_visit', 0.700, 'Status-signaling venues are visited as destinations, not convenience'),
('quality_signal',           'fitness_for_destination_visit', 0.750, 'Explicit quality endorsements mark worth-the-trip perception'),
('scarcity_signal',          'fitness_for_destination_visit', 0.650, 'Limited availability elevates perceived destination value'),

-- Ambiance/environmental signals → Operational Quality
('ambiance_signal',          'operational_quality',         0.700, 'Ambiance quality is a primary component of operational excellence perception'),
('service_signal',           'operational_quality',         0.850, 'Service quality is the highest-weighted operational signal in reviews'),
('consistency_signal',       'operational_quality',         0.800, 'Operational consistency signals process excellence and reliability'),
('value_signal',             'operational_quality',         0.600, 'Perceived value-for-money reflects operational pricing discipline'),

-- Retention signals → Retention Strength
('habit_signal',             'retention_strength',          0.900, 'Habit language is the strongest retention predictor'),
('familiarity_signal',       'retention_strength',          0.800, 'Staff-guest familiarity signals retention through relationship capital'),
('loyalty_signal',           'retention_strength',          0.850, 'Explicit loyalty statements in reviews directly measure retention strength'),
('consistency_signal',       'retention_strength',          0.700, 'Consistent experience reduces churn risk'),

-- Office lunch signals
('quick_service_signal',     'fitness_for_office_lunch',    0.800, 'Speed of service is the #1 driver for office lunch fitness (60min diminishing returns)'),
('proximity_signal',         'fitness_for_office_lunch',    0.750, 'Proximity to office district drives 60-70% of office worker repeat behavior'),
('value_signal',             'fitness_for_office_lunch',    0.600, 'Value perception matters for daily repeat purchase decisions'),
('habit_signal',             'fitness_for_office_lunch',    0.700, 'Routine lunch spot language directly indicates office lunch fitness');


-- ---------------------------------------------------------------------------
-- RESEARCH VALIDATION FLAGS
-- (Known incorrect claims in the running system — from validation report)
-- ---------------------------------------------------------------------------

INSERT INTO research_validation_flags (
    entity_type, entity_key, field_name,
    claimed_value, validated_value,
    validation_source, is_corrected, correction_notes
) VALUES

('channel', 'sms', 'open_rate_pct',
 '98%', '~20%',
 'Indian_FB_Consumer_Segmentation_Validation_Report.md',
 FALSE,
 'System marketing copy uses 98% SMS open rate. Must be corrected to ~20% in all client-facing outputs. WhatsApp (85-95%) is the correct high-open-rate channel for India.'),

('channel', 'instagram_reels', 'engagement_multiplier',
 '6.5x engagement vs static',
 '2x engagement; 10-50x reach (reach ≠ engagement)',
 'Indian_FB_Consumer_Segmentation_Validation_Report.md',
 FALSE,
 'The 6.5x claim conflates reach with engagement. Reels do achieve 10-50x reach but only 2x engagement vs static. Marketing router must distinguish reach claims from engagement claims.'),

('channel', 'micro_influencer', 'engagement_rate_range',
 '4-7% for 50K-500K follower range',
 '2-4% for 50K-500K; 4-8% is the correct rate for 10K-50K range',
 'Indian_FB_Consumer_Segmentation_Validation_Report.md',
 FALSE,
 'Follower range definitions are inverted in system. Fix: micro (10K-50K) = 4-8% engagement; mid-tier (50K-500K) = 2-4% engagement.'),

('archetype', 'all_archetypes', 'india_validation_status',
 'Validated segments for Indian F&B market',
 'Internal constructs — no published Indian F&B research validates these specific archetype definitions',
 'Indian_FB_Consumer_Segmentation_Validation_Report.md',
 FALSE,
 'Archetypes are hypothesis-driven internal constructs. Fitness dimension weights are also hypothesis-driven, not empirically validated. This is acceptable for a v1 product but should be documented as such in client materials.');
