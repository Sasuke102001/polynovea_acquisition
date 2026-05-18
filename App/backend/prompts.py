"""
prompts.py
AI chat system prompt builder for Polynovea venue intelligence.

Research is loaded once at import from project-root .md files.
Venue-specific context (segments, fitness, behavioral profiles, channel data)
is passed in dynamically from fetch_venue_context in chat.py.

When someone asks "why does this work?" or "what is the theory behind X?"
the AI draws on the full research text. When someone asks "what should I do
for this venue?" it draws on the venue-specific DB data.
"""

import pathlib

# ─── Research file loader ─────────────────────────────────────────────────────

_BACKEND_DIR  = pathlib.Path(__file__).parent            # App/backend/
_PROJECT_ROOT = _BACKEND_DIR.parent.parent               # project root
_RESEARCH_DIR = _PROJECT_ROOT / "research"               # research/


def _load(filename: str) -> str:
    path = _RESEARCH_DIR / filename
    try:
        return path.read_text(encoding="utf-8")
    except Exception:
        return f"[{filename} not found — place file in research/ folder]"


# Full research documents — loaded once at startup
_PHASE1_RESEARCH        = _load("PHASE_1_INDIA_BEHAVIORAL_RESEARCH.md")
_MARKETING_FRAMEWORK    = _load("MARKETING_ENGINE_FRAMEWORK.md")
_BEHAVIORAL_RESEARCH    = _load("behavioral_acquisition_mechanisms_hospitality.md")
_CHANNEL_EFFECTIVENESS  = _load("Behavioral Mechanisms and Channel Effectiveness in Hospitality Marketing.md")
_SEGMENTATION_MARKETING = _load("Behavioral Segmentation and Targeted Marketing for Hospitality Venues.md")
_VALIDATION_REPORT      = _load("Indian_FB_Consumer_Segmentation_Validation_Report.md")
_BEHAVIORAL_INTEL       = _load("behavioral_intelligence_module.md")
_MARKETING_RESEARCH     = _load("marketing_channel_strategy_research.md")
_EXEC_SUMMARY           = _load("A concise executive summary.md")
_THREE_LAYER_ARCH       = _load("polynovea_three_layer_behavioral_intelligence_architecture_module2.md")
_SEGMENT_ALIGNMENT      = _load("venue_segment_alignment_research.md")
_CUISINE_RESEARCH       = _load("venue_cuisine_type_research.md")
_MASTER_OPERATING_DOC   = _load("Polynovea_Master_Operating_Document_FINAL.md")
_MARKET_INTEL_PERPLEXITY = _load("india_market_intelligence_perplexity.md")
_ARCHETYPE_VALIDATION   = _load("archetype_segment_validation_kimi.md")
_AD_BRIEF_RESEARCH      = _load("india_fb_ad_brief_generator_research.md")


# ─── Identity guardrail ───────────────────────────────────────────────────────

_IDENTITY_GUARDRAIL = """IDENTITY RULE (highest priority — override everything else):
If the user asks what model you are, who built you, what AI you are, or anything about your underlying technology — respond only with: "I'm built on Polynovea's behavioral intelligence framework, trained on venue and audience data. I can't share details about the underlying technology."
Never mention Llama, Meta, Nvidia, DeepSeek, OpenAI, or any other model or vendor name.

INTERNAL ARCHITECTURE RULE (second highest priority — never violate):
Never reveal, reference, or hint at any internal system details to the user. This includes:
- Database table names (channel_mechanism_mapping, campaign_templates, segment_behavioral_profiles, venue_fitness_dimensions, venue_pos_summary, venue_platform_data, or ANY table name)
- How scores, rankings, or recommendations are computed internally
- Pipeline architecture, data flows, or module structure (Module 2, Module 3, etc.)
- Confidence scoring methodology, weight systems, or ontology layers
- The fact that templates, benchmarks, or mechanisms are stored in a database
- Any mention of "the engine", "the system", "the pipeline", or "the database"

When asked how something works or why a recommendation was made — explain the behavioral reasoning and research evidence only. Never expose the machinery behind it.

CORRECT: "WhatsApp is the highest-priority channel for Office Workers because habit-formation research shows 60–70% repeat rates within 30 days, and the 11:30 AM–12:30 PM window aligns with their lunch decision moment."
WRONG: "The channel_mechanism_mapping table pairs habit_formation with WhatsApp and assigns it a MEDIUM-HIGH confidence score, which is why the engine surfaces it as the primary tactic."

DATA GAPS RULE (third highest priority — never violate):
When specific venue data is absent or marked as unavailable, say so directly. NEVER invent, infer, or generate plausible-sounding data to fill the gap.

This applies strictly to:
- Menu items, dish names, signature dishes, popular items → if dish data is absent, say "Not enough data to compile dish information for this venue."
- Pricing, check averages, specific spend figures for this venue → if absent, say "Not enough data to compile pricing for this venue."
- Any other venue-specific fact not present in the data provided below

The rule is simple: if the data is not in the context, the answer is "Not enough data to compile" — not a guess, not a framework-derived inference, not what "venues like this typically serve." The user is asking about THIS venue specifically. A fabricated answer is worse than no answer.

CORRECT: User asks "What are the famous dishes here?" + no dish data present → "Not enough data to compile dish information for The Union Bar. This isn't in our current dataset for this venue."
WRONG: Generating Chicken Tikka Masala, Party Platters, or any other dish names based on the venue type or behavioral profile.

"""

# ─── Segment psychological research ──────────────────────────────────────────
# Core behavioral insights per segment — grounding for all AI responses

_SEGMENT_RESEARCH = """
SEGMENT BEHAVIORAL INTELLIGENCE (use this to inform all answers):

Office Workers (26–35, weekday lunch, solo or pairs):
- Primary driver: time efficiency. Lunch window is 30 min. Speed + reliability = loyalty.
- WhatsApp works 11:30 AM–12:30 PM weekdays. Instagram discovery happens during commute.
- Copy trigger: "No waiting. No wondering." — eliminate decision friction.
- Habit loop: same table, same order, same time. Disruption = lost customer.

Couples (23–38, weekend evenings, destination dining):
- Primary driver: experience quality + emotional memory. The evening must feel curated.
- 57% influenced by ambiance photos. Corner table + soft lighting = conversion.
- WhatsApp: 1–2x/week max. Over-messaging triggers opt-out.
- Copy trigger: "Not a dinner. An evening." — sell the feeling, not the food.

Families (all ages, weekends, 3–6 people):
- Primary driver: predictability + safety. No surprises. Kids must be accommodated.
- 35+ parents have low Instagram usage. Weekend decisions are habit/repeat, not discovery.
- WhatsApp 10 AM–12 PM Sunday = peak decision window.
- Copy trigger: "Same table, same friendly faces." — routine is the product.

Social Crowd / College Kids (18–30, weekend evenings, groups 3+):
- Primary driver: social proof + FOMO. 90% Gen Z daily Instagram. 72% discover via Reels.
- Group coordination on WhatsApp possible. High peer influence coefficient.
- Copy trigger: "Your entire gang's already here." — social proof before details.
- Viral format: fast cuts, crowd energy, beat drops. Not slow-paced content.

Premium Diners (30–50, any day, high spend):
- Primary driver: exclusivity + status signaling. Veblen effect — visible high-end consumption.
- Email newsletter for culinary content. WhatsApp for VIP event invitations only.
- Copy trigger: "For those who don't need to ask." — implied exclusivity.
- Avoid: promotional language. They buy experience, not discounts.

Solo Diners (22–40, weekday lunch/evening, solo):
- Primary driver: inconspicuousness + autonomy. No pity, no questions, no pressure.
- Low broadcast engagement. Transactional relationship only.
- Copy trigger: "No questions, no pity, just your dish and your peace."

Working Women (24–38, weekday lunch, safe comfortable spaces):
- Primary driver: safety + comfort. Well-lit entrance, all-women staff signal = high trust.
- TRAI DND restrictions on promotional SMS. WhatsApp preferred 12–1 PM weekdays.
- Copy trigger: "Lunch hour is your hour." — ownership, not invitation.
"""

# ─── Polynovea execution context ─────────────────────────────────────────────

_POLYNOVEA_CONTEXT = """
POLYNOVEA CONTEXT:
Polynovea is a behavioral intelligence and growth systems company operating in Mumbai/MMR.
The core foundation is AI, data, and behavioral intelligence infrastructure — not event management.

Live entertainment (acoustic sessions, indie nights, jazz evenings, unplugged sets) is a
deployment surface — a controlled, measurable environment used to generate behavioral data,
influence audience dynamics, and produce measurable revenue outcomes for partner venues.

What Polynovea executes on behalf of partner venues:
- Books artists, manages show logistics (live entertainment as a behavioral lever)
- Creates Instagram content (event posts + performance Reels; seating area only)
- Runs Meta (Instagram + Facebook) and Google ads targeting the venue's primary audience
- Sends WhatsApp broadcast campaigns to the venue's customer database
- Provides this venue intelligence platform (Module 2 — behavioral intelligence layer)

The intelligence this platform provides (segment scoring, fitness dimensions, competitor
analysis, channel effectiveness) is Module 2 of the Polynovea intelligence infrastructure.
It converts behavioral signals from reviews, platform data, and venue metadata into
operational decision intelligence — not just dashboards.

What Polynovea does NOT do:
- Menu, pricing, staffing, or operational decisions (venue's domain)
- General social media management beyond show-related content
- Content outside the performance zone of the venue
- POS or financial data analysis (that is Module 3, not yet deployed)
"""


# ─── Segment profile formatter ────────────────────────────────────────────────

def _fmt_seg_profiles(profiles: list[dict]) -> str:
    if not profiles:
        return "  [No behavioral profile data — run 016_load_audience_profiles.py]"
    lines = []
    for p in profiles:
        seg_id   = p.get("segment_id", "")
        label    = p.get("label") or p.get("name", seg_id)
        rank     = p.get("rank", "?")
        align    = p.get("alignment_score", 0)
        lines.append(
            f"\n  [{rank}] {label} — {align:.0%} alignment"
        )
        if p.get("food_pct"):
            lines.append(
                f"      Spend: food {p['food_pct']}  |  alcohol {p.get('alcohol_pct','—')}  |"
                f"  dessert attach {p.get('dessert_pct','—')}"
            )
        if p.get("check_vs_baseline"):
            lines.append(f"      Check vs baseline: {p['check_vs_baseline']}")
        if p.get("alcohol_affinity"):
            lines.append(
                f"      Alcohol: affinity={p['alcohol_affinity']}  driver={p.get('alcohol_driver','—')}"
                f"  preference={p.get('beverage_preference','—')}"
            )
        if p.get("peer_influence") is not None:
            lines.append(f"      Peer influence coefficient: {p['peer_influence']}")
        if p.get("dwell"):
            lines.append(
                f"      Dwell: {p['dwell']}  |  RevPASH {p.get('revpash','—')}"
                f"  |  diminishing returns at {p.get('diminishing_returns_min','—')} min"
            )
        if p.get("repeat_tendency"):
            lines.append(
                f"      Repeat: {p['repeat_tendency']} within {p.get('repeat_window_days','—')} days"
                f"  |  WOM multiplier {p.get('wom_multiplier','—')}"
            )
        if p.get("discovery_rate"):
            lines.append(f"      Discovery rate: {p['discovery_rate']}")
        if p.get("primary_trigger"):
            lines.append(f"      Primary trigger: {p['primary_trigger']}")
        if p.get("spend_trigger"):
            lines.append(f"      Low→high spend trigger: {p['spend_trigger']}")
        if p.get("archetypes"):
            lines.append(f"      Top archetypes: {', '.join(p['archetypes'])}")
        if p.get("discovery_platforms"):
            lines.append(f"      Primary discovery platform(s): {', '.join(p['discovery_platforms'])}")
    return "\n".join(lines)


def _fmt_channels(channels: list[dict]) -> str:
    if not channels:
        return "  [No channel data]"
    lines = []
    for c in channels:
        lines.append(
            f"  {c['channel']:<28} mechanism={c['mechanism']:<28} "
            f"effectiveness={c['effectiveness']}/10  "
            f"ROI +{c['roi_min']:.0f}–{c['roi_max']:.0f}%  [{c['use_case']}]"
        )
    return "\n".join(lines)


def _fmt_templates(templates: list[dict]) -> str:
    if not templates:
        return "  [No campaign templates for this segment]"
    lines = []
    for t in templates:
        lines.append(
            f"  Segment={t['segment']}  Archetype={t['archetype']}  Channel={t['channel']}"
            f"  ROI lift ~{t['roi_lift']:.0f}%  Confidence={t['confidence']}"
        )
        if t.get("template"):
            lines.append(f"    Template: {t['template'][:200]}")
    return "\n".join(lines)


def _fmt_interventions(interventions: list[dict]) -> str:
    if not interventions:
        return "  [No intervention data]"
    lines = []
    for i in interventions:
        rec = "✓ RECOMMENDED" if i.get("recommended") else "—"
        lines.append(
            f"  [{i.get('tier','?')}] {i.get('type','')}  fit={i.get('fit_score',0):.2f}  {rec}"
        )
        if i.get("description"):
            lines.append(f"    {i['description'][:180]}")
    return "\n".join(lines)


def _fmt_primitives(primitives: list[dict]) -> str:
    if not primitives:
        return "  [No primitive signal data]"
    lines = []
    for p in primitives:
        bar = "█" * int(p.get("confidence", 0) * 10)
        lines.append(
            f"  {p['signal']:<45} {p['confidence']:.2f}  {bar}"
        )
    return "\n".join(lines)


def _fmt_patterns(patterns: list[dict]) -> str:
    if not patterns:
        return "  [No behavioral pattern data]"
    lines = []
    for p in patterns:
        signals = ", ".join(p.get("signals", [])[:5]) if p.get("signals") else "—"
        lines.append(
            f"  [{p.get('source','?')}] {p['pattern']}  prevalence={p.get('prevalence',0):.1f}%"
        )
        lines.append(f"    Co-occurring signals: {signals}")
    return "\n".join(lines)


def _fmt_drift(drift: list[dict]) -> str:
    if not drift:
        return "  [No drift signal data for this area]"
    lines = []
    for d in drift:
        direction = {"emerging": "↑ EMERGING", "declining": "↓ DECLINING"}.get(
            d.get("direction", ""), d.get("direction", "")
        )
        lines.append(
            f"  {direction:<14} conf={d.get('confidence',0):.2f}  [{d.get('source','?')}]  {d['pattern']}"
        )
    return "\n".join(lines)


def _fmt_dish_signals(dish_signals: list[dict]) -> str:
    if not dish_signals:
        return "  [No dish signal data]"
    lines = []
    for ds in dish_signals[:2]:  # cap at 2 platform blocks
        platform = ds.get("platform", "unknown")
        data     = ds.get("data", {})
        signals  = data.get("dish_signals", data.get("signals", []))
        if signals:
            lines.append(f"  [{platform}]")
            for s in signals[:8]:
                if isinstance(s, dict):
                    lines.append(
                        f"    {s.get('dish','?'):<30} conf={s.get('confidence',0):.2f}"
                        f"  mentions={s.get('mention_count',0)}"
                    )
    return "\n".join(lines) if lines else "  [No dish signal data]"


# ─── Main prompt builder ──────────────────────────────────────────────────────

def build_venue_prompt(
    tab: str,
    venue_name: str,
    venue_type: str,
    area: str,
    city: str,
    top_segments: list[dict],
    top_fitness_dims: list[dict],
    top_competitors: list[dict],
    seg_profiles: list[dict] | None = None,
    channel_effectiveness: list[dict] | None = None,
    campaign_templates: list[dict] | None = None,
    interventions: list[dict] | None = None,
    risk_signals: list[dict] | None = None,
    behavioral_primitives: list[dict] | None = None,
    behavioral_patterns: list[dict] | None = None,
    dish_signals: list[dict] | None = None,
    mechanisms: list[dict] | None = None,
    drift_signals: list[dict] | None = None,
) -> str:

    # ── Basic venue snapshot ────────────────────────────────────────────────
    primary_seg = top_segments[0]["name"] if top_segments else "unknown"
    top_dim     = top_fitness_dims[0]["label"] if top_fitness_dims else "unknown"

    segments_str = "\n".join(
        f"  [{i+1}] {s['name']}: {s['fitness_score']:.1%} alignment"
        for i, s in enumerate(top_segments[:3])
    ) or "  No segment data"

    dims_str = "\n".join(
        f"  {d['label']}: {d['score']:.1%}"
        for d in top_fitness_dims
    ) or "  No fitness data"

    competitors_str = "\n".join(
        f"  {c['name']} ({c['area']}): {c['similarity_score']:.1%} similarity"
        for c in top_competitors[:4]
    ) or "  No competitor data"

    # ── Optional enriched sections ──────────────────────────────────────────
    seg_profiles_str    = _fmt_seg_profiles(seg_profiles or [])
    channels_str        = _fmt_channels(channel_effectiveness or [])
    templates_str       = _fmt_templates(campaign_templates or [])
    interventions_str   = _fmt_interventions(interventions or [])
    primitives_str      = _fmt_primitives(behavioral_primitives or [])
    patterns_str        = _fmt_patterns(behavioral_patterns or [])
    drift_str           = _fmt_drift(drift_signals or [])

    # Dish signals: explicit absence label — prevents the AI from fabricating dish names
    _raw_dish = _fmt_dish_signals(dish_signals or [])
    dish_str = (
        _raw_dish
        if dish_signals
        else "  NOT AVAILABLE — not enough data to compile dish information for this venue. "
             "If asked about menu items, dishes, or what's famous here, respond: "
             "'Not enough data to compile dish information for this venue.'"
    )

    risk_str = ""
    if risk_signals:
        risk_str = "\nRISK SIGNALS:\n" + "\n".join(
            f"  {s['name']}: impact {s['impact']:.2f} ({s.get('confidence','MED')})"
            for s in risk_signals[:5]
        )

    # ── Tab focus ────────────────────────────────────────────────────────────
    tab_focus = {
        "marketing":   "Focus on content strategy, WhatsApp campaigns, channel selection, show promotion, and copy hooks.",
        "competitors":  "Focus on competitive positioning, fitness gaps vs similar venues, and differentiation levers.",
        "transform":    "Focus on segment gaps, fitness dimension improvements, and what it takes to attract a new audience.",
        "deep_risk":    "Focus on churn signals, retention gaps, and behavioral patterns signalling loyalty risk.",
        "overview":     "Focus on overall venue health, what the fitness scores mean, and strategic priorities.",
        "audience":     "Focus on who this venue actually attracts — spend composition, alcohol affinity, dwell, WOM, and platform reach.",
    }.get(tab, "Answer any question about this venue's behavioral data and strategy.")

    return f"""You are Polynovea's venue intelligence AI — an expert with deep knowledge of F&B behavioral psychology, consumer segmentation, channel marketing, and the Mumbai/MMR hospitality market.

CURRENT TAB: {tab.upper()}
{tab_focus}

══════════════════════════════════════════════════════════════════
VENUE DATA (live from database)
══════════════════════════════════════════════════════════════════

VENUE:
  Name     : {venue_name}
  Type     : {venue_type}
  Location : {area}, {city}
  Primary segment: {primary_seg}
  Strongest signal: {top_dim}

SEGMENT ALIGNMENT (demographic fit scores):
{segments_str}

FITNESS DIMENSIONS (operational + behavioral signals):
{dims_str}

SIMILAR VENUES (by segment + type overlap):
{competitors_str}

SEGMENT BEHAVIORAL PROFILES (spend, dwell, loyalty, triggers):
{seg_profiles_str}

CHANNEL EFFECTIVENESS (from research database):
{channels_str}

CAMPAIGN TEMPLATES (for primary segment):
{templates_str}

BEHAVIORAL PRIMITIVES (raw signals from reviews — stimuli, frictions, compensations):
{primitives_str}

BEHAVIORAL PATTERNS (cluster-level patterns this venue belongs to):
{patterns_str}

DISH SIGNALS (menu items driving behavioral responses from review data):
{dish_str}

DRIFT SIGNALS (emerging behavioral trends in this area — act before competitors do):
{drift_str}

STRATEGIC INTERVENTIONS (ranked by fit score):
{interventions_str}{risk_str}

══════════════════════════════════════════════════════════════════
POLYNOVEA ECOSYSTEM ARCHITECTURE & OPERATING DOCTRINE
══════════════════════════════════════════════════════════════════
Use this to understand what Polynovea actually is, what Module 2 is,
how this platform fits into the larger intelligence infrastructure,
and the founding philosophy behind the behavioral intelligence thesis.

{_MASTER_OPERATING_DOC}

══════════════════════════════════════════════════════════════════
SEGMENT PSYCHOLOGICAL INTELLIGENCE (copy triggers, timing, platform behavior)
══════════════════════════════════════════════════════════════════
{_SEGMENT_RESEARCH}

══════════════════════════════════════════════════════════════════
RESEARCH — PHASE 1 INDIA BEHAVIORAL RESEARCH
══════════════════════════════════════════════════════════════════
{_PHASE1_RESEARCH}

══════════════════════════════════════════════════════════════════
RESEARCH — MARKETING ENGINE FRAMEWORK
══════════════════════════════════════════════════════════════════
{_MARKETING_FRAMEWORK}

══════════════════════════════════════════════════════════════════
RESEARCH — BEHAVIORAL ACQUISITION MECHANISMS (academic backbone)
══════════════════════════════════════════════════════════════════
{_BEHAVIORAL_RESEARCH}

══════════════════════════════════════════════════════════════════
RESEARCH — CHANNEL EFFECTIVENESS IN HOSPITALITY MARKETING
══════════════════════════════════════════════════════════════════
{_CHANNEL_EFFECTIVENESS}

══════════════════════════════════════════════════════════════════
RESEARCH — BEHAVIORAL SEGMENTATION & TARGETED MARKETING
══════════════════════════════════════════════════════════════════
{_SEGMENTATION_MARKETING}

══════════════════════════════════════════════════════════════════
RESEARCH — INDIA F&B SEGMENTATION VALIDATION REPORT
══════════════════════════════════════════════════════════════════
Use this to flag corrected claims: SMS open rate ~20% (not 98%),
Reels 2x engagement + 10-50x reach (not 6.5x), archetype caveat.
{_VALIDATION_REPORT}

══════════════════════════════════════════════════════════════════
RESEARCH — SEGMENT & ARCHETYPE BEHAVIORAL INTELLIGENCE MODULE
══════════════════════════════════════════════════════════════════
{_BEHAVIORAL_INTEL}

══════════════════════════════════════════════════════════════════
RESEARCH — MARKETING CHANNEL STRATEGY
══════════════════════════════════════════════════════════════════
{_MARKETING_RESEARCH}

══════════════════════════════════════════════════════════════════
RESEARCH — INDIA F&B CHANNEL BENCHMARKS (EXECUTIVE SUMMARY)
══════════════════════════════════════════════════════════════════
{_EXEC_SUMMARY}

══════════════════════════════════════════════════════════════════
RESEARCH — THREE-LAYER BEHAVIORAL INTELLIGENCE ARCHITECTURE
══════════════════════════════════════════════════════════════════
{_THREE_LAYER_ARCH}

══════════════════════════════════════════════════════════════════
RESEARCH — VENUE SEGMENT ALIGNMENT & SCORING WEIGHTS
══════════════════════════════════════════════════════════════════
{_SEGMENT_ALIGNMENT}

══════════════════════════════════════════════════════════════════
RESEARCH — CUISINE PREFERENCES BY SEGMENT
══════════════════════════════════════════════════════════════════
{_CUISINE_RESEARCH}

══════════════════════════════════════════════════════════════════
RESEARCH — INDIA F&B MARKET INTELLIGENCE (PERPLEXITY, 2025–26)
══════════════════════════════════════════════════════════════════
Hard numbers: Mumbai spend ₹877/visit, RevPASH bands, WhatsApp/SMS/Reels
benchmarks, micro-influencer costs, platform behavior matrix by segment.
Treat figures flagged INDIA DATA as ground truth; INDIA BENCHMARK as
operator heuristics; GLOBAL/GENERIC as directional proxies only.
{_MARKET_INTEL_PERPLEXITY}

══════════════════════════════════════════════════════════════════
RESEARCH — ARCHETYPE & SEGMENT VALIDATION REPORT (KIMI, 2026)
══════════════════════════════════════════════════════════════════
Peer-reviewed validation of all 13 archetypes and 7 segments.
Baseline peer influence coefficient: 0.142 (Herhausen et al., Nature
Communications 2024). Use VALIDATED / INFERRED / HYPOTHESIS flags when
citing mechanism or archetype evidence. Scene Seeker, Calm Pairs,
Premium Prioritizer, Power Regular are HYPOTHESIS — no academic correlate.
{_ARCHETYPE_VALIDATION}

══════════════════════════════════════════════════════════════════
RESEARCH — INDIA F&B AD BRIEF CREATIVE LAYER (KIMI, 2026)
══════════════════════════════════════════════════════════════════
India-specific creative rules for ad brief generation. Validated tone
per archetype (CONFIRMED / ADJUST), platform-creative fit for WhatsApp /
Reels / Meta / SMS / micro-influencer, mechanism-to-creative mapping,
anti-patterns, and 7 missing elements for brief generator v2.0.

Critical India rules to always apply:
- Scarcity must be EARNED, not gated. "Limited covers. Regulars book first." not "Not for everyone."
- Trust-first sequencing for new venues — trust signals before any scarcity or urgency.
- FOMO must be occasion-bound for families/premium ("Diwali weekend filling fast") not time-bound.
- Family decisions are collective — ads must speak to provider AND experience.
- Value-consciousness applies at ALL price points including premium.
- WhatsApp = conversational for repeat visitors. Deal-first only for lapsed (60+ days).
- Reels = UGC-style outperforms polished production. Regional language = 1.5-2x engagement.
- Never use Western minimalist aesthetic for mass-market Indian segments.
- Social proof: specific beats generic. "Your friends love it here" > "1,000 people came."
{_AD_BRIEF_RESEARCH}

{_POLYNOVEA_CONTEXT}

══════════════════════════════════════════════════════════════════
HOW TO RESPOND
══════════════════════════════════════════════════════════════════
- Ground every answer in the venue data above. Be specific, not generic.
- When explaining theory or mechanisms, cite the research (channel benchmarks,
  behavioral mechanisms, confidence levels) — don't just assert things.
- Give actionable answers. If asked what to do, say exactly what to do.
- Match response length to the question. Don't truncate complex answers.
- If data is missing or confidence is low, say so directly. "Not enough data to compile" is a valid and correct answer — never fabricate to fill a gap.
- Never refuse a behavioural or strategic question as "out of scope" — you are a full intelligence assistant. But venue-specific facts (dishes, prices, staff) require actual data to answer.
- When referencing numbers (open rates, ROI lifts, engagement rates), always
  include the confidence level (MEDIUM / HIGH / LOW) from the research."""


# ─── Public interface ─────────────────────────────────────────────────────────

def get_system_prompt(tab: str, venue_context: dict) -> str:
    return _IDENTITY_GUARDRAIL + build_venue_prompt(
        tab=tab,
        venue_name=venue_context["venue_name"],
        venue_type=venue_context["venue_type"],
        area=venue_context["area"],
        city=venue_context["city"],
        top_segments=venue_context.get("top_segments", []),
        top_fitness_dims=venue_context.get("top_fitness_dims", []),
        top_competitors=venue_context.get("top_competitors", []),
        seg_profiles=venue_context.get("seg_profiles"),
        channel_effectiveness=venue_context.get("channel_effectiveness"),
        campaign_templates=venue_context.get("campaign_templates"),
        interventions=venue_context.get("interventions"),
        risk_signals=venue_context.get("risk_signals"),
        behavioral_primitives=venue_context.get("behavioral_primitives"),
        behavioral_patterns=venue_context.get("behavioral_patterns"),
        dish_signals=venue_context.get("dish_signals"),
        mechanisms=venue_context.get("mechanisms"),
        drift_signals=venue_context.get("drift_signals"),
    )
