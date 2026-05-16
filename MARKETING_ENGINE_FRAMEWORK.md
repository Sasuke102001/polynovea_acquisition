# Polynovea Marketing Engine Framework
**Version:** 2.0
**Date:** 2026-05-14
**Status:** Phase 1 — Campaign Brief Engine (DB Complete)

---

## Core Principle

> **Never gate an insight behind missing data.**
>
> Every venue gets a full campaign brief from day one using what we have.
> Optional data sources (Zomato/Swiggy opt-in, POS data, campaign history) add REFINEMENT only.
> Their absence has zero impact on base campaign recommendation quality.
> This applies to every data point, every feature, every screen.

---

## Critical Framing

**The Marketing Tab is Polynovea's campaign brief — not a DIY guide for venue owners.**

Polynovea executes the campaigns. The venue owner sees: "here's our strategy for you."

The consultant opens the Marketing Tab during a meeting. It shows what Polynovea will do, how, why it will work for this specific venue, and what results to expect. The venue owner does not log into anything. They do not create content. They collaborate — their audience benefits, our data grows.

---

## Executive Summary

The Marketing Engine translates Module 2 behavioral intelligence into targeted **acquisition and retention campaigns that Polynovea executes on behalf of venues**.

**Phase 1 (NOW):** Behavioral recommendations + Polynovea executes in-house
- DB-driven campaign briefs per venue (acquisition + retention split)
- Content: carousels, posts, Reels — created entirely in-house at Polynovea
- Polynovea posts on its own Instagram, tags venue as **collaborator** → post appears on both feeds
- No account access needed. No creator. No vendor. All performance data stays with Polynovea.
- **Data confidence:** MEDIUM (vendor research benchmarks)

**Phase 2 (LATER):** Scale execution + proprietary data
- Hire one execution-only shooter: shoots Reels/photos/ambience shots, leaves, zero creative input
- Polynovea's Instagram becomes the hub of the Mumbai venue ecosystem
- 50+ campaigns = proprietary Mumbai venue performance data → confidence upgrades from MEDIUM → HIGH
- **Data confidence:** HIGH (Polynovea's own campaign data across Mumbai venues)

**The Bridge:** Content budget = research budget. Every campaign Polynovea runs generates real Mumbai data that no competitor can replicate.

---

## How Polynovea Executes

### Content Creation Model

**Phase 1 (Current):**
- Polynovea creates all content in-house: carousels, posts, Reels
- Content is data-driven — Module 2 insights tell us what people want to see
- No external creator. No vendor. Polynovea directs, Polynovea executes.

**Phase 2 (Later):**
- Hire one person with a pure execution brief: shoot, leave, no creative input
- Deliverables: Reels, venue photos, ambience shots only
- Polynovea posts on its own Instagram, tags venue as **collaborator** (Instagram Collab feature)
- Post appears on both feeds. No venue account access needed. All performance data stays with Polynovea.

### Instagram Collab Model

```
Polynovea Instagram account
  ├─ Creates: Reel / carousel / post for Venue X
  ├─ Tags: Venue X as collaborator
  ├─ Result: Post appears on BOTH Polynovea feed AND Venue X feed
  ├─ Venue X gains: content without effort
  ├─ Polynovea gains: Venue X's followers cross-pollinate to Polynovea account
  └─ Data: Impressions, engagement, reach — all attributed to Polynovea's account
```

### Audience Aggregation Flywheel

```
Venue 1 (2,000 followers) → Collab → Polynovea gains exposure to 2,000 diners
Venue 2 (3,500 followers) → Collab → Polynovea gains exposure to 3,500 diners
...
Venue 20 (avg 2,500 followers) → Combined: ~50,000 Mumbai diners following Polynovea
Venue 30 → Polynovea's reach = combined audience of all Mumbai venues worked with
  ↓
B2C followers (diners) → B2B conversions (venue owners see Polynovea's feed and want in)
  ↓
Polynovea's Instagram = hub of the Mumbai venue ecosystem
```

By venue 20–30, no cold outreach needed. Venues find Polynovea.

### Why Running Ads Is Non-Negotiable

- Every campaign = real Mumbai venue data
- `channel_mechanism_mapping.research_confidence` = MEDIUM today (vendor benchmarks)
- After 50 campaigns = HIGH — 50 Polynovea-run Mumbai campaigns
- Content budget = research budget for Phase 2. Same activity, dual return.
- No competitor can replicate proprietary Mumbai campaign performance data.

---

## Campaign Architecture

### Two-Track System

```
ACQUISITION (New Customers)
  ├─ #1 Instagram Reels  — Environmental Expectation   — ROI: +15–25%
  ├─ #2 Zomato/Swiggy   — Social Proof                — ROI: +25–60%
  └─ Not Recommended     — Facebook Ads (generic, low signal)
                         — YouTube Shorts (most venues; nightlife exception)

RETENTION (Existing Customers)
  ├─ PRIMARY   WhatsApp Broadcast — Habit Formation    — ROI: +30–40%
  ├─ SECONDARY Email              — Habit Formation    — ROI: +15–25%
  └─ TERTIARY  SMS                — FOMO/Urgency       — ROI: +10–15%
```

### Channel Priority Logic

**Why Instagram Reels #1 for acquisition:**
- Polynovea controls the content — data-driven framing, not ego-driven
- Instagram Collab means venue's followers see it without venue doing anything
- 6.5x higher engagement than static posts (Meta-published)
- Builds Polynovea's audience simultaneously
- Environmental Expectation: pre-visit visuals shape what customers expect to find

**Why Zomato/Swiggy #2 for acquisition:**
- Platform-native discovery — venue shows up when diners are actively searching
- Social Proof mechanism: ratings, reviews, crowd signals reduce perceived risk
- 25–60% order uplift during featured/promoted periods (platform-reported)
- Venue action checklist (no API needed — venue uses their own Zomato for Business dashboard)
- Optional data opt-in: venue can voluntarily share Zomato/Swiggy export → stored in `venue_platform_data` → adds refinement to future recommendations. If they don't share, base recommendations are unaffected.

**Why Facebook Ads are NOT RECOMMENDED:**
- Generic targeting: no behavioral signal, no archetype alignment
- Higher CPM with lower conversion than Instagram for hospitality
- Algorithm favors broad reach over deep engagement
- Polynovea's intelligence advantage is wasted on demographic-only targeting

**Why YouTube Shorts is NOT RECOMMENDED for most venues:**
- TikTok is banned in India — YouTube Shorts is the closest equivalent
- Lower engagement density than Instagram Reels for restaurant content
- Exception: high-energy nightlife venues where behind-the-scenes content can go viral

**Why WhatsApp is PRIMARY for retention:**
- 85–95% open rate (vs email's 18–28% in India)
- 3–5x ROI on repeat visit campaigns
- +40% repeat visit rate from weekly habit-formation broadcasts
- Direct, personal, conversational — matches how Mumbai diners actually communicate

---

## Behavioral Mechanisms

### 1. Environmental Expectation (Atmospheric Cues)

**What it is:** Pre-visit visual content shapes what customers expect to find. Quality imagery sets accurate expectations → higher satisfaction → more repeat visits.

**Primary channel:** Instagram Reels (Polynovea creates + posts)

**Target archetypes:** Calm Pairs, Discovery Explorers, Premium Prioritizers, Office Workers

**ROI benchmarks:**
- Instagram Reels active program: +15–25% engagement (6.5x vs static posts)
- Platform photo optimization (Zomato/Swiggy): +25–60% during featured periods

**Campaign execution (Polynovea):**
- Publish 3–4 Reels/week (algorithm rewards consistency)
- Focus on: signature dish reveal, ambience walkthrough, crowd energy, behind-the-scenes
- Trending audio + venue-appropriate vibe alignment
- Tag venue as collaborator → appears on both feeds
- Cross-post to Facebook Reels for extended reach at zero extra effort
- Best times: 6–10pm peak mobile browsing

**Message framing (Acquisition):**
```
[Reel caption]
"Where would you sit? 👀"
"Come experience..."
[Ambience shot / signature dish reveal / crowd moment]
→ Link in bio to booking
```

**Zomato/Swiggy action checklist (consultant gives venue):**
```
□ Upload 15–20 photos: food quality + ambience + seating variety
□ Prioritize: signature dishes, group seating, mood lighting
□ Update photos within 30 days of menu changes
□ Respond to all customer photo uploads within 2 hours
```

**Research basis:** Instagram Reels engagement 6.5x static (Meta published). Zomato algorithm: recency + photo quality + star rating. 73% of diners check venue photos before booking (platform guidance).
**Confidence:** MEDIUM-HIGH (Meta data published; Zomato case studies vendor-reported)

---

### 2. Social Proof (Crowd Psychology)

**What it is:** Customers assume a venue is good when they see others choosing it. Ratings, reviews, and crowd signals reduce perceived risk.

**Primary channel:** Zomato/Swiggy platform (venue's own dashboard)

**Target archetypes:** Discovery Explorers, Calm Pairs, Office Workers

**ROI benchmarks:**
- Zomato/Swiggy featured placement: +25–60% order uplift during visibility window
- 4.5+ star rating: material increase in click-to-booking conversion
- Instagram UGC carousel: +8–12% engagement for casual discovery

**Campaign execution (consultant delivers to venue):**
```
Zomato/Swiggy checklist:
□ Monitor rating continuously — address negative reviews within 24h
□ Use platform's promoted placement during lunch (11am–3pm) and dinner (6pm–11pm)
□ Invest in photos: food quality is the #1 platform ranking signal
□ Enable Dineout for additional visibility layer

Instagram social proof (Polynovea executes):
→ UGC carousel: "340 people dined with us last week" post
→ Feature review quotes in Stories
→ Show rating badge in posts when 4.5+
```

**Zomato/Swiggy data (additive refinement):**
When a venue opts in and shares their Zomato for Business dashboard export, data goes into `venue_platform_data`:
- Current rating + 30-day delta
- Monthly covers, peak day/hour
- Photo count + last update date
- Dineout enabled status

This adds refinement to recommendations (e.g., "your rating dropped 0.3 points — prioritise review response"). Absent data = same base recommendations. Never blocked.

**Research basis:** Spice Advisors: Zomato/Swiggy sponsored placement 25–60% uplift. SevenRooms: review visibility increases booking confidence.
**Confidence:** MEDIUM-HIGH

---

### 3. Habit Formation (Temporal Anchoring)

**What it is:** Customers repeat behaviour on specific days/times. Regular reminders reinforce the routine.

**Primary channel:** WhatsApp Broadcast

**Target archetypes:** Repeat Regulars, Trusted Regulars, Habit Formers

**ROI benchmarks:**
- WhatsApp weekly broadcasts: +30–40% repeat visits
- Email triggered campaigns: +15–25% repeat visits
- SMS pre-visit (2h before): +10–15% same-day confirmations

**Campaign execution (Polynovea writes, venue sends from their own WhatsApp):**
```
WhatsApp message template (PRIMARY):
"Hi [Name]! 👋
Your Friday lunch spot is ready for you at [Venue Name]
📍 [Location] | 🕐 [Time]
Book now: [link]"

Email template (SECONDARY):
Subject: "Your [Day] [Time] at [Venue Name] 🍽️"
Body: "Hey [Name], your favourite spot is ready."

SMS template (TERTIARY — same-day only):
"[Venue]: Your usual table is free today at [time].
Book: [link]"
```

**Channel hierarchy (retention):**
1. **WhatsApp** — weekly or bi-weekly broadcasts to known repeat customers. Conversational tone. Allow replies. 85–95% open rate.
2. **Email** — for deeper storytelling, menu updates, loyalty value. Send Tuesday for Friday patterns. 18–28% open rate in India.
3. **SMS** — last-minute confirmations only (2 hours before). Keep under 160 chars. 98% open rate.

**Research basis:** Waakif WhatsApp playbook: 85–95% open rates, 40% repeat improvement. Reelo.io: Indian restaurants targeting 60–70% retention; top performers reach 75–80%.
**Confidence:** MEDIUM (vendor-reported ROI; industry consensus on open rates)

---

### 4. FOMO (Fear of Missing Out)

**What it is:** Scarcity + time pressure triggers urgency and immediate action. Works best for event-driven and high-energy venues.

**Primary channel:** WhatsApp / SMS for events; Instagram Stories for awareness

**Target archetypes:** Party Seekers, Discovery Explorers

**ROI benchmarks:**
- SMS scarcity campaigns: +15–25% same-week bookings (2–4 hour conversion window)
- WhatsApp event broadcasts: +12–20% attendance
- Instagram Stories + countdown: +8–15% for nightlife venues

**Campaign execution (Polynovea creates assets, venue sends WhatsApp/SMS):**
```
WhatsApp event broadcast:
"🎉 Last [X] spots!
Tonight at [Venue]: [Event Name]
📍 [Location] | 🕐 [Time]
Book now: [link] — [hours]h left ⏱️"

Instagram Story (Polynovea posts via Collab):
Visual: DJ announcement / crowd photo / cocktail shot
Text overlay: "Only 2 hours | [X] spots left"
→ Countdown sticker
```

**Research basis:** SMS open rates ~98% (industry vendors). WhatsApp FOMO effectiveness from Zomato case studies (25–35% scarcity badge uplift).
**Confidence:** MEDIUM

---

### 5. Identity Signaling (Status Positioning)

**What it is:** Venue selection projects desired identity. Premium positioning influences high-income and status-conscious customers.

**Primary channel:** Instagram (aesthetic consistency, premium positioning)

**Target archetypes:** Premium Prioritizers, Calm Pairs (upscale segment), Lifestyle Regulars

**ROI benchmarks:**
- Instagram premium positioning: +10–15% awareness among target demographics
- Premium framing in Reels: +12–18% conversion for fine-dining / upscale venues

**Campaign execution (Polynovea):**
```
Instagram Reel / post:
"Curated dining for those who appreciate the finer things
4.7⭐ | Reserve your moment"
Visual: Premium food photography, intimate ambience, wine programme
→ Collaborator tag on venue
```

**Research basis:** Identity signaling effectiveness from Thanx and SevenRooms CDP case studies. Instagram dominance for premium brands from platform demographics.
**Confidence:** MEDIUM

---

## Optional Data Sources (Additive Refinement)

All optional. None gate any base recommendation.

| Source | Table | What It Adds | When Available |
|--------|-------|-------------|----------------|
| Zomato/Swiggy opt-in | `venue_platform_data` | Rating trend, cover counts, peak hours, photo score, Dineout status | Venue shares export voluntarily |
| POS data | `venue_pos_summary` | Revenue per cover, repeat rate, customer LTV, peak day/hour | Module 3 field work |
| Campaign performance | Phase 2 tables | Real ROI vs predicted, attribution by channel | Phase 2 ad integrations |
| Module 3 field data | TBD | Real-time behavioral validation | Module 3 launch |

**How opt-in works (Zomato/Swiggy):**
- During Module 2 consulting engagement, consultant asks: "Would you be willing to share your Zomato for Business dashboard export with us?"
- If yes → venue exports CSV → Polynovea loads into `venue_platform_data`
- This adds platform-specific signal: "your rating dropped 0.3 in 30 days, push more review responses before we run the social proof campaign"
- If no → base recommendations are identical. Zero impact.

**How POS data works:**
- Module 3 field work will establish POS integration per venue
- When available, data flows into `venue_pos_summary`
- Enables: revenue-per-cover modelling, actual repeat rates, CLV per segment
- Absent: fitness dimensions + behavioral patterns give equivalent directional signal

---

## Database Schema (Phase 1 — Complete)

```
behavioral_mechanism_catalog    5 rows   — mechanism descriptions, key triggers, best channels
channel_mechanism_mapping       25 rows  — effectiveness scores, ROI ranges, primary use case
campaign_templates              13 rows  — message templates per segment × mechanism × channel
```

### Channel Priority Reference (from `channel_mechanism_mapping`)

| Channel | Mechanism | Use Case | Effectiveness (1–10) | ROI Range |
|---------|-----------|----------|---------------------|-----------|
| instagram_reels | environmental_expectation | acquisition | 9 | +15–25% |
| zomato_swiggy | social_proof | acquisition | 8 | +25–60% |
| whatsapp_broadcast | habit_formation | retention | 9 | +30–40% |
| email | habit_formation | retention | 7 | +15–25% |
| sms | fomo | retention | 7 | +10–15% |
| youtube_shorts | environmental_expectation | acquisition | 5 | +8–15% (nightlife only) |
| facebook_ads | social_proof | acquisition | 3 | +2–5% (not recommended) |

*(Note: TikTok is banned in India. YouTube Shorts is the closest equivalent but lower priority for most venue types.)*

### `campaign_templates` Structure

```sql
campaign_templates
├─ template_id (PK)
├─ demographic_segment    -- office_workers, college_kids, couples, families, premium
├─ target_archetype       -- Party Seeker, Calm Pairs, Habit Former, Trusted Regular, etc.
├─ behavioral_mechanism   -- habit_formation, fomo, social_proof, identity_signaling, environmental_expectation
├─ channel                -- instagram_reels, zomato_swiggy, whatsapp_broadcast, email, sms, youtube_shorts
├─ message_template       -- template text with {{variables}}
├─ suggested_roi_lift_min
├─ suggested_roi_lift_max
├─ research_confidence    -- LOW | MEDIUM | HIGH
├─ why_it_works           -- plain-English explanation for consultant to show client
└─ implementation_notes   -- Polynovea execution notes
```

### Optional Scaffold Tables (Phase 1 — Empty Until Populated)

```sql
venue_platform_data      -- Zomato/Swiggy opt-in: rating, covers, peak hours, photo_count, dineout_enabled
venue_pos_summary        -- POS: revenue, covers, repeat_customer_rate, customer_lifetime_value
platform_performance_benchmarks  -- City-level aggregates from opt-in data
```

### Phase 2 Tables (Future — Post-Campaign Integration)

```sql
marketing_campaigns         -- Active campaigns per venue
campaign_performance        -- Daily tracking: impressions, clicks, bookings, revenue, ROI
attribution_tracking        -- Per-customer: which campaign brought them
roi_baseline_data           -- Before/after comparison per venue
channel_performance_benchmarks  -- Polynovea's own Mumbai campaign data (the proprietary moat)
```

---

## Marketing Tab UI Specification

### What the Consultant Sees (in Meeting)

**Section 1 — Customer Segments (Polynovea's target audience for this venue)**
```
3 segment cards based on venue_demographic_scores:
  [Office Workers — 42%]   Archetype: Trusted Regular | Visit time: Weekday lunch
  [Families — 31%]         Archetype: Habit Former    | Visit time: Weekend dinner
  [Couples — 18%]          Archetype: Calm Pairs      | Visit time: Weekend evening
```

**Section 2 — ACQUISITION (New Customers)** — `NEW CUSTOMERS` chip (green)
```
Card 1: Instagram Reels         #1 RECOMMENDED
  Mechanism: Environmental Expectation
  Effectiveness bar: ████████░░  8/10
  ROI: +15–25%
  Why it works for this venue: [personalised from fitness profile]
  Target segments: [Couples, Premium, Office Workers]

Card 2: Zomato/Swiggy           #2 RECOMMENDED
  Mechanism: Social Proof
  Effectiveness bar: ████████░░  8/10
  ROI: +25–60%
  Why it works for this venue: [personalised from fitness profile]
  Action checklist for venue's own dashboard:
    □ Upload 15–20 photos (food + ambience + seating)
    □ Enable Dineout listing
    □ Respond to all reviews within 24h

NOT RECOMMENDED row (dark red background):
  YouTube Shorts — Low group_energy score; not worth the format
  Facebook Ads   — Generic targeting wastes behavioral signal
```

**Section 3 — RETENTION (Existing Customers)** — `EXISTING CUSTOMERS` chip (violet)
```
Card 1: WhatsApp Broadcast       PRIMARY badge
  Mechanism: Habit Formation
  Effectiveness bar: █████████░  9/10
  ROI: +30–40%
  Why it works: [personalised]
  Message template (gold border box):
  ┌─────────────────────────────────────────────────────┐
  │ "Hi [Name]! 👋                                      │
  │  Your Friday lunch spot is ready for you at [Venue] │
  │  📍 [Area] | 🕐 12:30pm                             │
  │  Book now: [link]"                                   │
  └─────────────────────────────────────────────────────┘
  [Copy Template]

Card 2: Email — collapsed by default
  Habit Formation | +15–25%

Card 3: SMS — collapsed by default
  FOMO/Urgency | +10–15%
```

---

## Data Confidence Evolution

| Stage | Confidence | Basis |
|-------|-----------|-------|
| Phase 1 launch | MEDIUM | Vendor benchmarks (SevenRooms, Waakif, Zomato case studies, Meta published data) |
| After 10 campaigns | MEDIUM | Polynovea Mumbai data begins (small sample) |
| After 50 campaigns | HIGH | Polynovea-owned Mumbai venue performance data |
| After 200 campaigns | VERY HIGH | Statistical significance across venue types and segments |

**The competitive moat:** Every campaign Polynovea runs generates proprietary data. After 50 campaigns, `channel_mechanism_mapping.research_confidence` updates from MEDIUM → HIGH for the channels that performed. After 200 campaigns, no competitor who enters Mumbai can replicate 2 years of Polynovea's ground-truth performance data.

---

## Phase 2: Campaign Performance & Attribution

### Status: LATER — Contingent on Data Integration

**Phase 2 launches after:**
- ✅ Phase 1 is live and generating recommendations
- ⏳ Campaign performance pipeline is built (impressions, clicks, bookings)
- ⏳ POS integration from Module 3 is live (venue_pos_summary populated)
- ⏳ Repeat visit tracking is operational (Module 3)
- ⏳ Customer identification links visits across time

### What Changes in Phase 2

```
Same behavioral intelligence foundation
  +
Real campaign data (Polynovea's own campaigns)
  +
POS revenue data (Module 3)
  =
Predicted ROI vs Actual ROI comparison
Model confidence upgrades from MEDIUM → HIGH → VERY HIGH
```

### Phase 2 Dashboard (Consultant Mode)

```
CAMPAIGN PERFORMANCE — [Venue Name]

[Instagram Reels — "Office Lunch Series"]
  Status: ACTIVE (Week 2 of 4)
  Predicted: +18% new lunch covers
  Actual so far: +21% ✓
  Impressions: 12,400 | Engagement: 6.8% | Bookings: 38
  Revenue: ₹24,600 | Cost: ₹3,200 | ROI: 7.7x

[WhatsApp Broadcast — "Friday Habit"]
  Status: ACTIVE (Month 1)
  Predicted: +35% repeat visit frequency
  Actual: +38% ✓✓
  Broadcasts sent: 850 | Open rate: 91% | Click rate: 18%
  Bookings: 89 | Revenue: ₹38,900 | Cost: ₹0 | ROI: ∞
```

---

## Implementation Roadmap

### Phase 1: Campaign Brief Engine (Current)

**Database (COMPLETE):**
- ✅ `behavioral_mechanism_catalog` — 5 mechanisms
- ✅ `channel_mechanism_mapping` — 25 channel × mechanism mappings
- ✅ `campaign_templates` — 13 templates per segment × mechanism × channel
- ✅ `venue_platform_data` scaffold — ready for opt-in data
- ✅ `venue_pos_summary` scaffold — ready for Module 3

**UI (Pending — Screen 4):**
- 🔲 Marketing Tab in Next.js frontend
- 🔲 Segment cards (3 top segments from venue_demographic_scores)
- 🔲 Acquisition cards (Instagram Reels #1, Zomato/Swiggy #2)
- 🔲 Retention cards (WhatsApp PRIMARY, Email, SMS)
- 🔲 Not Recommended row (YouTube Shorts, Facebook Ads)
- 🔲 Message template box with Copy button
- 🔲 Personalised "why this works for you" text from demographic_archetype_interventions

**Backend (Pending):**
- 🔲 `/api/venues/{id}/marketing` endpoint
- 🔲 Campaign brief generation from venue fitness profile
- 🔲 Template personalisation using venue primitives + demographics

### Phase 2: Live Campaign Tracking (Future)

- 🔲 Ads performance pipeline integration
- 🔲 POS data ingestion (Module 3)
- 🔲 Attribution model
- 🔲 Predicted vs actual ROI comparison
- 🔲 Proprietary benchmark table population
- 🔲 Confidence upgrade from MEDIUM → HIGH

---

## Campaign Scenarios

### Scenario A — Office Lunch Venue (Repeat Regulars)

**Venue profile:** High office_lunch fitness (0.78), high repeat_habit (0.82), low group_energy (0.21)
**Primary segment:** Office Workers (42%), Families (31%)

**Polynovea campaign brief:**
```
ACQUISITION:
  Instagram Reels — Environmental Expectation
    Content: Weekday lunch service, quick bites, efficient flow, quality food
    Collab: Tag venue → reaches 3,200 followers
    Expected lift: +18% new lunch covers
    Not recommended: YouTube Shorts (wrong energy for this venue type)

RETENTION:
  WhatsApp Broadcast (PRIMARY) — Habit Formation
    Template: "Your Friday lunch spot is ready, [Name] 👋 Book: [link]"
    Send: Tuesday 10am (3 days before the habitual Friday visit)
    Expected lift: +35% repeat visit frequency

  Email (SECONDARY)
    For: Menu updates, loyalty recognition, new seasonal items
    Send: Wednesday for Friday patterns
    Expected lift: +18%
```

### Scenario B — Weekend Party Venue (Party Seekers)

**Venue profile:** High group_energy (0.87), high social_dwell (0.79), low office_lunch (0.12)
**Primary segment:** College Kids (55%), Premium (25%)

**Polynovea campaign brief:**
```
ACQUISITION:
  Instagram Reels — Environmental Expectation + FOMO
    Content: DJ lineup, crowd energy, dance floor, signature cocktail moments
    Collab: Tag venue → reaches 8,900 followers (nightlife audience)
    Expected lift: +22% new weekend bookings

  Zomato/Swiggy — Social Proof
    Action: Venue enables Dineout, promoted placement Thu–Sun 6–11pm
    Expected lift: +35% platform-attributed bookings

RETENTION:
  WhatsApp Broadcast — FOMO
    Template: "Last [X] spots tonight at [Venue] — [Event] 🔥 [link]"
    Send: Friday 2pm (creates urgency before evening rush)
    Expected lift: +25% same-day confirmations
```

### Scenario C — Intimate Dining (Calm Pairs)

**Venue profile:** High destination_visit (0.81), high retention_strength (0.76), low group_energy (0.18)
**Primary segment:** Couples (52%), Premium (28%)

**Polynovea campaign brief:**
```
ACQUISITION:
  Instagram Reels — Identity Signaling + Environmental Expectation
    Content: Plated dishes, mood lighting, intimate table setups, wine programme
    Tone: "Curated dining for those who appreciate the finer things"
    Collab: Tag venue → reaches 2,100 followers (premium audience)
    Expected lift: +15% new bookings among premium segment

  Zomato/Swiggy — Social Proof
    Action: 4.6+ rating protection, premium photo set, Dineout enabled
    Expected lift: +40% on platform conversion

RETENTION:
  WhatsApp VIP Broadcast — Identity Signaling
    Template: "Your table is waiting, [Name]. New tasting menu this weekend 🍷"
    Segment: High-spend repeat customers only
    Expected lift: +20% premium package adoption
```

---

## Key Metrics

### Phase 1 Success Criteria
- Campaign briefs feel relevant to consultant: >80% of venues have personalised "why this works"
- WhatsApp template copy rate: >50% of venues copy at least one template
- Zomato/Swiggy checklist completion: >40% of venues complete top 3 actions

### Phase 2 Success Criteria
- Predicted vs actual ROI variance: <10 percentage points
- Email campaigns: beat prediction by +4–8pp
- Instagram Reels: meet/beat prediction by +0–2pp
- WhatsApp: meet prediction within ±5pp
- After 50 campaigns: research_confidence upgraded to HIGH for top channels

---

## Version Control

- v1.0 — Initial framework (venue-owner DIY framing) — 2026-05-14
- v2.0 — Complete rewrite: Polynovea execution model, Instagram Collab, audience flywheel, correct channel priorities, YouTube Shorts replacing TikTok, "never gate an insight" principle, Zomato/Swiggy as additive opt-in — 2026-05-14

---

*Polynovea executes. The venue collaborates. The data is ours.*
