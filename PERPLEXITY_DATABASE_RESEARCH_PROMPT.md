# Perplexity Research Prompt: PostgreSQL Hosting Comparison

**For:** Polynovea Module 2 (Behavioral Intelligence Platform)  
**Database Needs:** PostgreSQL with moderate scale (500-2000 venues, 45K+ survey responses, behavioral analysis)  
**Budget:** $1000 credits available across Azure, AWS, Supabase  
**Timeline:** Starting MVP (4 cities in India), scaling to multiple domains + cities

---

## Research Prompt for Perplexity

```
Compare PostgreSQL database hosting for a behavioral intelligence startup:

CONTEXT:
I'm building Polynovea, a behavioral intelligence platform starting with Indian hospitality venues (4 cities, ~500-2000 venue profiles). I have $1000 in credits split across Azure, AWS, and Supabase.

Database specs:
- PostgreSQL required (migrations already written)
- Initial data: ~45 survey responses, ~1000 venues, ~10K reviews for analysis
- Feature database tables: 40+ tables (behavioral patterns, user archetypes, venue profiles, campaign templates, etc.)
- Concurrent users: Low (5-20 simultaneous for MVP; scaling to 100-500+ later)
- Query patterns: Mix of OLTP (user/venue lookups) and OLAP (analytics queries on primitives, pattern matching)
- Expected growth: Will add 2 more data sources (Zomato, MagicPin) and expand to other domains (art, finance, aerospace)

RESEARCH QUESTIONS:

1. FREE TIER COMPARISON (for 2026):
   - Azure Database for PostgreSQL: What free tier exists? Duration? Storage/compute limits?
   - AWS RDS for PostgreSQL: Free tier limits (12 months free - what exactly is included)?
   - Supabase PostgreSQL: Free tier specs (I read 500MB storage - is that current? What about API limits)?
   - Which free tier would last longest for a startup with my data volume?

2. PRICING BREAKDOWN (When free tier expires):
   - Estimate monthly cost for each platform at: 100GB storage, 10GB/month egress, 500K queries/month
   - What does $1000 in credits buy on each platform? (How many months of usage?)
   - Which platform's credits depreciate slowest (best value retention)?

3. CREDIT ELIGIBILITY & TERMS:
   - Azure: Are startup credits eligible for Database for PostgreSQL? Any restrictions?
   - AWS: Can RDS be paid with free tier credits? (I know compute is free; databases are separate)
   - Supabase: Do they have startup credits program? Can credits be applied to paid tiers?

4. SCALING PATH (6-18 months out):
   - Which platform scales smoothest from 100GB → 1TB (as I add Zomata/MagicPin/other sources)?
   - Cost difference at 500GB? At 2TB?
   - Reserved instance or commitment discounts available on each?

5. DEVELOPER EXPERIENCE (for indie/small team):
   - Which platform has best migration tooling (I have PostgreSQL dump files ready)?
   - Best API/SDK support for Python (my primary language)?
   - Easiest backup/disaster recovery setup for startup (low ops overhead)?

6. LOCK-IN RISK:
   - Can I export full PostgreSQL dump from each platform without vendor lock-in?
   - Are there any platform-specific features I should avoid (to keep future portability)?
   - Migration friction if I move from one to another later?

PREFERRED ANSWER FORMAT:
Create a comparison table with:
- Platform | Free Tier Duration | Free Tier Capacity | Cost After Free | My Estimated 6-Month Cost | Credit Longevity | Scaling Path | Recommendation for Stage
- Include specific month/year when free tier expires (2026 terms)
- Highlight which platform's $1000 credit goes furthest
- State confidence level (HIGH if official 2026 pricing available, LOW if extrapolated)

FOCUS ON: India-based startup context (Azure/AWS may have local pricing; Supabase global pricing).
```

---

## Key Decision Factors for Your Situation

| Factor | Why It Matters |
|--------|---|
| **Free tier duration** | MVP phase is 2-3 months; you want free tier to cover that |
| **Credit applicability** | Some platforms restrict credits to compute-only; need credit for DB costs |
| **Scalability path** | You'll go from 45 responses → 50K+ responses (Zomato/MagicPin/other domains) in 6-12 months |
| **Lock-in** | Your backend code should work on any PostgreSQL; avoid vendor proprietary features |
| **Developer velocity** | You want simple setup so you can focus on algorithms, not DevOps |

---

## Why This Matters for Phase 1-3

**Phase 1 (NOW - Weeks 1-3):**
- Build 40+ tables (demographic segments, campaign templates, behavioral patterns, etc.)
- Load 45 survey responses + 1000 venue profiles + patterns from step_4/step_5 JSON files
- Query load: Low (testing, internal tools)
- Storage: <10GB

**Phase 2 (3-4 weeks):** 
- Same schema; add live campaign performance tracking
- Query load: Moderate (web dashboard queries)
- Storage: 10-20GB

**Phase 3 (3+ months):**
- Add Zomata/MagicPin data sources (10x data volume)
- Query load: Moderate-High (real users on platform)
- Storage: 100-200GB

**Later (Months 6+):**
- Expand to other domains (art, finance, aerospace)
- Query load: High (production platform)
- Storage: 500GB-2TB

**Budget Implication:** You want a database that stays cheap at Phase 1-2 scale but doesn't surprise you with skyrocketing costs at Phase 3+ scale.

---

## Recommendation Framework (After Research)

Once Perplexity returns data, evaluate using this rubric:

```
SCORING (Higher = Better for You):

Free Tier:
  +3 points if free tier covers full Phase 1-2 (8-12 weeks)
  +1 point per month of free tier beyond that
  
Credit Value:
  +3 if $1000 credit covers 6+ months of production use
  +1 per additional month covered
  
Developer Experience:
  +2 if Python ORM + API support strong
  +2 if migration tools built-in
  +1 if backup/recovery simple
  
Scaling:
  +2 if smooth scaling to 500GB range
  +2 if pricing remains competitive at 100GB-1TB range
  +1 if reserved instance discounts available
  
Lock-in:
  +3 if pure PostgreSQL (zero lock-in)
  +1 if some platform-specific features but exportable
  -2 if significant vendor lock-in
  
DECISION RULE:
  Score ≥ 13 = Recommended
  Score 10-12 = Good if credit longevity high
  Score < 10 = Risky for indie/startup
```

---

## Before Running This Prompt

**You'll want to tell Perplexity:**
- "Focus on 2026 pricing and free tier terms (not 2023-2025 data)"
- "Include India region pricing if available (Azure/AWS) or global pricing (Supabase)"
- "I'm a startup with $1K total credits; assume startup rate or open-source discount eligibility if applicable"
- "Assume moderate growth (not hypergrowth); don't optimize for unicorn-scale scenarios"

---

## Once You Have the Research

I'll help you:
1. Create a decision matrix with actual numbers
2. Map which platform aligns best with your deployment timeline
3. Document your choice in the handover file (as part of infrastructure decisions)
4. Prepare migration scripts if you need to switch later

---

**Next Step:** Run the prompt above with Perplexity, then share the findings so we can pick the best option.
