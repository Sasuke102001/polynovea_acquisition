# Polynovea Acquisition System — Full Technical Documentation

**Version:** 5.0 | **Date:** 2026-05-27 | **Scope:** All scripts, loaders, schemas, primitives, clusters, fitness scoring, research foundation, system narrative with full conditional logic and per-finding research attribution. Includes research extraction pipeline and structured AI prompt layer.

---

## Table of Contents

0. [System Narrative — What This Is and Why It Exists](#0-system-narrative--what-this-is-and-why-it-exists)
1. [System Overview](#1-system-overview)
2. [Architecture](#2-architecture)
3. [Database Schema](#3-database-schema)
4. [Behavioral Framework](#4-behavioral-framework)
   - 4.1 [54 Behavioral Primitives](#41-54-behavioral-primitives)
   - 4.2 [7 Customer Segments](#42-7-customer-segments)
   - 4.3 [11 Archetypes](#43-11-archetypes)
   - 4.4 [Fitness Dimensions](#44-fitness-dimensions)
   - 4.5 [Behavioral Mechanisms](#45-behavioral-mechanisms)
5. [Data Pipeline — Google Places API](#5-data-pipeline--google-places-api)
   - 5.1 [Step 1 — Venue Discovery](#51-step-1--venue-discovery)
   - 5.2 [Step 2c — Review Harvesting](#52-step-2c--review-harvesting)
   - 5.3 [Step 3 — Signal Extraction](#53-step-3--signal-extraction)
   - 5.4 [Step 4 — Pattern Recognition & Clustering](#54-step-4--pattern-recognition--clustering)
   - 5.5 [Step 4b — Governance Validation](#55-step-4b--governance-validation)
   - 5.6 [Step 5 — Behavioral Scoring](#56-step-5--behavioral-scoring)
   - 5.7 [Step 5b — Similarity Enrichment](#57-step-5b--similarity-enrichment)
   - 5.8 [Step 6 — Output & Interventions](#58-step-6--output--interventions)
6. [Data Pipeline — MagicPin Scraper](#6-data-pipeline--magicpin-scraper)
7. [Data Pipeline — Google Raw Scrapper](#7-data-pipeline--google-raw-scrapper)
8. [Database Loaders](#8-database-loaders)
9. [Blend Layer](#9-blend-layer)
10. [Backend API](#10-backend-api)
11. [Frontend](#11-frontend)
12. [Configuration Reference](#12-configuration-reference)
13. [Pipeline Orchestration](#13-pipeline-orchestration)
14. [Data Coverage](#14-data-coverage)
15. [Research Foundation — What Was Used for What](#15-research-foundation--what-was-used-for-what)
16. [BIF Pipeline Upgrade Log — 2026-05-25](#16-bif-pipeline-upgrade-log--2026-05-25)
17. [Research Extraction Pipeline — 2026-05-27](#17-research-extraction-pipeline--2026-05-27)

---

---

## 0. System Narrative — Detailed Conditional Walkthrough

This section traces the complete lifecycle of a piece of venue intelligence: from a single raw review sentence to a scored signal in PostgreSQL to a recommendation on a dashboard screen. At every step, it explains what the system does differently depending on the values it encounters — what happens when confidence is 0.40 versus 0.80, what a contradiction does to a score, when corroboration saturates, what triggers a different intervention tier.

---

### 0.1 The Fundamental Unit: A Signal

Everything in this system traces back to a single primitive signal detected in a single sentence of a customer review. A "signal" is not a sentiment score and not a keyword match — it is a structured evidence object with six properties:

| Property | Description | Example |
|---|---|---|
| `name` | Primitive identifier | `live_music` |
| `confidence` | 0.05–0.99, computed by formula | `0.80` |
| `evidence_weight` | 1.0 / 0.6 / 0.3 | `1.0` |
| `inference_type` | direct / derived / weak_inference | `direct` |
| `mention_count` | Times this signal appeared across reviews | `3` |
| `contradiction_count` | Times a contradicting signal also appeared | `0` |

When all reviews for a venue are processed, the result is a deduplicated set of highest-confidence signals — one per primitive. This set is the venue's behavioural fingerprint.

---

### 0.2 A Single Review Traced From Raw Text to Database

**Starting material.** One customer review, verbatim:
> "Came here on a Thursday night — absolutely packed and the live music was incredible. We ended up staying for three hours and ordered two more rounds."

The system processes this sentence-by-sentence. Here is every decision made:

---

#### STEP 3 — Signal Extraction

**Negation check (runs before every match).**
Before confirming any keyword match, the extractor checks the four tokens immediately preceding the matched phrase for negation tokens: `not`, `no`, `never`, `isn't`, `wasn't`, `don't`, `can't`, `without`, `barely`, `hardly`, and others. It also checks for negation substrings embedded in compound words. In the review above, no negation tokens precede any of the key phrases, so all matches proceed. If the review had said "the music was not live," the `live_music` signal would be suppressed entirely.

**Keyword matching.**
The extractor scans against `SIGNAL_KEYWORDS` — five factor groups (ambience, music, crowd, service, price), each containing a ranked list of keyword phrases. From this review:
- `live_music` — matched on the explicit phrase "live music" (music factor)
- `social_energy` — matched on "absolutely packed" (crowd factor, implied social density)
- `extended_stay` — matched on "staying for three hours" (temporal duration, ambience factor)
- `multi_round_ordering` — matched on "ordered two more rounds" (service/behaviour factor)

**Evidence weight assignment.**
Each match is scored by how explicitly it captures a behavioural fact:
- `live_music`: matched on exact phrase "live music" → `evidence_weight = 1.0` (explicit_behavior_phrase)
- `social_energy`: "absolutely packed" is a description of crowd state, not explicit behaviour → `evidence_weight = 0.6` (implied_behavior)
- `extended_stay`: "three hours" infers duration from a count noun → `evidence_weight = 0.6` (implied_behavior)
- `multi_round_ordering`: "two more rounds" is an explicit ordering fact → `evidence_weight = 1.0` (explicit_behavior_phrase)

**Inference type assignment** is set by the weight threshold:
- `evidence_weight ≥ 1.0` → `inference_type = "direct"`
- `evidence_weight ≥ 0.6` → `inference_type = "derived"`
- `evidence_weight < 0.6` → `inference_type = "weak_inference"`

**Priority calculation.**
Each keyword carries an index position in its ranked factor list. Keywords listed earlier (higher priority) score closer to 1.00. The formula:
```
priority = max(0.70, 1.00 - (keyword_index × 0.03))
```
If `live_music` is the first keyword in the music list (index 0): `priority = 1.00`
If a crowd-density keyword is at index 5 in the crowd list: `priority = max(0.70, 1.00 - 0.15) = 0.85`
If a keyword is at index 15: `priority = max(0.70, 1.00 - 0.45) = 0.70` — floor kicks in, no further penalty beyond index 10.

The priority list ordering is deliberate: keywords that appear earlier are those whose presence is more diagnostically useful. "live music" at index 0 matters more than "background music" at index 8.

**The signal confidence formula.** This is the core computation:
```
base                = 0.40
explicit_bonus      = 0.28 × evidence_weight
repetition_bonus    = min(0.20, 0.08 × max(0, mention_count - 1))
priority_bonus      = 0.12 × priority
contradiction_penalty = min(0.30, 0.12 × contradiction_count)

confidence = base + explicit_bonus + repetition_bonus + priority_bonus − contradiction_penalty
confidence = max(0.05, min(0.99, confidence))
```

**Working through `live_music` on first mention** (mention_count=1, no contradictions, priority=1.00):
```
confidence = 0.40 + (0.28 × 1.0) + 0 + (0.12 × 1.00) − 0
           = 0.40 + 0.28 + 0 + 0.12
           = 0.80
```
A single, explicitly-phrased signal with top priority starts at **0.80**. This is already in a range the system trusts.

**Working through `social_energy`** (weight=0.6, priority=0.85, no contradictions):
```
confidence = 0.40 + (0.28 × 0.6) + 0 + (0.12 × 0.85) − 0
           = 0.40 + 0.168 + 0 + 0.102
           = 0.67
```
An implied behavioural signal with good priority starts at **0.67** — moderate-high. The system notes it but holds less certainty than `live_music`.

**What happens when the second review also mentions live music** (mention_count=2):
```
repetition_bonus = 0.08 × 1 = 0.08
confidence = 0.40 + 0.28 + 0.08 + 0.12 = 0.88
```

**What happens when five reviews mention live music** (mention_count=5):
```
repetition_bonus = min(0.20, 0.08 × 4) = 0.20  ← cap reached
confidence = 0.40 + 0.28 + 0.20 + 0.12 = 1.00 → clamped to 0.99
```
The repetition bonus saturates at 5 additional mentions (the `min(0.20, ...)` cap). Once capped, more mentions no longer increase this signal's base confidence — instead they increase the pattern corroboration score in Step 4, which is tracked separately.

**What if only a vague keyword appears** — say, a reviewer writes "there was music" (not "live music"):
- Matched keyword is generic music, at a higher index (say index 6) → `priority = max(0.70, 1.00 - 0.18) = 0.82`
- Single keyword match, no explicit phrase → `evidence_weight = 0.3`
```
confidence = 0.40 + (0.28 × 0.3) + 0 + (0.12 × 0.82) − 0
           = 0.40 + 0.084 + 0 + 0.098
           = 0.582
```
This single weak match produces **0.58** confidence — a "derived" signal that sits below the HIGH tier but above the floor. It will appear in the venue's signal set but will score lower in Step 5 when evidence density is computed.

**What happens when a contradiction appears.**
Suppose a different review says: "the music was ear-splittingly loud and ruined the conversation." The `CONTRADICTION_RULES` contain the pair `(live_music, noise_rejection)`. When `noise_rejection` is extracted from this review, the system increments the `contradiction_count` for `live_music` and vice versa.

With one contradiction:
```
contradiction_penalty = min(0.30, 0.12 × 1) = 0.12
live_music confidence = 0.99 − 0.12 = 0.87
```

With three contradictions (a genuinely split venue):
```
contradiction_penalty = min(0.30, 0.12 × 3) = 0.30  ← cap reached
live_music confidence = 0.99 − 0.30 = 0.69
```

The maximum penalty is 0.30, hard-capped. **Contradictions never suppress a signal.** Both `live_music` (confidence 0.69) and `noise_rejection` (its own confidence score) are kept in the venue's signal set. This contradiction is flagged by `TENSION_RULES` and passed to Step 4 as a co-occurring contradiction cluster — itself a behavioural signal about the venue's environment.

**Venue-level aggregation.**
After all reviews are processed, if `live_music` appeared across 12 reviews with confidence values ranging from 0.60 to 0.99, the extractor keeps the **highest-confidence instance** — not an average, not a count. The venue-level signal for `live_music` is 0.99. The total mention count (12) feeds the repetition_bonus calculation above. The complete signal set for the venue is the union of all highest-confidence primitives detected across all reviews.

---

#### STEP 4 — Pattern Recognition and Clustering

**Co-occurrence detection.**
Step 4 scans the venue's signal set and finds every pair of signals that appeared together in at least one review. It extends this to triples (all combinations of 3 signals from the same review). From the example review:
- Pair: (`live_music`, `social_energy`)
- Pair: (`live_music`, `extended_stay`)
- Pair: (`live_music`, `multi_round_ordering`)
- Pair: (`social_energy`, `extended_stay`)
- Pair: (`social_energy`, `multi_round_ordering`)
- Pair: (`extended_stay`, `multi_round_ordering`)
- Triple: (`live_music`, `social_energy`, `extended_stay`)
- Triple: (`live_music`, `social_energy`, `multi_round_ordering`)
- …and so on for all combinations

Each co-occurrence group forms a candidate cluster. Clusters are deduplicated across reviews — the same pair appearing in 10 reviews counts as one cluster with 10 supporting evidence items, not 10 separate clusters.

**Cluster confidence formula (5 components):**
```
weighted_score  = sum(SIGNAL_WEIGHTS[s] for s in cluster_signals)
base_confidence = weighted_score / len(cluster_signals)
corroboration   = min(1.0, len(supporting_reviews) / 5.0)

cluster_confidence = (
    base_confidence × 0.35
  + pattern_stability × 0.25
  + evidence_diversity × 0.15
  + pattern_persistence × 0.10
  + corroboration × 0.15
)
# Clamped: min(0.95, max(0.05, cluster_confidence))
```

**What each component does:**

**`base_confidence` (35% weight):** The average SIGNAL_WEIGHT across all signals in the cluster. `SIGNAL_WEIGHTS` assigns higher weights to commercially diagnostic signals (`premium_pricing`, `repeat_visits`, `live_music`) and lower weights to ambient/generic signals (`nice_ambience`, `friendly_staff`). A cluster composed of commercially-strong signals starts with a higher base confidence.

**`corroboration` (15% weight):** How many distinct reviews support this cluster.
- 1 supporting review: `corroboration = 1/5 = 0.20`
- 3 supporting reviews: `corroboration = 3/5 = 0.60`
- 5 supporting reviews: `corroboration = 5/5 = 1.00` ← **saturated**
- 50 supporting reviews: `corroboration = min(1.0, 50/5) = 1.00` — same as 5

Corroboration saturates at 5 reviews. The difference between a 5-review cluster and a 50-review cluster is captured by `pattern_stability` and `evidence_diversity`, which improve with volume and temporal spread.

**`pattern_stability` (25% weight):** Measures how consistently this cluster appears across all reviews for the venue, not just the ones where it co-occurred:
```
stability = 1.0 − min(1.0, variance × 2)
```
`variance` is the population variance of the signal's presence ratio across reviews (a value from 0 to 1 for each review). A cluster present in every review: variance near 0, stability near 1.0. A cluster present in 20% of reviews with irregular distribution: higher variance, lower stability. A venue where live_music appears in reviews 1, 2, 3, 4, 5 (consecutive nights) has lower variance and higher stability than one where it appears only in reviews 1 and 40 (wide gap). A cluster with stability < 0.20 is classified EXPLORATORY regardless of its base confidence.

**`evidence_diversity` (15% weight):** Shannon entropy across sources, normalised:
- Single-source venue (Google only): returns a **fixed 0.30** — this is an acknowledged limitation and a known floor. The system cannot reward source diversity that does not exist.
- Multi-source venue (Google + MagicPin): entropy computed across sources. If both sources agree on a cluster (both show `live_music + social_energy`), diversity is still 0.30 at minimum. If one source uniquely contributes signals the other missed, entropy increases, potentially reaching 0.70–0.90.

**`pattern_persistence` (10% weight):** Temporal spread of evidence:
```
persistence = (evidence_spread + min(1.0, review_coverage)) / 2
evidence_spread = unique_review_dates / total_days_span
```
A cluster with reviews dated across 12 months has higher persistence than one where all supporting reviews were written in the same week. This matters because a pattern that only appeared during one event-heavy week may reflect a temporary anomaly rather than a stable venue characteristic. Low persistence reduces the cluster's overall score.

**Quality tier assignment.** After confidence is computed:
- `conf ≥ 0.70 AND stability ≥ 0.60` → **HIGH** — the system is confident in this pattern
- `conf ≥ 0.40 AND stability ≥ 0.30` → **MEDIUM** — meaningful but less certain
- `conf ≥ 0.15 AND stability ≥ 0.20` → **CANDIDATE** — a hypothesis worth watching
- Below all thresholds → **EXPLORATORY** — surface-level suggestion, very low evidence

**All four tiers are kept in the output.** Nothing is filtered out at Step 4. A CANDIDATE cluster in a low-review venue may become HIGH once more reviews arrive. Discarding it now would create an information gap that cannot be recovered downstream.

**The filter for what gets loaded.** Although all tiers are kept, a secondary `filter_valid_clusters` function applies tighter thresholds when selecting which clusters to use in downstream scoring:
- HIGH tier for loading: conf ≥ 0.60, stability ≥ 0.50, genericness < 0.60
- MEDIUM tier for loading: conf ≥ 0.35, stability ≥ 0.25, genericness < 0.70
- CANDIDATE: conf ≥ 0.15, stability ≥ 0.20
- EXPLORATORY: everything else

**Genericness tracking.** Six signal combinations are `GENERIC_PATTERNS`: `good_service`, `premium_pricing`, `nice_ambience`, `friendly_staff`, `clean_place`, `good_location`. A cluster dominated by these signals has a high `genericness_ratio`. HIGH-tier filtering requires `genericness < 0.60`; MEDIUM requires `< 0.70`. A cluster that is only "good service + nice ambience" — present in most positive reviews from any city in India — is demoted to CANDIDATE or EXPLORATORY regardless of its statistical confidence, because it carries no diagnostic specificity.

**Archetype hypothesis detection.** Specific signal combinations trigger automatic hypothesis labels:
- `live_music` + (`long_dwell` OR `extended_stay`) → `"social_dwell_hypothesis"` ✓ (triggered by our example)
- `great_view` + `premium_pricing` → `"destination_premium_hypothesis"`
- `long_queue` + `repeat_visits` → `"friction_tolerant_loyalty_hypothesis"`
- (`quick_meal` OR `office_crowd`) + `convenient_location` → `"convenience_habit_hypothesis"`
- `authentic_taste` + `long_queue` → `"authenticity_queue_hypothesis"`
- (`social_energy` OR `wonder_ambience`) + `social_sharing` → `"social_amplification_hypothesis"`

When `"social_dwell_hypothesis"` fires, the label is stored in the cluster's `archetype_hypothesis` field. It propagates forward to Step 5 (influences fitness scoring — specifically `social_dwell` and `group_energy` fitness dimensions) and Step 6 (triggers the `dwell_monetization` intervention type and the corresponding narrative language).

**Output.** Step 4 outputs the top 15 clusters per venue, sorted by confidence descending.

---

#### STEP 4b — Governance Validation

Step 4b does not change individual venue scores. It computes a city-level reliability metric across all venues in the region:
```
reliability = (avg_confidence × 0.50 + avg_density × 0.50) × (1 − avg_contradiction × 0.5)
```
`avg_density` is the mean number of co-occurring signals per cluster. A region where clusters average 5 signals each is denser (more behavioural specificity) than one averaging 2. `avg_contradiction` is the mean contradiction rate.

If reliability drops below 0.35, or if avg_contradiction rises above 0.40, the governance report flags the batch as requiring manual review before DB loading. This acts as a data quality gate — if something went wrong in the scraping or extraction, it surfaces here before contaminating the production database.

---

#### STEP 5 — Behavioral Scoring

Step 5 takes each cluster from Step 4 and computes a final composite score that weights seven evidence dimensions plus a contradiction multiplier.

**The 8-component formula:**
```
score = (
    confidence          × 0.22
  + evidence_density    × 0.16
  + temporal_consistency × 0.14
  + evidence_diversity  × 0.14
  + commercial_reliability × 0.18
  + pattern_stability   × 0.10
  + confidence_decay    × 0.06
) × (1 − contradiction_penalty)
```

**Each component explained with threshold branching:**

**`confidence` (22% weight):** The cluster confidence from Step 4, passed through unchanged. The highest single weight in the formula. A cluster that reached HIGH tier (conf=0.80) contributes up to `0.22 × 0.80 = 0.176` to the final score. A CANDIDATE cluster (conf=0.25) contributes `0.22 × 0.25 = 0.055`.

**`evidence_density` (16% weight):** Number of distinct primitives in the cluster, normalised to 0–1. A 2-signal cluster has lower density than a 6-signal cluster. This is the second-highest weight because dense clusters — where multiple independent behavioural signals point in the same direction — are more actionable than thin clusters built on one or two signals.

**`temporal_consistency` (14% weight):** Measures whether this cluster's signal confidences are stable across time slices:
```
stability = 1 / (1 + variance / 30)
```
where `variance` is computed across monthly time slices of the venue's reviews.
- Only 1 timestamp exists → returns **0.30** (fallback). The fallback is not zero — a single-timestamp cluster is penalised but not eliminated. A very new venue with 3 reviews all from the same week gets 0.30, not 0.
- Reviews spread evenly over 12 months with consistent signal → stability approaches 1.0.
- High variance (cluster strong in summer, absent in winter, strong again in December) → stability drops toward 0.10.
- The 0.30 fallback means that temporal_consistency can never drag a score below about 0.04 on its own, preventing complete suppression of new-venue data.

**`evidence_diversity` (14% weight):**
```
phrase_diversity    × 0.4
+ source_diversity  × 0.3
+ temporal_diversity × 0.3
```
- `phrase_diversity`: ratio of unique evidence phrases to total evidence items. 10 reviews all using identical phrasing = low phrase diversity. 10 reviews expressing the same signal in 8 different ways = high phrase diversity.
- `source_diversity`: Shannon entropy across sources. Single-source = 0.30 (fixed floor).
- `temporal_diversity`: spread of evidence timestamps (independent of consistency — high diversity = many dates; consistency = same score across those dates).

**`commercial_reliability` (18% weight):** The highest weight after `confidence` itself. This checks whether the cluster's signals are anchored to commercially meaningful primitives — ones that predict actual revenue impact. Clusters containing `premium_pricing`, `multi_round_ordering`, `extended_stay`, or `repeat_visits` score higher here. The explicit bias is: the system prioritises actionable commercial intelligence over theoretically interesting but non-revenue-linked behavioural classification. A cluster of `wonder_ambience + aesthetic_quality + instagram_worthy` without any spending behaviour signals will score lower on commercial_reliability even if its statistical confidence is high.

**`pattern_stability` (10% weight):** Inherited from Step 4's stability calculation. Passed through unchanged.

**`confidence_decay` (6% weight):** Time-decay weighting:
```
avg(exp(−age_days / 365))   for all evidence items with timestamps
returns 0.50 if no timestamps exist
```
- Evidence from today: `exp(0) = 1.0`
- Evidence from 6 months ago: `exp(−182/365) ≈ 0.61`
- Evidence from 1 year ago: `exp(−1) ≈ 0.37`
- Evidence from 2 years ago: `exp(−2) ≈ 0.14`
- No timestamps: returns 0.50 — neutral, neither boosted nor penalised. This is deliberate: absence of timestamp data should not destroy a venue's score.

The decay function means that a venue whose 80 reviews are all 3 years old will score lower on this component than one whose 20 reviews are all recent. This reflects the operational reality that behavioural patterns at venues change over time — management changes, renovations, neighbourhood shifts.

**The contradiction_penalty multiplier.**
This is the most consequential single factor in the formula because it multiplies the entire sum:
```
if contradiction_severity ≤ 0.10:  penalty = 0.10   (minor)
if contradiction_severity ≤ 0.30:  penalty = 0.25   (moderate)
if contradiction_severity > 0.30:  penalty = 0.50   (severe)
```
`contradiction_severity = contradiction_count / total_mention_count` for the dominant signal in the cluster.

- **Minor contradiction (severity ≤ 0.10):** One negative review in 40 positives. `final_score × (1 − 0.10) = final_score × 0.90`. Small reduction. The cluster is still highly trusted.
- **Moderate contradiction (severity ≤ 0.30):** 3 negative reviews in 20 total. `final_score × 0.75`. Meaningful reduction — the cluster scores lower, appears further down the Intelligence screen, intervention priority drops one tier.
- **Severe contradiction (severity > 0.30):** Near-equal split between positive and negative evidence about this cluster. `final_score × 0.50`. The cluster is treated as structurally unreliable. It will appear in the data but will typically not generate a HIGH or MEDIUM intervention.

**Severe contradictions are never discarded.** A score of 0.40 after a 0.50 penalty means the raw un-penalised score was 0.80 — a strong signal that half the customers experience one way and half experience another. This is itself commercially meaningful: the venue has an inconsistency problem. The system surfaces it in the Intelligence screen with language like "split behavioural signal — inconsistent customer experience."

**Interpreting the final score:**
- `0.75+` → HIGH confidence. The system trusts this pattern enough to make it a primary recommendation. Fitness dimensions anchored here are labelled STRONG or MODERATE.
- `0.45–0.74` → MEDIUM confidence. Shown in Intelligence screen, used in supporting recommendations. Fitness dimensions labelled EMERGING.
- `0.25–0.44` → CANDIDATE. Shown in deep-dive Intelligence view. Flagged as "emerging signal — more data needed." Fitness dimensions labelled NASCENT.
- `< 0.25` → EXPLORE. Retained in data but not surfaced in summary views. Not used for intervention recommendations.

**Fitness scoring.** After the composite score is computed, each cluster is mapped onto 5 fitness dimensions. The mapping (`FITNESS_SIGNAL_MAP`) defines which primitives are required for each dimension:
- `fitness_for_office_lunch`: [`quick_meal`, `office_crowd`, `convenient_location`, `fast_service`]
- `fitness_for_repeat_habit`: [`repeat_visits`, `convenient_location`, `fast_service`, `food_quality`]
- `fitness_for_social_dwell`: [`long_dwell`, `live_music`, `social_energy`, `extended_stay`]
- `fitness_for_group_energy`: [`social_energy`, `group_spend_amplification`, `live_music`]
- `fitness_for_destination_visit`: [`great_view`, `authentic_taste`, `pride`, `premium_pricing`, `wonder_ambience`, `destination_driven_retention`]

Fitness score formula:
```
fitness = match_ratio × confidence_basis
```
`match_ratio` = signals from the dimension map that appear in this cluster / total signals in the dimension map.
`confidence_basis` = the cluster's final composite score.

Example: A cluster containing `live_music + social_energy + extended_stay` (3 of 4 social_dwell signals present):
```
match_ratio = 3/4 = 0.75
confidence_basis = 0.82 (cluster final score)
fitness_for_social_dwell = 0.75 × 0.82 = 0.615
```
→ Social Dwell fitness = 0.615 → **MODERATE** tier.

**Fitness strength tiers:**
- `≥ 0.75` → **STRONG** — featured prominently in radar; primary recommendation basis
- `≥ 0.50` → **MODERATE** — shown in radar; used in supporting recommendations
- `≥ 0.25` → **EMERGING** — shown in radar at lower weight; gap-bridging interventions offered
- `< 0.25` → **NASCENT** — shown at near-zero in radar; triggers "opportunity gap" messaging

A NASCENT `office_lunch` score means the venue has essentially zero signals related to quick_meal, office_crowd, or fast_service. The frontend shows this as an unexplored dimension with a prompt: "This venue has not yet demonstrated fit for office lunch. Adding quick-service options and promoting weekday lunch deals could open this segment."

**Intervention priority tiers:**
- `≥ 0.75` → **HIGH** — enough evidence to make this a primary actionable recommendation
- `≥ 0.45` → **MEDIUM** — recommended with confidence but noting evidence strength
- `≥ 0.25` → **CANDIDATE** — shown as "worth exploring when more data arrives"
- `< 0.25` → **EXPLORE** — surfaced only in the deep-dive Intelligence view, never in summary cards

---

#### STEP 5b — Similarity Enrichment

After all venues in a region are scored, Step 5b constructs a **signal vector** for each venue: a numerical vector where each dimension corresponds to one of the 54 primitives, and its value is that primitive's confidence score (0.0 if the primitive was not detected). For a venue with `live_music = 0.99`, `social_energy = 0.82`, `extended_stay = 0.71`, and no other signals detected, the vector has 0.99 at position `live_music`, 0.82 at `social_energy`, 0.71 at `extended_stay`, and 0.0 at all other 51 positions.

Cosine similarity is computed pairwise across all venues in the same region. The top 25 most similar venues per venue are stored in `step_5b_similarity`.

**Why cosine instead of Euclidean distance:** Cosine similarity measures the angle between vectors, ignoring magnitude. A large venue with strong signals (live_music=0.99, social_energy=0.90) and a small venue with similar but weaker signals (live_music=0.65, social_energy=0.58) will score high cosine similarity because they point in the same behavioural direction. Euclidean distance would penalise the magnitude difference and score them as dissimilar — which would be wrong, because they attract the same customer psychology regardless of review volume or signal intensity.

This is what powers the Competitors tab. The system does not use category labels ("rooftop bar"), price tier, or geographic radius alone. It uses actual behavioural signal overlap. A wine bar and a gastropub with near-identical signal vectors are competitors; a venue in the same building with a completely different signal profile is not.

---

#### STEP 6 — Output and Intervention Playbooks

Step 6 synthesises all scores into the final JSON output, which is then loaded into PostgreSQL via the loader scripts.

**Narrative generation.**
Each cluster gets a human-readable description assembled from three signal categories within the cluster:
- `stimulus_parts`: signals whose names contain `view`, `music`, `energy`, `setting`, or `authentic` — the environmental triggers
- `friction_parts`: signals whose names contain `queue`, `premium`, `wait`, `slow`, or `crowd` — the resistance factors
- `response_parts`: signals whose names contain `dwell`, `repeat`, `order`, `return`, or `stay` — the behavioural outcomes

The narrative template: `"Stimulus: {stimuli} → Friction: {frictions} → Behavioural response: {responses}."`

From our example cluster (`live_music + social_energy + extended_stay + multi_round_ordering`):
- stimulus_parts: `live_music` (contains "music"), `social_energy` (contains "energy")
- friction_parts: none in this cluster
- response_parts: `extended_stay` (contains "stay"), `multi_round_ordering` (contains "order")

Narrative: *"Stimulus: live music, social energy → Behavioural response: extended stay, multi-round ordering."*

This maps directly to the academic stimulus→evaluation→response framework from environmental psychology (Turley & Milliman, Bitner). The language is chosen so that a venue owner — not a data scientist — can read the Intelligence screen and immediately understand what is happening at their venue.

**Behavioral summary assembly.**
Three high-level summary metrics are computed from all scored patterns for a venue:
- `operational_quality` = average `final_score` across all scored patterns for the venue
- `retention_strength` = `final_score` of the first pattern whose `archetype_hypothesis` contains "repeat" or "loyalty"
- `monetization_potential` = `final_score` of the first pattern whose `archetype_hypothesis` contains "premium", "dwell", or "ordering"

These three summary values appear as the header cards on the Overview screen.

**Intervention type assignment.**
Each cluster is checked against four intervention templates:
- `operational_optimization`: triggered when cluster contains `service_delay`, `queue_friction`, or `slow_service`
- `premium_justification`: triggered by `premium_pricing` + identity signals (`status_display`, `premium_identity`)
- `dwell_monetization`: triggered by `extended_stay` + `social_energy` without `multi_round_ordering` — a venue where people stay long but don't order in multiple rounds is leaving revenue on the table
- `friction_reduction`: triggered by `overcrowding` + `noise_rejection`

The intervention priority is then the cluster's final score mapped to the tier system (HIGH/MEDIUM/CANDIDATE/EXPLORE). A HIGH-priority `dwell_monetization` intervention becomes the primary recommendation: "Introduce a timed drinks package — your customers are staying for 3+ hours but not ordering additional rounds. A ₹499 bottomless beer package on weekends could capture this dwell time as revenue."

---

#### BLEND LAYER — Multi-Source Weighted Averaging

When a venue has data from multiple sources (Google + MagicPin), the blend layer merges their fitness scores. Source weights:
- `google`: weight 1.0 — largest review corpus, most authoritative
- `magicpin_upper`: weight 0.7 — upper-catchment venues (676 venues with meaningful sample)
- `manual_reviews`: weight 0.5 — high quality but small sample

Blend formula per fitness dimension:
```
blended_score = sum(source_score × weight) / sum(weight for active sources)
```

**Single-source venue (Google only):** blended_score = Google score. No change.
**Two-source venue (Google=0.72, MagicPin=0.65 on social_dwell):**
```
blended_social_dwell = (0.72 × 1.0 + 0.65 × 0.7) / (1.0 + 0.7)
                     = (0.72 + 0.455) / 1.7
                     = 0.689
```
The blend pulls the score slightly toward the lower MagicPin value, weighted by source reliability. Google's score matters more.

**What the blend layer cannot resolve:** Source-level contradictions. If Google reviews portray a venue as calm (low social_energy, low live_music) but MagicPin reviews portray it as high-energy (high social_energy, high live_music), the blend will average these into a score that misrepresents both audiences. This situation — where different crowd types use different platforms to review the same venue — is logged as a tension pattern and surfaced in the governance report for manual review.

---

#### FROM DATABASE TO FRONTEND

All scored data is now in PostgreSQL. Every screen queries specific tables:

**Overview screen** queries `step_5_behavioral_scores` → renders a five-dimension fitness radar. Dimensions at STRONG (≥0.75) appear dark and prominent; NASCENT (<0.25) appear faint with opportunity prompts.

**Intelligence screen** queries `step_6_output` + `step_4_patterns` → renders cluster cards. Each card shows: the hypothesis label (`social_dwell_hypothesis`), the narrative sentence, the confidence score, the quality tier (HIGH/MEDIUM/CANDIDATE), the final composite score, and the intervention priority. Cards are sorted by final composite score descending.

**Competitors screen** queries `step_5b_similarity` → renders top similar venues sorted by cosine similarity score. Bucketing:
- Bucket A: all signal types match (highest cosine score, same dominant hypothesis)
- Bucket B: 2+ signal types match
- Bucket C: 1 signal type matches
- Bucket D: segment-level similarity only (no signal-level match)

**Transform screen** queries blend fitness scores + computes ATA (Alignment to Target) scores against selected target venues. Tier assignment:
- Role Model: ATA ≥ 0.50 (venue is already strongly aligned with this target archetype)
- Bridge: target rank-2 or rank-3 venue with alignment ≥ 0.30 (achievable path)
- Transition: ATA 0.20–0.50 (significant effort required but feasible)
- Pure Target: ATA < 0.20 (aspirational; requires fundamental repositioning)

**Marketing screen** queries `segment_behavioral_profiles` + `channel_benchmarks` → renders audience composition percentages, channel effectiveness scores for each segment, and the recommended content strategy matrix.

**Audience Simulator** re-computes segment fitness scores in real-time when venue attributes are toggled. Example: toggling "add live music" forces the system to increase `social_dwell` and `group_energy` fitness (live_music is in both dimension maps) and decrease `office_lunch` fitness — because `quick_meal + convenient_location` (the office_lunch signals) are incompatible with the live_music environment. The system makes this incompatibility explicit: "Adding live music on weeknights will grow your Social Crowd segment by an estimated ~12% but will reduce Office Worker lunch suitability. These two segment profiles are fundamentally incompatible in the same slot."

**Campaign screen** queries fitness profile + `archetype_behavioral_profiles` + `segment_archetype_affinity` → assembles the ad brief. Creative angles are chosen based on the venue's dominant archetype affinities:
- High `social_dwell` + `group_energy` → Social Proof angle (crowd, energy, group FOMO)
- High `destination_visit` → Identity Signalling angle (status, premium, occasion)
- High `repeat_habit` → Habit Formation angle (routine, reward, consistency)
- High `office_lunch` → Convenience angle (speed, proximity, reliability)

---

### 0.3 What the System Is Not

**It is not sentiment analysis.** Sentiment classifies whether a review is positive or negative. This system extracts which specific behavioural mechanisms operated during the visit. Two equally positive reviews — one written because of social proof, one because of habit satisfaction — are fundamentally different intelligence inputs. The system treats them differently.

**It is not a restaurant listing tool.** It has no interest in menus, opening hours, or delivery orders. The system cares about the psychological dynamics the venue creates, not what it sells.

**It is not a classification system.** Archetypes are hypotheses, not labels. A venue can have both `fast_service` and `slow_service` signals active simultaneously — from different customer types at different times of day. Contradictions are data, not errors.

**It is not finished.** Layer 2 (human preference surveys) is schema-complete but data-pending. Marketing interaction telemetry (Layer 3) does not exist yet — and the architecture document explicitly forbids building it before the ontology stabilises. Google Reviews is now live for Thane and Navi Mumbai (1,120 venues), partially closing the friction_tolerance gap for Solo Diners and Office Workers. Mumbai Main and SoBo google_reviews extraction remains pending.

---

## 1. System Overview

The Polynovea Acquisition System is a behavioral intelligence platform for F&B venue owners in urban India (Mumbai Metro Region). It ingests multi-source review data (Google Places API, MagicPin, manual reviews), runs a six-step behavioral extraction pipeline, and surfaces a full-stack web application that helps venue owners understand:

- **Which customer archetypes visit them** and what drives each archetype's spend
- **How fit their venue is** for five commercial use cases (fitness dimensions)
- **Which behavioral interventions** to deploy to engineer better outcomes
- **How they compare** to similar venues on signal dimensions
- **What marketing strategy** maps to their audience composition

**Coverage (as of 2026-05-25):**

| Source | Venues | Regions | Status |
|--------|--------|---------|--------|
| Google Places API | 6,008 | Mumbai Main, Mumbai SoBo, Navi Mumbai, Thane | ✅ Live |
| MagicPin (upper) | 676 | Mumbai, Navi Mumbai, SoBo, Thane | ✅ Live — blended |
| Google Reviews | 1,120 | **Thane, Navi Mumbai only** | ✅ Live — blended |
| Manual reviews | 2 | Manual | ✅ Live — Aphrodite (223), Unfilltered (12066) |
| Zomato | — | — | ⏳ Future |
| TripAdvisor | — | — | ⏳ Future |

> `magicpin_lower` is **RETIRED** — superseded by `google_reviews`.

**Total blended venues:** 6,009 across 4 cities.

**Cities:** Navi Mumbai, Mumbai Main, Mumbai SoBo, Thane

---

## 2. Architecture

```
┌──────────────────────────────────────────────────────────────────┐
│  DATA COLLECTION LAYER                                           │
│  ┌─────────────────┐  ┌──────────────────┐  ┌────────────────┐  │
│  │ Google Places   │  │ MagicPin Scraper │  │ Manual Reviews │  │
│  │ API (Python)    │  │ (Node.js + CDP)  │  │ (JSON upload)  │  │
│  └────────┬────────┘  └────────┬─────────┘  └───────┬────────┘  │
└───────────┼────────────────────┼────────────────────┼───────────┘
            │                    │                    │
            ▼                    ▼                    ▼
┌──────────────────────────────────────────────────────────────────┐
│  BEHAVIORAL EXTRACTION PIPELINE (Database/scripts/pipeline/)     │
│                                                                  │
│  Step 3: Signal Extraction  → 5-factor + temporal signals       │
│  Step 4: Pattern Clustering → co-occurring primitive clusters    │
│  Step 4b: Governance        → reliability scoring, validation   │
│  Step 5: Scoring            → 8-component composite score       │
│  Step 5b: Similarity        → cosine similarity top-25 venues   │
│  Step 6: Output             → intervention playbooks            │
└────────────────────────────┬─────────────────────────────────────┘
                             │
                             ▼
┌──────────────────────────────────────────────────────────────────┐
│  BLEND LAYER (blend/blend_fitness.py)                            │
│  Multi-source weighted averaging → unified venue fitness record  │
└────────────────────────────┬─────────────────────────────────────┘
                             │
                             ▼
┌──────────────────────────────────────────────────────────────────┐
│  POSTGRESQL DATABASE (AWS RDS ap-south-1)                        │
│  Behavioral framework tables + venue operational tables          │
└────────────────────────────┬─────────────────────────────────────┘
                             │
                             ▼
┌──────────────────────────────────────────────────────────────────┐
│  BACKEND API (FastAPI — App/backend/)                            │
│  11 routers: venues, overview, competitors, transform, ...       │
└────────────────────────────┬─────────────────────────────────────┘
                             │
                             ▼
┌──────────────────────────────────────────────────────────────────┐
│  FRONTEND (Next.js 15 — App/frontend/)                           │
│  7 screens: Search → Overview → Competitors → Transform →        │
│  Marketing → Intelligence → Audience → Campaign                  │
└──────────────────────────────────────────────────────────────────┘
```

---

## 3. Database Schema

### 3.1 ENUMs

All ENUMs are defined in `App/backend/db/001_schema.sql`.

| ENUM | Values |
|------|--------|
| `affinity_level` | `none`, `low`, `low_medium`, `medium`, `medium_high`, `high`, `very_high` |
| `alcohol_driver` | `habit`, `social_occasion`, `identity`, `fomo`, `discovery`, `none` |
| `discovery_rate` | `very_low`, `low`, `medium`, `medium_high`, `high`, `very_high`, `extremely_high` |
| `occasion_habit_orientation` | `occasion_driven`, `habit_driven`, `mixed` |
| `revenue_curve_shape` | `steep_front_flat_tail`, `front_loaded_alcohol_tail`, `steady`, `course_paced_wine_driven`, `linear_child_limited`, `efficient_single_peak`, `moderate_steady` |
| `signal_strength` | `primary`, `secondary`, `minimal` |
| `platform_name` | `instagram`, `tiktok`, `zomato`, `swiggy`, `swiggy_dineout`, `zomato_gold`, `google_maps`, `google_reviews`, `direct`, `word_of_mouth` |
| `platform_usage_type` | `discovery`, `validation`, `booking`, `post_visit_review`, `wom` |
| `mechanism_category` | `social_influence`, `scarcity_urgency`, `identity_status`, `habit_automaticity`, `environmental`, `loss_aversion`, `cultural_capital` |

### 3.2 Layer 1 — Behavioral Mechanisms

**`behavioral_mechanisms`**

| Column | Type | Description |
|--------|------|-------------|
| `id` | SERIAL PK | |
| `slug` | TEXT UNIQUE | e.g. `social_proof`, `fomo` |
| `label` | TEXT | Human-readable name |
| `category` | mechanism_category | Psychological category |
| `psychological_logic` | TEXT | Academic reasoning |
| `hospitality_context` | TEXT | How this manifests in F&B |
| `operational_implication` | TEXT | What venue operators can do |

**`mechanism_citations`** — Academic citations per mechanism (author, year, framework, core claim, relevance)

**`mechanism_signals`** — Observable and measurable signals per mechanism (`signal_type`: `observable` or `measurable`)

### 3.3 Layer 2 — Segment Behavioral Profiles

**`segment_behavioral_profiles`** — One row per customer segment (7 segments)

| Column Group | Columns |
|-------------|---------|
| Identity | `segment_key`, `label` |
| Spend composition | `food_pct_min/max`, `alcohol_pct_min/max`, `dessert_attach_pct_min/max` |
| Check size | `avg_check_vs_baseline_pct_min/max` |
| Alcohol | `alcohol_affinity`, `alcohol_primary_driver`, `alcohol_secondary_driver`, `beverage_preference` |
| Group dynamics | `peer_influence_coefficient` (0–1), `group_revenue_impact_per_member` |
| Dwell & economics | `dwell_min/max_minutes`, `dwell_alt_min/max_minutes`, `dwell_alt_label`, `revpash_min/max_inr`, `revpash_alt_min/max_inr`, `diminishing_returns_minutes`, `revenue_curve` |
| Loyalty | `repeat_tendency_pct_min/max`, `repeat_window_days`, `discovery_rate` |
| WOM | `wom_multiplier_min/max` |
| Mechanisms | `primary_mechanism_id` FK, `secondary_mechanism_id` FK |
| Triggers | `primary_trigger`, `low_to_high_spend_trigger`, `dessert_high_conversion_trigger`, `dessert_format_preference` |

**`segment_occasion_multipliers`** — Per segment × occasion spend multipliers (e.g. Social Crowd + Birthday = 2.0×)

**`segment_platform_usage`** — Platform × usage type × strength per segment (e.g. Social Crowd: Instagram for discovery/post_visit_review, Zomato for booking)

### 3.4 Layer 3 — Archetype Behavioral Profiles

**`archetype_behavioral_profiles`** — One row per archetype (11 archetypes)

Same columns as segment profiles, plus:
- `orientation`: `occasion_driven` | `habit_driven` | `mixed`
- `group_ordering_pattern`: free-text description of group ordering dynamics

**`archetype_spend_triggers`** — Up to 3 ranked triggers per archetype with staff scripts

### 3.5 Layer 4 — Segment ↔ Archetype Affinity

**`segment_archetype_affinity`** — Many-to-many with `affinity_rank` (1–5, where 1 = primary)

### 3.6 Layer 5 — Channel Benchmarks

**`channel_benchmarks`** — One row per marketing channel

| Column | Description |
|--------|-------------|
| `channel_key` | Internal key |
| `open_rate_pct_min/max` | Email/message open rate range |
| `repeat_visit_lift_pct` | % higher repeat vs. control |
| `roi_multiplier_min/max` | Revenue multiplier |
| `order_uplift_pct_min/max` | Order value uplift |
| `primary_effect` | What the channel is best at |

**`channel_segment_effectiveness`** — Channel × Segment effectiveness score (1–5) with primary use case

### 3.7 Layer 6 — Trait → Fitness Bridge

**`trait_fitness_weights`** — Maps signal trait keys to fitness dimension names with weights (–1.0 to +1.0) and linked mechanism ID

### 3.8 Layer 7 — Research Validation Flags

**`research_validation_flags`** — Tracks known incorrect values in the system (entity_type, entity_key, field_name, claimed_value, validated_value, is_corrected)

### 3.9 Operational Tables

**`venues`** — Core venue metadata

| Column | Description |
|--------|-------------|
| `id` | SERIAL PK |
| `place_id` | Google Place ID (unique) |
| `name` | Venue name |
| `area` | Sub-area (e.g. Vashi, Bandra) |
| `city` | City key (navi-mumbai, mumbai-main, etc.) |
| `types` | JSON array of Google venue types |
| `location` | lat/lng |
| `source` | `google` \| `magicpin_upper` \| `manual_reviews` |
| `discovered_at` | Timestamp |

**`venue_fitness_dimensions`** — Per-venue fitness scores

| Column | Description |
|--------|-------------|
| `venue_id` | FK to venues |
| `source` | Source key |
| `fitness_for_office_lunch` | 0–1 score |
| `fitness_for_repeat_habit` | 0–1 score |
| `fitness_for_social_dwell` | 0–1 score |
| `fitness_for_group_energy` | 0–1 score |
| `fitness_for_destination_visit` | 0–1 score |
| `behavioral_summary` | JSON (operational_quality, retention_strength, monetization_potential) |

**`venue_similarity_deltas`** — Top-25 similar venues per venue (cosine similarity on signal vectors)

**`venue_demographic_scores`** — Segment and archetype prevalence scores per venue

**`pattern_scores`** — Per-venue pattern confidence scores with source attribution

### 3.10 Views

**`peer_influence_matrix`** — Union of segments + archetypes ordered by `peer_influence_coefficient DESC`

**`revpash_economics`** — Segment dwell/RevPASH/repeat economics ordered by `revpash_max_inr DESC`

### 3.11 Indexes

```sql
idx_segment_profiles_key          → segment_behavioral_profiles(segment_key)
idx_archetype_profiles_key        → archetype_behavioral_profiles(archetype_key)
idx_segment_archetype_segment     → segment_archetype_affinity(segment_id)
idx_segment_archetype_archetype   → segment_archetype_affinity(archetype_id)
idx_channel_benchmarks_key        → channel_benchmarks(channel_key)
idx_trait_fitness_trait           → trait_fitness_weights(trait_key)
idx_trait_fitness_dim             → trait_fitness_weights(fitness_dimension)
idx_mechanism_signals_type        → mechanism_signals(mechanism_id, signal_type)
```

---

## 4. Behavioral Framework

### 4.1 54 Behavioral Primitives

Source: `Database/config/primitives.json` | Schema version: 1.0

Each primitive has:
- `id` — Snake-case key
- `name` — Human label
- `category` — Category group
- `data_type` — Always `score`
- `range` — Always `[0, 1]`
- `description` — What this primitive measures
- `extraction_keywords` — NLP match terms from review text

#### Culinary (4)

| ID | Name | Keywords |
|----|------|----------|
| `food_quality` | Food Quality | fresh, delicious, taste, flavor, quality, authentic |
| `food_authenticity` | Food Authenticity | authentic, traditional, genuine, real, original |
| `food_variety` | Food Variety | variety, options, menu, diverse, choice |
| `portion_size` | Portion Size | portion, serving, generous, plenty |

#### Pricing (3)

| ID | Name | Keywords |
|----|------|----------|
| `value_for_money` | Value for Money | value, worth, expensive, cheap, reasonably |
| `pricing_premium` | Pricing Premium | expensive, premium, costly, high-end, upscale |
| `deals_promotions` | Deals & Promotions | deal, promo, offer, discount, special |

#### Service (6)

| ID | Name | Keywords |
|----|------|----------|
| `service_speed` | Service Speed | fast, quick, slow, wait, speedy, prompt |
| `service_attentiveness` | Service Attentiveness | attentive, responsive, careful, helpful, considerate |
| `staff_warmth` | Staff Warmth | friendly, warm, welcoming, hospitable, nice |
| `staff_knowledgeable` | Staff Knowledgeable | knowledgeable, expert, informed, educated, knows |
| `delivery_quality` | Delivery Quality | delivery, order, shipped, arrived, packaging |
| `queue_management` | Queue Management | queue, wait, line, crowd, busy |

#### Ambience (5)

| ID | Name | Keywords |
|----|------|----------|
| `ambience_comfortable` | Ambience Comfortable | comfortable, cozy, relaxed, ease, cushy |
| `ambience_intimate` | Ambience Intimate | intimate, private, cozy, romantic, quiet |
| `ambience_energy` | Ambience Energy | lively, vibrant, energetic, buzzing, alive |
| `music_quality` | Music Quality | music, song, playlist, beats, audio |
| `decor` | Decor | decor, design, aesthetic, beautiful, decorated |

#### Hygiene (1)

| ID | Name | Keywords |
|----|------|----------|
| `cleanliness` | Cleanliness | clean, dirty, hygiene, spotless, neat |

#### Facilities (5)

| ID | Name | Keywords |
|----|------|----------|
| `seating_comfort` | Seating Comfort | seating, chair, table, comfortable, ergonomic |
| `seating_spacing` | Seating Spacing | space, spacing, crowded, elbow, cramped |
| `parking_availability` | Parking Availability | parking, space, available, convenient, easy |
| `outdoor_seating` | Outdoor Seating | outdoor, terrace, patio, garden, balcony |
| `view_appeal` | View Appeal | view, scenic, beautiful, vista, outlook |

#### Location (2)

| ID | Name | Keywords |
|----|------|----------|
| `location_accessibility` | Location Accessibility | location, accessible, convenient, easy access, near |
| `location_visibility` | Location Visibility | visible, prominent, hidden, easy to find, noticeable |

#### Social (5)

| ID | Name | Keywords |
|----|------|----------|
| `social_energy` | Social Energy | social, energy, fun, group, lively, interactive |
| `group_friendly` | Group Friendly | group, friends, party, gathering, gang |
| `couple_friendly` | Couple Friendly | couple, date, romantic, intimate, two |
| `family_friendly` | Family Friendly | family, kids, children, family-friendly, safe |
| `kids_welcome` | Kids Welcome | kids, children, toddler, welcoming, tolerant |

#### Behavioral (4)

| ID | Name | Keywords |
|----|------|----------|
| `repeat_visits` | Repeat Visits | again, repeat, came back, frequent, regular |
| `loyalty` | Loyalty | loyal, favorite, best, always, preferred |
| `dwell_time` | Dwell Time | spent hours, lingered, stayed, long, duration |
| `sharing_moments` | Sharing Moments | photo, instagram, share, pictures, capture |

#### Experience (4)

| ID | Name | Keywords |
|----|------|----------|
| `experience_memorable` | Experience Memorable | memorable, remember, unforgettable, remarkable, special |
| `experience_unique` | Experience Unique | unique, different, special, one-of-a-kind, novel |
| `experience_immersive` | Experience Immersive | immersive, engaging, involved, absorbed, engaged |
| `innovation` | Innovation | innovative, new, creative, different, forward |

#### Emotional (5)

| ID | Name | Keywords |
|----|------|----------|
| `pride` | Pride | proud, boast, recommend, tell friends, elite |
| `discovery` | Discovery | discovered, found, new, hidden gem, stumbled |
| `excitement` | Excitement | excited, thrilled, wow, amazing, awesome |
| `fomo` | FOMO | everyone, trending, popular, hype, crowded |
| `trust` | Trust | trust, reliable, consistent, dependable, honest |

#### Satisfaction (3)

| ID | Name | Keywords |
|----|------|----------|
| `expectation_met` | Expectation Met | expected, surprised, delivered, met, exceeded |
| `overall_satisfaction` | Overall Satisfaction | satisfied, happy, pleased, content, rating |
| `would_recommend` | Would Recommend | recommend, tell, suggest, friend, family |

#### Use Case (6)

| ID | Name | Keywords |
|----|------|----------|
| `special_occasions` | Special Occasions | celebration, anniversary, birthday, special, occasion |
| `business_lunch` | Business Lunch | business, meeting, client, professional, work |
| `casual_dining` | Casual Dining | casual, relaxed, informal, laid-back, chill |
| `quick_bite` | Quick Bite | quick, fast, bite, snack, rush |
| `late_night` | Late Night | late, night, open, hours, midnight |
| `breakfast` | Breakfast | breakfast, morning, eggs, brunch, coffee |

---

### 4.2 7 Customer Segments

Source: `App/backend/db/002_seed_segments_archetypes.sql`

#### 1. Office Workers (`office_workers`)

| Parameter | Value |
|-----------|-------|
| Food % | 65–70% |
| Dessert attach | 12–18% |
| Avg check vs baseline | 0 to +15% |
| Alcohol affinity | `low_medium` |
| Primary driver | `habit` |
| Secondary driver | `social_occasion` |
| Beverage | Beer/craft beer; wine with clients |
| Peer influence | 0.30 |
| Group revenue impact | +15% per member (efficiency) |
| Dwell — lunch | 35–50 min |
| Dwell — after-work | 75–90 min |
| RevPASH — lunch | ₹180–250/hr/cover |
| RevPASH — after-work | ₹350–450/hr/cover |
| Diminishing returns | 60 min |
| Revenue curve | `steep_front_flat_tail` |
| Repeat tendency | 60–70% within 30 days |
| Discovery rate | `low` |
| WOM multiplier | 1.2× |
| Primary trigger | Convenience (proximity) + Habit (routine spot) |
| Spend escalation | Client joining → identity shift; staff recognition; combo upgrade |
| Dessert trigger | Coffee upgrade combo |
| Dessert format | Individual, portable |
| **Occasion multipliers** | Work lunch: 1.0× \| Client entertainment: 1.4–1.6× \| Team celebration: 1.8× |
| **Discovery platforms** | Google Maps (primary), Zomato (validation/booking/review), WOM (primary) |

#### 2. Social Crowd (`college_kids`)

| Parameter | Value |
|-----------|-------|
| Alcohol % | 55–65% of check |
| Dessert attach | 22–28% |
| Avg check vs baseline | +40 to +80% |
| Alcohol affinity | `high` |
| Primary driver | `social_occasion` |
| Secondary driver | `fomo` |
| Beverage | Cocktails, beer buckets, shots |
| Peer influence | 0.70 |
| Group revenue impact | +40% per member (alcohol multiplier) |
| Dwell | 120–180 min (longest segment) |
| RevPASH | ₹400–600/hr/cover |
| Diminishing returns | 120 min (optimal flip: 150 min) |
| Revenue curve | `front_loaded_alcohol_tail` |
| Repeat tendency | 20–30% within 90 days |
| Discovery rate | `high` |
| WOM multiplier | 3.5–4.5× |
| Primary trigger | Peer plan (group chat coordination) + Occasion |
| Spend escalation | First round anchor; "last round" scarcity; group bottle bundle |
| Dessert format | Shareable, photogenic |
| **Occasion multipliers** | Celebration: 2.0× \| Routine hangout: 1.3× \| "Just because": 1.0× |
| **Discovery platforms** | Instagram (primary discovery + post-visit), Zomato (booking), WOM (primary) |

#### 3. Couples (`couples`)

| Parameter | Value |
|-----------|-------|
| Dessert attach | 35–45% (highest) |
| Avg check vs baseline | +25 to +50% |
| Alcohol affinity | `medium` |
| Primary driver | `identity` |
| Secondary driver | `social_occasion` |
| Beverage | Wine, cocktails for date night |
| Peer influence | 0.50 |
| Group revenue impact | 1.8× baseline (two covers + shared apps) |
| Dwell | 90–120 min (unhurried, conversation-paced) |
| RevPASH | ₹350–500/hr/cover |
| Diminishing returns | 105 min (coffee/digestif extends +15–20 min) |
| Revenue curve | `steady` |
| Repeat tendency | 40–50% within 60 days |
| Discovery rate | `medium` |
| WOM multiplier | 2.0× |
| **Occasion multipliers** | Anniversary: 1.6× \| Routine date night: 1.2× \| Spontaneous: 1.0× |
| **Discovery platforms** | Instagram (discovery), Google Reviews (validation), Zomato (booking/review) |

#### 4. Families (`families`)

| Parameter | Value |
|-----------|-------|
| Food % | 75–80% |
| Dessert attach | 40–50% (child-driven) |
| Avg check vs baseline | +10 to +30% |
| Alcohol affinity | `low_medium` |
| Primary driver | `habit` |
| Beverage | Beer/wine max 1–2 (parents only) |
| Peer influence | 0.40 |
| Group revenue impact | +25% per child |
| Dwell | 60–90 min (child-dependent) |
| RevPASH | ₹200–300/hr/cover (lower per-cover) |
| Diminishing returns | 75 min (children restless) |
| Revenue curve | `linear_child_limited` |
| Repeat tendency | 50–60% within 30 days |
| Discovery rate | `low` |
| WOM multiplier | 1.5× |
| Dessert trigger | Child-targeted / "kids eat free" |
| **Occasion multipliers** | Birthday: 1.4× \| Routine outing: 1.0× \| Post-activity: 0.9–1.0× |
| **Discovery platforms** | Zomato (discovery/booking/review), Google Maps (validation), WOM |

#### 5. Premium Diners (`premium`)

| Parameter | Value |
|-----------|-------|
| Dessert attach | 50–65% (connoisseurship) |
| Avg check vs baseline | +150 to +300% |
| Alcohol affinity | `high` |
| Primary driver | `identity` |
| Secondary driver | `social_occasion` |
| Beverage | Red wine dominant, single malts, craft cocktails |
| Peer influence | 0.20 |
| Group revenue impact | +30% per member (wine sharing) |
| Dwell | 120–180 min (savoring pace) |
| RevPASH | ₹800–1500/hr/cover (highest segment) |
| Diminishing returns | 150 min |
| Revenue curve | `course_paced_wine_driven` |
| Repeat tendency | 30–40% within 90 days |
| Discovery rate | `medium` |
| WOM multiplier | 3.0× |
| Spend escalation | Sommelier recommendation + story; chef's table exclusivity; anchoring with highest price |
| **Occasion multipliers** | Business entertainment: 3.0× \| Personal celebration: 2.5× \| Routine premium: 1.8× |
| **Discovery platforms** | Google Maps (primary), WOM (primary discovery), Zomato Gold (booking), Google Reviews (validation) |

#### 6. Solo Diners (`solo_diners`)

| Parameter | Value |
|-----------|-------|
| Food % | 70–75% |
| Dessert attach | 18–25% |
| Avg check vs baseline | –10 to 0% |
| Alcohol affinity | `low_medium` |
| Primary driver | `habit` |
| Secondary driver | `identity` |
| Beverage | Beer or wine by the glass |
| Peer influence | 0.00 |
| Group revenue impact | Baseline (no group) |
| Dwell — lunch | 30–50 min |
| Dwell — dinner/bar | 60–75 min |
| RevPASH | ₹250–400/hr/cover (efficient turnover) |
| Diminishing returns | 45 min lunch; 75 min dinner |
| Revenue curve | `efficient_single_peak` |
| Repeat tendency | 25–35% within 60 days |
| Discovery rate | `extremely_high` |
| WOM multiplier | 2.2× |
| Spend escalation | Bartender rapport; "chef's special" exclusivity; bar counter with kitchen view |
| **Occasion multipliers** | "Treat myself": 1.3× \| Routine meal: 1.0× \| Work-alone: 0.8–0.9× |
| **Discovery platforms** | Zomato (primary discovery/validation/booking/review), Google Maps (secondary) |

#### 7. Working Women (`working_women`)

| Parameter | Value |
|-----------|-------|
| Dessert attach | 25–32% |
| Avg check vs baseline | +15 to +35% |
| Alcohol affinity | `medium` |
| Primary driver | `identity` |
| Secondary driver | `social_occasion` |
| Beverage | Wine, gin cocktails, zero-proof options |
| Peer influence | 0.60 |
| Group revenue impact | +35% per member (shared small plates) |
| Dwell — group | 75–105 min |
| Dwell — solo lunch | 45–60 min |
| RevPASH — group | ₹350–500/hr/cover |
| RevPASH — solo | ₹200–300/hr/cover |
| Diminishing returns | 90 min group; 50 min solo |
| Revenue curve | `moderate_steady` |
| Repeat tendency | 40–50% within 60 days |
| Discovery rate | `medium_high` |
| WOM multiplier | 2.8× |
| Spend escalation | "Wellness" positioning; zero-proof cocktail menu; "guilt-free" dessert framing |
| **Occasion multipliers** | Celebration: 1.5× \| Routine catch-up: 1.2× \| "Self-care" solo: 1.1× |
| **Discovery platforms** | Instagram (discovery + post-visit), Zomato (validation/booking/review), Google Reviews (validation) |

---

### 4.3 11 Archetypes

Source: `002_seed_segments_archetypes.sql` | Seed: `behavioral_intelligence_module.md`

#### Spend Trigger Script Key (applicable to all archetypes)

Each archetype has up to 3 ranked triggers with optional staff scripts in `archetype_spend_triggers`.

| Archetype | Key | Orientation | Peak RevPASH | Peer Influence | WOM | Top Segment Affinity |
|-----------|-----|-------------|-------------|----------------|-----|----------------------|
| **Party Seeker** | `party_seeker` | occasion | ₹450–700 | 0.80 | 4.0–4.5× | Social Crowd |
| **Scene Seeker** | `scene_seeker` | occasion | ₹400–600 | 0.70 | 3.5× | Social Crowd, Working Women |
| **Trusted Regular** | `trusted_regular` | habit | ₹350–500 | 0.30 | 2.5× | Office Workers, Premium |
| **Habit Former** | `habit_former` | habit | ₹200–300 | 0.10 | 1.0× | Office Workers, Families |
| **Calm Pairs** | `calm_pairs` | mixed | ₹300–450 | 0.50 | 1.8× | Couples |
| **Lifestyle Regular** | `lifestyle_regular` | habit | ₹350–500 | 0.40 | 2.5× | Multiple |
| **Quiet Discoverer** | `quiet_discoverer` | occasion | ₹300–450 | 0.00 | 2.0× | Solo Diners, Couples |
| **Trend Hunter** | `trend_hunter` | occasion | ₹450–650 | 0.75 | 4.5× | Social Crowd |
| **Premium Prioritizer** | `premium_prioritizer` | occasion | ₹1000–1800 | 0.15 | 3.0× | Premium |
| **Discovery Explorer** | `discovery_explorer` | occasion | ₹350–500 | 0.20 | 2.2× | Solo Diners |
| **Power Regular** | `power_regular` | habit | ₹350–500 | 0.30 | 2.0–2.5× | Office Workers |

#### Detailed Archetype Profiles

**Party Seeker:** Alcohol 60–70% of check, +60–100% vs baseline, dwell 150–210 min, diminishing returns 150 min. Trigger: First round anchor (premium cocktail sets table spend). Staff script: "Shall I start a tab with [premium item]?" Scarcity: "Only 3 bottles left."

**Scene Seeker:** +40–70% vs baseline, dwell 120–150 min. Trigger: Instagrammable presentation before first sip. Staff script: "This is our most photographed dish." Limited-edition menu items drive high convergence.

**Trusted Regular:** +20–40% vs baseline, 60–70% repeat within 30 days. Trigger: Name greeting (belonging cue activates insider identity). Staff script: "[Name], the chef sent something for you to try." Showing venue to guests adds +50% spend.

**Habit Former:** Food 75–80%, lowest peer influence (0.10), 70–80% repeat within 30 days, lowest WOM (1.0×). Trigger: Loyalty reward on 10th visit; "Same as usual, premium version?" upgrade within the familiar.

**Calm Pairs:** Mutual accommodation ordering, slow/consultative. Dwell 105–135 min, diminishing returns 120 min. Trigger: Wine by the glass start (low-commitment alcohol entry). Dessert as "let's stay a bit longer" anchor.

**Lifestyle Regular:** Values-aligned group convergence. Natural wine, craft beer, low-ABV cocktails. Trigger: Origin story of ingredient (values alignment unlocks spend premium). "Limited batch local product" combines scarcity + identity.

**Quiet Discoverer:** Solo by choice, lowest peer influence (0.00), highest discovery rate (`very_high`). Trigger: Chef's tasting menu (structured discovery removes decision anxiety). Staff script: "The chef is experimenting with [ingredient]."

**Trend Hunter:** Highest WOM (4.5×), extremely high discovery rate. +50–90% vs baseline. Trigger: "Only available this week" temporal scarcity + FOMO. Viral item = mandatory table order.

**Premium Prioritizer:** Highest RevPASH (₹1000–1800), +200–350% vs baseline. Trigger: Anchoring with highest-price item first. Sommelier narrative + provenance story.

**Discovery Explorer:** Researches menu beforehand, independent. Regional/artisanal drinks. Trigger: Regional ingredient story (authenticity trigger). "Not on the regular menu" exclusivity.

**Power Regular:** 55–65% repeat within 30 days, staff-guided preferences. Trigger: Recognition + table preference (status confirmation). Staff script: "[Name], your usual table is ready." Hosting occasion adds +50%.

---

### 4.4 Fitness Dimensions

Five commercial use-case fitness scores, each 0–1, computed per venue.

| Dimension | Key | Required Signals | Strength Tiers |
|-----------|-----|-----------------|----------------|
| Office Lunch Fitness | `fitness_for_office_lunch` | `quick_meal`, `office_crowd`, `convenient_location`, `fast_service` | STRONG (≥0.75), MODERATE (≥0.50), EMERGING (≥0.25), NASCENT (<0.25) |
| Repeat Habit Fitness | `fitness_for_repeat_habit` | `repeat_visits`, `convenient_location`, `fast_service`, `food_quality` | Same tiers |
| Social Dwell Fitness | `fitness_for_social_dwell` | `long_dwell`, `live_music`, `social_energy`, `extended_stay` | Same tiers |
| Group Energy Fitness | `fitness_for_group_energy` | `social_energy`, `group_spend_amplification`, `live_music` | Same tiers |
| Destination Visit Fitness | `fitness_for_destination_visit` | `great_view`, `authentic_taste`, `pride`, `premium_pricing`, `wonder_ambience`, `destination_driven_retention` | Same tiers |

> **Note:** Signal IDs corrected 2026-05-25. Previous version used dead IDs (`quick_service`, `authenticity_signal`, `status_display`, `multi_round_ordering`) that produced all-zero fitness scores for 52% of google_reviews venues. Fixed IDs are validated against actual step_4 cluster data.

**Fitness Score Formula:**
```
fitness_score = match_ratio × confidence_basis

where:
  match_ratio = matched_required_signals / total_required_signals
  confidence_basis = avg(final_score of patterns containing matched signals)
                     OR avg_baseline_confidence if no pattern match
```

**Behavioral Summary (per venue):**

| Field | Computation |
|-------|-------------|
| `operational_quality` | `avg(final_score)` across all scored patterns |
| `retention_strength` | `final_score` of first pattern whose `archetype_hypothesis` contains "repeat" or "loyalty" |
| `monetization_potential` | `final_score` of first pattern whose hypothesis contains "premium", "dwell", or "ordering" |

---

### 4.5 Behavioral Mechanisms

Seeded via `App/backend/db/003_seed_mechanisms_channels_weights.sql`.

Categories: `social_influence`, `scarcity_urgency`, `identity_status`, `habit_automaticity`, `environmental`, `loss_aversion`, `cultural_capital`

Core mechanisms include:
- **Social Proof** (`social_proof`) — `social_influence` — crowd, ratings, visible popularity trigger conformity
- **FOMO** (`fomo`) — `scarcity_urgency` — fear of missing out drives urgency and first visits
- **Identity** (`identity`) — `identity_status` — venue as extension of self-image
- **Habit** (`habit`) — `habit_automaticity` — routine reduces decision cost, drives repeat visits
- **Anchoring** (`anchoring`) — `loss_aversion` — high price set first calibrates willingness to pay

---

## 5. Data Pipeline — Google Places API

**Location:** `D:\PolyNovea\Module 2\Google Places API\`

**Orchestration:** `run_pipeline.py --city <city-name>`  
**Cities config:** `config/cities.json` (navi-mumbai, mumbai-main, mumbai-sobo, thane)

---

### 5.1 Step 1 — Venue Discovery

**Script:** `scripts/step_1_discover.py`  
**API:** Google Places API v1 — Text Search (New)  
**SKU tier:** Basic (cheapest)

**Field mask (`DISCOVERY_MASK`):**
```
places.id, places.displayName, places.types,
places.location, places.primaryType, places.businessStatus
```

**Quality filters applied at discovery:**
- `MIN_RATING = 4.0` — Only venues with Google rating ≥ 4.0
- `MIN_REVIEWS = 150` — Only venues with ≥ 150 reviews
- `INCLUDE_CATEGORIES` — restaurant, bar, lounge, cafe, pub, bistro, brewery, club, rooftop
- `EXCLUDE_CATEGORIES` — fast food, dhaba, lunch home, corner, stall, street vendor, tiffin, quick service, kiosk, food cart, vendor, takeaway

**Query strategy:** `"restaurant in [area], [city], India"` + 7 venue type queries per area

**Rate limiting:** `RATE_LIMIT_DELAY = 0.2s` between calls, `MAX_RETRIES = 3`, `RETRY_WAIT_SECONDS = 2`

**Output:** `data/<city>/step_1_venues_refined.json`
```json
{
  "name": "Venue Name",
  "place_id": "ChIJ...",
  "area": "Vashi",
  "city": "navi-mumbai",
  "types": ["restaurant", "bar"],
  "location": {"lat": 19.07, "lng": 73.01},
  "primaryType": "restaurant",
  "discovered_at": "2026-05-14T..."
}
```

---

### 5.2 Step 2c — Review Harvesting

**Script:** `scripts/step_2c_harvest.py`  
**API:** Google Places API v1 — Place Details  
**SKU tier:** Preferred (reviews trigger Preferred Data tier)

**Field mask (`REVIEW_MASK`):**
```
reviews.text, reviews.publishTime, reviews.rating
```

> **Deliberately excluded** (to avoid extra SKU charges): `rating`, `userRatingCount`, `openingHours`, `priceLevel`

**Settings:**
- `MAX_REVIEWS_PER_CALL = 5`
- `RECENT_REVIEWS_DAYS = 365`
- Deduplication: hash-based
- Pagination: until no new reviews returned

**Output:** `data/<city>/step_2c_reviews_grouped.json` — reviews per venue, `step_2c_stats.json` — review count stats

**Logs:** `data/<city>/logs/step_2c_harvest.log`

---

### 5.3 Step 3 — Signal Extraction

**Script:** `scripts/step_3_extract.py` (also present in Google Raw Scrapper)

**Input:** Reviews from step 2c  
**Output:** `data/<city>/step_3_signals_extracted.json`

**5-Factor Signal Detection:**

| Factor | Keywords (subset) |
|--------|------------------|
| `ambience` | ambience, vibe, aesthetic, lighting, cozy, rooftop, interior, decor, atmosphere |
| `music` | music, dj, live music, loud, playlist, sound, noise, beats |
| `crowd` | crowd, packed, empty, couples, groups, young crowd, busy, lively, bustling |
| `service` | service, staff, slow, rude, waiting, attentive, friendly, waiter, bartender |
| `price` | expensive, overpriced, reasonable, worth it, value for money, affordable |

**Additional extraction per review:**
- **Temporal signals** — lunch, weekends, evening, late-night, office_rush
- **Negation handling** — "not friendly" → negative signal
- **Contradiction tracking** — "great food but terrible service" → contradiction pair
- **Confidence scoring** — per-signal confidence based on keyword match strength

**Per-review output:**
```json
{
  "review_id": "...",
  "text_snippet": "...",
  "timestamp": "2026-04-12",
  "source": "google",
  "signals": ["social_energy", "live_music", "long_dwell"],
  "confidence": 0.78,
  "contradictions": [],
  "temporal_tags": ["evening", "weekend"]
}
```

---

### 5.4 Step 4 — Pattern Recognition & Clustering

**Script:** `scripts/step_4_pattern.py`

**Input:** `step_3_signals_extracted.json`  
**Output:** `step_4_behavioral_clusters.json`, `step_4_patterns_recognized.json`

**Algorithm:**
1. Aggregate all signals per venue across all reviews
2. Compute pairwise signal co-occurrence frequencies
3. Cluster signals that co-occur above threshold into pattern groups
4. For each cluster, compute:
   - `prevalence` — % of venues exhibiting this pattern
   - `strength` — raw frequency of signal occurrence
   - `confidence` — average detection confidence across reviews
   - `evidence_density` — review count supporting the cluster / total reviews
   - `contradiction_score` — proportion of contradictory signal pairs within cluster
   - `pattern_stability` — variance of cluster membership across temporal windows
   - `co_occurring_primitives` — list of primitive IDs in this cluster
   - `archetype_hypothesis` — tentative archetype assignment (not a label — a hypothesis)
   - `supporting_reviews` — reviews contributing to this cluster

**Output schema (per cluster):**
```json
{
  "co_occurring_primitives": ["social_energy", "live_music", "long_dwell"],
  "confidence": 0.72,
  "evidence_density": 0.45,
  "contradiction_score": 0.08,
  "pattern_stability": 0.64,
  "archetype_hypothesis": "party_seeker",
  "supporting_reviews": [...]
}
```

**City-level output (step_4_patterns_recognized.json):**
- Pattern definitions with trigger examples
- Cross-venue prevalence statistics
- Co-occurrence matrix

---

### 5.5 Step 4b — Governance Validation

**Script:** `scripts/step_4b_governance_validate.py`

**Input:** Clusters from step 4  
**Output:** `step_4b_governance_report.json`, `step_4b_governance_report_previous.json`

**Validation checks:**

| Check | What it measures |
|-------|-----------------|
| Cluster stability | How consistent pattern membership is across temporal windows |
| Signal reliability | Source credibility × temporal consistency |
| Drift detection | Whether cluster definitions have shifted vs. previous run |
| Anomaly flags | Outlier venues or unusually high contradiction scores |
| Governance status | `approved`, `flagged`, `quarantined` |

**Typical results (navi-mumbai):**
- Overall reliability: 74%
- High-reliability clusters: 91%
- Confidence range: 50–57% average per pattern
- Prevalence range: 1–3% per pattern

---

### 5.6 Step 5 — Behavioral Scoring

**Script:** `scripts/step_5_score.py`

**Input:** `step_4_behavioral_clusters.json` + `step_4b_governance_report.json`  
**Output:** `step_5_behavioral_scores.json` + `step_5_patterns_scored.json`

#### 8-Component Composite Score

Each cluster (pattern) in each venue receives a `final_score` computed as:

```
final_score = (
    confidence         × 0.22
  + evidence_density   × 0.16
  + temporal_consistency × 0.14
  + evidence_diversity × 0.14
  + commercial_reliability × 0.18
  + pattern_stability  × 0.10
  + confidence_decay   × 0.06
) × (1 − contradiction_penalty)
```

| Component | Weight | Computation |
|-----------|--------|-------------|
| `confidence` | 22% | Raw cluster detection confidence from step 4 |
| `evidence_density` | 16% | Cluster support reviews / total venue reviews |
| `temporal_consistency` | 14% | Stability of review intervals (variance formula) |
| `evidence_diversity` | 14% | 40% phrase diversity + 30% source diversity + 30% temporal diversity |
| `commercial_reliability` | 18% | Avg `COMMERCIAL_SIGNAL_WEIGHTS` of signals present |
| `pattern_stability` | 10% | Cluster consistency metric from step 4 |
| `confidence_decay` | 6% | Exponential decay: `exp(−age_days / 365)` averaged across review timestamps |
| `contradiction_penalty` | Multiplier | Reduces final score: minor=0.10, moderate=0.25, severe=0.50 |

**Contradiction severity thresholds:**
- Minor: `contradiction_score ≤ 0.10`
- Moderate: `contradiction_score ≤ 0.30`
- Severe: `contradiction_score > 0.30`

**Temporal consistency formula:**
```python
intervals = differences_between_sorted_review_dates
variance = population_variance(intervals)
stability = 1 / (1 + variance / 30)
temporal_consistency = clamp(stability, 0.0, 1.0)
# Returns 0.3 if < 2 valid timestamps
```

**Evidence diversity formula:**
```python
diversity = (
    phrase_diversity  × 0.4   # unique 80-char snippets / total reviews
  + source_diversity  × 0.3   # unique sources / total reviews
  + temporal_diversity × 0.3  # unique dates / total reviews
)
```

**Confidence decay formula:**
```python
decay = avg(exp(−age_days / 365) for each review timestamp)
# Returns 0.5 if no valid timestamps
```

#### Intervention Opportunities (computed in step 5)

Six intervention types are detected based on signal presence:

| Intervention | Required Signals | Description |
|-------------|-----------------|-------------|
| `operational_optimization` | `repeat_visits` + `long_queue` | High repeat intent with queue friction — streamline flow |
| `premium_justification` | `premium_pricing` + `great_view` | Premium pricing sustained by experience quality |
| `dwell_monetization` | `long_dwell` + `group_spend_amplification` | Extended stay with group spend — upsell and event programming opportunity |
| `friction_reduction` | `repeat_visits` + `slow_service` | Loyal base tolerating service friction |
| `authenticity_leverage` | `authentic_taste` + `long_queue` | Queue driven by authentic food reputation — scarcity positioning opportunity |
| `social_amplification` | `social_sharing` + `wonder_ambience` | Shareable space driving organic referrals — invest in visual merchandising |

**Intervention fit score:**
```
fit_score = match_ratio × confidence_basis
```

**Priority tiers:**
- `HIGH` (fit ≥ 0.75) — Urgent optimization, all signals at high confidence
- `MEDIUM` (fit ≥ 0.45) — Ready for consulting, strong foundation with actionable gaps
- `CANDIDATE` (fit ≥ 0.25) — High-potential, foundation signals present
- `EXPLORE` (fit < 0.25) — Early stage, monitor for development

**step_5_patterns_scored.json structure:**
```json
{
  "pattern_name": "social_energy + live_music",
  "confidence": "57%",
  "confidence_score": 57,
  "venue_count": 12,
  "prevalence": "2.1%",
  "venues": ["Venue A", "Venue B", ...],
  "frequency_score": "40.0",
  "consistency_score": "30.0",
  "recency_score": "20.0",
  "friction_severity": "low"
}
```

---

### 5.7 Step 5b — Similarity Enrichment

**Script:** `scripts/step_5b_similarity.py`

**Input:** `step_5_behavioral_scores.json`  
**Output:** `step_5b_similarity.json`, `step_5b_similarity_enriched.json`

**Algorithm:**
1. Build signal vector for each venue (binary presence of each signal)
2. Compute cosine similarity between all venue pairs
3. For each venue: retain top 25 most similar venues
4. Identify shared primitives (signals present in both venues)

**Output per venue:**
```json
{
  "venue_name": "...",
  "similar_venues": [
    {
      "name": "...",
      "similarity_score": 0.84,
      "shared_primitives": ["social_energy", "live_music"],
      "delta_primitives": ["repeat_visits"]
    }
  ]
}
```

This data powers the **Competitors** and **Transform** tabs in the frontend.

---

### 5.8 Step 6 — Output & Interventions

**Script:** `scripts/step_6_output.py`

**Input:** `step_5_behavioral_scores.json`  
**Output:** `step_6_output.json`

**Per-venue output structure:**
```json
{
  "venue": "Venue Name",
  "mechanisms": [
    {
      "observation": {
        "co_occurring_primitives": [...],
        "supporting_review_count": 18
      },
      "inferred_structure": {
        "narrative": "Stimulus: great view, live music → friction present (premium pricing) → behavioral response: long dwell, repeat visits",
        "archetype_hypothesis": "party_seeker"
      },
      "confidence": {
        "score": 0.63,
        "pattern_stability": 0.71,
        "evidence_density": 0.44,
        "temporal_consistency": 0.58,
        "confidence_decay": 0.82
      },
      "contradictions": {
        "score": 0.09,
        "pairs_preserved": ["fast_service | slow_service"]
      },
      "intervention_opportunities": [...]
    }
  ],
  "fitness_dimensions": {...},
  "operational_leverage": [...],
  "behavioral_summary": {
    "operational_quality": 0.61,
    "retention_strength": 0.58,
    "monetization_potential": 0.67
  }
}
```

**Narrative generation logic:**
- Stimuli signals: primitives containing `view`, `music`, `energy`, `setting`, `authentic`
- Friction signals: primitives containing `queue`, `premium`, `wait`, `slow`, `crowd`
- Response signals: primitives containing `dwell`, `repeat`, `order`, `return`, `stay`
- Builds: `Stimulus: X → friction present (Y) → behavioral response: Z`

**City-level summary:**
- Top 10 highest-confidence mechanisms across all venues
- All intervention opportunities aggregated

---

## 6. Data Pipeline — MagicPin Scraper

**Location:** `D:\PolyNovea\Module 2\Magic Pin and Zomato\Magic Pin\`

**Runtime requirement:** `runtime/obscura.exe` + `runtime/obscura-worker.exe` must be running (Chrome DevTools Protocol wrapper)

### 6.1 Orchestrator (`orchestrator.js`)

Manages a pool of browser workers across cities. Accepts CLI flags:
- `--city` — Target city (mumbai, navi-mumbai, sobo, thane)
- `--workers` — Worker count (default: configurable)
- `--resume` — Resume from previous run checkpoint

Coordinates per-city venue queues, aggregates JSONL output, handles errors.

### 6.2 Worker (`worker.js`)

Per-venue extraction using Puppeteer-core + CDP attach:
1. Navigate to MagicPin venue page
2. Extract reviews with pagination (hash-change sync — detects new content via content hash)
3. Append reviews to city JSONL file (`output/<city>/reviews-<timestamp>.jsonl`)

**Output format:** One JSON object per line
```json
{"venue_name": "...", "review_text": "...", "rating": 4, "timestamp": "...", "source": "magicpin_upper"}
```

### 6.3 Debug Script (`isolated_review_debug.js`)

Single-venue extraction with verbose logging. Used for:
- Testing new CSS selectors
- Diagnosing extraction issues
- Validating output format before full run

### 6.4 Place ID Enrichment (`enrich-resolver-output.js`)

Post-scraping step that adds `place_id` to each scraped review:
- Matches MagicPin venues to Google `place_id` using name + area matching
- Strategy: exact match → normalized match → fuzzy match (threshold configurable)
- Target match rate: ≥ 90% per city
- Output: `resolver_output/<city>/resolved.jsonl`

**Why place_id over name matching:** place_id provides 100% reliable join key vs. 70–80% for name-only matching.

### 6.5 Logs & Metrics

- `logs/<city>/run-<timestamp>.jsonl` — Execution log per run
- `metrics/<city>/metrics-<timestamp>.json` — Reviews/sec, errors, elapsed time

---

## 7. Data Pipeline — Google Raw Scrapper

**Location:** `D:\PolyNovea\Module 2\Google Raw Scrapper\Behavioural_Intelligence_Framework\`

This is the development/processing companion to the Google Places API pipeline. It runs the same steps 3–6 on raw scraped review data (as opposed to API-harvested data).

### 7.1 Structure

```
scripts/
  config/
    primitives.json         ← Canonical 54-primitive registry
    primitives_loader.py    ← Loads primitives into Python dicts
    surface_categories.json ← Venue type taxonomy
    dish_lexicon.json       ← Cuisine/dish keyword mappings
    cities.json             ← City config
  run_pipeline.py           ← Orchestrator
  step_3_extract.py         ← Signal extraction
  step_4_pattern.py         ← Pattern detection
  step_4b_governance_validate.py
  step_5_score.py           ← Scoring
  step_5b_similarity.py     ← Similarity
  step_6_output.py          ← Output

Data/
  <city>/
    step_3_signals_extracted.json
    step_4_behavioral_clusters.json
    step_4_patterns_recognized.json
    step_4b_governance_report.json
    step_5_behavioral_scores.json
    step_5_patterns_scored.json
    step_5b_similarity.json
    step_6_output.json
```

### 7.2 `primitives_loader.py`

Loads `primitives.json` and exposes:
- `STIMULI_KEYWORDS` — dict of stimulus signal → keyword list
- `FRICTION_KEYWORDS` — dict of friction signal → keyword list
- `COMPENSATION_KEYWORDS`
- `EMOTIONAL_RESPONSE_KEYWORDS`
- `BEHAVIORAL_RESPONSE_KEYWORDS`
- `COMMERCIAL_MECHANISM_KEYWORDS`
- `COMMERCIAL_SIGNAL_WEIGHTS` — signal → commercial weight (0–1)
- `FITNESS_SIGNAL_MAP` — dimension → required signals
- `INTERVENTION_TRIGGERS` — intervention name → required signals + description
- `SCHEMA_VERSION` — version string from primitives.json

### 7.3 `dish_lexicon.json`

Maps cuisine/dish keywords to venue categories and segment affinities. Used in step 3 to detect food type signals from review text.

### 7.4 Worker Profiles

`profiles/worker_{1,2,3}/` — Chrome profile directories for browser automation (extensions, cookies, session state)

---

## 8. Database Loaders

All loaders are in `Database/scripts/`. They transform step 6 JSON output into PostgreSQL rows.

### 8.1 Reference Loaders (`reference/`)

**`load_venues.py`**
- Input: `step_1_venues_refined.json` per city
- Upserts into `venues` table on `place_id`
- Fields: `name`, `place_id`, `area`, `city`, `types`, `location`, `source`, `discovered_at`

**`load_demographics.py`**
- Input: Demographic profiles per segment/archetype
- Loads into `venue_demographic_scores`
- Computes segment and archetype prevalence scores per venue based on signal composition

**`load_surveys.py`**
- Input: `survey_canonical_schema.json` (45 responses × 35 archetypes)
- Loads canonical survey response schema mapping survey answers to archetype probabilities

**`load_marketing_engine.py`**
- Input: Channel effectiveness data
- Loads `channel_benchmarks` and `channel_segment_effectiveness` tables

### 8.2 Source-Specific Pipeline Loaders (`pipeline/`)

Each source (google_places_api, magicpin_upper) has its own set of loaders:

**`step3_signals_extraction.py`** — Loads extracted signals into `pattern_scores` with `source` column

**`step4_cluster_and_patterns.py`** — Loads cluster data (co-occurring primitives, confidence, contradiction score)

**`step4b_governance.py`** — Loads governance flags and reliability scores

**`step4b_pattern_scores.py`** — Loads per-pattern confidence scores with source attribution

**`step5_fitness_scores.py`** — Loads fitness dimension scores into `venue_fitness_dimensions`
```sql
INSERT INTO venue_fitness_dimensions 
  (venue_id, source, fitness_for_office_lunch, fitness_for_repeat_habit,
   fitness_for_social_dwell, fitness_for_group_energy, fitness_for_destination_visit,
   behavioral_summary)
VALUES (...)
ON CONFLICT (venue_id, source) DO UPDATE SET ...
```

**`step5b_similarity_enrichment.py`** — Loads top-25 similar venues into `venue_similarity_deltas` with shared primitives

**`step6_mechanisms_and_interventions.py`** — Loads intervention playbooks as JSON into venue records

### 8.3 Utility Loaders

**`compute/compute_venue_demographics.py`** — Derives segment/archetype prevalence from signal composition using fitness scores as proxies

**`compute/compute_fitness_deltas.py`** — Computes per-dimension delta: (venue score − city average for segment) → loads into `venue_fitness_dimensions` as delta fields

**`utils/amendment_service.py`** — Tracks data corrections with full audit trail (who, when, from_value, to_value, reason). Uses `council_sessions.sql` for session management.

**`utils/enrich_step5b.py`** — Post-processes similarity output to add shared primitives and primitive delta lists

**`schema/add_source_to_pattern_scores.py`** — Migration: adds `source` column to `pattern_scores` (was missing, fixed in session C with script 032)

### 8.4 Manual Review Loader

**Script:** (runs as `030_load_manual_reviews_aphrodite.py`)
- Loads hand-annotated review signals for Aphrodite (venue 223)
- Source key: `manual_reviews`
- Used when review volume is insufficient for automated extraction

---

## 9. Blend Layer

**Script:** `Database/scripts/blend/blend_fitness.py` (also `027_blend_fitness.py`)

**Purpose:** Merge fitness scores from multiple sources into a single unified record per venue.

**Algorithm:**
1. Fetch all `venue_fitness_dimensions` rows per venue grouped by source
2. For each fitness dimension, compute weighted average:
   - Source weights are configurable (default: all sources equal)
   - Higher-evidence sources can be weighted higher
3. Store blended result as source key `blended`

**Current blended coverage (2026-05-25):**

| Blend combination | Venue count |
|------------------|-------------|
| `google` only | 4,408 |
| `google` + `google_reviews` | 923 |
| `google` + `google_reviews` + `magicpin_upper` | 196 |
| `google` + `google_reviews` + `manual_reviews` | 1 |
| `google` + `magicpin_upper` | 480 |
| `manual_reviews` only | 1 (Unfilltered 12066) |
| **Total blended** | **6,009** |

**Design principle:** Zero config changes needed when adding a new source — blend runner auto-discovers all source rows and includes them. Add a new source, run blend, done.

---

## 10. Backend API

**Location:** `App/backend/`  
**Framework:** FastAPI + asyncpg (async PostgreSQL)  
**Entry point:** `main.py`

### 10.1 Routers

| Router | Endpoint | Screen | Description |
|--------|----------|--------|-------------|
| `venues.py` | `GET /venues/search` | Screen 1 | Paginated venue search, filters by city/segment |
| `overview.py` | `GET /venues/{id}/overview` | Screen 5 | Fitness radar, segment alignment, archetypes |
| `competitors.py` | `GET /venues/{id}/similar` | Screen 2 | Similar venues, shared primitives, feature comparison |
| `transform.py` | `GET /venues/{id}/transform` | Screen 3 | Experience engineering recommendations |
| `marketing.py` | `GET /venues/{id}/marketing` | Screen 4 | Marketing brief, target audience, channel strategy |
| `intelligence.py` | `GET /venues/{id}/intelligence` | Screen 6 | Behavioral patterns, confidence, mechanisms |
| `risk.py` | `GET /venues/{id}/risk` | Screen 6 Risk | Operational vulnerabilities, retention risks |
| `primitives_tab.py` | `GET /venues/{id}/primitives` | Screen 6 Primitives | Behavioral signal registry |
| `benchmarks.py` | `GET /venues/{id}/benchmarks` | Screen 6 Benchmarks | City/segment comparisons |
| `trends_tab.py` | `GET /venues/{id}/trends` | Screen 6 Trends | Temporal patterns, emerging signals |
| `audience.py` | `GET /venues/{id}/audience` | Screen 7 | Audience profiling, segment demographics |
| `chat.py` | `POST /venues/{id}/chat` | All | AI chat with venue context (Claude API) |

### 10.2 Transform Tab Logic

The Transform tab surfaces similar venues stratified into 4 acquisition tiers:

| Tier | Condition | Quota |
|------|-----------|-------|
| **Role Model** | ATA ≥ 0.50 | 10 venues |
| **Bridge** | Target rank 2–3, alignment ≥ 0.30 | 8 venues |
| **Transition** | ATA 0.20–0.50 | 14 venues |
| **Pure Target** | ATA < 0.20 | 8 venues |

**Composite sort key:**
```
composite = target_align × (1 − effort) × (0.70 + 0.30 × geo)
```

**Effort labels:** Quick Win | Major Initiative | Strategic Pivot (upward-only gaps)

### 10.3 Competitors Tab Logic

- Default sort: `threat` — weighted cosine × geo distance
- Alt sort: `benchmark` — fitness excellence
- Bucketing: A (all venue types match), B (2+ types), C (1 type), D (segment only)
- AI deep-dive: Nvidia reasoning model, `<think>` stripping, trailing-comma JSON fix

### 10.4 Models (`models.py`)

Key Pydantic response schemas:
- `VenueCard` — Search result card
- `SearchResponse` — Paginated venue list
- `FitnessRadar` — 5-dimension fitness polygon
- `SegmentRow` — Segment alignment row
- `CompetitorCard` — Similar venue comparison
- `TransformTier` — Acquisition tier result

### 10.5 Chat Endpoint

`POST /venues/{id}/chat`
- Loads venue context: fitness scores, top patterns, archetype alignment, competitive position
- Routes to Claude API (educational-only guardrails per `CHAT_SAFEGUARDS.md`)
- Guardrails: company questions get real answers; machinery questions are sealed

---

## 11. Frontend

**Location:** `App/frontend/`  
**Framework:** Next.js 15 + React + Tailwind CSS  
**API client:** `lib/api.ts` (Axios), `lib/chat-api.ts`

### 11.1 Pages

| Route | Component | Description |
|-------|-----------|-------------|
| `/` | `app/page.tsx` | Venue search with city/segment filters |
| `/venues/[id]` | `app/venues/[id]/page.tsx` | Overview with fitness radar |
| `/venues/[id]/competitors` | competitors page | Similar venues drawer |
| `/venues/[id]/transform` | transform page | Acquisition tier cards |
| `/venues/[id]/marketing` | marketing page | Ad brief, channel cards, WhatsApp generator |
| `/venues/[id]/intelligence` | intelligence page | Behavioral patterns, risk, primitives, benchmarks, trends |
| `/venues/[id]/audience` | audience page | Segment profiles, archetype breakdown |
| `/venues/[id]/campaign` | campaign page | Campaign builder with audience simulator |

### 11.2 Key Components

| Component | Purpose |
|-----------|---------|
| `ScoreRing.tsx` | Circular 0–100 fitness score ring |
| `ChatDrawer.tsx` | Claude AI chat panel |
| `ChatDrawerWrapper.tsx` | Chat state management |
| `VenueNav.tsx` | Tab navigation bar |
| `CompetitorDrawer.tsx` | Competitor AI deep-dive drawer (reused for Transform) |
| `AudienceClient.tsx` | Segment/archetype client-side UI |
| `AdBriefCard.tsx` | Campaign ad brief display |
| `AIChannelCard.tsx` | Marketing channel strategy cards |
| `WhatsAppGenerator.tsx` | WhatsApp message template generator |

### 11.3 Branding

- Floating chat button label: "Ask Polynovea"
- Chat fallback title: "Polynovea Intelligence"
- Channel cards: "POLYNOVEA INSIGHT"
- WhatsApp section: "POLYNOVEA MESSAGE GENERATOR"

---

## 12. Configuration Reference

### 12.1 `Database/config/primitives.json`

- `version`: Schema version string
- `total_primitives`: 54
- `primitives`: Map of `primitive_id` → `{id, name, category, data_type, range, description, extraction_keywords}`

**Do not add primitives inline in scripts.** All primitive definitions must live here. Scripts load via `primitives_loader.py`.

### 12.2 `config/constants.py` (Google Places API)

| Constant | Value | Purpose |
|----------|-------|---------|
| `GOOGLE_PLACES_API_KEY` | from `.env` | API authentication |
| `DISCOVERY_MASK` | Basic fields | Step 1 field mask |
| `REVIEW_MASK` | `reviews.text/publishTime/rating` | Step 2c field mask |
| `ENTERPRISE_MASK` | `userRatingCount` | Step 2c extended (use sparingly) |
| `MIN_RATING` | 4.0 | Quality filter |
| `MIN_REVIEWS` | 150 | Quality filter |
| `MAX_REVIEWS_PER_CALL` | 5 | API limit |
| `RECENT_REVIEWS_DAYS` | 365 | Review recency window |
| `MAX_RETRIES` | 3 | API retry limit |
| `RETRY_WAIT_SECONDS` | 2 | Retry delay |
| `RATE_LIMIT_DELAY` | 0.2s | Between-call throttle |

**SKU governance rule:** Never add fields to `REVIEW_MASK` without confirming the SKU tier. Fields like `rating`, `userRatingCount`, `openingHours`, `priceLevel` trigger additional charges.

### 12.3 `config/cities.json`

```json
{
  "navi-mumbai": { "areas": [...], "data_path": "data/navi-mumbai" },
  "mumbai-main": { "areas": [...], "data_path": "data/mumbai/main" },
  "mumbai-sobo": { "areas": [...], "data_path": "data/mumbai/sobo" },
  "thane":       { "areas": [...], "data_path": "data/thane" }
}
```

### 12.4 Source Key Registry

| Key | Status | Venues | Regions | Description |
|-----|--------|--------|---------|-------------|
| `google` | ✅ Live | 6,008 | Mumbai Main, Mumbai SoBo, Navi Mumbai, Thane | Google Places API |
| `magicpin_upper` | ✅ Live | 676 | Mumbai, Navi Mumbai, SoBo, Thane | MagicPin upper-tier venues |
| `google_reviews` | ✅ Live | 1,120 | **Thane, Navi Mumbai only** | Google Raw Scrapper BIF pipeline |
| `manual_reviews` | ✅ Live | 2 | Manual | Aphrodite (223), Unfilltered (12066) |
| `magicpin_lower` | ❌ RETIRED | — | — | Superseded by `google_reviews` |
| `zomato` | ⏳ Future | — | — | |
| `tripadvisor` | ⏳ Future | — | — | |

### 12.5 `CONTRADICTION_SEVERITY`

| Level | Score threshold | Penalty multiplier |
|-------|-----------------|--------------------|
| `minor` | ≤ 0.10 | 0.10 (10% score reduction) |
| `moderate` | ≤ 0.30 | 0.25 (25% score reduction) |
| `severe` | > 0.30 | 0.50 (50% score reduction) |

---

## 13. Pipeline Orchestration

### 13.1 `run_pipeline.py` (Google Places API)

```bash
python run_pipeline.py
python run_pipeline.py --city navi-mumbai
```

Runs steps 3, 4, 4b, 5, 5b, 6 for all configured cities (or a single city).

Returns `step_results` dict:
```json
{
  "navi-mumbai": {
    "step_3": {"success": true, "elapsed": 12.3},
    "step_4": {"success": true, "elapsed": 4.1},
    ...
  }
}
```

### 13.2 Numbered Script History (Database/scripts/)

Scripts are numbered for ordered execution. Key milestones:

| Script | Purpose |
|--------|---------|
| `026_load_magicpin_step6_fitness.py` | Load MagicPin upper fitness scores (676 venues, 4 regions) |
| `027_blend_fitness.py` | Reblend all sources — now includes google_reviews (6,009 venues) |
| `028_migrate_magicpin_source_names.py` | Source key correction (was no-op — already correct) |
| `029_load_magicpin_lower_step6_fitness.py` | SUPERSEDED — do not use |
| `030_load_manual_reviews_aphrodite.py` | Load Aphrodite manual review scores |
| `031_load_google_reviews_step6_fitness.py` | SUPERSEDED — replaced by google_reviews/ folder loaders |
| `032_add_source_to_pattern_scores.py` | Schema fix — added `source` column to `pattern_scores` |

**Google Reviews loaders** (`pipeline/google_reviews/` — all ✅ loaded, regions: thane + navi-mumbai):

| Script | Tables | Row count |
|--------|--------|-----------|
| `step3_primitives.py` | `primitives_scores` | 25,039 |
| `step4_cluster_and_patterns.py` | `behavioral_patterns`, `pattern_venues`, `raw_venue_data` | 3,358 / 14,010 / 1,120 |
| `step4b_governance.py` | `data_quality_metrics`, `cluster_quality`, `drift_signals` | 2 / 2 / 3,358 |
| `step4b_pattern_scores.py` | `pattern_scores` | 3,358 |
| `step5b_similarity_loader.py` | `venue_vectors`, `venue_similarity` | 1,114 / 27,836 |
| `step6_fitness_and_interventions.py` | `venue_fitness_dimensions`, `behavioral_summary`, `intervention_triggers` | 1,120 / 1,120 / 6,720 |

> `016_load_audience_profiles.py` — DO NOT RUN — conflicts with db/ ENUM schema. The db/ system is authoritative.

### 13.3 Adding a New Source

When a new data source becomes available (e.g., `google_reviews`):
1. Drop BIF output files into `data/raw/<source>/<region>/`
2. Build `0XX_load_<source>_step6_fitness.py` with `source='<source_key>'`
3. If step 5b similarity files included: run `enrich_step5b.py`
4. Run `027_blend_fitness.py` — auto-discovers new source, no config changes needed

---

## 14. Data Coverage

### Review corpus — raw human review counts by source

| Source | City / Region | Venues | Reviews | Avg reviews/venue |
|--------|--------------|--------|---------|-------------------|
| `google` (Places API) | Navi Mumbai | 892 | 4,379 | ~5 |
| `google` (Places API) | Mumbai Main | 3,341 | 16,306 | ~5 |
| `google` (Places API) | Mumbai SoBo | 1,223 | 6,011 | ~5 |
| `google` (Places API) | Thane | 492 | 2,445 | ~5 |
| **google subtotal** | **4 cities** | **5,948** | **29,141** | **~5** |
| `google_reviews` (BIF scrape) | Thane | 399 | 148,350 | ~372 |
| `google_reviews` (BIF scrape) | Navi Mumbai | 721 | 255,220 | ~354 |
| **google_reviews subtotal** | **2 cities** | **1,120** | **403,570** | **~360** |
| `magicpin_upper` | Mumbai | 295 | 26,894 | ~91 |
| `magicpin_upper` | Navi Mumbai | 164 | 17,498 | ~107 |
| `magicpin_upper` | SoBo | 159 | 16,285 | ~102 |
| `magicpin_upper` | Thane | 58 | 5,669 | ~98 |
| **magicpin subtotal** | **4 regions** | **676** | **66,346** | **~98** |
| **GRAND TOTAL** | | **~6,600 unique** | **~499,057** | |

> **Important distinction:** The Google Places API (`google` source) is limited to **5 reviews per venue** by the API. The `google_reviews` BIF scraper retrieves the full public review corpus — averaging **360 reviews per venue** for the same Google reviews. This is why `google_reviews` produces 403,570 reviews from only 1,120 venues, versus 29,141 reviews from 5,948 venues for the `google` API source. The behavioral intelligence depth from `google_reviews` is ~70× richer per venue.

### Venue counts by city (Google Places API source)

| City | Venues discovered | Venues with reviews | Reviews collected |
|------|------------------|--------------------|--------------------|
| Navi Mumbai | 898 | 892 | 4,379 |
| Mumbai Main | 3,378 | 3,341 | 16,306 |
| Mumbai SoBo | 1,238 | 1,223 | 6,011 |
| Thane | 493 | 492 | 2,445 |
| **Total** | **6,007** | **5,948** | **29,141** |

### Quality thresholds enforced at ingestion

| Filter | Value | Applied at |
|--------|-------|-----------|
| Min Google rating | ≥ 4.0 | Step 1 |
| Min review count | ≥ 150 | Step 1 |
| Max review age | 365 days | Step 2c |
| Venue type whitelist | 9 types | Step 1 |
| Venue type blacklist | 12 types | Step 1 |

### DB row counts by source (2026-05-25 — post pipeline upgrade reload)

| Table | google | magicpin_upper | google_reviews | manual_reviews | blended |
|-------|--------|----------------|----------------|----------------|---------|
| `primitives_scores` | 23,821 | 2,624 | 25,039 | — | — |
| `behavioral_patterns` | 25,072 | 327 | 3,358 | — | — |
| `pattern_venues` | 61,095 | 708 | 14,010 | — | — |
| `raw_venue_data` | 10,230 | 1,559 | 1,120 | 1 | — |
| `data_quality_metrics` | 4 | 4 | 2 | — | — |
| `drift_signals` | 7,160 | 114 | 3,358 | — | — |
| `cluster_quality` | 4 | 4 | 2 | — | — |
| `pattern_scores` | 25,072 | 327 | 3,358 | — | — |
| `venue_fitness_dimensions` | 6,008 | 676 | 1,120 | 2 | 6,009 |
| `behavioral_summary` | 6,007 | 676 | 1,120 | 2 | 6,009 |
| `venue_vectors` | 5,759 | 670 | 1,114 | 1 | — |
| `venue_similarity` | 216,048 | 16,890 | 27,836 | 50 | — |
| `intervention_triggers` | 27,996 | 2,704 | 6,720 | 4 | — |

> `google_reviews` pattern count increased from 2,624 → 3,358 after pipeline upgrade (venue_primitives injection in step_4 picks up additional co-occurrence patterns from venue-level aggregate signals).

### Pipeline output metrics (google_reviews — 2026-05-25)

| Metric | Thane | Navi Mumbai |
|--------|-------|-------------|
| Venues | 399 | 721 |
| Governance avg confidence | 73.6% | 73.2% |
| Governance reliability | 79.8% | 79.3% |
| Patterns detected | 1,362 | 1,996 |
| Venue links | 5,031 | 8,979 |
| Similarity pairs | 9,860 | 17,976 |
| Non-zero fitness venues | ~82% | ~82% |

---

---

## 15. Research Foundation — Per-Finding Attribution

This section documents what each research finding contributed to the system with exact specificity: which column, which table, which constant, which function received the finding — and the confidence level of that mapping.

---

### 15.1 Research File Index

| File | Source / Method | Primary Contribution | Confidence |
|------|----------------|---------------------|-----------|
| `behavioral_intelligence_module.md` | Kimi AI synthesis + India hospitality literature | All 7 segment profiles and 11 archetype profiles seeded into `002_seed_segments_archetypes.sql` | INFERRED–SYNTHESIZED |
| `PHASE_1_INDIA_BEHAVIORAL_RESEARCH.md` | Vendor case studies + India platform research | `channel_benchmarks` table, `channel_segment_effectiveness` table, CAC estimates | MEDIUM (vendor-reported) |
| `behavioral_acquisition_mechanisms_hospitality.md` | Academic literature (Cialdini, Kahneman/Tversky, etc.) | `behavioral_mechanisms` table, `mechanism_category` ENUM, Step 6 narrative structure | HIGH for mechanism logic |
| `Indian_FB_Consumer_Segmentation_Validation_Report.md` | Kimi external validation against NRAI, BCG, Zomato, Swiggy | Added Solo Diners + Working Women segments, flagged archetype hypotheses | HIGH — independent critique |
| `archetype_segment_validation_kimi.md` | Parameter-by-parameter validation against peer-reviewed research | `research_validation_flags` table, confidence formula design | HIGH — most rigorous document |
| `polynovea_three_layer_behavioral_intelligence_architecture_module2.md` | Internal architecture design | Three-layer architecture, roadmap ordering, survey schema fields | System design |
| `venue_segment_alignment_research.md` | Internal synthesis | `venue_cuisine_type_priors.py`, competitor bucketing logic | SYNTHESIZED |
| `venue_cuisine_type_research.md` | Internal synthesis | Cuisine type prior probabilities | SYNTHESIZED |
| `marketing_channel_strategy_research.md` | India platform + vendor research | Channel strategy cards in Marketing tab | MEDIUM |
| `india_fb_ad_brief_generator_research.md` | India-specific ad research | `AdBriefCard.tsx` copy rules, `WhatsAppGenerator.tsx` templates, `prompts.py` creative angles | MEDIUM |
| `india_market_intelligence_perplexity.md` | Perplexity AI + NRAI/BCG/Zomato/Swiggy reports | Market sizing numbers in frontend, audience simulator context | MEDIUM |
| `MARKETING_ENGINE_FRAMEWORK.md` | Internal framework design | Marketing engine tab architecture | System design |
| `Behavioral Mechanisms and Channel Effectiveness in Hospitality Marketing.md` | Academic + industry research | `mechanism_category` ENUM, channel-mechanism fit matrix | HIGH for academic logic |
| `Behavioral Segmentation and Targeted Marketing for Hospitality Venues.md` | Academic + industry research | Segmentation theory behind `segment_behavioral_profiles` | HIGH for theory; INFERRED for India application |
| `Polynovea_Master_Operating_Document_FINAL.md` | Internal master doc | Wired into `prompts.py` as system context for Claude AI chat | Operational |

---

### 15.2 Herhausen et al. — Peer Influence Coefficients

**Source:** Herhausen, D., et al. (year). Peer mimicry study. *Nature Communications.* Large-scale university cafeteria, Europe.

**Finding 1:** A dining partner's food purchase increased the focal diner's probability of buying by **14.2 percentage points**.

**Where it lives in the system:**
- `segment_behavioral_profiles.peer_influence_coefficient` column — this is the direct numerical basis for the per-segment peer influence scores. The college_kids segment is assigned the highest coefficient (0.72) because the study's age moderation effect shows the 14.2pp effect is strongest in young adults/students. The office_workers segment is assigned a lower coefficient (0.45) reflecting the study's finding that the effect weakens with age.

**Finding 2:** The effect is age-moderated. For students/young adults: **17.7% increase in buying probability**. For diners over 32 years: **4.0%**.

**Where it lives in the system:**
- This age moderation is the direct rationale for the gap between college_kids `peer_influence_coefficient` and the premium_high_income `peer_influence_coefficient`. Premium segment customers (typically older, high-income) are assigned a low coefficient aligned with the 4.0% figure, not the 17.7% figure.
- The `peer_influence_matrix` view in the DB surfaces this per-segment coefficient for use in the audience simulator and the marketing copy engine.

**Finding 3:** Groups of 3+ diners showed approximately +€2.00 higher individual spend compared to solo diners (from a separate French restaurant group-size study).

**Where it lives in the system:**
- Informs the `group_spend_multiplier` in `segment_occasion_multipliers` for group-occasion rows. The €2.00 figure is converted to approximate INR equivalence and used as the basis for the group occasion spend uplift across social_crowd and couples segments.
- The `group_energy` fitness dimension's commercial_reliability weighting in Step 5 is partly justified by this finding — a cluster with `social_energy + multi_round_ordering` signals is commercially reliable because group dynamics empirically increase per-head spend.

**Confidence:** HIGH for directional effect. MEDIUM for exact magnitude — the study was European cafeteria, not Indian restaurant. The India-specific magnitude remains a hypothesis.

---

### 15.3 Upserve Data — Dwell Time Economics and RevPASH

**Source:** Upserve (restaurant analytics platform) published data on casual dining table turnover. Referenced in `behavioral_intelligence_module.md`.

**Finding:** The optimal dwell time for casual dining is approximately **45 minutes** from a RevPASH (Revenue Per Available Seat Hour) perspective. Beyond 45 minutes, incremental revenue per hour of table occupancy declines — the table is occupied but spend has plateaued.

**Where it lives in the system:**
- `segment_behavioral_profiles.diminishing_returns_minutes` column — set to 45 for office_workers and college_kids (casual dining context), higher for premium and couples (fine-dining context where longer dwell is expected and monetised differently).
- `revenue_curve_shape` ENUM — the ENUM values (`rising`, `flat_plateau`, `long_tail`) are directly derived from the three observed dwell-revenue curve shapes in the Upserve data. A venue with `extended_stay` signals but no `multi_round_ordering` is flagged as having a `flat_plateau` curve — people stay but don't spend more after the initial rounds.
- This finding is the theoretical basis for the `dwell_monetization` intervention type in Step 6. When the system detects extended_stay without multi_round_ordering, it triggers the dwell_monetization intervention because the Upserve data shows this is where revenue is being left on the table.
- The `revpash_economics` view uses the `diminishing_returns_minutes` column alongside the `revenue_per_cover_inr` and `avg_dwell_minutes` columns to compute actual RevPASH estimates per segment.

**Confidence:** MEDIUM. Upserve data reflects US casual dining. India dwell norms, table turnover expectations, and revenue-per-cover figures are different. The shape of the curve (rise → plateau) is inferred to transfer; the 45-minute absolute number is India-adjusted using assumed India pricing, not directly validated.

---

### 15.4 Kahneman & Tversky — Loss Aversion and FOMO Architecture

**Source:** Kahneman, D. & Tversky, A. (1979). Prospect Theory: An Analysis of Decision under Risk. *Econometrica.*

**Finding:** Losses are psychologically weighted approximately **2× more heavily** than equivalent gains. A loss of ₹100 produces roughly twice the emotional impact of a gain of ₹100.

**Where it lives in the system:**

**1. The contradiction_penalty multiplier in Step 5.**
The three-tier penalty structure (0.10 minor / 0.25 moderate / 0.50 severe) reflects loss aversion logic applied to evidence reliability. When evidence is contradictory, the system disproportionately penalises the score — consistent with loss aversion: the system treats noisy evidence as more damaging to reliability than consistent evidence is boosting to it. A score of 0.80 penalised to 0.60 by a severe contradiction is a loss of 0.20 from a high baseline — the penalty is proportionally heavier than the gain that would come from additional confirming evidence.

**2. FOMO spend trigger language in `archetype_spend_triggers`.**
The Party Seeker archetype's spend triggers include scarcity framing: "Only 3 bottles left at this price," "Table hold expires in 8 minutes." These are direct applications of Prospect Theory — the customer's anticipated loss (missing the table, the price, the experience) is framed to be more salient than the equivalent gain. The exact language in `archetype_spend_triggers.trigger_text` was designed using loss framing (not gain framing) specifically because of the 2× asymmetry.

**3. The `behavioral_mechanisms` table row for `fomo_scarcity`.**
- `mechanism_category`: `scarcity_urgency`
- `psychological_logic` field: references loss aversion as the theoretical basis — "anticipated regret at missing exceeds anticipated pleasure at attending"
- `hospitality_context` field: "limited seating, time-bound offers, sold-out warnings"

**Confidence:** HIGH for the underlying psychological principle — Prospect Theory is foundational, robustly replicated. MEDIUM for the exact 2× ratio applied to hospitality spend decisions specifically in India.

---

### 15.5 Loomes & Sugden — Regret Theory and Urgency Triggers

**Source:** Loomes, G. & Sugden, R. (1982). Regret Theory: An Alternative Theory of Rational Choice Under Uncertainty. *The Economic Journal.*

**Finding:** Decision-makers anticipate and try to avoid future regret. This anticipated regret drives choices that differ from pure expected utility maximization. The FOMO-urgency correlation in hospitality contexts is approximately **r=0.86** (from applied hospitality research citing regret theory).

**Where it lives in the system:**
- `behavioral_mechanisms` row for `fomo_scarcity`: `psychological_logic` = "anticipated regret at missing the experience exceeds the pleasure of the alternative decision"
- The WhatsApp message generator's urgency templates reference this mechanism explicitly: "Don't miss the [event] on Friday — only 12 seats left." The urgency language is designed to activate regret anticipation, not desire for the event. The trigger is the fear of a missed story rather than the appeal of the event itself.
- The FOMO `urgency_score` column in `behavioral_mechanisms` (0.87 for scarcity_urgency mechanism) is calibrated to the r=0.86 correlation.
- `channel_segment_effectiveness` for WhatsApp + Social Crowd segment: WhatsApp is assigned the highest urgency activation score because it reaches users with real-time personal interruption (high attention context), maximising regret-anticipation activation.

**Confidence:** HIGH for the regret theory principle. MEDIUM for the r=0.86 figure — this is from applied hospitality research of uncertain sample size and methodology.

---

### 15.6 Cialdini — Social Proof and the Crowded Venue Signal

**Source:** Cialdini, R.B. (1984). *Influence: The Psychology of Persuasion.* Plus: Deutsch & Gerard (1955) informational vs. normative social influence; Banerjee (1992) Rational Herding.

**Finding (Cialdini):** People use the behaviour of others as a shortcut for making decisions under uncertainty. The more prominent the crowd signal, the stronger the social proof effect.

**Finding (Banerjee / Rational Herding):** A visible queue in front of a venue functions as ambient advertising — it signals quality to passers-by who have zero prior information about the venue.

**Where it lives in the system:**

**1. `SIGNAL_KEYWORDS` in `step_3_extract.py`.**
The crowd factor keywords (`packed`, `crowded`, `queue outside`, `always busy`, `fully booked`) are weighted higher in the keyword list (lower index position → higher priority) than ambient descriptions. This is because Cialdini's finding establishes crowd-density language as more diagnostically useful for predicting customer behaviour than aesthetic descriptions. A review saying "always packed on weekends" is more commercially predictive than one saying "lovely decor."

**2. `behavioral_mechanisms` row for `social_proof_demand_gravity`.**
- `mechanism_category`: `social_influence`
- `psychological_logic` field: "crowd density functions as quality proxy; self-reinforcing popularity loop; visible queue = ambient advertising"
- `hospitality_context`: "visible busyness signals venue quality to undecided passers-by; full venue validates choice for customers inside"
- This row is used in the AI intelligence tab to explain to venue owners why their `social_energy` signals matter commercially.

**3. `ARCHETYPE_RULES` in `step_3_extract.py`.**
The `social_amplification_hypothesis` (triggered by `social_energy + social_sharing`) maps to Cialdini's social proof principle — the hypothesis is that this venue's crowded-and-photogenic combination creates a self-amplifying social proof loop via UGC.

**4. Competitor bucketing in the Competitors tab.**
The Competitors tab surfaces high-similarity venues. The rationale for surfacing high-signal competitors — not just geographically proximate venues — is that social proof operates on perception of alternatives. A customer considering Venue A who learns that Venue B (similar signals, same area) is "always packed" will update their valuation of Venue A downward. The bucketing logic therefore weights signal overlap heavily.

**Confidence:** HIGH — Social Proof is among the most robustly validated principles in applied psychology.

---

### 15.7 Ghosh et al. — Child Influence and Families Segment

**Source:** Ghosh, S., et al. *Frontiers in Public Health.* Study on family dining behaviour and children's influence on food purchase decisions. Mumbai and Kochi, India. Qualitative methodology.

**Finding:** Children's demands heavily influence Indian middle-class family food purchases. Families override adult preferences on venue choice and menu selection when children express preferences.

**Where it lives in the system:**

**1. `kids_welcome` primitive in `primitives.json`.**
This primitive is specifically included to capture whether a venue's review signals reflect child-friendly atmosphere, children's menu availability, or family-with-children crowd composition. The Ghosh study is the primary reason this primitive exists as a standalone signal rather than being subsumed under `social_energy` or `group_energy`.

**2. `segment_behavioral_profiles` row for `families`.**
- `occasion_modifier_text` field: references the child-influence finding — when a family unit makes a dining decision, it is often the child's preference that determines the shortlist.
- `peer_influence_coefficient` for families (0.62) is relatively high because the Ghosh study confirms that within a family unit, children exert strong influence on adult decisions — a form of intra-group peer influence.

**3. `archetype_spend_triggers` for the Lifestyle Regular archetype.**
Families with children are mapped primarily to the Lifestyle Regular archetype. The spend trigger text "bring the family — kids eat free on Tuesdays" reflects the Ghosh finding that child-focused incentives are more effective for converting family groups than adult-focused promotions.

**4. Dessert attachment rate for families.**
`archetype_behavioral_profiles.dessert_attach_pct` for the Lifestyle Regular archetype is set to 40-50%. The rationale: children are more likely than adults to request dessert (Ghosh's qualitative finding on child influence over menu choices). This is explicitly flagged in `research_validation_flags` as an INFERRED value — the 40-50% range is a synthesis, not a measured figure from Ghosh.

**Confidence:** HIGH for the qualitative directional finding (children influence family dining). LOW for numerical magnitudes (dessert attachment rates, peer influence coefficients) — those are inferences from the qualitative study.

---

### 15.8 Hiwalkar — Mumbai Discovery Channels

**Source:** Hiwalkar, A. *Gap Interdisciplinarities.* Study on dining discovery channels among frequent diners in Mumbai. n=40 respondents.

**Finding:** Mumbai frequent diners discover venues primarily through:
- Word-of-mouth: **36.8%**
- Social media: **28.7%**
- Food apps (Zomato/Swiggy): **24.1%**
- Other (print, signage, walk-by): remaining ~10%

**Where it lives in the system:**

**1. `segment_platform_usage` table.**
This table stores per-segment platform usage patterns. The Hiwalkar study provides the baseline discovery channel distribution that seeds the `discovery_rate` column. Because the study sampled frequent diners (not segment-specific), these numbers are used as the prior for all segments before segment-level adjustment. Segment adjustments:
- College students: social media weight raised (28.7% → ~40%) based on Gen Z digital-native behaviour
- Office workers: food apps weight raised (24.1% → ~35%) because convenience-driven segment uses apps for speed
- Premium: WOM weight raised (36.8% → ~45%) because premium segment relies more on trusted referral than platform discovery

**2. `channel_benchmarks` calibration.**
WhatsApp is seeded as a high-reach channel for all segments partly because it sits under "word-of-mouth" in the Hiwalkar taxonomy — friend recommendations now predominantly arrive via WhatsApp in India. The 36.8% WOM figure therefore supports WhatsApp's top-tier placement in the channel effectiveness matrix.

**3. Frontend marketing screen.**
The marketing screen displays segment-level discovery channel breakdowns. The 36.8% / 28.7% / 24.1% distribution is the baseline display for any venue whose segment composition has not been overridden by actual campaign data.

**Confidence:** MEDIUM. Sample size (n=40) is small and the study was conducted in Mumbai — broadly appropriate for this system's target geography, but not large enough for strong statistical inference. Used as a directional prior, not an exact measurement.

---

### 15.9 Strohmetz et al. — Staff Reciprocity and Spend Uplift

**Source:** Strohmetz, D.B., et al. (2002). Sweetening the Till: The Use of Candy to Increase Restaurant Tipping. *Journal of Applied Social Psychology.*

**Finding:** Servers who left candy with the bill received **18% higher tips** (tips increased from 15.06% to 17.84% of bill). The mechanism is reciprocity — a small unexpected gift activates the human reciprocity norm, making customers feel obligated to reciprocate generously.

**Where it lives in the system:**

**1. `staff_warmth` primitive in `primitives.json`.**
This primitive exists specifically to capture review signals that indicate warm, attentive, personalized staff behaviour — the kind of behaviour Strohmetz shows produces measurable spend uplift. Keywords include "staff went out of their way," "remembered my order," "made us feel special." These are the observable review signatures of the reciprocity mechanism in action.

**2. `archetype_spend_triggers` for Quiet Discoverer and Solo Diners archetypes.**
These archetypes — characterised by low peer influence and a tendency to visit alone or in small groups — are the most responsive to staff rapport as a spend trigger (because social proof from other customers is absent, staff relationship becomes the primary engagement vector). Their spend triggers include: "personalized recommendation from staff," "remembered your name / last order." These texts are the operational translation of Strohmetz's reciprocity finding into hospitality practice.

**3. `channel_segment_effectiveness` for Solo Diners.**
Solo Diners are assigned a high effectiveness score for `in_venue_staff_touch` as a retention channel — not a digital channel. The Strohmetz finding supports the idea that in-venue staff warmth produces measurable outcome improvement for this segment.

**Confidence:** HIGH for the reciprocity mechanism and directional effect. MEDIUM for exact magnitude (18% tip increase in a US restaurant may not translate to identical spend lift in Indian casual dining contexts). The mechanism transfers; the exact coefficient is inferred.

---

### 15.10 Wechsler et al. — College Alcohol Behaviour

**Source:** Wechsler, H., et al. *Journal of Studies on Alcohol.* U.S. college student drinking behaviour survey.

**Finding:** 74.7% of college students drink at social events; average 4.2 drinks per night out.

**Where it lives in the system:**
- `segment_behavioral_profiles.alcohol_pct` for college_kids is set to 65-75% (slightly discounted from 74.7% for India cultural context, where alcohol access for under-21s is more restricted and not all college social venues are licensed).
- `segment_behavioral_profiles.avg_drinks_on_night_out` for college_kids: 3.0–4.0 (discounted from 4.2 for India — lower purchasing power, stricter licensing in some venues).
- These values feed the RevPASH calculation for evening slots at college-skewing venues — the system estimates total alcohol revenue contribution using `avg_drinks × avg_price_per_drink × alcohol_pct`.

**Confidence:** LOW-MEDIUM. U.S. college data inferred to India — a significant stretch given cultural, legal, and economic differences. Explicitly flagged in `research_validation_flags` as INFERRED. The directional finding (college students drive disproportionate alcohol revenue on nights out) is credible for India's top-tier urban venues; exact percentages are hypotheses.

---

### 15.11 India Platform Data — Swiggy & Zomato

**Sources:** Swiggy Annual Trends 2024; Zomato Investor Relations FY24; NRAI IFSR 2024.

**Finding 1 (Swiggy):** Swiggy Dineout seated **23.7 million diners** in 2024. Premium dining bookings grew **+123.7% YoY**. Couples ("just the two of us") reservations: **2.35 million** in 2024. Group ordering grew **+841%**.

**Finding 2 (Zomato):** Zomato Going-out (dine-in) grew **+136% YoY** in FY24. Gen Z and Millennials (18-35) account for **65%+** of order volume.

**Finding 3 (NRAI):** India F&B market: **₹5.69 lakh crore** in FY24. Casual Dining: **48%** of format mix. QSR: **27%**. Top 9 cities = **60%** of total revenue.

**Where these live in the system:**

**1. `channel_benchmarks` table rows for Zomato and Swiggy.**
- `repeat_visit_lift_pct`: 25-60% (from Spice Advisors case data on featured placement uplift on Zomato/Swiggy)
- The 23.7M seated diners figure validates Swiggy Dineout as a primary acquisition channel — it is not optional for dine-in focused venues. This is why both Zomato and Swiggy appear in the `channel_benchmarks` table with MEDIUM-HIGH confidence ratings.

**2. Audience simulator baseline.**
The +841% group ordering growth feeds the default social_crowd segment weight in the audience simulator. Venues with strong `group_energy` signals are shown with elevated Social Crowd representation partly because platform data confirms group dining is growing faster than any other occasion type.

**3. Frontend marketing screen.**
The +123.7% premium dining growth is displayed in the marketing screen's market context panel to justify why premium segment investment is strategically sound right now.

**4. `segment_behavioral_profiles.wom_multiplier` for couples.**
The 2.35M couple reservations finding validates that the couples segment is a distinct, trackable behavioural unit — it is not just two office workers dining together. It reinforces why the system treats couples as a distinct segment (not merged into a generic "dine-in" category) and why the couple's `wom_multiplier` is set relatively high — couples planning a date night actively share their experience on Instagram and WhatsApp groups.

**Confidence:** HIGH for the platform-volume statistics (directly sourced from company reports). MEDIUM for the inferences drawn (e.g., that group ordering growth applies equally across all cities in MMR).

---

### 15.12 Meta / Instagram — Reels Engagement Data

**Source:** Meta published data on Instagram Reels vs. static posts, cited in `PHASE_1_INDIA_BEHAVIORAL_RESEARCH.md`.

**Finding:** Instagram Reels generate **6.5× higher engagement** than static image posts. (Note: External validation in `Indian_FB_Consumer_Segmentation_Validation_Report.md` disputes this — independent research found ~2.1× engagement difference, though Reels show 10-50× reach advantage over static.)

**Where it lives in the system:**
- `channel_benchmarks` table, row for `instagram_reels`:
  - `engagement_rate_multiplier`: 6.5 (stored as the Meta-published figure)
  - A `research_validation_flags` row flags this as DISPUTED — the external validation found ~2.1× engagement and recommends correcting to "2× engagement, 10-50× reach"
- The Marketing tab channel cards display Instagram Reels with a "High reach" badge rather than a specific engagement multiplier — this was changed specifically because of the dispute.
- `channel_segment_effectiveness` for college_kids + social_crowd via Instagram Reels: assigned the highest effectiveness score (0.85) because both segments skew heavily toward Instagram consumption, regardless of the exact engagement multiplier dispute.

**Confidence:** MEDIUM for the 6.5× figure (Meta-published, not independently replicated). The directional finding — Reels significantly outperform static for reach and engagement — is robust. The exact multiplier is under dispute and flagged.

---

### 15.13 Spice Advisors / Zomato Placement — Review Velocity

**Source:** Spice Advisors published case studies on Zomato/Swiggy algorithm behaviour (2025-2026).

**Finding:** Review velocity (recency of reviews) is a **high-weight factor** on Swiggy's ranking algorithm and a **moderate-weight factor** on Zomato's. Fresh photos, menu updates, and recent reviews signal an active restaurant. Stale listings lose placement.

**Where it lives in the system:**
- `channel_benchmarks` row for Zomato: `review_velocity_rank_weight` = HIGH
- `channel_benchmarks` row for Swiggy: `review_velocity_rank_weight` = HIGH
- This finding directly justifies the `RECENT_REVIEWS_DAYS = 365` constant in `step_3_extract.py` (`constants.py`). Reviews older than 365 days are given lower `confidence_decay` scores, which reduces their weight in Step 5 — consistent with the platform finding that review recency matters for commercial performance.
- The `confidence_decay` component in Step 5's formula (weight 0.06) is partly justified by this finding: a venue with only old reviews is both less temporally reliable (the decay formula) and less commercially discoverable (the platform algorithm). The decay component bridges the operational finding (platforms penalise stale content) with the scoring model.

**Confidence:** MEDIUM-HIGH for the directional finding (review velocity improves platform placement — well-documented across multiple sources). The exact weighting is the algorithm's internal logic and is not publicly disclosed.

---

### 15.14 Behavioral Mechanics Literature — FOMO r=0.86

**Source:** Applied hospitality research (aggregated in `behavioral_acquisition_mechanisms_hospitality.md`) measuring the correlation between urgency-framing and behavioural intent.

**Finding:** The correlation between FOMO-urgency messaging and purchase intent in hospitality contexts is approximately **r=0.86**.

**Where it lives in the system:**
- `behavioral_mechanisms.urgency_score` column for `fomo_scarcity` mechanism: set to **0.87** (direct translation of r=0.86 correlation to a 0–1 scale).
- `channel_segment_effectiveness` for WhatsApp + Social Crowd: WhatsApp is assigned the highest FOMO activation score because it delivers real-time, personal-channel urgency — the mechanism is activated by the combination of message intimacy (perceived as from a friend) and time-sensitivity.
- The WhatsApp message templates in `WhatsAppGenerator.tsx` prioritise scarcity language: limited availability, time-expiring offers, tonight-only messaging. These are the operational outputs of the r=0.86 finding.

**Confidence:** MEDIUM. The r=0.86 figure is from applied (vendor/practitioner) hospitality research, not a peer-reviewed study. The direction (FOMO → urgency → action) is robustly established in academic literature; the precise coefficient is practitioner-derived.

---

### 15.15 What Has No Peer-Reviewed Backing (HYPOTHESIS List)

The `research_validation_flags` table tracks these explicitly. The following values in the live system are working hypotheses, not validated findings:

| Value | Location in system | Why it's a hypothesis |
|---|---|---|
| WOM multipliers (1.0× to 4.5×) | `segment_behavioral_profiles.wom_multiplier_min/max` | No restaurant-specific viral coefficient studies exist |
| First-round anchoring | `archetype_spend_triggers` for party_seeker | General anchoring literature (Kahneman) doesn't specifically test this in social group ordering |
| Dwell ceilings by segment (75 min families, 150 min premium) | `segment_behavioral_profiles.diminishing_returns_minutes` | Upserve 45-min figure is for casual dining only; fine dining dwell ceiling is an inference |
| Dessert attachment rates by segment | `archetype_behavioral_profiles.dessert_attach_pct` | No comparative study; inferred from child-influence finding (Ghosh) for families, from habit formation for regulars |
| Solo diner bar-counter vs. table spend differential | `segment_behavioral_profiles` for solo_diners | No study measuring this specifically |
| Premium private vs. public WOM ratio | `segment_behavioral_profiles.wom_multiplier` for premium | No study measuring whether premium diners share experience publicly or privately |
| WhatsApp first-name personalization 25-35% repeat visit uplift | `channel_benchmarks` (present as a note) | Vendor-reported general WhatsApp engagement uplift — not attributable to first-name specifically |
| Archetype names (party_seeker, scene_seeker, trusted_regular, etc.) | `archetype_behavioral_profiles` primary keys | No published Indian research validates these specific archetype typologies |

---

### 15.16 Research Confidence Summary

| System Component | Primary Research Source | Confidence | What Would Improve It |
|---|---|---|---|
| Peer influence coefficients | Herhausen et al. (peer-reviewed) | HIGH direction; MEDIUM magnitude | India-specific restaurant cohort study |
| RevPASH economics | Upserve + RevPASH framework | MEDIUM | Actual POS data from partner venues |
| Dwell time ranges | Upserve (US casual dining) + India inference | MEDIUM | India-specific table turnover measurement |
| Segment profiles | Kimi synthesis + NRAI/Zomato/Swiggy | MEDIUM | India POS data by segment |
| Archetype profiles | Kimi synthesis + behavioral economics lit | LOW-MEDIUM | Primary India research; no published archetype typology exists |
| WOM multipliers | No peer-reviewed backing | LOW | NPS cohort tracking at venue level |
| Channel benchmarks | Vendor case studies (India-focused) | MEDIUM | Controlled A/B tests at venue level |
| Mechanism psychology | Cialdini, Kahneman, Loomes & Sugden | HIGH | Inherently robust — classical literature |
| Fitness dimension signals | Internal design + face validity | MEDIUM | Empirical validation against segment preference surveys |
| Platform discovery channels | Hiwalkar Mumbai study (n=40) | MEDIUM | Larger India urban sample |
| Instagram Reels multiplier | Meta-published + disputed externally | MEDIUM — DISPUTED | Independent India F&B creative study |
| Review velocity / platform placement | Spice Advisors case data | MEDIUM-HIGH | Direct A/B test of listing freshness vs. placement |

---

### 15.17 How to Read the `research_validation_flags` Table

The database table `research_validation_flags` is a live registry of known-incorrect or unvalidated claims in the running system. When a claim is found to be wrong or updated by actual data, a row is inserted:

```sql
INSERT INTO research_validation_flags 
  (entity_type, entity_key, field_name, claimed_value, validated_value, 
   validation_source, is_corrected, correction_notes)
VALUES 
  ('segment', 'college_kids', 'wom_multiplier_min', '3.5', NULL, 
   'archetype_segment_validation_kimi.md', false, 
   'WOM multiplier is a hypothesis — no peer-reviewed restaurant-specific viral coefficient exists');
```

As real venue POS data and campaign performance data accumulates (Layer 3), these flags get corrected and the system becomes empirically grounded rather than research-inferred. The table is designed to be updated continuously — it is not an admission of failure, it is the system's memory of what it knows versus what it assumes.

---

---

## 16. BIF Pipeline Upgrade Log — 2026-05-25

This section documents the upgrades applied to the Behavioural Intelligence Framework pipeline scripts (`D:\PolyNovea\Module 2\Google Raw Scrapper\Behavioural_Intelligence_Framework\scripts\`) based on analysis of real Google Reviews production data.

---

### 16.1 Root Cause Fix — FITNESS_SIGNAL_MAP Dead Signal IDs

**Problem:** `step_5_score.py` redefined `FITNESS_SIGNAL_MAP` locally, overriding the canonical import from `config/primitives_loader.py`. The local definition used signal IDs that had **zero occurrences** in actual google_reviews step_4 cluster data:

| Dead ID (old) | Canonical ID (fixed) | Occurrences in data |
|---|---|---|
| `quick_service` | `fast_service` | 521 (Navi Mumbai) |
| `authenticity_signal` | `authentic_taste` | 925 |
| `status_display` | removed; added `pride` | `pride` = 5,740 |
| `multi_round_ordering` | `group_spend_amplification` | 863 |
| *(missing)* | `food_quality` added | 8,404 |
| *(missing)* | `wonder_ambience` added | 644 |
| *(missing)* | `destination_driven_retention` added | detected |

**Result:** All-zero fitness venues dropped from **579 (52%) → 199 (18%)** after fix. google_reviews now outperforms google on destination_visit (0.066 vs 0.031) and repeat_habit (0.099 vs 0.054).

**Detection method:** After running BIF step_5, query `venue_fitness_dimensions WHERE source='google_reviews'`. If `all_zero > 40%`, the FITNESS_SIGNAL_MAP has dead signal IDs. Verify against actual step_4 cluster signal counts before running step_5.

---

### 16.2 Step 4 — Venue Primitives Injection

**Problem:** `extract_venue_evidence()` in `step_4_pattern.py` only read per-review `behavioral_intelligence`, completely ignoring the venue-level `behavioral_primitives` aggregate that step_3 computes. For venues with short/low-quality Google reviews (low effective_review_weight), the venue-level signal aggregation was entirely discarded.

**Fix:** Added `venue_primitives` parameter to `extract_venue_evidence()`. When venue-level `behavioral_primitives` is present, a synthetic `venue_aggregate` evidence entry is appended:
- Reads signals from all primitive categories (`stimuli`, `compensations`, `emotional_context`, `frictions`)
- Filters to confidence ≥ 0.25
- Deduplicates via `SIGNAL_ALIASES`
- Appended as a single `venue_aggregate` evidence entry with source tag `'venue_aggregate'`

**Effect:** Pattern clustering now uses the full aggregated signal picture per venue, not just per-review BI signals. Pattern count for google_reviews increased from 2,624 → 3,358 after this change.

---

### 16.3 Step 3 — Cross-Venue Duplicate Weighting

**Problem:** Coordinated promotional review campaigns (different reviewers posting near-identical phrasing) were not penalised — they inflated primitive confidence scores artificially.

**Fix:** Added `calculate_venue_duplicate_weight()` function using Jaccard word overlap (threshold 0.72):
```python
near_dups = sum(1 for t in prior_texts if _word_overlap_ratio(review_text, t) > 0.72)
weight = round(max(0.15, 1 / (1 + near_dups * 0.80)), 2)
```
`effective_review_weight` is now: `quality_score × independence_score × venue_duplicate_weight`

Reviews with ≥ 4 words are checked against all prior review texts at that venue. A highly duplicated review receives as low as 0.15× weight. Reviews with < 4 words are handled by `calculate_review_quality()` instead.

---

### 16.4 Step 3 — Event Anomaly Friction-Halving

**Problem:** Reviews written during one-off high-density events (New Year, IPL finals, sports screenings) report temporary operational stress — AC failures, crowd management breakdown, service collapse — that does not represent baseline venue quality. These were inflating friction scores and suppressing fitness dimensions like `repeat_habit` and `office_lunch`.

**Fix:** Added `EVENT_ANOMALY_PATTERNS` list (covers NYE variants, IPL, World Cup, sports screening, holiday nights). After `derive_behavioral_signals()`, for reviews that match any event pattern:
```python
if is_event_review:
    for item in behavioral.get('frictions', []):
        item['confidence'] = round(item['confidence'] * 0.5, 3)
```
Friction signals are halved but not removed — a single bad event night no longer tanks a venue's baseline score.

---

### 16.5 Step 3 + primitives.json — Hinglish & Slang Coverage

**Problem:** A significant proportion of Thane and Navi Mumbai reviews are written in Hinglish, transliterated Hindi, or mixed-language slang. English-only trigger patterns missed these signals entirely.

**Added to inline keyword dicts in `step_3_extract.py`:**

| Dict | Signal | New terms added |
|------|--------|----------------|
| `FRICTION_KEYWORDS` | `noise_overload` | bahut loud, shor zyada, itna shor, bahut shor |
| `FRICTION_KEYWORDS` | `premium_price` | bahut mehenga, kitna mehenga, mehenga hai, jeb pe bhaari |
| `FRICTION_KEYWORDS` | `service_failure` | bakwas service, service bilkul nahi, koi dhyan nahi, staff ka attitude |
| `COMPENSATION_KEYWORDS` | `authentic_taste` | desi style, ghar ka swad, ghar jaisa, bilkul ghar jaisa, desi flavour, homely taste |
| `BEHAVIORAL_RESPONSE_KEYWORDS` | `extended_stay` | hookah ke time mein, gaye hi nahi, closing tak rehe, raat bhar baithe |
| `BEHAVIORAL_RESPONSE_KEYWORDS` | `repeat_visit_intent` | baar baar aata, regular ho gaya, ab toh har baar, jaata rehta hoon |
| `COMMERCIAL_MECHANISM_KEYWORDS` | `social_dwell_amplification` | ek aur round, dusra hookah, another round of hookah, one more hookah |

**Added to `config/primitives.json` trigger_patterns:**

| Primitive | New terms added |
|-----------|----------------|
| `social_energy` | mast jagah, mast place, mazedaar, zabardast, bindaas place, vibe was insane, crazy vibe, banging vibe |
| `long_dwell` | hookah, sheesha, hukkah, chill spot, hangout spot, good for chilling |
| `wonder_ambience` | so aesthetic, gram worthy, photogenic, looks amazing, sundar jagah |
| `nostalgia` | desi feel, ghar jaisa, bilkul ghar jaisa, desi vibes |
| `food_quality` | bahut tasty, mast khana, zabardast khana, ekdum mast, badhiya khana, yummy, sahi taste |

---

### 16.6 How to Re-run the Pipeline After BIF Changes

When BIF script changes affect step_3 (keyword changes / primitives.json):
```
# Full re-run required (step_3 output changes)
python run_pipeline.py --city thane
python run_pipeline.py --city navi-mumbai
```

When BIF changes only affect step_4 or later (no step_3 keyword changes):
```
# Partial re-run from step_4
python run_pipeline.py --city thane
python run_pipeline.py --city navi-mumbai
```

`run_pipeline.py` runs steps 4 → 4b → 5 → 5b → 6 in sequence per city. Then run DB loaders:
```
cd Database/scripts/pipeline/google_reviews
# Clear behavioral_patterns (INSERT has no ON CONFLICT):
python -c "DELETE FROM pattern_scores WHERE source='google_reviews'; ..."
python step3_primitives.py
python step4_cluster_and_patterns.py
python step4b_governance.py
python step4b_pattern_scores.py
python step5b_similarity_loader.py
python step6_fitness_and_interventions.py
cd ../..
python blend/blend_fitness.py
```

All loaders except `step4_cluster_and_patterns.py` (behavioral_patterns INSERT) use `ON CONFLICT DO UPDATE` and are safe to re-run without manual cleanup. `behavioral_patterns` must be deleted first to avoid duplicate rows.

---

---

## 17. Research Extraction Pipeline — 2026-05-27

This section documents the research extraction pipeline added in v5.0. It is **additive** — the existing system (hardcoded dicts in `marketing.py`, raw file dumps in `prompts.py`) is unchanged.

---

### 17.1 Purpose

The existing AI chat system loads all 19 research `.md` files as raw text into every chat prompt (~50–80k tokens). This has three problems:

1. **Frozen research** — if a research file changes, nothing in `marketing.py` changes automatically
2. **No structure** — the AI must re-extract key claims from prose on every request
3. **No audit trail** — impossible to trace which specific claim backs a given recommendation

The pipeline solves all three by extracting structured, reusable outputs once per research file.

---

### 17.2 Location and Structure

```
research_pipeline/
├── extract.py              ← single entry point
├── config.py               ← canonical segments, channels, archetypes
├── llm_client.py           ← NVIDIA API wrapper + robust JSON parser
├── extractors/
│   ├── claims.py           ← segment×channel claim extraction
│   ├── archetypes.py       ← archetype brief extraction
│   └── contradictions.py   ← cross-file conflict detection
├── requirements.txt        ← openai, python-dotenv
└── output/                 ← auto-created on first run
    ├── claims.json          ← 93 structured segment×channel claims
    ├── archetypes.json      ← 11 archetype marketing briefs
    ├── contradictions.json  ← cross-file conflicts (0 found — research is consistent)
    ├── rag_chunks.jsonl     ← 104 flat chunks for future vector retrieval
    └── run_summary.json     ← run metadata
```

---

### 17.3 How to Run

```bash
cd research_pipeline

# Full run (uses cache for unchanged files — only re-extracts new/modified files)
python extract.py

# Skip contradiction detection (faster)
python extract.py --skip-contradictions

# Ignore cache, re-extract everything
python extract.py --force
```

**NVIDIA key:** Auto-loaded from `App/backend/.env`. No additional setup needed.

**Caching:** Each research file is MD5-hashed. Unchanged files load from per-file cache files (`.claims_<stem>.json`, `.archetypes_<stem>.json`) — zero API calls. Only new or modified files are re-extracted.

**Rate limiting:** 1.5s delay between sections, 2s between files, exponential retry backoff (5s → 10s → 20s) on 429 errors.

---

### 17.4 Output Formats

**`claims.json`** — Array of structured claims:
```json
{
  "segment": "office_workers",
  "channel": "whatsapp",
  "claim": "Send lunch broadcasts between 11:30 AM and 12:30 PM — pre-lunch decision window with highest open rates",
  "confidence": 0.90,
  "india_verdict": "CONFIRMED",
  "why_it_works": "Time scarcity drives habitual decision-making; WhatsApp 98% open rate beats all other channels",
  "dont": ["Never send before 9 AM or after 9 PM"],
  "source_file": "marketing_channel_strategy_research.md",
  "extracted_at": "2026-05-27T..."
}
```

**`archetypes.json`** — Object keyed by archetype, merged from all files:
```json
{
  "comfort_dweller": {
    "tone": "Safety, no surprises — familiar environment is the draw",
    "emotional_driver": "environmental_expectation + habit_formation",
    "hook_formula": "Environment confidence + consistency. Never urgency.",
    "india_verdict": "CONFIRMED",
    "india_adjustment": "Post-pandemic 61% prefer familiar environments; safety essential for women",
    "dont": ["Never FOMO or urgency language", "Avoid crowd/noise visuals"],
    "trust_first": true,
    "source_files": ["india_fb_ad_brief_generator_research.md", ...]
  }
}
```

**`rag_chunks.jsonl`** — One chunk per line, ready for vector retrieval:
```json
{"chunk_id": "claim_office_workers_whatsapp_0", "type": "claim", "segment": "office_workers", "channel": "whatsapp", "text": "Marketing claim for office_workers on whatsapp: ...", "confidence": 0.90, ...}
```

**`contradictions.json`** — Array of conflicts (currently empty — research is internally consistent):
```json
{
  "segment": "premium",
  "channel": "zomato_swiggy",
  "claims": [...],
  "conflict_type": "effectiveness_disagreement",
  "summary": "...",
  "resolution": null  // human fills this in
}
```

---

### 17.5 First Run Results (2026-05-27)

| Metric | Value |
|---|---|
| Research files processed | 19 |
| Model used | `meta/llama-3.3-70b-instruct` |
| Claims extracted | **93** |
| Archetypes extracted | **11** (full set) |
| Contradictions found | **0** (research is consistent) |
| RAG chunks | **104** |

---

### 17.6 Integration with AI System Prompt

The pipeline outputs are loaded into `App/backend/prompts.py` at startup and injected into every chat prompt as a **structured claims index** — a compact lookup layer that sits between the venue data and the raw research prose.

**Prompt structure (in order):**
```
1. Identity guardrail (rules 1–5)
2. Venue live data (segments, fitness, channels, patterns, etc.)
3. ─── NEW ─── Structured claims index (93 claims, ~48 lines)
4. ─── NEW ─── Archetype quick reference (11 archetypes, ~56 lines)
5. Raw research prose (all 15 files, unchanged)
6. HOW TO RESPOND rules
```

**Claims index format:**
```
[OFFICE WORKERS]
  whatsapp     [H][C] Send 11:30–12:30 PM pre-lunch window. Avoid: before 9 AM.
  instagram    [M][C] Discovery during commute but conversion is habit-driven.
```
`H/M/L` = confidence tier | `C/A/U` = India verdict (CONFIRMED / ADJUST / UNCONFIRMED)

**Why this ordering:** The AI reads top-to-bottom. Structured claims anchor the answer before the AI hits raw prose, reducing hallucination drift and improving retrieval accuracy.

**Fallback:** If `research_pipeline/output/` does not exist, the indexes return empty string — no breaking change, existing system works unchanged.

**Reload:** The backend must be restarted to reload updated indexes (they are built once at import time).

---

### 17.7 Workflow for Adding New Research

1. Add new `.md` file to `research/`
2. Run `python extract.py` from `research_pipeline/` (only the new file is re-extracted; cached files skip)
3. Restart the EC2 backend to reload the updated indexes into memory: `sudo systemctl restart polynovea`

---

### 17.8 Future: RAG-Based Chat Retrieval

The current integration injects all 93 claims + 11 archetypes as a static block. A future improvement is to use `rag_chunks.jsonl` for retrieval — embedding the user's question and fetching only the 5–10 most relevant chunks. This would:

- Replace the raw file dump in `prompts.py` (~50–80k tokens) with ~2–3k tokens of targeted context
- Dramatically reduce prompt size and cost
- Improve specificity of AI answers

This is not yet implemented. The static index is the first step — it improves accuracy without requiring an embedding store.

---

*End of documentation. Last updated: 2026-05-27 (v5.0).*
