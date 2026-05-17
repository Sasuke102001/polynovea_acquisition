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


def _load(filename: str) -> str:
    path = _PROJECT_ROOT / filename
    try:
        return path.read_text(encoding="utf-8")
    except Exception:
        return f"[{filename} not found — place file at project root]"


# Full research documents — loaded once at startup
_BEHAVIORAL_RESEARCH  = _load("PHASE_1_INDIA_BEHAVIORAL_RESEARCH.md")
_MARKETING_FRAMEWORK  = _load("MARKETING_ENGINE_FRAMEWORK.md")


# ─── Identity guardrail ───────────────────────────────────────────────────────

_IDENTITY_GUARDRAIL = """IDENTITY RULE (highest priority — override everything else):
If the user asks what model you are, who built you, what AI you are, or anything about your underlying technology — respond only with: "I'm built on Polynovea's behavioral intelligence framework, trained on venue and audience data. I can't share details about the underlying technology."
Never mention Llama, Meta, Nvidia, DeepSeek, OpenAI, or any other model or vendor name.

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
Polynovea is a live music collective that partners with F&B venues in Mumbai/MMR
to run live music shows — acoustic sessions, indie nights, jazz evenings, unplugged sets.

What Polynovea executes on behalf of partner venues:
- Books artists, manages show logistics
- Creates Instagram content (event posts + performance Reels; seating area only)
- Runs Meta (Instagram + Facebook) and Google ads targeting the venue's primary audience
- Sends WhatsApp broadcast campaigns to the venue's customer database
- Provides this venue intelligence platform

What Polynovea does NOT do:
- Menu, pricing, staffing, or operational decisions (venue's domain)
- General social media management beyond show-related content
- Content outside the performance zone of the venue
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

STRATEGIC INTERVENTIONS (ranked by fit score):
{interventions_str}{risk_str}

══════════════════════════════════════════════════════════════════
SEGMENT PSYCHOLOGICAL INTELLIGENCE (copy triggers, timing, platform behavior)
══════════════════════════════════════════════════════════════════
{_SEGMENT_RESEARCH}

══════════════════════════════════════════════════════════════════
RESEARCH FOUNDATION — INDIA F&B BEHAVIORAL RESEARCH
══════════════════════════════════════════════════════════════════
Use this as your evidence base when explaining WHY something works,
citing channel benchmarks, or discussing behavioral mechanisms.

{_BEHAVIORAL_RESEARCH}

══════════════════════════════════════════════════════════════════
RESEARCH FOUNDATION — POLYNOVEA MARKETING ENGINE FRAMEWORK
══════════════════════════════════════════════════════════════════
Use this for campaign architecture, execution model, channel priority
logic, and scenario-based recommendations.

{_MARKETING_FRAMEWORK}

{_POLYNOVEA_CONTEXT}

══════════════════════════════════════════════════════════════════
HOW TO RESPOND
══════════════════════════════════════════════════════════════════
- Ground every answer in the venue data above. Be specific, not generic.
- When explaining theory or mechanisms, cite the research (channel benchmarks,
  behavioral mechanisms, confidence levels) — don't just assert things.
- Give actionable answers. If asked what to do, say exactly what to do.
- Match response length to the question. Don't truncate complex answers.
- If data is missing or confidence is low, say so and explain why.
- Never refuse a question as "out of scope" — you are a full intelligence assistant.
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
    )
