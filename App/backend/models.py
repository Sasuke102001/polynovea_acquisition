"""
models.py
Pydantic response models for all API endpoints.
One model per screen / section — keeps routers clean.
"""

from pydantic import BaseModel
from typing import Any


# ─── Shared atoms ────────────────────────────────────────────────────────────

class ArchetypeChip(BaseModel):
    name: str
    demographic_label: str   # "Loyal weekday diners · 26–35 · office crowd"


class FitnessDimension(BaseModel):
    key: str                 # "fitness_for_office_lunch"
    label: str               # "Office Lunch"
    score: float             # 0.0 – 1.0


class DeltaBar(BaseModel):
    dimension: str           # "fitness_for_office_lunch"
    label: str               # "Office Lunch"
    client_score: float
    similar_score: float
    delta: float             # similar − client (positive = similar is better)
    direction: str           # "higher" | "lower" | "neutral"
    short_label: str         # "Stronger"
    client_statement: str    # plain-English statement for the UI


# ─── Screen 1 — Venue Search ─────────────────────────────────────────────────

class VenueCard(BaseModel):
    id: int
    place_id: str
    name: str
    area: str
    city: str
    types: list[str]              # ["Casual Dine", "Bar"]  (display-friendly)
    top_segments: list[str]       # top 2 segment display names
    top_archetypes: list[ArchetypeChip]   # top 2
    health_score: int             # 0–100 composite of operational_quality + retention_strength


class SearchResponse(BaseModel):
    venues: list[VenueCard]
    total: int
    limit: int
    offset: int


# ─── Screen 5 — Overview Tab ─────────────────────────────────────────────────

class VenueHeader(BaseModel):
    id: int
    name: str
    area: str
    city: str
    types: list[str]


class FitnessRadar(BaseModel):
    dimensions: list[FitnessDimension]   # 5 core dimensions for radar


class SegmentRow(BaseModel):
    segment_id: str
    segment_name: str        # "Office Workers"
    demographic_label: str   # "26–35 · Weekday lunch · Solo or pairs"
    alignment_score: float
    alignment_pct: int       # 0–100 for display
    archetypes: list[ArchetypeChip]


class ArchetypeBar(BaseModel):
    name: str
    demographic_label: str
    prevalence_pct: int


class CustomerProfile(BaseModel):
    top_segments: list[SegmentRow]       # top 2
    archetype_distribution: list[ArchetypeBar]   # top 5


class HealthScore(BaseModel):
    score: int               # 0–100
    label: str               # "GOOD" | "STRONG" | "NEEDS WORK" | "AT RISK"
    operational_quality: float
    retention_strength: float
    data_confidence: str = "MED"   # "HIGH" | "MED" | "LOW" — non-zero radar dim count


class InsightCard(BaseModel):
    title: str
    subtitle: str
    priority_tier: str       # CRITICAL / HIGH / MEDIUM / LOW  (for working: blank)


class OverviewResponse(BaseModel):
    venue: VenueHeader
    fitness_radar: FitnessRadar
    customer_profile: CustomerProfile
    health_score: HealthScore
    working_for_you: list[InsightCard]   # top 3 recommended=true interventions
    gaps_to_close: list[InsightCard]     # top 3 recommended=false interventions


# ─── Screen 2 — Competitors Tab ──────────────────────────────────────────────

class SimilarVenueCard(BaseModel):
    id: int
    name: str
    area: str
    city: str
    types: list[str]
    top_archetypes: list[ArchetypeChip]
    top_segments: list[str]             # segment display names
    delta_bars: list[DeltaBar]          # 8 pre-computed, UI shows 3 at a time
    similarity_score: float
    rank: int
    tier: str | None = None             # Transform only: "role_model" | "bridge" | "transition" | "pure_target"
    effort_label: str | None = None     # Transform only: "Quick Win" | "Major Initiative" | "Strategic Pivot"


class ClientVenueCard(BaseModel):
    id: int
    name: str
    area: str
    city: str
    types: list[str]
    top_archetypes: list[ArchetypeChip]
    top_segments: list[str]
    fitness_scores: list[FitnessDimension]   # all 8


class CompetitorsResponse(BaseModel):
    client_venue: ClientVenueCard
    similar_venues: list[SimilarVenueCard]
    total_similar: int       # total available for pagination
    offset: int
    limit: int
    insight_callout: str     # auto-generated from largest delta


# ─── Competitor Deep Dive ─────────────────────────────────────────────────────

class CompetitorInsight(BaseModel):
    dimension: str
    label: str
    client_score: float
    competitor_score: float
    delta: float           # competitor − client (positive = competitor stronger)
    narrative: str         # AI-generated, objective analytical tone


class CompetitorDeepDive(BaseModel):
    client_name: str
    competitor_id: int
    competitor_name: str
    competitor_area: str
    competitor_city: str
    competitor_types: list[str]
    bucket_label: str      # "Direct Peer" | "Close Match" | "Partial Match" | "Segment Match"
    learn_from: list[CompetitorInsight]   # top 3 where competitor > client
    avoid: list[CompetitorInsight]        # top 3 where client > competitor
    strategic_brief: str                  # AI-generated 2–3 sentence overview


# ─── Screen 3 — Transform Tab ────────────────────────────────────────────────

class SegmentOption(BaseModel):
    segment_id: str
    segment_name: str
    demographic_label: str
    is_current: bool         # true = venue already attracts this segment
    current_alignment_pct: int


class TransformResponse(BaseModel):
    current_segments: list[SegmentOption]
    target_segment: SegmentOption | None
    similar_venues: list[SimilarVenueCard]   # filtered by target segment
    total_similar: int
    offset: int
    limit: int
    gap_callout: str         # biggest fitness gap to close for target segment


# ─── Screen 4 — Marketing Tab ────────────────────────────────────────────────

class MarketingSegmentCard(BaseModel):
    segment_id: str
    segment_name: str        # "Office Workers"
    demographic_label: str   # "26–35 · Weekday lunch"
    alignment_pct: int
    top_archetype: ArchetypeChip
    visit_time: str          # "Weekday lunch"


class ChannelCard(BaseModel):
    channel: str             # "instagram_reels"
    channel_label: str       # "Instagram Reels"
    mechanism: str           # "environmental_expectation"
    mechanism_label: str     # "Environmental Expectation"
    effectiveness_score: float   # 1–10
    roi_lift_min: int
    roi_lift_max: int
    roi_label: str           # "+15–25% new customers"
    why_it_works: str        # personalised from venue fitness profile
    target_segments: list[str]
    primary_use_case: str    # "acquisition" | "retention"
    badge: str | None        # "#1 RECOMMENDED" | "PRIMARY" | None
    message_template: str | None    # WhatsApp/Email template text
    action_checklist: list[str] | None   # Zomato/Swiggy checklist
    creative_angle: dict | None = None   # Instagram: {what, avoid, audio, rationale}
    copy_hooks: list[str] | None = None  # 3 segment-specific hooks (research-validated)
    send_timing: str | None = None       # WhatsApp: optimal send window by segment


class NotRecommendedItem(BaseModel):
    channel: str
    channel_label: str
    reason: str


class GrowthTargetSection(BaseModel):
    target_segment_id: str
    target_segment_name: str
    demographic_label: str
    acquisition_channels: list[ChannelCard]   # top-2 acquisition, re-scored for target
    retention_channel: ChannelCard            # WhatsApp — converting current customers


class MarketingResponse(BaseModel):
    top_segments: list[MarketingSegmentCard]
    acquisition_channels: list[ChannelCard]
    retention_channels: list[ChannelCard]
    consulting_channels: list[ChannelCard] = []   # advice Polynovea gives but does not execute
    not_recommended: list[NotRecommendedItem]
    growth_target: "GrowthTargetSection | None" = None   # present when ?target_segment= is set


# ─── Screen 6 — Deep Analysis: Risk Tab ─────────────────────────────────────

class ChurnRisk(BaseModel):
    level: str          # "HIGH" | "MED" | "LOW"
    score: float        # retention_strength 0–1
    label: str          # human-readable explanation


class RiskResponse(BaseModel):
    venue_name: str
    venue_area: str
    churn_risk: ChurnRisk
    critical_interventions: list["RecommendationRow"]   # CRITICAL/HIGH priority (or best available)
    friction_items: list["RecommendationRow"]            # friction/barrier intervention types


# ─── Screen 6 — Deep Analysis: Primitives Tab ────────────────────────────────

class PrimitiveScore(BaseModel):
    primitive_id: str   # "live_music"
    label: str          # "Live Music"
    score: float        # 0.0–1.0
    category: str       # "Atmosphere" | "Social" | "Food" | "Service" | "Signals"
    has_signal: bool    # True if scored in primitives_scores


class PrimitiveConflict(BaseModel):
    primitive_a: str    # primitive_id
    primitive_b: str    # primitive_id
    reason: str         # plain-English explanation


class PrimitiveGroup(BaseModel):
    category: str
    primitives: list[PrimitiveScore]


class PrimitivesResponse(BaseModel):
    venue_name: str
    venue_area: str
    groups: list[PrimitiveGroup]   # grouped by category, sorted by score
    top_5: list[PrimitiveScore]
    bottom_5: list[PrimitiveScore]
    conflicts: list[PrimitiveConflict]
    total_scored: int


# ─── Screen 6 — Deep Analysis: Intelligence Tab ──────────────────────────────

class RecommendationRow(BaseModel):
    intervention_type: str
    title: str               # human-readable from intervention_type
    description: str
    priority_tier: str       # CRITICAL | HIGH | MEDIUM | LOW
    fit_score: float
    expected_impact: str     # from tier_description
    recommended: bool


class PricingPower(BaseModel):
    monetization_potential: float
    headroom_label: str      # "HIGH" | "MED" | "LOW"
    revenue_levers: list[dict[str, Any]]   # [{label, status, sub}]


class ArchetypeIntervention(BaseModel):
    archetype_name: str
    intervention_type: str
    description: str
    expected_roi: str | None


class IntelligenceResponse(BaseModel):
    recommendations: list[RecommendationRow]
    archetype_distribution: list[ArchetypeBar]
    pricing_power: PricingPower
    archetype_interventions: list[ArchetypeIntervention]


# ─── Screen 6 — Deep Analysis: Benchmarks Tab ──────────────────────────────

class BenchmarkBar(BaseModel):
    dimension: str           # "fitness_for_office_lunch"
    label: str               # "Office Lunch"
    client_score: float      # 0.0–1.0
    city_avg: float
    peer_avg: float          # top 25 similar venues by segment
    client_percentile: int   # 0–100: where client sits vs city


class BenchmarksResponse(BaseModel):
    venue_name: str
    venue_area: str
    city: str
    benchmark_bars: list[BenchmarkBar]
    city_comparison: str     # "Above city average" | "Below city average"
    peer_insight: str        # "Best performer on Office Lunch" | "Lagging on Social Dwell"


# ─── Screen 6 — Deep Analysis: Trends Tab ───────────────────────────────────

class TrendSignal(BaseModel):
    pattern_description: str
    confidence: float        # 0.0–1.0
    trend_direction: str     # "emerging" | "declining" | "stable"
    signal_label: str        # "Emerging" | "Declining" friendly label


class RisingPattern(BaseModel):
    pattern_name: str
    confidence: float        # from pattern_scores.confidence_score
    prevalence_pct: float    # pattern_scores.prevalence
    status: str              # "Rising" | "Stable" | "Declining"


class TrendsResponse(BaseModel):
    venue_name: str
    venue_area: str
    trend_signals: list[TrendSignal]      # top emerging/declining signals
    rising_patterns: list[RisingPattern]   # top 5 by confidence
    insight_callout: str                   # "Emerging pattern: [description]"


# ─── Audience Tab ─────────────────────────────────────────────────────────────

class AudiencePlatformRow(BaseModel):
    platform: str
    usage_type: str
    strength: str


class OccasionMultiplier(BaseModel):
    occasion_label: str
    multiplier_min: float
    multiplier_max: float
    notes: str | None


class SpendTrigger(BaseModel):
    archetype_name: str
    trigger_text: str
    staff_script: str | None


class AudienceSegmentProfile(BaseModel):
    segment_id: str
    segment_name: str
    alignment_pct: float
    segment_rank: int
    # Spend composition
    food_pct_min: int | None
    food_pct_max: int | None
    alcohol_pct_min: int | None
    alcohol_pct_max: int | None
    dessert_attach_pct_min: int | None
    dessert_attach_pct_max: int | None
    avg_check_vs_baseline_pct_min: int | None
    avg_check_vs_baseline_pct_max: int | None
    # Alcohol
    alcohol_affinity: str           # "low", "medium", "high", etc.
    alcohol_affinity_score: float   # 0.0–1.0 normalised
    alcohol_primary_driver: str     # "habit", "social_occasion", "identity", "fomo"
    beverage_preference: str | None
    # Group dynamics
    peer_influence_coefficient: float
    # Dwell & economics
    dwell_min_minutes: int | None
    dwell_max_minutes: int | None
    revpash_min_inr: int | None
    revpash_max_inr: int | None
    diminishing_returns_minutes: int | None
    # Loyalty
    repeat_tendency_pct_min: int | None
    repeat_tendency_pct_max: int | None
    repeat_window_days: int | None
    wom_multiplier_min: float | None
    wom_multiplier_max: float | None
    discovery_rate: str
    # Triggers
    primary_trigger: str | None
    low_to_high_spend_trigger: str | None
    # Related
    top_archetypes: list[ArchetypeChip]
    platforms: list[AudiencePlatformRow]
    occasion_multipliers: list[OccasionMultiplier]
    spend_triggers: list[SpendTrigger]


class AudienceAggregate(BaseModel):
    alcohol_affinity_score: float    # 0.0–1.0 weighted average across top segments
    alcohol_affinity_label: str      # "Low", "Low-Medium", "Medium", "Medium-High", "High"
    expected_revpash_min: int
    expected_revpash_max: int
    avg_wom_multiplier: float
    avg_peer_influence: float
    dominant_discovery_platform: str
    structural_insight: str          # the "your mix is structurally X" paragraph


class AudienceResponse(BaseModel):
    venue_id: int
    venue_name: str
    venue_area: str
    segment_profiles: list[AudienceSegmentProfile]
    aggregate: AudienceAggregate


# ─── Ad Brief Generator ──────────────────────────────────────────────────────────

class PlatformBriefRules(BaseModel):
    format: str
    hook_style: str
    cta: str
    dont: list[str]


class AdBrief(BaseModel):
    venue_name: str
    venue_area: str
    target_segment: str           # "Office Workers"
    target_archetype: str         # "Habit Former"
    channel: str                  # "whatsapp"
    channel_label: str            # "WhatsApp Broadcast"

    # Creative brief
    tone: str
    emotional_driver: str         # "habit_formation + reciprocity"
    hook: str                     # hook formula description
    cta: str
    visual_direction: str

    # India-specific layer
    india_rules: list[str]        # critical India rules for this archetype + channel
    trust_first: bool             # mandate trust signals before scarcity/urgency
    language_rec: str             # "Hinglish" | "Regional" | "English-ok"
    occasion_anchor: str | None   # festival/cultural calendar suggestion

    # Anti-patterns
    dont_say: list[str]
    anti_pattern_flags: list[str]

    # Platform rules
    platform_rules: PlatformBriefRules

    # Ready-to-use copy starters
    copy_hooks: list[str]

    data_confidence: str          # "HIGH" | "MED" | "LOW"


# ─── Brief Content Generator ─────────────────────────────────────────────────────

class BriefGenerateRequest(BaseModel):
    direction: str = ""   # optional user direction; empty = AI picks


# ─── Chat ───────────────────────────────────────────────────────────────────────

class ChatRequest(BaseModel):
    tab: str        # "marketing", "competitors", "transform", "deep_risk"
    question: str
    mode: str = "fast"   # "fast" = single model | "council" = 3-model debate


class ChatMessage(BaseModel):
    role: str       # "user" | "assistant"
    content: str
