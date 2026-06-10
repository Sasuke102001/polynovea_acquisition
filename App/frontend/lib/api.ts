/**
 * lib/api.ts
 * Typed API client for the Polynovea Acquisition System.
 * Matches FastAPI Pydantic models in backend/models.py exactly.
 */

// Server components (SSR on Vercel): fetch EC2 directly — server-to-server, no mixed-content restriction.
// Client components (browser): use relative URL so Vercel rewrite proxies to EC2 (avoids HTTPS→HTTP block).
const API_BASE =
  typeof window === "undefined"
    ? (process.env.BACKEND_URL ?? "http://localhost:8000")
    : "";

// ─── Shared atoms ─────────────────────────────────────────────────────────────

export interface ArchetypeChip {
  name: string;
  demographic_label: string;
}

export interface FitnessDimension {
  key: string;
  label: string;
  score: number;
}

export interface DeltaBar {
  dimension: string;
  label: string;
  client_score: number;
  similar_score: number;
  delta: number;
  direction: string;   // "higher" | "lower" | "neutral"
  short_label: string;
  client_statement: string;
}

// ─── Screen 1: Venue Search ───────────────────────────────────────────────────

export interface VenueCard {
  id: number;
  place_id: string;
  name: string;
  area: string;
  city: string;
  types: string[];
  top_segments: string[];
  top_archetypes: ArchetypeChip[];
  health_score: number;
}

export interface SearchResponse {
  venues: VenueCard[];
  total: number;
  limit: number;
  offset: number;
}

export async function searchVenues(
  q: string,
  city?: string,
  venueType?: string,
  limit = 20,
  offset = 0,
): Promise<SearchResponse> {
  const params = new URLSearchParams({
    q,
    limit: String(limit),
    offset: String(offset),
  });
  if (city) params.set("city", city);
  if (venueType) params.set("venue_type", venueType);
  const res = await fetch(`${API_BASE}/api/venues/search?${params}`, {
    cache: "no-store",
  });
  if (!res.ok) throw new Error(`Search failed: ${res.status}`);
  return res.json() as Promise<SearchResponse>;
}

// ─── Screen 5: Overview ───────────────────────────────────────────────────────

export interface VenueHeader {
  id: number;
  name: string;
  area: string;
  city: string;
  types: string[];
}

export interface SegmentRow {
  segment_id: string;
  segment_name: string;
  demographic_label: string;
  alignment_score: number;
  alignment_pct: number;
  archetypes: ArchetypeChip[];
}

export interface ArchetypeBar {
  name: string;
  demographic_label: string;
  prevalence_pct: number;
}

export interface CustomerProfile {
  top_segments: SegmentRow[];
  archetype_distribution: ArchetypeBar[];
}

export interface HealthScore {
  score: number;
  label: string;
  operational_quality: number;
  retention_strength: number;
  data_confidence?: string;   // "HIGH" | "MED" | "LOW" — non-zero radar dim count
}

export interface InsightCard {
  title: string;
  subtitle: string;
  priority_tier: string;
}

export interface OverviewResponse {
  venue: VenueHeader;
  fitness_radar: { dimensions: FitnessDimension[] };
  customer_profile: CustomerProfile;
  health_score: HealthScore;
  working_for_you: InsightCard[];
  gaps_to_close: InsightCard[];
}

export async function getOverview(venueId: string | number): Promise<OverviewResponse> {
  const res = await fetch(`${API_BASE}/api/venues/${venueId}/overview`, {
    cache: "no-store",
  });
  if (!res.ok) throw new Error(`Overview failed: ${res.status}`);
  return res.json() as Promise<OverviewResponse>;
}

// ─── Screen 2: Competitors ────────────────────────────────────────────────────

export interface SimilarVenueCard {
  id: number;
  name: string;
  area: string;
  city: string;
  types: string[];
  top_archetypes: ArchetypeChip[];
  top_segments: string[];
  delta_bars: DeltaBar[];
  similarity_score: number;
  rank: number;
  tier?: string | null;          // Transform only: "role_model" | "bridge" | "transition" | "pure_target"
  effort_label?: string | null;  // Transform only: "Quick Win" | "Major Initiative" | "Strategic Pivot"
}

export interface ClientVenueCard {
  id: number;
  name: string;
  area: string;
  city: string;
  types: string[];
  top_archetypes: ArchetypeChip[];
  top_segments: string[];
  fitness_scores: FitnessDimension[];
}

export interface CompetitorsResponse {
  client_venue: ClientVenueCard;
  similar_venues: SimilarVenueCard[];
  total_similar: number;
  offset: number;
  limit: number;
  insight_callout: string;
}

export async function getCompetitors(
  venueId: string | number,
  limit = 3,
  offset = 0,
): Promise<CompetitorsResponse> {
  const res = await fetch(
    `${API_BASE}/api/venues/${venueId}/similar?limit=${limit}&offset=${offset}`,
    { cache: "no-store" },
  );
  if (!res.ok) throw new Error(`Competitors failed: ${res.status}`);
  return res.json() as Promise<CompetitorsResponse>;
}

// ─── Screen 3: Transform ─────────────────────────────────────────────────────

export interface SegmentOption {
  segment_id: string;
  segment_name: string;
  demographic_label: string;
  is_current: boolean;
  current_alignment_pct: number;
}

export interface TransformResponse {
  current_segments: SegmentOption[];
  target_segment: SegmentOption | null;
  similar_venues: SimilarVenueCard[];
  total_similar: number;
  offset: number;
  limit: number;
  gap_callout: string;
}

export async function getTransform(
  venueId: string | number,
  targetSegment?: string,
  limit = 3,
  offset = 0,
): Promise<TransformResponse> {
  const params = new URLSearchParams({
    limit: String(limit),
    offset: String(offset),
  });
  if (targetSegment) params.set("target_segment", targetSegment);
  const res = await fetch(
    `${API_BASE}/api/venues/${venueId}/transform?${params}`,
    { cache: "no-store" },
  );
  if (!res.ok) throw new Error(`Transform failed: ${res.status}`);
  return res.json() as Promise<TransformResponse>;
}

// ─── Screen 4: Marketing ─────────────────────────────────────────────────────

export interface MarketingSegmentCard {
  segment_id: string;
  segment_name: string;
  demographic_label: string;
  alignment_pct: number;
  top_archetype: ArchetypeChip;
  visit_time: string;
}

export interface CreativeAngle {
  what: string;
  avoid: string;
  audio: string;
  rationale: string;
}

export interface ChannelCard {
  channel: string;
  channel_label: string;
  mechanism: string;
  mechanism_label: string;
  effectiveness_score: number;
  roi_lift_min: number;
  roi_lift_max: number;
  roi_label: string;
  why_it_works: string;
  target_segments: string[];
  primary_use_case: string;
  badge: string | null;
  message_template: string | null;
  action_checklist: string[] | null;
  creative_angle: CreativeAngle | null;
  copy_hooks: string[] | null;
  send_timing: string | null;
}

export interface NotRecommendedItem {
  channel: string;
  channel_label: string;
  reason: string;
}

export interface GrowthTargetSection {
  target_segment_id: string;
  target_segment_name: string;
  demographic_label: string;
  acquisition_channels: ChannelCard[];
  retention_channel: ChannelCard;
}

export interface MarketingResponse {
  top_segments: MarketingSegmentCard[];
  acquisition_channels: ChannelCard[];
  retention_channels: ChannelCard[];
  consulting_channels: ChannelCard[];
  not_recommended: NotRecommendedItem[];
  growth_target?: GrowthTargetSection | null;
}

export async function getMarketing(
  venueId: string | number,
  targetSegment?: string,
): Promise<MarketingResponse> {
  const params = new URLSearchParams();
  if (targetSegment) params.set("target_segment", targetSegment);
  const qs = params.toString();
  const res = await fetch(
    `${API_BASE}/api/venues/${venueId}/marketing${qs ? `?${qs}` : ""}`,
    { cache: "no-store" },
  );
  if (!res.ok) throw new Error(`Marketing failed: ${res.status}`);
  return res.json() as Promise<MarketingResponse>;
}

// ─── Screen 6: Deep Analysis / Risk ─────────────────────────────────────────

export interface ChurnRisk {
  level: string;   // "HIGH" | "MED" | "LOW"
  score: number;
  label: string;
}

export interface RiskResponse {
  venue_name: string;
  venue_area: string;
  churn_risk: ChurnRisk;
  critical_interventions: RecommendationRow[];
  friction_items: RecommendationRow[];
}

export async function getRisk(venueId: string | number): Promise<RiskResponse> {
  const res = await fetch(`${API_BASE}/api/venues/${venueId}/risk`, {
    cache: "no-store",
  });
  if (!res.ok) throw new Error(`Risk failed: ${res.status}`);
  return res.json() as Promise<RiskResponse>;
}

// ─── Screen 6: Deep Analysis / Primitives ────────────────────────────────────

export interface PrimitiveScore {
  primitive_id: string;
  label: string;
  score: number;
  category: string;    // "Atmosphere" | "Social" | "Food" | "Service" | "Signals"
  has_signal: boolean;
}

export interface PrimitiveConflict {
  primitive_a: string;
  primitive_b: string;
  reason: string;
}

export interface PrimitiveGroup {
  category: string;
  primitives: PrimitiveScore[];
}

export interface PrimitivesResponse {
  venue_name: string;
  venue_area: string;
  groups: PrimitiveGroup[];
  top_5: PrimitiveScore[];
  bottom_5: PrimitiveScore[];
  conflicts: PrimitiveConflict[];
  total_scored: number;
}

export async function getPrimitives(venueId: string | number): Promise<PrimitivesResponse> {
  const res = await fetch(`${API_BASE}/api/venues/${venueId}/primitives`, {
    cache: "no-store",
  });
  if (!res.ok) throw new Error(`Primitives failed: ${res.status}`);
  return res.json() as Promise<PrimitivesResponse>;
}

// ─── Screen 6: Deep Analysis / Intelligence ──────────────────────────────────

export interface RecommendationRow {
  intervention_type: string;
  title: string;
  description: string;
  priority_tier: string;
  fit_score: number;
  expected_impact: string;
  recommended: boolean;
}

export interface RevenueLever {
  label: string;
  status: string;
  sub: string;
}

export interface PricingPower {
  monetization_potential: number;
  headroom_label: string;
  revenue_levers: RevenueLever[];
}

export interface ArchetypeIntervention {
  archetype_name: string;
  intervention_type: string;
  description: string;
  expected_roi: string | null;
}

export interface IntelligenceResponse {
  recommendations: RecommendationRow[];
  archetype_distribution: ArchetypeBar[];
  pricing_power: PricingPower;
  archetype_interventions: ArchetypeIntervention[];
}

export async function getIntelligence(venueId: string | number): Promise<IntelligenceResponse> {
  const res = await fetch(`${API_BASE}/api/venues/${venueId}/intelligence`, {
    cache: "no-store",
  });
  if (!res.ok) throw new Error(`Intelligence failed: ${res.status}`);
  return res.json() as Promise<IntelligenceResponse>;
}

// ─── Screen 6: Deep Analysis / Benchmarks ───────────────────────────────────

export interface BenchmarkBar {
  dimension: string;
  label: string;
  client_score: number;
  city_avg: number;
  peer_avg: number;
  client_percentile: number;
}

export interface BenchmarksResponse {
  venue_name: string;
  venue_area: string;
  city: string;
  benchmark_bars: BenchmarkBar[];
  city_comparison: string;
  peer_insight: string;
}

export async function getBenchmarks(venueId: string | number): Promise<BenchmarksResponse> {
  const res = await fetch(`${API_BASE}/api/venues/${venueId}/benchmarks`, {
    cache: "no-store",
  });
  if (!res.ok) throw new Error(`Benchmarks failed: ${res.status}`);
  return res.json() as Promise<BenchmarksResponse>;
}

// ─── Screen 6: Deep Analysis / Trends ───────────────────────────────────────

export interface TrendSignal {
  pattern_description: string;
  confidence: number;
  trend_direction: string;
  signal_label: string;
}

export interface RisingPattern {
  pattern_name: string;
  confidence: number;
  prevalence_pct: number;
  status: string;
}

export interface TrendsResponse {
  venue_name: string;
  venue_area: string;
  trend_signals: TrendSignal[];
  rising_patterns: RisingPattern[];
  insight_callout: string;
}

export async function getTrends(venueId: string | number): Promise<TrendsResponse> {
  const res = await fetch(`${API_BASE}/api/venues/${venueId}/trends`, {
    cache: "no-store",
  });
  if (!res.ok) throw new Error(`Trends failed: ${res.status}`);
  return res.json() as Promise<TrendsResponse>;
}

// ─── Audience Tab ─────────────────────────────────────────────────────────────

export interface AudiencePlatformRow {
  platform: string;
  usage_type: string;
  strength: string;
}

export interface OccasionMultiplier {
  occasion_label: string;
  multiplier_min: number;
  multiplier_max: number;
  notes: string | null;
}

export interface SpendTrigger {
  archetype_name: string;
  trigger_text: string;
  staff_script: string | null;
}

export interface AudienceSegmentProfile {
  segment_id: string;
  segment_name: string;
  alignment_pct: number;
  segment_rank: number;
  // Spend composition
  food_pct_min: number | null;
  food_pct_max: number | null;
  alcohol_pct_min: number | null;
  alcohol_pct_max: number | null;
  dessert_attach_pct_min: number | null;
  dessert_attach_pct_max: number | null;
  avg_check_vs_baseline_pct_min: number | null;
  avg_check_vs_baseline_pct_max: number | null;
  // Alcohol
  alcohol_affinity: string;        // "low" | "low_medium" | "medium" | "medium_high" | "high" | "very_high"
  alcohol_affinity_score: number;  // 0.0–1.0
  alcohol_primary_driver: string;  // "habit" | "social_occasion" | "identity" | "fomo" | "discovery"
  beverage_preference: string | null;
  // Group
  peer_influence_coefficient: number;
  // Dwell & economics
  dwell_min_minutes: number | null;
  dwell_max_minutes: number | null;
  revpash_min_inr: number | null;
  revpash_max_inr: number | null;
  diminishing_returns_minutes: number | null;
  // Loyalty
  repeat_tendency_pct_min: number | null;
  repeat_tendency_pct_max: number | null;
  repeat_window_days: number | null;
  wom_multiplier_min: number | null;
  wom_multiplier_max: number | null;
  discovery_rate: string;
  // Triggers
  primary_trigger: string | null;
  low_to_high_spend_trigger: string | null;
  // Related
  top_archetypes: ArchetypeChip[];
  platforms: AudiencePlatformRow[];
  occasion_multipliers: OccasionMultiplier[];
  spend_triggers: SpendTrigger[];
}

export interface AudienceAggregate {
  alcohol_affinity_score: number;
  alcohol_affinity_label: string;
  expected_revpash_min: number;
  expected_revpash_max: number;
  avg_wom_multiplier: number;
  avg_peer_influence: number;
  dominant_discovery_platform: string;
  structural_insight: string;
}

export interface AudienceResponse {
  venue_id: number;
  venue_name: string;
  venue_area: string;
  segment_profiles: AudienceSegmentProfile[];
  aggregate: AudienceAggregate;
}

export async function getAudience(venueId: string | number): Promise<AudienceResponse> {
  const res = await fetch(`${API_BASE}/api/venues/${venueId}/audience`, {
    cache: "no-store",
  });
  if (!res.ok) throw new Error(`Audience failed: ${res.status}`);
  return res.json() as Promise<AudienceResponse>;
}

export async function getAllSegments(): Promise<{ segments: AudienceSegmentProfile[] }> {
  const res = await fetch(`${API_BASE}/api/venues/segments`, {
    cache: "force-cache",
  });
  if (!res.ok) throw new Error(`Segments failed: ${res.status}`);
  return res.json() as Promise<{ segments: AudienceSegmentProfile[] }>;
}

// ─── Ad Brief Generator ───────────────────────────────────────────────────────

export interface PlatformBriefRules {
  format: string;
  hook_style: string;
  cta: string;
  dont: string[];
}

export interface AdBrief {
  venue_name: string;
  venue_area: string;
  target_segment: string;
  target_archetype: string;
  channel: string;
  channel_label: string;
  tone: string;
  emotional_driver: string;
  hook: string;
  cta: string;
  visual_direction: string;
  india_rules: string[];
  trust_first: boolean;
  language_rec: string;
  occasion_anchor: string | null;
  dont_say: string[];
  anti_pattern_flags: string[];
  platform_rules: PlatformBriefRules;
  copy_hooks: string[];
  data_confidence: string;
}

// ─── Competitor Deep Dive ─────────────────────────────────────────────────────

export interface CompetitorInsight {
  dimension: string;
  label: string;
  client_score: number;
  competitor_score: number;
  delta: number;           // competitor − client (positive = competitor stronger)
  narrative: string;       // AI-generated, objective analytical text
}

export interface CompetitorDeepDive {
  client_name: string;
  competitor_id: number;
  competitor_name: string;
  competitor_area: string;
  competitor_city: string;
  competitor_types: string[];
  bucket_label: string;    // "Direct Peer" | "Close Match" | "Partial Match" | "Segment Match"
  learn_from: CompetitorInsight[];
  avoid: CompetitorInsight[];
  strategic_brief: string;
}

export async function getCompetitorDeepDive(
  venueId: string | number,
  compId: string | number,
): Promise<CompetitorDeepDive> {
  const res = await fetch(
    `${API_BASE}/api/venues/${venueId}/competitor/${compId}`,
    { cache: "no-store" },
  );
  if (!res.ok) throw new Error(`Competitor deep dive failed: ${res.status}`);
  return res.json() as Promise<CompetitorDeepDive>;
}

export async function getAdBrief(
  venueId: string | number,
  channel?: string,
  segment?: string,
): Promise<AdBrief> {
  const params = new URLSearchParams();
  if (channel) params.set("channel", channel);
  if (segment) params.set("segment", segment);
  const qs = params.toString();
  const res = await fetch(
    `${API_BASE}/api/venues/${venueId}/marketing/brief${qs ? `?${qs}` : ""}`,
    { cache: "no-store" },
  );
  if (!res.ok) throw new Error(`Ad brief failed: ${res.status}`);
  return res.json() as Promise<AdBrief>;
}
