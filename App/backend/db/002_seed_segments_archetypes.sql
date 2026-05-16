-- =============================================================================
-- SEED: SEGMENT & ARCHETYPE BEHAVIORAL PROFILES
-- Source: behavioral_intelligence_module.md (Kimi, v1.0)
-- Urban India context | Mumbai / MMR focus
-- =============================================================================

-- ---------------------------------------------------------------------------
-- SEGMENT BEHAVIORAL PROFILES
-- ---------------------------------------------------------------------------

INSERT INTO segment_behavioral_profiles (
    segment_key, label,
    food_pct_min, food_pct_max,
    alcohol_pct_min, alcohol_pct_max,
    dessert_attach_pct_min, dessert_attach_pct_max,
    avg_check_vs_baseline_pct_min, avg_check_vs_baseline_pct_max,
    alcohol_affinity, alcohol_primary_driver, alcohol_secondary_driver, beverage_preference,
    peer_influence_coefficient, group_revenue_impact_per_member,
    dwell_min_minutes, dwell_max_minutes,
    dwell_alt_min_minutes, dwell_alt_max_minutes, dwell_alt_label,
    revpash_min_inr, revpash_max_inr,
    revpash_alt_min_inr, revpash_alt_max_inr,
    diminishing_returns_minutes, revenue_curve,
    repeat_tendency_pct_min, repeat_tendency_pct_max, repeat_window_days,
    discovery_rate, wom_multiplier_min, wom_multiplier_max,
    primary_trigger, low_to_high_spend_trigger,
    dessert_high_conversion_trigger, dessert_format_preference
) VALUES

-- 1. OFFICE WORKERS
(
    'office_workers', 'Office Workers',
    65, 70,     -- food %
    NULL, NULL, -- alcohol % (low, not broken out separately)
    12, 18,     -- dessert attach %
    0, 15,      -- avg check vs baseline (baseline to +15% weekday)
    'low_medium', 'habit', 'social_occasion', 'Beer / craft beer; wine with clients',
    0.30, '+15% per additional member (efficiency)',
    35, 50,     -- dwell lunch
    75, 90, 'after-work/dinner',
    180, 250,   -- revpash lunch
    350, 450,   -- revpash after-work
    60,         -- diminishing returns (post-60min lunch; no additional ordering)
    'steep_front_flat_tail',
    60, 70, 30, -- repeat 60-70% within 30 days
    'low', 1.2, 1.2,
    'Convenience (proximity to office) + Habit (routine lunch spot)',
    'Client joining identity shift; staff recognition by name; limited lunch combo upgrade to premium protein',
    'Coffee upgrade combo', 'Individual, portable'
),

-- 2. SOCIAL CROWD (college_kids)
(
    'college_kids', 'Social Crowd',
    NULL, NULL,
    55, 65,     -- drink-heavy: 55-65% of check
    22, 28,
    40, 80,     -- +40-80% above baseline
    'high', 'social_occasion', 'fomo', 'Cocktails, beer buckets, shots',
    0.70, '+40% per member (alcohol multiplier)',
    120, 180,   -- dwell (longest segment)
    NULL, NULL, NULL,
    400, 600,   -- revpash (front-loaded)
    NULL, NULL,
    120,        -- diminishing returns at 120min; optimal flip at 150min
    'front_loaded_alcohol_tail',
    20, 30, 90,
    'high', 3.5, 4.5,
    'Peer plan (group chat coordination) + Occasion (birthday, promotion, weekend)',
    'First round anchor (premium cocktail sets table spend level); "last round" scarcity nudge; group bundle discount on bottles',
    'Shared "dessert shots" format', 'Shareable, photogenic'
),

-- 3. COUPLES
(
    'couples', 'Couples',
    NULL, NULL,
    NULL, NULL,
    35, 45,     -- high dessert attach
    25, 50,     -- +25-50% above baseline
    'medium', 'identity', 'social_occasion', 'Wine, cocktails for date night',
    0.50, 'Baseline × 1.8 (two covers, shared apps)',
    90, 120,    -- dwell (unhurried, conversation-paced)
    NULL, NULL, NULL,
    350, 500,   -- revpash (steady curve)
    NULL, NULL,
    105,        -- diminishing returns; coffee/digestif extends 15-20min
    'steady',
    40, 50, 60,
    'medium', 2.0, 2.0,
    'Occasion (anniversary, birthday, date night ritual) + Habit (weekly date night spot)',
    '"Chef''s special for two" framing; wine pairing suggestion; dessert as "perfect way to end the evening"',
    '"Perfect for sharing" framing', 'Shared plate, romantic'
),

-- 4. FAMILIES
(
    'families', 'Families',
    75, 80,     -- food-heavy
    NULL, NULL,
    40, 50,     -- very high dessert (child-driven)
    10, 30,     -- lower per-capita but high table total
    'low_medium', 'habit', NULL, 'Beer / wine (1-2 max); parents only',
    0.40, '+25% per child (dessert/beverage)',
    60, 90,     -- dwell (child-dependent)
    NULL, NULL, NULL,
    200, 300,   -- revpash (lower per-cover)
    NULL, NULL,
    75,         -- children restless post-75min
    'linear_child_limited',
    50, 60, 30,
    'low', 1.5, 1.5,
    'Habit (Sunday lunch tradition) + Convenience (kid-friendly menu, high chairs, parking)',
    '"Family feast" bundle (perceived value); kids'' activity pack upsell; dessert presented as reward for children''s patience',
    'Child-targeted / "kids eat free"', 'Familiar, colorful'
),

-- 5. PREMIUM DINERS
(
    'premium', 'Premium Diners',
    NULL, NULL,
    NULL, NULL,
    50, 65,     -- very high dessert (connoisseurship)
    150, 300,   -- +150-300% above baseline
    'high', 'identity', 'social_occasion', 'Red wine dominant, single malts, craft cocktails',
    0.20, '+30% per member (wine sharing)',
    120, 180,   -- dwell (savoring pace)
    NULL, NULL, NULL,
    800, 1500,  -- revpash highest segment
    NULL, NULL,
    150,        -- post-dessert and digestif, revenue ceases
    'course_paced_wine_driven',
    30, 40, 90,
    'medium', 3.0, 3.0,
    'Occasion (celebration, business deal, milestone) + Identity (venue as extension of self-image)',
    'Sommelier recommendation with story; "chef''s table" exclusivity; limited vintage availability; anchoring with highest-price item first',
    'Cheese course / dessert wine', 'Sophisticated, small'
),

-- 6. SOLO DINERS
(
    'solo_diners', 'Solo Diners',
    70, 75,
    NULL, NULL,
    18, 25,
    -10, 0,     -- -10% to baseline
    'low_medium', 'habit', 'identity', 'Beer or wine by the glass',
    0.00, 'Baseline (no group)',
    30, 50,     -- lunch
    60, 75, 'dinner/bar solo',
    250, 400,   -- revpash (efficient turnover)
    NULL, NULL,
    45,         -- 45min lunch; 75min dinner
    'efficient_single_peak',
    25, 35, 60,
    'extremely_high', 2.2, 2.2,
    'Habit (regular solo lunch/dinner) + Discovery (trying new place alone) + Convenience (quick solo seat at bar)',
    'Bartender rapport and recommendation; "chef''s special" exclusivity; bar counter seat with kitchen view',
    'Self-reward framing', 'Individual, comforting'
),

-- 7. WORKING WOMEN
(
    'working_women', 'Working Women',
    NULL, NULL,
    NULL, NULL,
    25, 32,
    15, 35,     -- +15-35% above baseline; health premium accepted
    'medium', 'identity', 'social_occasion', 'Wine, gin cocktails, zero-proof options',
    0.60, '+35% per member (shared small plates)',
    75, 105,    -- group
    45, 60, 'solo lunch',
    350, 500,   -- group revpash
    200, 300,   -- solo revpash
    90,         -- group 90min; solo 50min
    'moderate_steady',
    40, 50, 60,
    'medium_high', 2.8, 2.8,
    'Peer plan (group coordination) + Habit (regular after-work spot) + Discovery (new "safe" venue)',
    '"Wellness" positioning of premium items; zero-proof cocktail menu (identity-aligned); "guilt-free" dessert framing',
    '"Guilt-free" positioning', 'Small portion, dark chocolate'
);


-- ---------------------------------------------------------------------------
-- SEGMENT OCCASION MULTIPLIERS
-- ---------------------------------------------------------------------------

-- Office Workers
INSERT INTO segment_occasion_multipliers (segment_id, occasion_label, multiplier_min, multiplier_max, notes)
SELECT id, 'Work lunch', 1.00, 1.00, 'Baseline spend' FROM segment_behavioral_profiles WHERE segment_key = 'office_workers'
UNION ALL
SELECT id, 'Client entertainment', 1.40, 1.60, '+40-60% (alcohol, appetizers, premium mains)' FROM segment_behavioral_profiles WHERE segment_key = 'office_workers'
UNION ALL
SELECT id, 'Team celebration', 1.80, 1.80, '+80% with round-based alcohol' FROM segment_behavioral_profiles WHERE segment_key = 'office_workers';

-- Social Crowd
INSERT INTO segment_occasion_multipliers (segment_id, occasion_label, multiplier_min, multiplier_max, notes)
SELECT id, 'Celebration (birthday/promotion)', 2.00, 2.00, '+100% spend (bottles, shots, premium cocktails)' FROM segment_behavioral_profiles WHERE segment_key = 'college_kids'
UNION ALL
SELECT id, 'Routine hangout', 1.30, 1.30, '+30% spend' FROM segment_behavioral_profiles WHERE segment_key = 'college_kids'
UNION ALL
SELECT id, '"Just because" outing', 1.00, 1.00, 'Baseline with alcohol focus' FROM segment_behavioral_profiles WHERE segment_key = 'college_kids';

-- Couples
INSERT INTO segment_occasion_multipliers (segment_id, occasion_label, multiplier_min, multiplier_max, notes)
SELECT id, 'Anniversary / celebration', 1.60, 1.60, '+60% (wine, premium mains, dessert)' FROM segment_behavioral_profiles WHERE segment_key = 'couples'
UNION ALL
SELECT id, 'Routine date night', 1.20, 1.20, '+20% spend' FROM segment_behavioral_profiles WHERE segment_key = 'couples'
UNION ALL
SELECT id, 'Spontaneous', 1.00, 1.00, 'Baseline with exploration tendency' FROM segment_behavioral_profiles WHERE segment_key = 'couples';

-- Families
INSERT INTO segment_occasion_multipliers (segment_id, occasion_label, multiplier_min, multiplier_max, notes)
SELECT id, 'Birthday celebration', 1.40, 1.40, '+40% (cake, special menu)' FROM segment_behavioral_profiles WHERE segment_key = 'families'
UNION ALL
SELECT id, 'Routine family outing', 1.00, 1.00, 'Baseline spend' FROM segment_behavioral_profiles WHERE segment_key = 'families'
UNION ALL
SELECT id, 'Post-activity (mall/movie)', 0.90, 1.00, 'Convenience-driven, lower dwell' FROM segment_behavioral_profiles WHERE segment_key = 'families';

-- Premium Diners
INSERT INTO segment_occasion_multipliers (segment_id, occasion_label, multiplier_min, multiplier_max, notes)
SELECT id, 'Business entertainment', 3.00, 3.00, '+200% (bottles, premium cuts)' FROM segment_behavioral_profiles WHERE segment_key = 'premium'
UNION ALL
SELECT id, 'Personal celebration', 2.50, 2.50, '+150%' FROM segment_behavioral_profiles WHERE segment_key = 'premium'
UNION ALL
SELECT id, 'Routine premium dining', 1.80, 1.80, '+80%' FROM segment_behavioral_profiles WHERE segment_key = 'premium';

-- Working Women
INSERT INTO segment_occasion_multipliers (segment_id, occasion_label, multiplier_min, multiplier_max, notes)
SELECT id, 'Celebration (promotion/birthday)', 1.50, 1.50, '+50% spend' FROM segment_behavioral_profiles WHERE segment_key = 'working_women'
UNION ALL
SELECT id, 'Routine catch-up', 1.20, 1.20, '+20% spend' FROM segment_behavioral_profiles WHERE segment_key = 'working_women'
UNION ALL
SELECT id, '"Self-care" solo outing', 1.10, 1.10, '+10%' FROM segment_behavioral_profiles WHERE segment_key = 'working_women';

-- Solo Diners
INSERT INTO segment_occasion_multipliers (segment_id, occasion_label, multiplier_min, multiplier_max, notes)
SELECT id, '"Treat myself"', 1.30, 1.30, '+30% (premium main, dessert)' FROM segment_behavioral_profiles WHERE segment_key = 'solo_diners'
UNION ALL
SELECT id, 'Routine meal', 1.00, 1.00, 'Baseline' FROM segment_behavioral_profiles WHERE segment_key = 'solo_diners'
UNION ALL
SELECT id, 'Work-alone', 0.80, 0.90, 'Coffee + light meal, low spend' FROM segment_behavioral_profiles WHERE segment_key = 'solo_diners';


-- ---------------------------------------------------------------------------
-- SEGMENT PLATFORM USAGE
-- ---------------------------------------------------------------------------

INSERT INTO segment_platform_usage (segment_id, platform, usage_type, strength) VALUES

-- Office Workers
((SELECT id FROM segment_behavioral_profiles WHERE segment_key = 'office_workers'), 'google_maps', 'discovery', 'primary'),
((SELECT id FROM segment_behavioral_profiles WHERE segment_key = 'office_workers'), 'zomato', 'validation', 'primary'),
((SELECT id FROM segment_behavioral_profiles WHERE segment_key = 'office_workers'), 'zomato', 'booking', 'primary'),
((SELECT id FROM segment_behavioral_profiles WHERE segment_key = 'office_workers'), 'swiggy', 'booking', 'secondary'),
((SELECT id FROM segment_behavioral_profiles WHERE segment_key = 'office_workers'), 'zomato', 'post_visit_review', 'primary'),
((SELECT id FROM segment_behavioral_profiles WHERE segment_key = 'office_workers'), 'word_of_mouth', 'wom', 'primary'),

-- Social Crowd
((SELECT id FROM segment_behavioral_profiles WHERE segment_key = 'college_kids'), 'instagram', 'discovery', 'primary'),
((SELECT id FROM segment_behavioral_profiles WHERE segment_key = 'college_kids'), 'zomato', 'validation', 'secondary'),
((SELECT id FROM segment_behavioral_profiles WHERE segment_key = 'college_kids'), 'zomato', 'booking', 'primary'),
((SELECT id FROM segment_behavioral_profiles WHERE segment_key = 'college_kids'), 'swiggy_dineout', 'booking', 'secondary'),
((SELECT id FROM segment_behavioral_profiles WHERE segment_key = 'college_kids'), 'instagram', 'post_visit_review', 'primary'),
((SELECT id FROM segment_behavioral_profiles WHERE segment_key = 'college_kids'), 'word_of_mouth', 'wom', 'primary'),

-- Couples
((SELECT id FROM segment_behavioral_profiles WHERE segment_key = 'couples'), 'instagram', 'discovery', 'primary'),
((SELECT id FROM segment_behavioral_profiles WHERE segment_key = 'couples'), 'google_reviews', 'validation', 'primary'),
((SELECT id FROM segment_behavioral_profiles WHERE segment_key = 'couples'), 'zomato', 'booking', 'primary'),
((SELECT id FROM segment_behavioral_profiles WHERE segment_key = 'couples'), 'zomato', 'post_visit_review', 'primary'),
((SELECT id FROM segment_behavioral_profiles WHERE segment_key = 'couples'), 'instagram', 'post_visit_review', 'secondary'),
((SELECT id FROM segment_behavioral_profiles WHERE segment_key = 'couples'), 'word_of_mouth', 'wom', 'primary'),

-- Families
((SELECT id FROM segment_behavioral_profiles WHERE segment_key = 'families'), 'zomato', 'discovery', 'primary'),
((SELECT id FROM segment_behavioral_profiles WHERE segment_key = 'families'), 'google_maps', 'validation', 'primary'),
((SELECT id FROM segment_behavioral_profiles WHERE segment_key = 'families'), 'zomato', 'booking', 'primary'),
((SELECT id FROM segment_behavioral_profiles WHERE segment_key = 'families'), 'zomato', 'post_visit_review', 'primary'),
((SELECT id FROM segment_behavioral_profiles WHERE segment_key = 'families'), 'word_of_mouth', 'wom', 'primary'),

-- Premium Diners
((SELECT id FROM segment_behavioral_profiles WHERE segment_key = 'premium'), 'google_maps', 'discovery', 'primary'),
((SELECT id FROM segment_behavioral_profiles WHERE segment_key = 'premium'), 'word_of_mouth', 'discovery', 'primary'),
((SELECT id FROM segment_behavioral_profiles WHERE segment_key = 'premium'), 'zomato', 'validation', 'primary'),
((SELECT id FROM segment_behavioral_profiles WHERE segment_key = 'premium'), 'google_reviews', 'validation', 'primary'),
((SELECT id FROM segment_behavioral_profiles WHERE segment_key = 'premium'), 'zomato_gold', 'booking', 'primary'),
((SELECT id FROM segment_behavioral_profiles WHERE segment_key = 'premium'), 'direct', 'booking', 'secondary'),
((SELECT id FROM segment_behavioral_profiles WHERE segment_key = 'premium'), 'zomato', 'post_visit_review', 'primary'),
((SELECT id FROM segment_behavioral_profiles WHERE segment_key = 'premium'), 'instagram', 'post_visit_review', 'secondary'),

-- Solo Diners
((SELECT id FROM segment_behavioral_profiles WHERE segment_key = 'solo_diners'), 'zomato', 'discovery', 'primary'),
((SELECT id FROM segment_behavioral_profiles WHERE segment_key = 'solo_diners'), 'zomato', 'validation', 'primary'),
((SELECT id FROM segment_behavioral_profiles WHERE segment_key = 'solo_diners'), 'zomato', 'booking', 'primary'),
((SELECT id FROM segment_behavioral_profiles WHERE segment_key = 'solo_diners'), 'google_maps', 'discovery', 'secondary'),
((SELECT id FROM segment_behavioral_profiles WHERE segment_key = 'solo_diners'), 'zomato', 'post_visit_review', 'primary'),

-- Working Women
((SELECT id FROM segment_behavioral_profiles WHERE segment_key = 'working_women'), 'instagram', 'discovery', 'primary'),
((SELECT id FROM segment_behavioral_profiles WHERE segment_key = 'working_women'), 'zomato', 'validation', 'primary'),
((SELECT id FROM segment_behavioral_profiles WHERE segment_key = 'working_women'), 'google_reviews', 'validation', 'secondary'),
((SELECT id FROM segment_behavioral_profiles WHERE segment_key = 'working_women'), 'zomato', 'booking', 'primary'),
((SELECT id FROM segment_behavioral_profiles WHERE segment_key = 'working_women'), 'swiggy', 'booking', 'secondary'),
((SELECT id FROM segment_behavioral_profiles WHERE segment_key = 'working_women'), 'instagram', 'post_visit_review', 'primary'),
((SELECT id FROM segment_behavioral_profiles WHERE segment_key = 'working_women'), 'zomato', 'post_visit_review', 'secondary'),
((SELECT id FROM segment_behavioral_profiles WHERE segment_key = 'working_women'), 'word_of_mouth', 'wom', 'primary');


-- ---------------------------------------------------------------------------
-- ARCHETYPE BEHAVIORAL PROFILES
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
    discovery_rate, wom_multiplier_min, wom_multiplier_max
) VALUES

('party_seeker', 'Party Seeker', 'occasion_driven',
    NULL, NULL, 60, 70, 15, 20, 60, 100,
    'very_high', 'social_occasion', 'Quantity + quality; shots, premium cocktails',
    0.80, 'Very high; first drink sets table tone; round-based purchasing',
    150, 210, 450, 700, 150,
    15, 25, 90, 'very_high', 4.0, 4.5),

('scene_seeker', 'Scene Seeker', 'occasion_driven',
    NULL, NULL, NULL, NULL, 25, 30, 40, 70,
    'high', 'identity', 'Aesthetic cocktails, wine',
    0.70, 'High convergence on photogenic, trending items',
    120, 150, 400, 600, 120,
    15, 20, 90, 'very_high', 3.5, 3.5),

('trusted_regular', 'Trusted Regular', 'habit_driven',
    NULL, NULL, NULL, NULL, 30, 38, 20, 40,
    'medium_high', 'habit', '"Usual" drink + openness to staff suggestion',
    0.30, 'Low; brings guests and sets own order; guests defer to regular',
    60, 90, 350, 500, 75,
    60, 70, 30, 'low', 2.5, 2.5),

('habit_former', 'Habit Former', 'habit_driven',
    75, 80, NULL, NULL, 12, 18, 0, 10,
    'low', 'habit', 'Occasional beer / wine',
    0.10, 'Minimal; immune to peer influence; same order pattern',
    35, 75, 200, 300, 45,
    70, 80, 30, 'very_low', 1.0, 1.0),

('calm_pairs', 'Calm Pairs', 'mixed',
    NULL, NULL, NULL, NULL, 30, 35, 15, 30,
    'medium', 'social_occasion', 'Wine, slow cocktails',
    0.50, 'Mutual accommodation; collaborative, slow, consultative',
    105, 135, 300, 450, 120,
    45, 55, 60, 'low', 1.8, 1.8),

('lifestyle_regular', 'Lifestyle Regular', 'habit_driven',
    NULL, NULL, NULL, NULL, 25, 30, 25, 45,
    'medium', 'identity', 'Natural wine, craft beer, low-ABV cocktails',
    0.40, 'Values trump peer pressure; values-aligned group convergence',
    60, 90, 350, 500, 75,
    50, 60, 30, 'medium', 2.5, 2.5),

('quiet_discoverer', 'Quiet Discoverer', 'occasion_driven',
    70, 75, NULL, NULL, 22, 28, 10, 25,
    'low_medium', 'discovery', 'Pairing-focused, not quantity',
    0.00, 'N/A — solo by choice',
    75, 105, 300, 450, 90,
    20, 30, 90, 'very_high', 2.0, 2.0),

('trend_hunter', 'Trend Hunter', 'occasion_driven',
    NULL, NULL, NULL, NULL, 35, 42, 50, 90,
    'high', 'fomo', 'Trending cocktails, viral drinks',
    0.75, 'Viral item = mandatory table order; group coordinates with fellow trend hunters',
    90, 120, 450, 650, 105,
    10, 15, 90, 'extremely_high', 4.5, 4.5),

('premium_prioritizer', 'Premium Prioritizer', 'occasion_driven',
    NULL, NULL, NULL, NULL, 50, 65, 200, 350,
    'very_high', 'identity', 'Wine (red dominant), single malts, rare vintages',
    0.15, 'Independent; confident own palate; may recommend to table',
    150, 180, 1000, 1800, 150,
    35, 45, 90, 'medium', 3.0, 3.0),

('discovery_explorer', 'Discovery Explorer', 'occasion_driven',
    NULL, NULL, NULL, NULL, 28, 35, 20, 40,
    'medium', 'discovery', 'Regional / artisanal drinks',
    0.20, 'Independent explorer; researches menu beforehand',
    90, 120, 350, 500, 105,
    15, 25, 90, 'extremely_high', 2.2, 2.2),

('power_regular', 'Power Regular', 'habit_driven',
    NULL, NULL, NULL, NULL, 25, 35, 20, 40,
    'medium', 'habit', 'Known preferences, staff-guided',
    0.30, 'Consistent with occasional group influence when hosting',
    60, 90, 350, 500, 75,
    55, 65, 30, 'low', 2.0, 2.5);


-- ---------------------------------------------------------------------------
-- ARCHETYPE SPEND TRIGGERS
-- ---------------------------------------------------------------------------

INSERT INTO archetype_spend_triggers (archetype_id, trigger_rank, trigger_text, staff_script) VALUES
-- Party Seeker
((SELECT id FROM archetype_behavioral_profiles WHERE archetype_key = 'party_seeker'), 1, 'First round anchor — premium cocktail ordered by dominant orderer sets table spend level', 'Shall I start a tab with [premium item]?'),
((SELECT id FROM archetype_behavioral_profiles WHERE archetype_key = 'party_seeker'), 2, '"Only 3 bottles left" scarcity signal', NULL),
((SELECT id FROM archetype_behavioral_profiles WHERE archetype_key = 'party_seeker'), 3, 'Group bundle discount on bottles', NULL),

-- Scene Seeker
((SELECT id FROM archetype_behavioral_profiles WHERE archetype_key = 'scene_seeker'), 1, 'Instagrammable presentation — visual trigger before first sip', 'This is our most photographed dish'),
((SELECT id FROM archetype_behavioral_profiles WHERE archetype_key = 'scene_seeker'), 2, 'Limited-edition collaboration menu item', NULL),
((SELECT id FROM archetype_behavioral_profiles WHERE archetype_key = 'scene_seeker'), 3, 'Influencer at nearby table (social proof cascade)', NULL),

-- Trusted Regular
((SELECT id FROM archetype_behavioral_profiles WHERE archetype_key = 'trusted_regular'), 1, 'Staff greeting by name (belonging cue activates insider identity)', '[Name], the chef sent something for you to try'),
((SELECT id FROM archetype_behavioral_profiles WHERE archetype_key = 'trusted_regular'), 2, '"We have something new you''d love" — insider preview access', 'We have something new you''d love'),
((SELECT id FROM archetype_behavioral_profiles WHERE archetype_key = 'trusted_regular'), 3, 'Bringing guests — "showing off their spot" +50% spend', NULL),

-- Habit Former
((SELECT id FROM archetype_behavioral_profiles WHERE archetype_key = 'habit_former'), 1, 'Loyalty reward on 10th visit — disrupts routine in a sanctioned way', 'Your usual, or shall we try the chef''s special today?'),
((SELECT id FROM archetype_behavioral_profiles WHERE archetype_key = 'habit_former'), 2, '"Same as usual, premium version?" — upgrade within the familiar', NULL),
((SELECT id FROM archetype_behavioral_profiles WHERE archetype_key = 'habit_former'), 3, 'Limited-time upgrade of their regular order', NULL),

-- Calm Pairs
((SELECT id FROM archetype_behavioral_profiles WHERE archetype_key = 'calm_pairs'), 1, 'Wine by the glass to start — low-commitment entry into alcohol spend', 'May I suggest a wine to start your evening?'),
((SELECT id FROM archetype_behavioral_profiles WHERE archetype_key = 'calm_pairs'), 2, 'Dessert as "let''s stay a bit longer" conversation anchor', NULL),
((SELECT id FROM archetype_behavioral_profiles WHERE archetype_key = 'calm_pairs'), 3, 'Quiet corner table upgrade (environment confirms occasion)', NULL),

-- Lifestyle Regular
((SELECT id FROM archetype_behavioral_profiles WHERE archetype_key = 'lifestyle_regular'), 1, 'Origin story of ingredient — values alignment unlocks spend premium', 'This is from a farm we work with directly'),
((SELECT id FROM archetype_behavioral_profiles WHERE archetype_key = 'lifestyle_regular'), 2, '"Limited batch" local product — scarcity + values identity combo', NULL),
((SELECT id FROM archetype_behavioral_profiles WHERE archetype_key = 'lifestyle_regular'), 3, 'Chef''s values narrative (sourcing philosophy, sustainability)', NULL),

-- Quiet Discoverer
((SELECT id FROM archetype_behavioral_profiles WHERE archetype_key = 'quiet_discoverer'), 1, 'Chef''s tasting menu — structured discovery removes decision anxiety', 'The chef is experimenting with [ingredient] — shall I bring a tasting?'),
((SELECT id FROM archetype_behavioral_profiles WHERE archetype_key = 'quiet_discoverer'), 2, '"Not on the regular menu" exclusivity signal', NULL),
((SELECT id FROM archetype_behavioral_profiles WHERE archetype_key = 'quiet_discoverer'), 3, 'Educational staff interaction — builds expertise identity', NULL),

-- Trend Hunter
((SELECT id FROM archetype_behavioral_profiles WHERE archetype_key = 'trend_hunter'), 1, '"Only available this week" — temporal scarcity + FOMO cascade', 'This is what everyone is posting about right now'),
((SELECT id FROM archetype_behavioral_profiles WHERE archetype_key = 'trend_hunter'), 2, '"Viral" / "trending now" framing on menu or staff script', NULL),
((SELECT id FROM archetype_behavioral_profiles WHERE archetype_key = 'trend_hunter'), 3, 'Queue / waitlist signal (scarcity validates desirability)', NULL),

-- Premium Prioritizer
((SELECT id FROM archetype_behavioral_profiles WHERE archetype_key = 'premium_prioritizer'), 1, 'Anchoring with highest-price item first — calibrates spend expectations upward', 'I have something special that just arrived'),
((SELECT id FROM archetype_behavioral_profiles WHERE archetype_key = 'premium_prioritizer'), 2, 'Sommelier narrative + provenance story', NULL),
((SELECT id FROM archetype_behavioral_profiles WHERE archetype_key = 'premium_prioritizer'), 3, '"Only 5 bottles in the city" — scarcity + connoisseurship identity', NULL),

-- Discovery Explorer
((SELECT id FROM archetype_behavioral_profiles WHERE archetype_key = 'discovery_explorer'), 1, 'Regional ingredient story — authenticity trigger', 'Would you like to try something from [region]? The chef sources it directly'),
((SELECT id FROM archetype_behavioral_profiles WHERE archetype_key = 'discovery_explorer'), 2, '"Chef''s special not on the menu" — exclusive discovery signal', NULL),
((SELECT id FROM archetype_behavioral_profiles WHERE archetype_key = 'discovery_explorer'), 3, 'Limited exploration tasting menu — structured discovery format', NULL),

-- Power Regular
((SELECT id FROM archetype_behavioral_profiles WHERE archetype_key = 'power_regular'), 1, 'Recognition + table preference — status confirmation', '[Name], your usual table is ready'),
((SELECT id FROM archetype_behavioral_profiles WHERE archetype_key = 'power_regular'), 2, '"Something we''re testing — wanted your opinion" — insider identity', NULL),
((SELECT id FROM archetype_behavioral_profiles WHERE archetype_key = 'power_regular'), 3, 'Hosting occasion — +50% when bringing clients or guests', NULL);


-- ---------------------------------------------------------------------------
-- SEGMENT ↔ ARCHETYPE AFFINITY
-- ---------------------------------------------------------------------------

-- Source: behavioral_intelligence_module.md + utils.py SEGMENT_TOP_ARCHETYPES

INSERT INTO segment_archetype_affinity (segment_id, archetype_id, affinity_rank)
SELECT s.id, a.id, x.rank FROM (VALUES
    -- Office Workers
    ('office_workers', 'habit_former',      1),
    ('office_workers', 'lifestyle_regular', 2),
    ('office_workers', 'trusted_regular',   3),
    ('office_workers', 'power_regular',     4),

    -- Social Crowd
    ('college_kids', 'party_seeker',     1),
    ('college_kids', 'scene_seeker',     2),
    ('college_kids', 'trend_hunter',     3),

    -- Couples
    ('couples', 'calm_pairs',       1),
    ('couples', 'lifestyle_regular',2),
    ('couples', 'quiet_discoverer', 3),

    -- Families
    ('families', 'habit_former',      1),
    ('families', 'lifestyle_regular', 2),

    -- Premium Diners
    ('premium', 'premium_prioritizer', 1),
    ('premium', 'trusted_regular',     2),
    ('premium', 'lifestyle_regular',   3),

    -- Solo Diners
    ('solo_diners', 'quiet_discoverer',  1),
    ('solo_diners', 'habit_former',      2),
    ('solo_diners', 'lifestyle_regular', 3),
    ('solo_diners', 'discovery_explorer',4),

    -- Working Women
    ('working_women', 'lifestyle_regular', 1),
    ('working_women', 'scene_seeker',      2),
    ('working_women', 'trusted_regular',   3)
) AS x(seg_key, arch_key, rank)
JOIN segment_behavioral_profiles s ON s.segment_key = x.seg_key
JOIN archetype_behavioral_profiles a ON a.archetype_key = x.arch_key;
