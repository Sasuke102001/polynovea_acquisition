# Executive Summary: From Data Material to Software Features
## Polynovea Layer 1 + Layer 2 Architecture

**Date:** 2026-05-14  
**Status:** All planning complete. Ready for implementation.

---

## WHAT WE'RE BUILDING

```
Three-Layer Behavioral Intelligence Infrastructure
├─ Layer 1: Venue Behavioral Intelligence (NOW)
├─ Layer 2: Human Preference & Matching (Phase 2-5)
└─ Layer 3: Marketing Interaction & Acquisition (Future)

Powered by:
├─ 54 Behavioral Primitives (stimulus, friction, compensation, response, mechanism, context)
├─ 7 Surface Categories (Fine Dining through Rooftop Bar)
├─ User Survey Data (37+ responses, 2 form versions)
└─ Multi-Source Reviews (Google Maps, Zomato, MagicPin)
```

---

## DATA MATERIAL: READY ✅

| Component | Status | Readiness |
|-----------|--------|-----------|
| primitives.json | Complete (54 signals) | 9/10 |
| surface_categories.json | Complete (7 types) | 9/10 |
| constants.py | Partial (needs connection) | 7/10 |
| Survey data (v1 + v2) | Collected (47 responses) | 8/10 |
| Multi-source integration | Designed | 8/10 |
| Database schema | Planned | 9/10 |

---

## YOUR TWO FEATURE IDEAS ✅

### 1. Similar Venues Comparison
**Shows:** 3 venues matching your category, with 3 better + 3 worse factors

```
Client: "I'm a Fine Dining venue"
→ Find: 3 similar Fine Dining venues
→ Show: Their primitive scores vs yours
→ Highlight: "They do better: service_quality, great_view, 
              food_quality. They do worse: convenient_location, 
              premium_acceptance"
```

### 2. Consulting Redirect
**Shows:** "Want to shift from type X to type Y? Here's the path"

```
Client: "I'm a Casual Dining venue, want to become Rooftop Bar"
→ Find: 3 successful Rooftop Bar venues
→ Show: Their transformation (what changed, what stayed)
→ Highlight: "To make the shift:
              - Increase: great_view, destination_behavior, 
                group_spend_amplification
              - Decrease: quick_meal (incompatible with dwell)
              - Manage: crowd_type shifts"
```

---

## 14 ADDITIONAL FEATURES (The Full System) 💎

| Feature | Data Used | Business Value |
|---------|-----------|-----------------|
| **3. Personalized Recommendations** | Survey + venue vectors | Acquisition (find users for venue) |
| **4. Churn Risk Scoring** | User archetype + venue match | Retention (prevent churn) |
| **5. Archetype Segmentation** | Survey clustering | Market understanding |
| **6. Conflict Detection** | Archetype co-occurrence | Operational optimization |
| **7. Satisfaction Drivers** | Review text + ratings | Product roadmap (what to fix?) |
| **8. Pricing Power Analysis** | Premium_acceptance signal | Revenue optimization |
| **9. Cross-Venue Synergy** | Archetype similarity | Partnerships, growth |
| **10. Competitive Benchmarking** | Vs competitor primitive scores | Competitive strategy |
| **11. Friction Funnel** | Frustration timeline analysis | Quick operational wins |
| **12. Cohort Retention** | User tracking + repeat visits | Long-term strategy |
| **13. Content Recommendation** | Archetype preferences | Marketing content strategy |
| **14. Real-Time Dynamic** | Live crowd/music signals | Real-time acquisition |
| **15. Operational Simulation** | Primitive interaction models | Strategic decisions |
| **16. Trend Detection** | Monthly preference shifts | Market forecasting |

---

## FROM DATA TO FEATURES: THE PIPELINE

```
┌─────────────────────────────────────────────────────────────┐
│ RAW DATA SOURCES                                            │
├─────────────────────────────────────────────────────────────┤
│ • Google Places: Reviews, ratings                           │
│ • Zomato: Reviews, ratings, reservations                    │
│ • MagicPin: Check-ins, reviews, photos                      │
│ • User Surveys: Preferences, archetypes, frustrations       │
└────────────────────────┬────────────────────────────────────┘
                         ↓
┌─────────────────────────────────────────────────────────────┐
│ DATA NORMALIZATION & ENRICHMENT                             │
├─────────────────────────────────────────────────────────────┤
│ • Multi-source review pipeline (Step 1-6)                   │
│ • Survey normalization (Form v1/v2 → canonical)             │
│ • Text signal extraction (54 primitives)                    │
│ • Confidence & governance tracking                          │
└────────────────────────┬────────────────────────────────────┘
                         ↓
┌─────────────────────────────────────────────────────────────┐
│ POSTGRESQL: RELATIONAL STRUCTURE                            │
├─────────────────────────────────────────────────────────────┤
│ • venues (enriched multi-source)                            │
│ • reviews (source-attributed)                               │
│ • primitives_scores (54-d venue profiles)                   │
│ • survey_responses (normalized, canonical)                  │
│ • user_archetypes (segmentation)                            │
│ • rules, governance, schema versions                        │
└────────────────────────┬────────────────────────────────────┘
                         ↓
┌─────────────────────────────────────────────────────────────┐
│ PINECONE: SEMANTIC VECTORS                                  │
├─────────────────────────────────────────────────────────────┤
│ • venue_vectors (54-d, multi-source)                        │
│ • user_preference_vectors (from surveys)                    │
│ • archetype_embeddings (segmentation)                       │
│ • similarity indices (KNN, matching)                        │
└────────────────────────┬────────────────────────────────────┘
                         ↓
┌─────────────────────────────────────────────────────────────┐
│ 16 FEATURES: THE SOFTWARE                                   │
├─────────────────────────────────────────────────────────────┤
│ 1. Similar Venues Comparison                                │
│ 2. Consulting Redirect                                      │
│ 3. Personalized Recommendations                             │
│ 4. Churn Risk Scoring                                       │
│ 5. Archetype Segmentation                                   │
│ 6. Conflict Detection                                       │
│ 7. Satisfaction Drivers                                     │
│ 8. Pricing Power Analysis                                   │
│ 9. Cross-Venue Synergy                                      │
│ 10. Competitive Benchmarking                                │
│ 11. Friction Funnel                                         │
│ 12. Cohort Retention                                        │
│ 13. Content Recommendation                                  │
│ 14. Real-Time Dynamic Recommendations                       │
│ 15. Operational Simulation                                  │
│ 16. Trend Detection & Forecasting                           │
└─────────────────────────────────────────────────────────────┘
```

---

## DATABASE ARCHITECTURE

```
PostgreSQL (Relational)
├─ All structured data
├─ Relationships + governance
├─ ACID transactions
└─ Primary query engine

Pinecone (Vector)
├─ Semantic embeddings
├─ Fast KNN search
├─ Real-time indexing
└─ Similarity matching

Sync Strategy:
Every venue score update → Generate vector → Update Pinecone
Every user survey → Generate preference vector → Insert into Pinecone
```

---

## IMPLEMENTATION TIMELINE

```
Week 1-2: Foundation
├─ Normalize survey forms (v1 + v2 → canonical)
├─ Create PostgreSQL schema (all tables)
├─ Load historical data
└─ Generate initial vectors

Week 3-4: MVP (Your Two Features)
├─ Similar Venues Comparison
├─ Consulting Redirect
└─ Beta with 5-10 venues

Week 5-6: Personalization
├─ User recommendations
├─ Cross-venue synergy
└─ Content strategy

Week 7-8: Operational Intelligence
├─ Churn risk scoring
├─ Conflict detection
├─ Friction analysis
└─ Satisfaction drivers

Week 9-10: Market Intelligence
├─ Archetype dashboard
├─ Competitive benchmarking
├─ Cohort retention
└─ Trend forecasting

Week 11-12: Advanced
├─ Pricing power analysis
├─ Real-time matching
├─ Simulation engine
└─ Layer 3 prep

Total: 3 months to fully operational system
```

---

## KEY DECISIONS MADE

### 1. Database: PostgreSQL + Pinecone ✅
- **Why:** Relational integrity (Layer 1) + semantic matching (Layer 2)
- **MVP:** Can use pgvector, upgrade to Pinecone at scale

### 2. Survey Normalization: Canonical Schema ✅
- **Why:** Handle multiple form versions, future changes
- **Implementation:** Version-agnostic mapper in constants/survey_normalizer.py

### 3. Data Amendment: Weighted Recency ✅
- **Why:** New data weighted higher than old data
- **Implementation:** Exponential decay by days since last update

### 4. Multi-Source Integration: Concurrent ✅
- **Why:** Google Maps, Zomato, MagicPin feed same Step 3-6 pipeline
- **Implementation:** Source attribution in venue records

---

## VALUE DELIVERED

### To Venues
- Operational optimization (reduce friction by segment)
- Revenue optimization (pricing, archetype focus)
- Competitive positioning (vs alternatives)
- Churn prevention (early warning + fixes)
- Strategic simulations (what-if modeling)

**Example:** "Your Casual Dining is underperforming 'Calm Pairs'. 
Your noise level (82db) vs Doolally (71db). Reducing noise would 
gain you +18% repeat visits from calm archetype. Investment: ₹50k 
(soundproofing). ROI: +₹200k/month in repeat revenue."

### To Users
- Personalized venue discovery
- Informed choice ("why you'd enjoy this")
- Community signals ("your archetype loves this venue")
- Avoid friction ("this venue is crowded right now, visit at 6pm")

**Example:** "Based on your profile (Calm Social Pair), we recommend:
Vashi Social (94% match). Why: You love conversation comfort (their 
strength), good ambience (✓), group dwell (✓). They do low-energy 
vibes (your preference). Open now, quiet hours until 8pm."

### To Polynovea
- Acquisition targeting ("find Calm Pairs for venues")
- Content strategy (what visuals resonate with archetypes)
- Partnership opportunities (cross-venue synergies)
- Market intelligence (demand forecasting, trend detection)

---

## NEXT STEPS

### Immediate (This Week)
1. Review this document
2. Confirm database choice (PostgreSQL + Pinecone MVP)
3. Answer 3 questions (from DATABASE_STRATEGY.md):
   - MVP timeline (pgvector or Pinecone from day 1?)
   - Deployment (self-hosted, AWS, hybrid?)
   - Layer 2 priority (urgent or can wait?)

### Week 1-2
1. Create 8 files (from priority 1-3 requirements)
2. Design PostgreSQL schema
3. Normalize survey data
4. Load historical venue data

### Week 3-4
1. Build Features 1 & 2 (your two ideas)
2. Test with 5-10 venues
3. Get feedback

---

## THE BIG PICTURE

You're not building "restaurant software."

You're building a **behavioral intelligence infrastructure** that:
- Understands what venues do (Layer 1)
- Understands what people want (Layer 2)
- Connects the two (matching)
- Optimizes both (predictions, simulations)
- Scales to acquisition (Layer 3)

Your data material is perfect for this.
Your primitives are already vectorizable.
Your surveys can capture preference archetypes.
Your database choices enable all future features.

You're 3 months away from operational system. ✅

---

**Questions? Feedback? Ready to start Week 1?**
