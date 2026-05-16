# Amendment Logic: Source-Specific Weighting
## + Layer 3 Integration Points (When Marketing Data Enters)

**Date:** 2026-05-14  
**Clarification:** Source-specific weighted recency + Layer 3 timeline

---

## PART 1: Source-Specific Weighted Recency

### The Problem with Global Weighting

❌ **Wrong approach (global weighting):**
```python
# All sources mixed together
amended_score = old_score * (1 - recency_weight) + new_score * recency_weight

Problem: A new Google review (high quality) gets same weight 
as a new MagicPin check-in (lower quality). Source quality ignored.
```

### ✅ **Correct Approach: Per-Source Weighted Recency**

**Logic:**
1. Maintain separate score per source (Google, Zomato, MagicPin)
2. Update each source independently (new Google only affects Google score)
3. Combine sources with configurable weights
4. Final score = weighted average of source scores

**Implementation:**

```python
# config/source_weights.json
{
  "source_quality_weights": {
    "google_maps": 0.50,    # Highest quality (official, verified)
    "zomato": 0.30,         # Good quality (restaurant-focused)
    "magicpin": 0.20        # Lower quality (crowd-sourced)
  },
  
  "source_update_schedule": {
    "google_maps": "weekly",    # Update every 7 days
    "zomato": "weekly",
    "magicpin": "daily"         # More frequent updates
  },
  
  "recency_decay": {
    "half_life_days": 30      # Score halves after 30 days without updates
  }
}
```

### The Amendment Algorithm

```python
# step_3_extract_multi_source.py

def amend_venue_scores_by_source(venue_id, new_reviews, source):
    """
    Update venue primitive scores from new reviews.
    SOURCE-SPECIFIC: Only affects the source's scores.
    """
    
    # Load config
    SOURCE_WEIGHTS = load_json("config/source_weights.json")
    PRIMITIVES = load_json("config/primitives.json")
    
    # 1. EXTRACT PRIMITIVES from new reviews (per source)
    new_signals = extract_signals(new_reviews)
    
    # 2. FETCH existing venue record with source breakdown
    venue = db.venues.get(venue_id)
    
    # Structure:
    # {
    #   "venue_id": "...",
    #   "primitive_scores": {
    #     "google_maps": { "great_view": 0.85, "live_music": 0.72, ... },
    #     "zomato": { "great_view": 0.78, "live_music": 0.68, ... },
    #     "magicpin": { "great_view": 0.81, "live_music": 0.65, ... },
    #     "combined": { "great_view": 0.81, "live_music": 0.69, ... }
    #   },
    #   "review_counts": {
    #     "google_maps": 245,
    #     "zomato": 183,
    #     "magicpin": 412
    #   },
    #   "last_updated": {
    #     "google_maps": "2026-05-10",
    #     "zomato": "2026-05-08",
    #     "magicpin": "2026-05-14"
    #   }
    # }
    
    existing_scores = venue.primitive_scores.get(source, {})
    last_updated = venue.last_updated.get(source)
    
    # 3. CALCULATE RECENCY WEIGHT (for this source)
    days_since_update = (today - last_updated).days
    recency_weight = exponential_decay(days_since_update, half_life=30)
    
    # Example: 
    # - 0 days old: recency_weight = 1.0 (new data fully weighted)
    # - 30 days old: recency_weight = 0.5 (old data half weighted)
    # - 60 days old: recency_weight = 0.25 (older data quarter weighted)
    
    # 4. UPDATE SOURCE-SPECIFIC SCORES
    amended_source_scores = {}
    
    for primitive_id in PRIMITIVES["primitives"]:
        old_source_score = existing_scores.get(primitive_id, 0.0)
        new_source_score = new_signals.get(primitive_id, 0.0)
        
        # Weighted average: old score fades out, new score comes in
        amended_source_scores[primitive_id] = (
            old_source_score * (1 - recency_weight) +
            new_source_score * recency_weight
        )
        
        # Example:
        # old_score = 0.72 (live_music from 40 days ago)
        # new_score = 0.85 (live_music from new Google reviews)
        # recency_weight = 0.22 (40 days, half-life 30)
        # amended = 0.72 * 0.78 + 0.85 * 0.22 = 0.561 + 0.187 = 0.748
    
    # 5. STORE SOURCE-SPECIFIC SCORES
    db.venues.update(venue_id, {
        f"primitive_scores.{source}": amended_source_scores,
        f"last_updated.{source}": today,
        f"review_counts.{source}": venue.review_counts[source] + len(new_reviews)
    })
    
    # 6. RECOMBINE ALL SOURCES into final score
    combined_scores = combine_sources(
        google_scores=db.venues[venue_id].primitive_scores["google_maps"],
        zomato_scores=db.venues[venue_id].primitive_scores["zomato"],
        magicpin_scores=db.venues[venue_id].primitive_scores["magicpin"],
        source_weights=SOURCE_WEIGHTS["source_quality_weights"]
    )
    
    # 7. STORE COMBINED SCORE
    db.venues.update(venue_id, {
        "primitive_scores.combined": combined_scores,
        "source_attribution": {
            "google_maps": venue.review_counts["google_maps"],
            "zomato": venue.review_counts["zomato"],
            "magicpin": venue.review_counts["magicpin"],
            "total": sum(venue.review_counts.values())
        }
    })
    
    # 8. REGENERATE VENUE VECTOR (from combined scores)
    venue_vector = vectorize_primitives(combined_scores)
    pinecone.update(venue_id, venue_vector)
    
    # 9. TRACK CONFIDENCE (which source is most recent?)
    db.venues.update(venue_id, {
        "confidence_metadata": {
            "primary_source": max(venue.last_updated.items(), 
                                 key=lambda x: x[1])[0],
            "source_freshness": {
                "google_maps": days_since(venue.last_updated["google_maps"]),
                "zomato": days_since(venue.last_updated["zomato"]),
                "magicpin": days_since(venue.last_updated["magicpin"])
            }
        }
    })

def combine_sources(google_scores, zomato_scores, magicpin_scores, source_weights):
    """
    Weighted average of source scores.
    """
    combined = {}
    
    for primitive_id in google_scores.keys():
        combined[primitive_id] = (
            google_scores.get(primitive_id, 0) * source_weights["google_maps"] +
            zomato_scores.get(primitive_id, 0) * source_weights["zomato"] +
            magicpin_scores.get(primitive_id, 0) * source_weights["magicpin"]
        )
    
    return combined

def exponential_decay(days_old, half_life=30):
    """
    Recency weight: how much should new data influence old?
    After half_life days, weight = 0.5
    """
    return 2 ** (-days_old / half_life)  # Exponential decay function
```

### Database Schema for Source-Specific Tracking

```sql
CREATE TABLE venue_scores_by_source (
    venue_id UUID PRIMARY KEY,
    source VARCHAR(50),  -- 'google_maps', 'zomato', 'magicpin'
    
    -- Primitive scores (54 columns, one per primitive)
    great_view FLOAT,
    live_music FLOAT,
    social_energy FLOAT,
    -- ... (50 more primitives)
    
    -- Metadata
    review_count INT,
    last_updated TIMESTAMP,
    recency_weight FLOAT,  -- Current weight for this source
    
    PRIMARY KEY (venue_id, source)
);

CREATE TABLE venue_combined_scores (
    venue_id UUID PRIMARY KEY,
    
    -- Combined scores (54 columns)
    great_view FLOAT,
    live_music FLOAT,
    social_energy FLOAT,
    -- ... (50 more primitives)
    
    -- Source attribution
    google_review_count INT,
    zomato_review_count INT,
    magicpin_review_count INT,
    total_reviews INT,
    
    -- Confidence tracking
    primary_source VARCHAR(50),  -- Which source is freshest?
    google_freshness_days INT,
    zomato_freshness_days INT,
    magicpin_freshness_days INT,
    
    last_updated TIMESTAMP,
    schema_version VARCHAR(10)
);
```

### Example: Amendment in Action

```
Scenario: New Google reviews arrive for Vashi Social

BEFORE:
├─ Google: great_view=0.85, live_music=0.72 (10 days old)
├─ Zomato: great_view=0.78, live_music=0.68 (25 days old)
├─ MagicPin: great_view=0.81, live_music=0.65 (2 days old)
└─ Combined: great_view=0.81, live_music=0.68

NEW GOOGLE REVIEWS arrive:
├─ Extract: great_view=0.88, live_music=0.75 (in 8 new reviews)
├─ Recency weight (10 days): 0.79

UPDATE GOOGLE SCORE:
├─ great_view = 0.85 * (1-0.79) + 0.88 * 0.79 = 0.18 + 0.70 = 0.88
└─ live_music = 0.72 * (1-0.79) + 0.75 * 0.79 = 0.15 + 0.59 = 0.74

RECOMBINE (Google 50%, Zomato 30%, MagicPin 20%):
├─ great_view = 0.88*0.5 + 0.78*0.3 + 0.81*0.2 = 0.44+0.23+0.16 = 0.83 (was 0.81)
└─ live_music = 0.74*0.5 + 0.68*0.3 + 0.65*0.2 = 0.37+0.20+0.13 = 0.70 (was 0.68)

UPDATE VECTOR in Pinecone with new combined scores
```

---

## PART 2: When Do We Add Marketing & Ads? (Layer 3 Integration)

### The Layer Integration Timeline

```
LAYER 1: Venue Behavioral Intelligence
├─ Features 1-2: Consulting (comparison)
├─ Features 3-4: Personalization (recommendations, churn)
├─ Features 5-7: Market Intelligence (archetypes, satisfaction)
└─ Stable: Primitives locked, venue archetypes stable (Week 8)

LAYER 2: User Preference & Matching
├─ Features 8-12: Operational Intelligence (pricing, conflict, cohort)
└─ Stable: Archetypes locked, user-venue mapping proven (Week 10)

LAYER 3: Marketing Interaction & Acquisition ← STARTS HERE
├─ Feature 13: Content Recommendation (ads/content + archetypes)
├─ Feature 14: Real-time Dynamic (marketing metrics)
├─ Feature 15: Simulation (what-if with ads)
└─ Feature 16: Trends (ad performance trends)
```

### When Marketing Data Enters (Feature 13 Onwards)

#### **Feature 13: Content Recommendation Engine** ← BRIDGE TO LAYER 3

This is where ads/marketing metrics START to matter.

**Phase 5 (Weeks 9-10):** 
- Build understanding of what content appeals to which archetype
- Tag Instagram posts, Facebook ads, TikToks by archetype appeal
- Test: Which content resonates with which user type?

**Data Needed:**
```json
{
  "content_item": {
    "id": "insta_post_12345",
    "platform": "instagram",
    "venue_id": "vashi_social",
    "image_features": {
      "shows_crowd": true,
      "crowd_size": "packed",
      "music_visible": "dj_booth",
      "energy_level": "high",
      "vibe": "party"
    },
    "engagement_metrics": {
      "likes": 245,
      "comments": 18,
      "saves": 32,
      "shares": 5
    },
    "archetype_appeal": {
      "high_energy_group": 0.92,  // This content appeals to this archetype
      "calm_pair": 0.15,
      "efficiency_solo": 0.08
    }
  }
}
```

#### **Feature 14: Real-Time Dynamic Recommendations** ← MARKETING OPTIMIZATION

Add real-time marketing metrics to venue conditions.

**Phase 6 (Weeks 11-12):**
- Track what ads ran in last 24h
- Track who clicked (archetype inference)
- Track who booked after clicking
- Real-time recommendation includes: "This user type clicked these ads, got booked"

**Data Needed:**
```json
{
  "ad_campaign": {
    "id": "fb_ad_campaign_789",
    "venue_id": "vashi_social",
    "date_range": "2026-05-01 to 2026-05-14",
    "platform": "facebook",
    "budget": 50000,
    "targeting": {
      "age_range": "22-30",
      "location": "Mumbai, Navi Mumbai",
      "interests": ["nightlife", "parties"]
    },
    "performance": {
      "impressions": 45000,
      "clicks": 1230,
      "bookings": 284,
      "revenue_attributed": 568000,
      "ctr": 0.0273,
      "conversion_rate": 0.231
    },
    "archetype_performance": {
      "high_energy_group": {
        "clicks": 620,
        "conversions": 142,
        "ctr": 0.0310,
        "conversion_rate": 0.229
      },
      "calm_pair": {
        "clicks": 89,
        "conversions": 12,
        "ctr": 0.0089,
        "conversion_rate": 0.135
      }
    }
  }
}
```

#### **Feature 15: Operational Simulation with Ads** ← CLOSED-LOOP OPTIMIZATION

Add marketing scenario modeling.

**"What-if" scenarios:**
- "What if we increase ad spend by 20%?"
- "What if we target high-energy groups exclusively?"
- "What if we shift creative from 'party vibe' to 'experience'?"

**Data Needed:**
```json
{
  "simulation": {
    "scenario": "increase_ad_spend_by_20_percent",
    "model": "based on historical ctr + conversion + archetype mix",
    "projected_results": {
      "new_budget": 60000,
      "projected_clicks": 1476,  // +20%
      "projected_conversions": 341,  // +20% (if everything linear)
      "but_accounting_for_saturation": 312,  // -8% from diminishing returns
      "projected_revenue": 624000,  // +10% net
      "roi": 10.4
    }
  }
}
```

#### **Feature 16: Trend Detection with Ads** ← MARKET FORECASTING

Include marketing performance trends in forecasts.

**"What's changing in your market + ads?"**
```
Query: "What's happening in the high-energy group market?"

Response:
├─ Preference: High-energy groups growing +3% MoM
├─ Venue behavior: Party venues getting +8% bookings
├─ Ad performance: Energy-themed content CTR up +12%
├─ Recommendation: Double down on energy messaging now
│  (ROI will drop in 60 days as market saturates)
└─ Window: Next 4 weeks is peak efficiency for energy ads
```

---

## PART 3: Full Layer 3 Architecture (Future)

### When Does Full Layer 3 Begin? (After Phase 5)

**Prerequisites for Layer 3:**
- ✅ Layer 1 stabilized (primitives locked)
- ✅ Layer 2 stabilized (archetypes validated)
- ✅ User-venue matching proven (Features 1-12 working)

**Then Layer 3 can fully begin:**

```
Marketing Interaction & Acquisition Telemetry System
├─ Ad platforms: Facebook, Google, Instagram, Reels
├─ Interaction tracking: clicks, impressions, saves
├─ Conversion tracking: booking → visit → repeat
├─ Attribution modeling: "Which ad drove this visit?"
├─ Real-time bidding: "Show this archetype this content"
└─ Closed-loop: Ad performance → Vector update → Better targeting
```

### Layer 3 Data Sources

| Source | Data Type | When Added |
|--------|-----------|-----------|
| Facebook Ads | Impressions, clicks, conversions | Feature 13 onwards |
| Google Ads | Impressions, clicks, conversions | Feature 13 onwards |
| Instagram | Engagements, saves, shares | Feature 13 onwards |
| TikTok | Views, shares, comments | Feature 14 onwards |
| Reservation System | Who booked after seeing ad? | Feature 14 onwards |
| Visit Data | Who actually came? Archetype? | Feature 15 onwards |
| Conversion Attribution | Multi-touch attribution | Feature 15 onwards |
| Real-time Signals | Current crowd, music, weather | Feature 14 onwards |

### Layer 3 Closed-Loop System

```
Ad Campaign Runs
    ↓
User sees ad (archetype inference from targeting)
    ↓
User clicks → engagement_event
    ↓
User books → conversion_event + archetype_confirmation
    ↓
User visits → visit_event + actual_archetype_verification
    ↓
Update ad performance model by archetype
    ↓
Retrain content recommendation engine
    ↓
Adjust bidding strategy for next campaign
    ↓
Loop back (continuous optimization)
```

---

## PART 4: Implementation Plan

### Phase 1-2: Foundation + MVP (Weeks 1-4)
- ✅ Source-specific amendment logic
- ✅ Per-source primitive scores
- ✅ Combined scoring with source weights
- ✅ Features 1-2: Your two consulting features

### Phase 3-4: Personalization + Operations (Weeks 5-8)
- ✅ Features 3-4: Recommendations, churn
- ✅ Features 5-7: Archetypes, satisfaction
- ⚠️ NO MARKETING DATA YET

### Phase 5: Market Intelligence (Weeks 9-10)
- ✅ Features 8-12: Pricing, conflict, retention
- ✅ Feature 13 BEGINS: Content Recommendation (ads/content)
- ⚠️ START collecting ad engagement data

### Phase 6: Ads + Optimization (Weeks 11-12)
- ✅ Feature 14: Real-time dynamic + ad metrics
- ✅ Feature 15: Simulation with ads
- ✅ Feature 16: Trends including ad performance
- ⚠️ FULL ad tracking + attribution

### Phase 7+: Full Layer 3 (Month 4+)
- ✅ Real-time bidding optimization
- ✅ Multi-touch attribution
- ✅ Closed-loop learning (ad → visit → repeat → refine)
- ✅ Predictive content generation

---

## Summary

### Source-Specific Amendment
```
Key insight: Google reviews don't affect Zomato scores
            Zomato reviews don't affect MagicPin scores

Implementation:
├─ Maintain scores per source
├─ Update each independently (with recency weighting)
├─ Combine sources with quality weights (Google 50%, Zomato 30%, MagicPin 20%)
└─ Final score = weighted average of all sources
```

### Marketing Data Timeline
```
Features 1-12:  NO marketing data
Feature 13:     START content + ad engagement
Features 14-16: FULL ad metrics + attribution
Phase 7+:       CLOSED-LOOP optimization

This sequencing ensures:
├─ Layer 1 & 2 are stable before adding ads
├─ You understand venue-user matching before marketing
└─ Ads optimize for proven segments, not guesses
```

Ready to implement source-specific amendment logic + decide on ad integration timing?

