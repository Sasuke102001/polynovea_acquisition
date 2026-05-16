# Polynovea Module 2 & 3: Complete Framework

**Version:** 1.0  
**Date:** 2026-05-14  
**Status:** Ready for Database Implementation  

---

## 🎯 Executive Summary

We built a **behavioral intelligence system** that:
1. **Module 2**: Understands what customers expect vs. what venues deliver (gap analysis)
2. **Module 3**: Engineers the experience to close that gap (show design)
3. **Geocluster**: Learns from each venue to make the next one faster

**This is not analytics. This is experience engineering grounded in behavioral science.**

---

## 📊 Module 2: Understanding the Gap

### What Module 2 Does

Identifies the gap between:
- **Expectations** (what people say they want)
- **Reality** (what venues currently deliver)
- **Output**: Targeted marketing + intervention blueprint

### Module 2 Data Sources

#### 1. Survey Data (Expectations - "Woulds")
- **45 responses** normalized to canonical schema
- **35 computed archetypes**:
  - Party Seeker (wants: social_energy, social_sharing, excitement)
  - Calm Pairs (wants: comfort, intimate, slow dining)
  - Discovery Explorer (wants: authenticity, new experiences)
  - etc.
- **What they SAY they value** (intentions, not yet proven)

#### 2. Review Data (Reality - "Actuals")
- **54 behavioral primitives** extracted from reviews
- **898 venues analyzed** in Phase 1 (Navi Mumbai, SOBO, Main Mumbai, Thane)
- **5,558 behavioral patterns** recognized
- **What customers HAVE experienced** (proven behavior)

### Module 2 Analysis

**Gap Identification Example:**

```
EXPECTATIONS (Surveys)
├─ Party Seeker archetype wants:
│  ├─ social_energy (people interacting)
│  ├─ social_sharing (Instagram-worthy moments)
│  ├─ excitement (music, energy, vibe)
│  └─ multi_round_ordering (stay longer, order more)

REALITY (Reviews)
├─ Banana Leaf Airoli has:
│  ├─ ✓ food_quality
│  ├─ ✓ social_energy (partial)
│  ├─ ✗ live_music (GAP)
│  ├─ ✗ extended_stay infrastructure (GAP)
│  └─ ✗ excitement signals (GAP)

GAP = Customers WANT [music + extended stay] 
      Venue LACKS [music + extended stay]
```

### Module 2 Output: 4 Artifacts

#### 1. **step_5_behavioral_scores.json**
- Per-venue detailed scores
- 5 fitness dimensions (office_lunch, repeat_habit, social_dwell, group_energy, destination_visit)
- Intervention opportunities categorized by tier
- Behavioral summary (operational_quality, retention_strength, monetization_potential)

#### 2. **step_5_patterns_scored.json**
- Market-level patterns with confidence (50-57%)
- Prevalence across venues (1%-3%)
- Which venues exemplify each pattern

#### 3. **step_5b_similarity.json**
- Top 25 similar venues per venue
- Shared primitives (what they have in common)
- Pre-computed for instant lookup (Feature 1: Similar Venues Comparison)

#### 4. **step_4b_governance_report.json**
- Data quality metrics:
  - 74% reliability score
  - 91% high-reliability clusters
  - No governance flags
- Drift signals (emerging new patterns)

### Module 2 Data Quality

| Metric | Value | Meaning |
|--------|-------|---------|
| Total Venues | 898 | Phase 1 coverage |
| Total Patterns | 5,558 | Combinations recognized |
| High Reliability | 91% | Good quality data |
| Avg Confidence | 0.66 | 66% average confidence |
| Avg Reliability | 0.79 | 79% pattern stability |
| Overall Score | 0.743 | 74% data quality |

**Assessment**: Solid for emerging market. Good enough for MVP. Not perfect, but real.

### Module 2 Output: Targeted Marketing

**What We Market** (NOT the gap):
```
Use EXISTING good signals + EXPECTED benefits:

"Experience [what venue has + what customer expects]"

Example:
├─ "Great food" (venue HAS this - from reviews)
├─ "Social atmosphere" (venue HAS this - from reviews)
├─ "+ Memorable nights out" (Party Seeker expects this)
└─ → Market this combination NOW

Module 3 will ADD music/extended_stay later
Then you can re-market: "Now with live music!"
```

**Why this works**: Customer arrives with correct expectations. Module 3 exceeds expectations. Win.

---

## 🎬 Module 3: Engineering the Show

### What Module 3 Does

**Deliberately engineers the customer experience to close gaps identified in Module 2.**

Uses:
- Module 2 data (what gaps exist)
- Music psychology (how to trigger desired states)
- Behavioral psychology (where to place triggers)
- Neurological psychology (when neural systems activate)
- Real-time measurement (before/after proof)

### Module 3 Timeline

#### **Days 1-5: Baseline Measurement**

**Measure current state** (no changes yet):
```
POS Data:
├─ Average orders per customer
├─ Order timing patterns
├─ Revenue per 5-day period
└─ Order combinations

Behavioral Observations:
├─ Dwell time per customer
├─ Repeat visits (same-day)
├─ Group vs. individual customers
├─ Staff interaction patterns
└─ Customer energy/mood

Environment:
├─ Current music (if any)
├─ Space utilization
├─ Queue management
└─ Customer flow patterns
```

**Geocluster Calibration** (compare to similar venues):
```
First venue:     No cluster yet
Second venue:    Compare to venue 1
Third+ venue:    Compare to average of previous venues
20+ venues:      Very confident baseline predictions
```

#### **Days 6-10: Intervention (The Show)**

**Engineer based on Module 2 gaps + psychology:**

##### Example: Party Seeker Gap Closure

```
MODULE 2 IDENTIFIED GAP:
├─ Party Seeker wants: social_energy, social_sharing, music, extended_stay
└─ Venue lacks: live_music, seating for groups, multi-drink prompting

INTERVENTION DESIGNED:

Music Psychology
├─ Add: 120-130 BPM upbeat playlist
├─ Why: Increases heart rate + dopamine + desire to stay
├─ When: Peak hours (6-10pm)
└─ How: Background + 2x live music nights/week

Behavioral Psychology
├─ Seating: Rearrange for group tables (4-8 people)
├─ Why: Encourages friends to sit together + social contagion
├─ Visibility: Make bar prominent
└─ Trigger: "Second drink special" messaging at 20min mark

Neurological Psychology
├─ Staff warmth: Train for genuine interest (oxytocin)
├─ Social proof: Seat groups near window (visible to street)
└─ Memory formation: Photo op with branded background

Operations
├─ Pre-order system (reduce queue friction)
├─ Multi-drink bundling (lower price perception)
└─ Follow-up (text/email: "See you next week!")
```

#### **Days 11-15: Measure Results**

**Compare to baseline:**
```
BEFORE (Days 1-5)        vs.    AFTER (Days 11-15)
─────────────────────────────────────────────────
1.4 orders/customer      →      1.8 orders (+28%)
18 min dwell time        →      32 min dwell (+78%)
12% repeat visits        →      31% repeat visits (+158%)
$8,400 revenue           →      $13,200 revenue (+57%)
0 multi-round orders     →      35% multi-round orders
```

**Validation Questions**:
- Did dwell_time increase as predicted by fitness_for_social_dwell?
- Did multi_round_ordering signal activate as expected?
- Did Party Seeker archetypes show up (survey validation)?
- Did staff warmth improve (neuro psychology working)?

---

## 🔄 The Flywheel: How It Scales

### Single Venue Cycle

```
Module 2 (Analyze)
├─ Identify gaps
├─ Target marketing
└─ → Customer arrives with correct expectations

Module 3 (Engineer)
├─ Day 1-5: Baseline
├─ Day 6-10: Intervention
├─ Day 11-15: Measure
└─ → Prove the gap was closed

Add to Geocluster
├─ Store baseline patterns
├─ Store intervention results
├─ Store archetype response
└─ → Next venue is faster
```

### Multi-Venue Network

```
Venue 1: Baseline data → Geocluster (empty)
Venue 2: Baseline + Geocluster (1 venue) → Richer prediction
Venue 3: Baseline + Geocluster (2 venues) → More confident
...
Venue 10: Baseline + Geocluster (9 venues) → Very confident
Venue 20: Baseline + Geocluster (19 venues) → Playbooks proven

By Venue 20:
├─ "Navi Mumbai casual dining baseline" = predictable
├─ "SOBO fine dining playbook" = proven
├─ "Repeat customers archetype response" = known
└─ → Next venue: plug and play
```

### Scaling Timeline

| Stage | Venues | Geocluster Status | Data Quality | Speed |
|-------|--------|-------------------|--------------|-------|
| Phase 1 | 1-5 | Building | Sparse + Cluster | Slow |
| Phase 2 | 6-15 | Navi Mumbai + SOBO | Richer + Cluster | Medium |
| Phase 3 | 16-30 | All Phase 1 cities | Rich + Cluster | Fast |
| Phase 4 | 31+ | Multi-city playbooks | Very Rich | Very Fast |

---

## 🎯 Key Concepts Recap

### Tier System (No Filtering, All Categorized)

#### Intervention Opportunities
```
HIGH (0.75+):        Urgent optimization needed
├─ Has all required signals at high confidence
├─ Example: repeat_visits + long_queue = "optimize throughput"
└─ Action: Implement immediately

MEDIUM (0.45-0.74):  Ready for consulting
├─ Has most required signals at good confidence
├─ Example: long_dwell + some ordering = "add multi-round strategy"
└─ Action: Recommended

CANDIDATE (0.25-0.44): High-potential client
├─ Has foundation signals, missing 1-2
├─ Example: repeat_visits but no queue = "build loyalty, then scale"
└─ Action: Perfect for consulting, needs activation

EXPLORE (<0.25):     Early stage, monitor
├─ Has minimal signals
├─ Example: just food_quality = "everything else is possible"
└─ Action: Watch for emergence
```

#### Fitness Dimensions
```
STRONG (0.75+):      Venue strongly fits this use case
MODERATE (0.50-0.74): Venue partially fits
EMERGING (0.25-0.49): Some signals present
NASCENT (<0.25):     Minimal signals, needs development
```

### 54 Behavioral Primitives

**What they are**: Signals extracted from review text that indicate customer behavior

**Examples**:
- food_quality (taste, freshness, authenticity)
- social_energy (people interacting, vibe, excitement)
- long_dwell (customers staying long)
- repeat_visits (customers returning regularly)
- pride (status, premium feeling)
- social_sharing (Instagram-worthy, tagging friends)
- staff_warmth (attentive, friendly, caring)
- quick_service (fast ordering/delivery)

**How they combine**: Co-occurring primitives create patterns
- food_quality + social_energy + pride = "Premium Social Dining"
- repeat_visits + long_queue = "Operational optimization opportunity"

### 35 User Archetypes

**What they are**: Customer types extracted from survey responses

**Examples**:
- Party Seeker (social, excited, wants to share)
- Calm Pairs (intimate, quiet, relaxed)
- Discovery Explorer (authentic, new experiences, curious)
- Premium Prioritizer (status, quality, willing to spend)
- Repeat Regular (convenience, familiar, predictable)

**How they're used**: 
- Match venue patterns to archetype preferences
- Predict which customers will respond to intervention
- Validate Module 2 patterns

### Demographic-Archetype Bridge (NEW)

**What it is**: A translation layer that connects how venue owners think (demographics) with how Module 2 thinks (behavioral archetypes)

**Why it matters**:
- Venue owners say: "I want college kids" (demographic)
- Module 2 shows: "That's 70% Party Seekers + 20% Discovery Explorers" (archetype breakdown)
- Sales team can pitch in language venue owners understand
- App shows both perspectives to bridge the gap

**How it works**:

From survey data, we segment by demographics:
```
College Kids (22-25, 2-4 people, weekends)
├─ Party Seeker: 70%
├─ Discovery Explorer: 20%
└─ Repeat Regular: 10%

Office Workers (26-35, lunch hours)
├─ Repeat Regular: 60%
├─ Premium Prioritizer: 30%
└─ Calm Pairs: 10%

Families (all ages, 2-6 people, weekends)
├─ Calm Pairs: 50%
├─ Discovery Explorer: 40%
└─ Premium Prioritizer: 10%
```

Each demographic-archetype pair gets:
- Expected ROI (1.57x revenue for Party Seekers)
- Specific interventions (music, seating, multi-round ordering)
- Critical primitives to focus on (social_energy, excitement, social_sharing)
- Expected behavior changes (dwell time, repeat visits, order value)

**For venue pitch**:
- Client: "I want to attract more young professionals on weekends"
- You show: "That means primarily Party Seekers (these interventions) + some Explorers (these different tactics)"
- Everyone understands the demographic, understands the intervention strategy

### Intervention Types

**4 Core Interventions** (expanded to 6 in Module 3):

```
1. Operational Optimization
   ├─ Triggers: repeat_visits + long_queue
   ├─ Gap: Queue friction despite loyalty
   └─ Action: Speed, pre-order, parallel service

2. Premium Justification
   ├─ Triggers: premium_pricing + great_view
   ├─ Gap: Price is high but experience doesn't match
   └─ Action: Reinforce view, elevate experience

3. Dwell Monetization
   ├─ Triggers: long_dwell + multi_round_ordering
   ├─ Gap: People stay but don't order more
   └─ Action: Music, secondary drinks, events

4. Friction Reduction
   ├─ Triggers: repeat_visits + slow_service
   ├─ Gap: Loyal customers tolerate bad service
   └─ Action: Staff training, speed improvements

5. Authenticity Leverage (Module 3 addition)
   ├─ Triggers: authentic_taste + long_queue
   └─ Action: Scarcity positioning, brand storytelling

6. Social Amplification (Module 3 addition)
   ├─ Triggers: social_sharing + wonder_ambience
   └─ Action: Visual design, photo ops, brand moments
```

---

## 📈 Database Output Summary

### What's Ready to Load

| File | Purpose | Records |
|------|---------|---------|
| step_5_behavioral_scores.json | Per-venue intelligence | 898 venues |
| step_5b_similarity.json | Venue similarity pool | 898 × 25 similar |
| step_5_patterns_scored.json | Market patterns | ~200 patterns |
| step_4b_governance_report.json | Data quality | Quality metrics |
| survey_responses_normalized.csv | Customer data | 45 responses |

### What Gets Built Next

```
PostgreSQL Tables:
├─ venues (metadata, area, type)
├─ primitives_scores (54 dimensions per venue)
├─ fitness_dimensions (5 use-cases per venue)
├─ behavioral_patterns (co-occurring primitives)
├─ pattern_scores (confidence, prevalence)
├─ intervention_triggers (opportunities per venue)
├─ venue_similarity (similarity pool)
├─ data_quality_metrics (governance data)
├─ user_archetypes (35 types from surveys)
├─ demographic_segments (college_kids, office_workers, families, etc.)
├─ demographic_archetype_mapping (70% Party Seeker for college_kids, etc.)
├─ demographic_archetype_interventions (specific tactics per demographic-archetype pair)
└─ demographic_behavioral_alignment (which primitives matter for each segment)

Application Features (16 total):
├─ 1. Similar Venues Comparison
├─ 2. Consulting Redirect
├─ 3-12. Core Intelligence (recommendations, churn, archetype, etc.)
└─ 13-16. Foundation for Ads (content, real-time, simulation, trends)
```

---

## ✅ Validation & Confidence

### What's Proven
- ✅ 54 primitives extracted reliably from reviews
- ✅ 35 archetypes computed from survey data
- ✅ 898 venues analyzed with 74% data quality
- ✅ Patterns make sense (food_quality + social_energy appears together)
- ✅ No filtering = no false negatives (everything visible)

### What's NOT Yet Proven (Will Be in Module 3)
- ❓ Do primitives predict actual customer behavior?
- ❓ Do interventions actually move the needle?
- ❓ Which archetypes respond to which interventions?
- ❓ What's the ROI per intervention type?

**This is why Module 3 exists: to validate in real venues with real customers.**

---

## 🚀 Next Steps (In Order)

### Immediate
1. ✅ Module 2 complete (all analysis done)
2. ⏳ Build PostgreSQL database from Module 2 outputs
3. ⏳ Create baseline application features (1-2)

### Short Term (2-4 weeks)
4. ⏳ Module 3 with first 3-5 client venues
5. ⏳ Measure baseline + intervention results
6. ⏳ Validate primitives against real behavior

### Medium Term (1-2 months)
7. ⏳ Build geocluster from first cohort
8. ⏳ Prove ROI per intervention type
9. ⏳ Create playbooks per venue category

### Long Term (3+ months)
10. ⏳ Scale to 20+ venues (network effects kick in)
11. ⏳ Add Zomata + MagicPin data (Phase 2)
12. ⏳ Build all 35 features

---

## 📞 Key Numbers to Remember

- **898 venues** analyzed in Phase 1
- **54 primitives** total behavioral signals
- **35 archetypes** from survey data
- **5,558 patterns** recognized
- **25 similar venues** per venue (pre-computed)
- **74% reliability** in data quality
- **50-57% confidence** in pattern scoring
- **4 intervention types** core + 2 expanded = 6 total
- **5 days baseline** + 5 days intervention = 10 days per venue
- **~57% revenue increase** expected from successful interventions (example)

---

## 🎯 Remember: Why This Works

**Not because it's perfect. Because it's:**
1. **Real** - Based on actual reviews + actual surveys
2. **Transparent** - Everything is visible (no filtering)
3. **Measurable** - Before/after proof in Module 3
4. **Psychological** - Grounded in music, behavioral, neuro science
5. **Scalable** - Each venue makes next venue faster (geocluster)
6. **Learning** - Improves with every client

---

## 📝 Quick Reference

**When you forget the framework:**

```
Module 2 answers: "What gap exists between expectations and reality?"
└─ Data: Surveys (what people want) + Reviews (what venues deliver)
└─ Output: Gap analysis + targeted marketing blueprint

Module 3 answers: "How do we close that gap?"
└─ Method: Baseline (5 days) + Intervention (music + psychology) + Measure (5 days)
└─ Proof: Before/after revenue, dwell time, order patterns
└─ Learning: Each venue improves the geocluster for next venue
```

---

**Version Control:**
- v1.0 - Complete framework documented (2026-05-14)
- Last Updated: 2026-05-14
- Next Review: After first 3 Module 3 client venues complete

---

*This framework is your reference guide. Bookmark it. Refer back to it. It won't change much, but it will get richer with each venue you execute.*
