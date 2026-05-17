-- =============================================================================
-- SEED: NEW ARCHETYPES + BENCHMARK CORRECTIONS
-- Sources:
--   archetype_segment_validation_kimi.md   (Kimi, 2026)
--   india_market_intelligence_perplexity.md (Perplexity, 2025-26)
-- =============================================================================


-- ---------------------------------------------------------------------------
-- NEW ARCHETYPES: SOCIAL BUTTERFLY + COMFORT DWELLER
-- ---------------------------------------------------------------------------
-- Both are INFERRED (not directly validated in F&B literature, but grounded
-- in nightlife/entertainment research and comfort-seeking consumer behavior).
-- Peer influence baseline per Herhausen et al. (Nature Communications, 2024):
--   Universal baseline = 0.142. Adjusted per archetype per Kimi validation.
-- ---------------------------------------------------------------------------

INSERT INTO archetype_behavioral_profiles (
    archetype_key, label, orientation,
    food_pct_min, food_pct_max,
    alcohol_pct_min, alcohol_pct_max,
    dessert_attach_pct_min, dessert_attach_pct_max,
    avg_check_vs_baseline_pct_min, avg_check_vs_baseline_pct_max,
    alcohol_affinity, alcohol_primary_driver, beverage_preference,
    peer_influence_coefficient, group_ordering_pattern,
    dwell_min_minutes, dwell_max_minutes,
    revpash_min_inr, revpash_max_inr,
    diminishing_returns_minutes,
    repeat_tendency_pct_min, repeat_tendency_pct_max, repeat_window_days,
    discovery_rate, wom_multiplier_min, wom_multiplier_max,
    primary_mechanism_id, secondary_mechanism_id
) VALUES

-- SOCIAL BUTTERFLY
-- Literature: WolfBrown jazz segmentation (Social Butterflies = 2nd largest cluster,
--   frequency-driven, social-connection-first, price-sensitive, high WOM network).
--   Hattingh 2025 nightclub typology: 36% of sample. INFERRED for dining context.
-- India data: SOCIAL Voices from the Hood (n=10,000): 53% choose by WOM,
--   56% enjoy a drink on night out, 28% dine out 1-2x per week.
(
    'social_butterfly', 'Social Butterfly', 'mixed',
    NULL, NULL,        -- food % (social occasions, variable)
    NULL, NULL,        -- alcohol % (social drinkers, not heavy)
    20, 28,            -- dessert attach %
    10, 30,            -- avg check vs baseline (+10-30%)
    'medium_high', 'social_occasion', 'Cocktails, beer, shareable pitchers',
    0.20,              -- Herhausen baseline 0.142 adjusted upward for social context; Kimi: 0.18-0.22
    'Social-first convergence — follows group consensus; trend-follower not setter',
    75, 120,           -- dwell (social meals; not as long as Calm Pairs)
    300, 450,          -- revpash (moderate; price-sensitive)
    105,               -- diminishing returns
    30, 40, 60,        -- repeat 30-40% within 60 days (soft preferences, rotates venues)
    'high',            -- discovery rate: 0.7-0.8 (high social exposure, but passive not active)
    3.5, 5.0,          -- WOM multiplier (large network, talks about multiple venues)
    (SELECT id FROM behavioral_mechanisms WHERE slug = 'social_proof'),
    (SELECT id FROM behavioral_mechanisms WHERE slug = 'fomo')
),

-- COMFORT DWELLER
-- Literature: WolfBrown "Comfort Seekers" (low engagement, familiarity-preferring).
--   Euromonitor 2020: post-uncertainty, familiar food/environments gain preference.
--   Seating comfort studies: comfortable seating extends dwell 15-25%, increases spend.
--   Post-COVID Indian dining: 40% prioritize clean/safe environment over taste. INFERRED.
(
    'comfort_dweller', 'Comfort Dweller', 'habit_driven',
    65, 75,            -- food-heavy (food and dessert, not alcohol-oriented)
    NULL, NULL,        -- alcohol % (occasional; wine/beer with meal only)
    28, 38,            -- dessert attach % (high; dessert = comfort indulgence)
    5, 20,             -- avg check vs baseline (moderate spend, not premium)
    'low_medium', 'habit', 'Wine by the glass, familiar beer',
    0.10,              -- Herhausen: >32yrs effect = 4.0% absolute; low conformity. Kimi: 0.08-0.12
    'Low conformity; knows what they want; chooses based on comfort, not group pressure',
    90, 150,           -- dwell (long; the environment is the point)
    200, 350,          -- revpash (lower per-cover, compensated by long dwell)
    135,               -- diminishing returns (slow burn; stays past normal turnover)
    50, 65, 45,        -- repeat 50-65% within 45 days (strong within repertoire of 3-5 venues)
    'low',             -- discovery rate: 0.2-0.3 (passive; finds via trusted friends or walked by)
    2.0, 3.0,          -- WOM multiplier (recommends within close network only)
    (SELECT id FROM behavioral_mechanisms WHERE slug = 'environmental_expectation'),
    (SELECT id FROM behavioral_mechanisms WHERE slug = 'habit_formation')
);


-- ---------------------------------------------------------------------------
-- SPEND TRIGGERS: SOCIAL BUTTERFLY
-- ---------------------------------------------------------------------------

INSERT INTO archetype_spend_triggers (archetype_id, trigger_rank, trigger_text, staff_script) VALUES
((SELECT id FROM archetype_behavioral_profiles WHERE archetype_key = 'social_butterfly'),
 1,
 'Group deal / share plate activation — social facilitation of spending when the table commits together',
 'There is a sharing platter that works really well for a group your size — want me to bring that out?'),

((SELECT id FROM archetype_behavioral_profiles WHERE archetype_key = 'social_butterfly'),
 2,
 '"Everyone is going" social proof — group consensus removes individual spend hesitation',
 NULL),

((SELECT id FROM archetype_behavioral_profiles WHERE archetype_key = 'social_butterfly'),
 3,
 'Weekday happy hour as entry point — price-sensitivity handled upfront unlocks longer session',
 NULL);


-- ---------------------------------------------------------------------------
-- SPEND TRIGGERS: COMFORT DWELLER
-- ---------------------------------------------------------------------------

INSERT INTO archetype_spend_triggers (archetype_id, trigger_rank, trigger_text, staff_script) VALUES
((SELECT id FROM archetype_behavioral_profiles WHERE archetype_key = 'comfort_dweller'),
 1,
 'Staff recognition by name or "usual" — belonging cue activates comfort identity and loyalty',
 'Welcome back — shall I get your usual, or is there something you''d like to try today?'),

((SELECT id FROM archetype_behavioral_profiles WHERE archetype_key = 'comfort_dweller'),
 2,
 'Atmospheric upgrade (quiet corner, preferred section) — environment confirmation extends dwell and adds courses',
 NULL),

((SELECT id FROM archetype_behavioral_profiles WHERE archetype_key = 'comfort_dweller'),
 3,
 'Comfort-food or familiar menu item recommended by staff — reduces decision anxiety, unlocks dessert attach',
 'The [dish] is exactly what you''d expect — nothing surprising, just very good');


-- ---------------------------------------------------------------------------
-- SEGMENT ↔ ARCHETYPE AFFINITY: NEW ARCHETYPES
-- ---------------------------------------------------------------------------
-- Social Butterfly: high affinity with social/group segments
-- Comfort Dweller: high affinity with habit and family segments

INSERT INTO segment_archetype_affinity (segment_id, archetype_id, affinity_rank)
SELECT s.id, a.id, x.rank FROM (VALUES
    -- Social Butterfly affinities
    ('college_kids',    'social_butterfly', 4),  -- after party_seeker, scene_seeker, trend_hunter
    ('working_women',   'social_butterfly', 4),  -- after lifestyle_regular, scene_seeker, trusted_regular
    ('couples',         'social_butterfly', 4),  -- after calm_pairs, lifestyle_regular, quiet_discoverer

    -- Comfort Dweller affinities
    ('families',        'comfort_dweller',  3),  -- after habit_former, lifestyle_regular
    ('office_workers',  'comfort_dweller',  5),  -- routine comfort-seeking in office context
    ('working_women',   'comfort_dweller',  5),  -- safety + comfort overlap
    ('solo_diners',     'comfort_dweller',  5)   -- solo comfort-seeking (café dweller type)
) AS x(seg_key, arch_key, rank)
JOIN segment_behavioral_profiles s ON s.segment_key = x.seg_key
JOIN archetype_behavioral_profiles a ON a.archetype_key = x.arch_key;


-- ---------------------------------------------------------------------------
-- PEER INFLUENCE MECHANISM CITATION
-- (Herhausen et al. 2024 — the validated baseline used throughout Kimi report)
-- ---------------------------------------------------------------------------

INSERT INTO mechanism_citations (mechanism_id, author, year, framework_name, core_claim, relevance) VALUES
((SELECT id FROM behavioral_mechanisms WHERE slug = 'social_proof'),
 'Herhausen et al.', 2024,
 'Peer Food Choice Mimicry (Nature Communications)',
 'A peer ordering first increases a focal diner''s probability of choosing the same item by 14.2 percentage points absolute (83% relative increase). Effect strongest for students/young adults (≤22 yrs: 17.7%) and weakest for older diners (>32 yrs: 4.0%). Groups of 3+ show +€2.00 higher individual spend vs solo diners.',
 'Validated baseline for peer_influence_coefficient across all archetypes. Use 0.142 as the universal floor; adjust upward for younger/social archetypes (Party Seeker: 0.80, Social Butterfly: 0.20) and downward for older/habit-driven (Comfort Dweller: 0.10, Habit Former: 0.10).');


-- ---------------------------------------------------------------------------
-- CHANNEL BENCHMARK CORRECTIONS (Perplexity 2025-26)
-- ---------------------------------------------------------------------------

-- WhatsApp: Perplexity narrows to 90-98% open rate, 40-60% CTR (India, cross-vertical)
UPDATE channel_benchmarks
SET open_rate_pct_min    = 90,
    open_rate_pct_max    = 98,
    validation_notes     = 'Validated India: WebEngage >90% read rate; AiSensy 98% open + 45-60% CTR; WhatsApp vs Email study 98% open + 45-60% CTR (Perplexity 2025-26, cross-vertical India).'
WHERE channel_key = 'whatsapp';

-- Micro-influencer: Perplexity corrects follower range to 1K-25K (Modash Mumbai definition)
-- Previous DB label said 10K-50K which is wrong for India
UPDATE channel_benchmarks
SET label            = 'Micro-Influencer (1K–25K followers, India)',
    validation_notes = 'CORRECTED follower range: Modash Mumbai defines micro as 1K-25K followers. Cost: ₹1,000-₹10,000 per post for 1K-10K tier (India, cross-category, wdcweb 2025). Previous range 10K-50K was wrong. ROI "6.5x" figure is UNSUBSTANTIATED — no India F&B citation found (Perplexity 2025-26).'
WHERE channel_key = 'micro_influencer';

-- Instagram Reels: Perplexity gives India-specific engagement data
-- upGrowth India 2026: Reels 3.5-5% engagement vs feed posts 1-2%
UPDATE channel_benchmarks
SET primary_effect   = 'Discovery channel; Reels 3.5-5% engagement vs 1-2% for feed posts (India, upGrowth 2026); strong for Social Crowd and Working Women',
    validation_notes = 'UPDATED: India-specific data from upGrowth 2026 — Reels engagement 3.5-5% vs feed 1-2%. Previous claim "2x engagement, 10-50x reach" is partially correct directionally. "6.5x engagement" claim remains UNSUBSTANTIATED. Do not cite 6.5x in any client output.'
WHERE channel_key = 'instagram_reels';


-- ---------------------------------------------------------------------------
-- NEW RESEARCH VALIDATION FLAGS
-- ---------------------------------------------------------------------------

INSERT INTO research_validation_flags (
    entity_type, entity_key, field_name,
    claimed_value, validated_value,
    validation_source, is_corrected, correction_notes
) VALUES

('channel', 'micro_influencer', 'follower_range',
 '10K-50K followers',
 '1K-25K followers (India, Modash Mumbai definition)',
 'india_market_intelligence_perplexity.md — Modash Mumbai micro-influencer listing',
 TRUE,
 'DB label and validation_notes updated to 1K-25K. Channel benchmark now correct.'),

('channel', 'micro_influencer', 'roi_multiplier',
 '6.5x ROI per post',
 'UNSUBSTANTIATED — no India F&B citation found',
 'india_market_intelligence_perplexity.md',
 FALSE,
 'The 6.5x ROI figure appears in internal docs but has no credible India F&B source. Remove from all client-facing marketing outputs. Only defensible cost data: ₹1,000-₹10,000 per post for 1K-10K tier.'),

('channel', 'whatsapp', 'ctr',
 'Not previously specified',
 '40-60% CTR (India, cross-vertical)',
 'india_market_intelligence_perplexity.md — AiSensy, WebEngage, wassy.in India studies',
 TRUE,
 'WhatsApp CTR now documented as 40-60% for India campaigns. Added to channel benchmark validation notes.'),

('segment', 'all_segments', 'peer_influence_coefficient',
 'Internal estimates (no academic baseline cited)',
 'Validated baseline: 0.142 absolute effect (Herhausen et al., Nature Communications 2024). Age moderation: ≤22 yrs = 0.177; >32 yrs = 0.040.',
 'archetype_segment_validation_kimi.md',
 FALSE,
 'All peer_influence_coefficient values in segment_behavioral_profiles and archetype_behavioral_profiles are INFERRED adjustments relative to the 0.142 baseline, not independently validated. Acceptable for v1 but should be documented in client materials. Herhausen citation now in mechanism_citations.'),

('archetype', 'scene_seeker', 'literature_status',
 'Validated segment',
 'HYPOTHESIS — no academic correlate in restaurant consumer psychology literature',
 'archetype_segment_validation_kimi.md',
 FALSE,
 'Scene Seeker does not map to any recognized academic archetype cluster. Internally constructed. Flag in any client-facing archetype explanation.'),

('archetype', 'calm_pairs', 'literature_status',
 'Validated segment',
 'HYPOTHESIS — couples studied as group-size unit, not as psychological archetype',
 'archetype_segment_validation_kimi.md',
 FALSE,
 'Calm Pairs has no standalone academic correlate. Closest: two-person group-size effects in European casual dining research (French restaurant study). Internally constructed.'),

('archetype', 'premium_prioritizer', 'literature_status',
 'Validated segment',
 'HYPOTHESIS — not a validated archetype in restaurant consumer psychology',
 'archetype_segment_validation_kimi.md',
 FALSE,
 'Premium Prioritizer has no direct academic correlate. Blends Veblen conspicuous consumption theory with connoisseurship behavior. Internally constructed.'),

('archetype', 'power_regular', 'literature_status',
 'Validated segment',
 'HYPOTHESIS — not a validated archetype in restaurant consumer psychology',
 'archetype_segment_validation_kimi.md',
 FALSE,
 'Power Regular has no direct academic correlate. Blends Routiner and status-signaling behavior. Internally constructed.');
