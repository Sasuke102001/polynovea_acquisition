# Layer 2 Strategy + Comprehensive Feature Roadmap
## Beyond Venue Comparison: The Full Behavioral Intelligence System

**Date:** 2026-05-14  
**Data:** 37 survey responses (Form v2) + 10 responses (Form v1)  
**Scope:** Normalization, data ingestion, feature roadmap

---

## PART 1: Survey Data Audit

### Current State

**Form v1 (Simple)** — 10 responses
- Basic demographics (age, city, frequency)
- Binary/single-select preferences
- Simple text responses

**Form v2 (Detailed)** — 37 responses  
- Rich demographics (age, city, frequency, timing, duration, social composition)
- Multi-select dropdowns (up to 10 selections per question)
- Rating scales (1-5)
- Checkbox arrays (music preferences, frustrations)
- Free-text responses

**Problem:** Two different schemas. Future forms will likely change again.

---

## PART 2: Survey Normalization Strategy

### The Normalization Problem

Current forms have:
- Different column names ("age_group" vs "Age Group")
- Different scales (free text vs checkboxes vs ratings)
- Different granularity (Form v1 asks "when", Form v2 asks "when" + "duration")
- Missing values handled differently

### Solution: Canonical Survey Schema

Create a **version-agnostic canonical schema** that:
1. Maps any form version to a standard structure
2. Allows future form changes without breaking data
3. Enables cross-version analysis

**Implementation:**

```json
{
  "canonical_survey_schema": {
    "schema_version": "2.0",
    "released_date": "2026-05-14",
    
    "respondent_demographics": {
      "age_group": {
        "canonical_field": "age_bracket",
        "data_type": "categorical",
        "possible_values": ["18-21", "22-25", "26-30", "30+"],
        "form_v1_mapping": "age_group",
        "form_v2_mapping": "Age Group"
      },
      
      "city_or_area": {
        "canonical_field": "location",
        "data_type": "string",
        "form_v1_mapping": "city",
        "form_v2_mapping": "City / Area"
      },
      
      "visit_frequency": {
        "canonical_field": "monthly_visits",
        "data_type": "categorical",
        "possible_values": ["1-2", "3-5", "6+"],
        "form_v1_mapping": "frequency",
        "form_v2_mapping": "How often do you go out in a month?"
      },
      
      "typical_duration": {
        "canonical_field": "stay_duration_minutes",
        "data_type": "categorical",
        "possible_values": [60, 120, 180, 240],  // 1h, 2h, 3h, 4h+
        "form_v1_mapping": "duration",
        "form_v2_mapping": "Typical time you stay when you go out"
      },
      
      "social_composition": {
        "canonical_field": "group_type",
        "data_type": "categorical",
        "possible_values": ["alone", "partner", "small_group_2-4", "large_group_5+", "work_team"],
        "form_v1_mapping": "company",
        "form_v2_mapping": "Who do you usually go with?"
      }
    },
    
    "visit_behavior": {
      "visit_timing": {
        "canonical_field": "preferred_timing",
        "data_type": "categorical",
        "possible_values": ["weekdays", "weekends", "both"],
        "form_v1_mapping": "when",
        "form_v2_mapping": "When do you usually go out?"
      },
      
      "primary_purpose": {
        "canonical_field": "visit_intent",
        "data_type": "categorical",
        "possible_values": ["food_drink", "entertainment", "work_chill", "socializing", "celebration"],
        "form_v1_mapping": "reason",
        "form_v2_mapping": "Primary purpose when you go out"
      },
      
      "typical_spend": {
        "canonical_field": "spend_range_rupees",
        "data_type": "categorical",
        "possible_values": ["0-1000", "1000-3000", "3000-5000", "5000+"],
        "form_v1_mapping": "spend",
        "form_v2_mapping": "Typical total spend per outing"
      }
    },
    
    "preference_signals": {
      "spend_drivers": {
        "canonical_field": "what_makes_spend_more",
        "data_type": "array[categorical]",
        "max_selections": 3,
        "possible_values": [
          "music_entertainment", "comfort_environment", "people_company",
          "quality_experience", "food_quality", "service", "offers_pricing",
          "time_spent", "mood_of_place"
        ],
        "form_v1_mapping": "spend_more",
        "form_v2_mapping": "What makes you spend more?"
      },
      
      "venue_selection_criteria": {
        "canonical_field": "decision_factors",
        "data_type": "array[categorical]",
        "max_selections": 5,
        "possible_values": [
          "quality_experience", "ambience_environment", "music_entertainment",
          "crowd_people", "pricing", "location", "convenience", "reviews_recommendations",
          "familiarity", "offers_deals", "service"
        ],
        "form_v1_mapping": "choose_place",
        "form_v2_mapping": "What makes you choose a place?"
      },
      
      "importance_ratings": {
        "canonical_field": "importance_scale",
        "data_type": "object[string -> int(1-5)]",
        "dimensions": [
          "quality_experience", "comfort_environment", "service",
          "pricing_fairness", "crowd_people", "music_entertainment",
          "convenience", "safety_ease"
        ],
        "form_v2_mapping": "Rate how important these are when you choose where to go?"
      },
      
      "music_preferences": {
        "canonical_field": "music_importance",
        "data_type": "object[string -> boolean]",
        "dimensions": [
          "volume_control", "familiar_songs", "energy_level",
          "live_performance", "background_vibe", "conversation_comfort", "crowd_mood"
        ],
        "form_v2_mapping": "When music is part of the experience, what matters most to you?"
      }
    },
    
    "archetype_signals": {
      "energy_preference": {
        "canonical_field": "energy_preference",
        "data_type": "categorical",
        "possible_values": ["high_energy_exciting", "balanced", "calm_comfortable"],
        "form_v1_mapping": "energy_pref",
        "form_v2_mapping": "Which feels more like you?"
      },
      
      "decision_confidence": {
        "canonical_field": "review_dependence",
        "data_type": "categorical",
        "possible_values": ["very_little", "somewhat", "a_lot"],
        "form_v2_mapping": "How much do reviews / recommendations affect your decision?"
      },
      
      "crowd_sensitivity": {
        "canonical_field": "crowd_impact",
        "data_type": "categorical",
        "possible_values": ["very_little", "somewhat", "a_lot"],
        "form_v1_mapping": "crowd_impact",
        "form_v2_mapping": "How much does the crowd at a place affect your decision?"
      }
    },
    
    "open_text_signals": {
      "frustrations": {
        "canonical_field": "visit_frustrations",
        "data_type": "text",
        "form_v1_mapping": "frustrations",
        "form_v2_mapping": "What frustrates you the most when you're out?"
      },
      
      "avoidance_triggers": {
        "canonical_field": "avoidance_reasons",
        "data_type": "text",
        "form_v1_mapping": null,
        "form_v2_mapping": "What makes you avoid a place even if it looks good online?"
      },
      
      "favorite_venues": {
        "canonical_field": "regular_venues",
        "data_type": "array[text]",
        "form_v2_mapping": "Name 3-4 places you go to often"
      },
      
      "retention_factors": {
        "canonical_field": "stay_longer_triggers",
        "data_type": "text",
        "form_v1_mapping": "leave_or_stay",
        "form_v2_mapping": "What makes you stay longer?"
      },
      
      "recommendation_drivers": {
        "canonical_field": "recommendation_factors",
        "data_type": "text",
        "form_v2_mapping": "What makes a place feel worth recommending?"
      }
    }
  }
}
```

### Normalization Workflow

```
Raw Survey Response (any form version)
    ↓
Identify form version + submission date
    ↓
Map fields using canonical_survey_schema
    ↓
Transform values (standardize "18-21" vs "18–21", etc.)
    ↓
Handle missing values (store as null, not empty string)
    ↓
Extract text primitives from open-ended responses
    ↓
Store in PostgreSQL in canonical format
    ↓
Create preference vector for Layer 2 matching
```

### Code: Normalization Mapper

```python
# config/survey_normalizer.py

class SurveyNormalizer:
    """
    Handles multiple survey form versions.
    Maps any form version to canonical schema.
    """
    
    CANONICAL_SCHEMA = load_json("config/survey_schema.json")
    
    def __init__(self, form_version: str, submission_date: datetime):
        self.form_version = form_version
        self.submission_date = submission_date
        self.schema = self.get_schema_for_version(form_version)
    
    def normalize(self, raw_response: dict) -> dict:
        """Transform raw response to canonical format"""
        canonical = {}
        
        for canonical_field, field_spec in self.CANONICAL_SCHEMA.items():
            source_field = field_spec.get(f"form_{self.form_version}_mapping")
            
            if not source_field or source_field not in raw_response:
                canonical[canonical_field] = None
                continue
            
            raw_value = raw_response[source_field]
            canonical[canonical_field] = self.transform_value(
                raw_value, 
                field_spec
            )
        
        return canonical
    
    def transform_value(self, raw_value, field_spec):
        """Apply transformation rules (type conversion, standardization)"""
        data_type = field_spec.get("data_type")
        
        if data_type == "categorical":
            return self.standardize_categorical(raw_value, field_spec)
        elif data_type == "array[categorical]":
            return self.standardize_array(raw_value, field_spec)
        elif data_type == "int(1-5)":
            return int(raw_value) if raw_value else None
        elif data_type == "text":
            return raw_value.strip() if raw_value else None
        else:
            return raw_value
```

---

## PART 3: Data Ingestion Pipeline (Multiple Sources)

### Future Data Sources

```
Google Places API
├─ Reviews (via existing pipeline)
├─ Venue metadata
└─ Real-time ratings/counts

Zomato API
├─ Reviews + ratings
├─ Menu data
└─ Reservation data

MagicPin API
├─ Check-ins
├─ Reviews
└─ Photos

User Survey
├─ Preference signals
├─ Frustrations
└─ Satisfaction metrics
```

### Data Flow Architecture

```
Multi-Source Ingestion
    ├─ Google: Reviews → Step 3-6 pipeline (existing)
    ├─ Zomato: Reviews → Step 3-6 pipeline (same)
    ├─ MagicPin: Check-ins + Reviews → Step 3-6 pipeline
    └─ Survey: Responses → Normalization → Canonical Schema
    
         ↓ (all converge)
    
PostgreSQL
    ├─ venues (enriched with data from all sources)
    ├─ reviews (with source attribution)
    ├─ primitives (updated scores across sources)
    ├─ survey_responses (canonical format)
    └─ confidence_governance (tracks source quality)
    
         ↓
    
Pinecone
    ├─ venue_vectors (54-d, multi-source)
    ├─ user_preference_vectors (from surveys)
    └─ similarity indices
```

### Amendment Logic

When new review data arrives (from any source):

```python
# step_3_extract.py (updated for multi-source)

def extract_and_amend(venue_id, new_reviews, source):
    """
    Extract primitives from new reviews.
    Amend existing venue scores based on new data.
    """
    
    # 1. Extract primitives from new reviews
    new_signals = extract_signals(new_reviews)
    
    # 2. Fetch existing venue record
    existing_venue = db.venues.get(venue_id)
    existing_scores = existing_venue.primitive_scores
    
    # 3. Calculate weighted average (old + new)
    amended_scores = {}
    for primitive_id in PRIMITIVES:
        old_score = existing_scores.get(primitive_id, 0)
        new_score = new_signals.get(primitive_id, 0)
        
        # Weight by recency: newer sources weighted higher
        days_old = (today - existing_venue.last_updated).days
        recency_weight = exp(-days_old / 30)  # Exponential decay
        
        amended_scores[primitive_id] = (
            old_score * (1 - recency_weight) +
            new_score * recency_weight
        )
    
    # 4. Update venue record
    db.venues.update(venue_id, {
        "primitive_scores": amended_scores,
        "source_attribution": {
            "google_maps": review_count_google,
            "zomato": review_count_zomato,
            "magicpin": review_count_magicpin
        },
        "last_updated": today,
        "version": current_schema_version
    })
    
    # 5. Regenerate venue vector
    venue_vector = vectorize_primitives(amended_scores)
    pinecone.update(venue_id, venue_vector)
```

---

## PART 4: What Else Can We Build? (15+ Features)

### Currently Planned (by you)
1. ✅ **Similar Venues Comparison** — Show 3 venues with 3 better/worse factors
2. ✅ **Consulting Redirect** — "Want to become type Y? Here's what Y venues do differently"

### Additional Features (High-Impact)

#### **FEATURE 3: Personalized Venue Recommendations**

**What:** "Based on your preferences, here are venues matched to you"

**How it works:**
```
User survey response
    ↓
Create user preference vector (54 dimensions)
    ↓
Search Pinecone for similar venue vectors
    ↓
Rank by compatibility score
    ↓
Filter by constraints (price, location, timing)
    ↓
Return: "Top 5 venues for you" with explanation
    
Example: "Doolally is 94% compatible with you because you love:
         - good vibe (live_music + social_energy)
         - affordable (matches your ₹1-3k spend range)
         - crowd comfort (group_spend_amplification)"
```

**Business value:** Acquisition (find users for venues)

---

#### **FEATURE 4: Predictive Churn Risk Scoring**

**What:** "Which venues will lose customers in the next 30/90 days?"

**How it works:**
```
Analyze user archetype + venue match
    ↓
Detect misalignment signals:
├─ User values calm, venue = high-energy
├─ User values music, venue = low-quality DJ
├─ User values group-dwell, venue = rushed service
└─ Crowd archetype changed (shift from calm to chaotic)
    ↓
Predict churn probability (0-1)
    ↓
Flag venue for intervention
    
Example: "Vashi Social has 73% churn risk.
         Reason: 4 recent reviews from 'calm seekers' all mention
         'noise overload' and 'left early'. Your crowd shifted."
```

**Business value:** Operational intelligence (prevent churn)

---

#### **FEATURE 5: Archetype Segmentation Dashboard**

**What:** "What user archetypes exist in your market?"

**How it works:**
```
All survey responses
    ↓
Cluster by preference patterns
    ↓
Identify archetypes:
├─ "Calm Social Pair" (26% of users)
│  ├─ Energy: Balanced
│  ├─ Spend: ₹1-3k
│  ├─ Duration: 2-3h
│  ├─ Priorities: Conversation comfort, food, ambience
│  └─ Frustrations: Noise, overcrowding
│
├─ "High-Energy Group Explorer" (31%)
│  ├─ Energy: High
│  ├─ Spend: ₹3-5k
│  ├─ Duration: 3+h
│  ├─ Priorities: Music, crowd energy, people
│  └─ Frustrations: No DJ, fake vibe
│
└─ "Efficiency-Minded Solo" (18%)
   ├─ Energy: Balanced
   ├─ Spend: <₹1k
   ├─ Duration: 1-2h
   ├─ Priorities: Convenience, price, quick service
   └─ Frustrations: Waiting, high prices
```

**Dashboard shows:**
- % of market in each archetype
- Which archetypes grow fastest
- Which venues attract which archetypes
- Archetype migration patterns (calm → high-energy over time?)

**Business value:** Marketing targeting + venue positioning

---

#### **FEATURE 6: Conflict Detection & Resolution**

**What:** "Which user archetypes clash in the same venue?"

**How it works:**
```
Analyze co-occurrence patterns
    ↓
Detect conflicts:
├─ "Calm seekers" and "high-energy seekers" both visit
   → Both leave frustrated
├─ "Solo workers" and "party groups" both visit
   → Solo workers leave early, groups feel restricted
└─ "Conversation people" and "ambient music people" both visit
   → Music volume satisfies no one
    ↓
Suggest operational fixes:
├─ Time-based: "Host calm vibes weekdays, party vibes weekends"
├─ Space-based: "Create quiet corner + party zone"
├─ Music-based: "Progressive volume increase after 9pm"
└─ Crowd-based: "Limit party group size on conversation nights"
```

**Business value:** Operational optimization (reduce friction)

---

#### **FEATURE 7: Satisfaction Driver Analysis**

**What:** "What combinations of factors drive highest satisfaction?"

**How it works:**
```
Analyze survey free-text responses
    ↓
Extract satisfaction factors:
├─ "Good food + ambience" → 92% satisfaction
├─ "Good food alone" → 71%
├─ "Music + people" → 88%
├─ "Music alone" → 62%
├─ "All four together" → 96%
    ↓
Identify interaction effects:
├─ Service quality amplifies music enjoyment (+15%)
├─ Comfort + company matters more than food
├─ View compensates for high price
    ↓
Generate optimization recommendations
    
Example: "Your venue's satisfaction is 72%. To reach 85%:
         - Upgrade service (gains +8% across all users)
         - Add live music (gains +12% for groups, +5% for pairs)
         - Both together = +18% (synergistic)"
```

**Business value:** Product roadmap (what to fix first?)

---

#### **FEATURE 8: Pricing Power Analysis**

**What:** "How much premium can this venue charge?"

**How it works:**
```
Analyze premium_acceptance signals
    ↓
Find user archetypes who accept premium pricing
    ↓
Identify premium justifiers:
├─ View (rooftop bar can charge +30%)
├─ Experience exclusivity (+25%)
├─ Social destination status (+20%)
├─ Food quality (+15%)
    ↓
Predict revenue impact of price change
    
Example: "Vashi Social attracts high-energy groups who value
         music + people + extended stay.
         Premium power: +15% (limited).
         Suggested: Stay at ₹3-5k range, not ₹5k+.
         Going higher risks 23% churn of your core group."
```

**Business value:** Revenue optimization

---

#### **FEATURE 9: Cross-Venue Synergy Recommendations**

**What:** "Which other venues should users also visit?"

**How it works:**
```
User visits Venue A
    ↓
Extract their archetype from visit behavior
    ↓
Find Venue B with different strengths but same core appeal
    ↓
Recommend Venue B
    
Example: User goes to calm cafe (good for work).
         Recommend: Similar calm venue good for evening dates.
         
         User goes to party bar (high energy, music).
         Recommend: High-energy lounge for post-party chilling
         (same crowd energy, different pace).
```

**Business value:** Cross-venue partnerships + growth

---

#### **FEATURE 10: Competitive Benchmarking**

**What:** "How does your venue stack up? By archetype."

**How it works:**
```
Select benchmark set (competitors or category leaders)
    ↓
Compare primitive scores across archetypes
    ↓
Show strength/weakness by user type
    
Example Dashboard:
┌─────────────────────────────────────────┐
│ Your Venue vs Competitors                │
├─────────────────────────────────────────┤
│ For "Calm Social Pairs":                 │
│ You:        ████░░░░░░ 65%              │
│ Doolally:   ██████░░░░ 78% ✓ Better      │
│ Eve:        ██████████ 92% ✗ Much better │
│                                          │
│ Gap: -27 points. To compete:            │
│ • Reduce noise (your #1 pain)           │
│ • Improve service (their #1 strength)   │
│ • Emphasize conversation comfort       │
```

**Business value:** Competitive strategy

---

#### **FEATURE 11: Friction Funnel Analysis**

**What:** "Where in the visit do people leave?"

**How it works:**
```
Analyze timeline of frustrations
    ↓
Map friction to visit stage:
├─ Before arrival: "Parking hard" → lose 15%
├─ On arrival: "Long wait" → lose 10%
├─ During meal: "Bad service" → lose 18%
├─ During drinks: "Music too loud" → lose 12%
└─ After 2h: "Uncomfortable crowd" → lose 22%
    ↓
Rank by impact (where does each friction affect most users?)
    ↓
Suggest fixes by stage
    
Example: "Your users' #1 friction is 'music too loud'
         affecting 34% of visitors.
         It causes early leaving in 23% of cases.
         Fix: Volume control strategy = +8% retention."
```

**Business value:** Operational fixes (quick wins)

---

#### **FEATURE 12: Cohort Retention Analysis**

**What:** "Which user cohorts stay? Which churn?"

**How it works:**
```
Track users over time (via email/phone)
    ↓
Measure repeat visit behavior
    ↓
Segment by entry cohort:
├─ "First-time high-energy seekers" → 31% repeat (3 months)
├─ "First-time calm seekers" → 47% repeat
├─ "Referred calm seekers" → 68% repeat
├─ "Referred high-energy" → 54% repeat
    ↓
Identify retention drivers
    
Example: "Calm seekers have 52% higher retention.
         Why? They value consistency (lower churn).
         Strategy: Optimize for calm seekers as your core,
                   keep high-energy as occasional volume."
```

**Business value:** Retention strategy

---

#### **FEATURE 13: Content Recommendation Engine (Layer 3 prep)**

**What:** "What photos/content would appeal to which archetype?"

**How it works:**
```
Analyze user preferences
    ↓
Tag content dimensions:
├─ Image shows: "Packed crowd, DJ, high energy"
│  → Appeal to "High-Energy Group" (+85% engagement)
│  → Repel "Calm Pair" (-60%)
│
├─ Image shows: "Quiet corner, coffee, couple"
│  → Appeal to "Calm Pair" (+90%)
│  → Repel "Party Group" (-75%)
└─ Image shows: "Food, ambient lighting, conversation"
   → Appeal to all (+60% average)
    ↓
Recommend content mix for each venue
    
Example: "To retain your calm-seeker base, post 60% ambient
         content, 20% food, 20% couple-friendly moments.
         Avoid: Party photos, packed crowds, loud-vibes."
```

**Business value:** Marketing content strategy

---

#### **FEATURE 14: Dynamic Recommendation (Real-time)**

**What:** "Show users the right venue at the right time"

**How it works:**
```
User query: "Where should I go tonight with my partner?"
    ↓
Identify archetype: "Calm Social Pair"
    ↓
Check real-time conditions:
├─ What's the crowd size right now? (via check-ins)
├─ What's the music vibe right now? (via venue staff tags)
├─ Is it quiet or loud right now? (via user mentions)
└─ How long is the wait? (via reservation system)
    ↓
Filter venues by real-time state
    ↓
Recommend: "Vashi Social is perfect right now.
            It's calm (low music, small crowd, 15-min wait).
            In 1 hour it'll get busier. Go now."
```

**Business value:** Real-time acquisition

---

#### **FEATURE 15: Operational Simulation / "What-If"**

**What:** "If we change X, what happens to satisfaction?"

**How it works:**
```
Venue manager specifies change:
"What if we turn off the DJ?"
    ↓
System runs simulation:
├─ Project impact on each archetype
├─ "High-energy groups": -28% satisfaction
├─ "Calm pairs": +18% satisfaction
├─ "Neutral explorers": -5%
├─ Net: -12% (overall loss)
    ↓
Recommend safeguards:
"Alternative: Keep DJ but lower volume after 9pm.
 Impact: -3% for high-energy, +12% for calm, net +4%"
```

**Business value:** Strategic decision-making

---

#### **FEATURE 16: Trend Detection & Prediction**

**What:** "What's changing in user preferences? Predict next quarter."

**How it works:**
```
Monthly user preference data
    ↓
Detect trends:
├─ "Calm-seeking is growing +3% month-over-month"
├─ "Music importance declining for 26-30 age group"
├─ "Group-dwell behavior moving to weekday evenings"
└─ "Premium pricing tolerance rising in Navi Mumbai"
    ↓
Project forward 90 days
    ↓
Alert venues to market shifts
    
Example: "Your market is shifting: Calm seekers growing
         (was 24%, will be 31% in Q3).
         Prepare: Reduce noise, boost comfort, premium-ify."
```

**Business value:** Market forecasting

---

## PART 5: Database Schema Implications

To support all 16 features, PostgreSQL needs tables:

```sql
-- Core Layer 1
CREATE TABLE venues (...)
CREATE TABLE reviews (...)
CREATE TABLE primitives_scores (...)

-- Core Layer 2
CREATE TABLE survey_responses (...)  -- normalized
CREATE TABLE user_preferences (...)  -- canonical format
CREATE TABLE user_archetypes (...)   -- segmentation

-- Supporting
CREATE TABLE archetype_definitions (...)
CREATE TABLE conflict_matrix (...)     -- which archetypes clash?
CREATE TABLE satisfaction_drivers (...) -- factor combinations
CREATE TABLE pricing_power_scores (...)
CREATE TABLE churn_risk_scores (...)
CREATE TABLE competitive_benchmarks (...)
CREATE TABLE cohort_retention (...)
CREATE TABLE trend_analysis (...)
```

---

## PART 6: Implementation Roadmap

### Phase 1: Foundation (Weeks 1-2)
- [ ] Normalize existing survey responses (Forms v1 + v2)
- [ ] Create PostgreSQL schema (Layer 1 + Layer 2 base)
- [ ] Load survey data into database
- [ ] Generate user preference vectors (Pinecone)

### Phase 2: Consulting Features (Weeks 3-4)
- [x] Feature 1: Similar Venues Comparison
- [x] Feature 2: Consulting Redirect
- [ ] Add confidence scoring (which factors matter most?)

### Phase 3: Personalization (Weeks 5-6)
- [ ] Feature 3: Personalized Recommendations
- [ ] Feature 13: Content Recommendation Engine (prep for Layer 3)
- [ ] Feature 9: Cross-Venue Synergy

### Phase 4: Operational Intelligence (Weeks 7-8)
- [ ] Feature 4: Churn Risk Scoring
- [ ] Feature 6: Conflict Detection
- [ ] Feature 11: Friction Funnel Analysis
- [ ] Feature 7: Satisfaction Driver Analysis

### Phase 5: Market Intelligence (Weeks 9-10)
- [ ] Feature 5: Archetype Segmentation Dashboard
- [ ] Feature 10: Competitive Benchmarking
- [ ] Feature 12: Cohort Retention Analysis
- [ ] Feature 16: Trend Detection

### Phase 6: Advanced (Weeks 11-12)
- [ ] Feature 8: Pricing Power Analysis
- [ ] Feature 14: Real-time Dynamic Recommendations
- [ ] Feature 15: Operational Simulation

---

## PART 7: The Value Stack

**For Venues:**
- Operational optimization (reduce friction)
- Revenue optimization (pricing, archetype focus)
- Competitive positioning
- Churn prevention
- Simulations ("what if?")

**For Users:**
- Personalized recommendations
- Discover venues matching them
- Informed choice (why they'd enjoy it)
- Community signals (which archetypes enjoy this?)

**For Polynovea:**
- Acquisition targeting (find users for venues)
- Content strategy (what to post for which archetype)
- Partnership opportunities (cross-venue synergies)
- Market forecasting (predict demand shifts)

---

## Summary

**Beyond the two features you mentioned:**
- You can build **14 additional major features**
- Each unlocks different business value (operational, financial, strategic)
- All feed into a **unified behavioral intelligence infrastructure**
- Your data material (primitives + surveys + reviews) can support all of them

**The database choice (PostgreSQL + Pinecone) enables:**
- Relational integrity (venues, surveys, primitives)
- Semantic matching (vector similarity)
- Real-time predictions (churn, archetype, trends)
- Scalable analytics (millions of users × thousands of venues)

Ready to build this? Start with Phase 1 (normalization + schema).

