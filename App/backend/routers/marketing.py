"""
routers/marketing.py
GET /api/venues/{venue_id}/marketing  →  MarketingResponse  (Screen 4 — Marketing Tab)

Channel selection and copy are driven by validated research (Kimi 2026-05-15):
  - CHANNEL_SEGMENT_RATIONALE  — channel × segment effectiveness + rationale
  - DIM_CREATIVE_ANGLES        — Instagram creative direction per fitness dimension
  - SEG_COPY_TRIGGERS          — psychological hooks per segment
  - SEG_WHATSAPP_TIMING        — optimal send window per segment

Acquisition: Instagram Reels (#1) → Zomato/Swiggy (#2)
Retention:   WhatsApp (PRIMARY) → Email → SMS
"""

import asyncio
import os
from fastapi import APIRouter, HTTPException, Query
from fastapi.responses import StreamingResponse

from database import get_pool
from models import (
    MarketingResponse, MarketingSegmentCard, ChannelCard,
    NotRecommendedItem, GrowthTargetSection,
    AdBrief, PlatformBriefRules, BriefGenerateRequest,
)

_NVIDIA_API_BASE  = "https://integrate.api.nvidia.com/v1"
_NVIDIA_KEY       = os.getenv("NVIDIA_API_KEY_CREATIVE")
_NVIDIA_MODEL     = os.getenv("NVIDIA_MODEL_CREATIVE", "nvidia/nemotron-3-nano-omni-30b-a3b-reasoning")
from routers.utils import (
    SEGMENT_LABELS, SEGMENT_TOP_ARCHETYPES, make_archetype_chip,
    CHANNEL_LABELS, MECHANISM_LABELS, DIM_LABELS,
)

router = APIRouter()

_float = lambda v: float(v) if v is not None else 0.0

# ─── Research data (Kimi 2026-05-15) ─────────────────────────────────────────
# Source: marketing_channel_strategy_research.md
# Format: {channel_key: {segment: (effectiveness, confidence, rationale)}}
# channel_key maps our internal names to the research matrix entries.

CHANNEL_SEGMENT_RATIONALE: dict[str, dict[str, str]] = {
    "instagram_organic": {
        "college_kids":   "90% Gen Z daily usage; 72% discover restaurants through Reels; high social proof sensitivity matches viral format",
        "couples":        "57% influenced by food photos; ambiance Reels drive date-night decisions; intimacy cues convert",
        "premium":        "Status signaling through aesthetic content; Veblen effect — visible consumption of high-end dining",
        "working_women":  "High penetration but time-constrained; discovery happens but conversion requires speed",
        "office_workers": "Discovery during commute/breaks; but lunch decisions are habit-driven, not discovery-driven",
        "families":       "Lower Instagram usage among 35+ parents; weekend decisions are habit/repeat, not discovery",
        "solo_diners":    "Inconspicuousness preference conflicts with public social content; utilitarian decision-making",
    },
    "zomato_swiggy": {
        "office_workers": "Primary lunch delivery/dine-in discovery platform; habitual daily usage; near-me filters",
        "families":       "Family-friendly filters; combo meals; weekend dining discovery; high trust in ratings",
        "college_kids":   "Primary discovery platform for 18–24; peer reviews + photos = social proof; price comparison",
        "couples":        "Date night discovery but limited ambiance signaling; ratings matter more than photos",
        "premium":        "Zomato Gold drives some discovery; exclusivity conflicts with mass platform positioning",
        "solo_diners":    "Quick discovery but limited solo-diner filtering; operational quality not visible",
        "working_women":  "Safety/comfort not filterable; platform lacks women-specific signals",
    },
    "whatsapp": {
        "families":       "Repeat habit + routine; weekend reservation reminders; birthday/anniversary offers — 98% open rate",
        "office_workers": "Lunch order confirmations; daily menu broadcasts; habit loop reinforcement — decision window 11:30–12:30",
        "premium":        "Exclusive event invitations; personalized service; VIP treatment signaling at 1:1 intimacy",
        "couples":        "Date night reminders work; but over-messaging (3+/week) triggers opt-outs — keep to 1–2/week",
        "college_kids":   "Group order coordination possible; Gen Z prefers Instagram/Telegram for social coordination",
        "working_women":  "Safety updates + order confirmations convert; avoid promotional broadcasts — feels invasive",
        "solo_diners":    "Low engagement with broadcasts; utilitarian relationship — transactional only",
    },
    "email": {
        "premium":        "Newsletter subscribers for culinary content; wine pairings; chef's table invitations — 43.6% open rate (MailerLite 2025)",
        "families":       "Weekend newsletter; kids' menu updates; lower open rates vs WhatsApp",
        "office_workers": "Lunch menu emails; but time-constrained = low open rates during work hours",
        "couples":        "Date night suggestions; competes with Instagram for attention",
        "college_kids":   "Low email engagement; Gen Z rarely checks email; Instagram/WhatsApp preferred",
        "working_women":  "Email overload in professional life; WhatsApp preferred for personal communication",
        "solo_diners":    "No relationship depth to sustain email engagement; transactional only",
    },
    "sms": {
        "office_workers": "Lunch confirmations; table ready alerts; time-sensitive = high relevance; 98% open rate",
        "families":       "Reservation reminders; birthday offers; high open rate = message seen",
        "premium":        "VIP alerts possible; but SMS feels less premium than WhatsApp; brand mismatch",
        "couples":        "Reservation confirmations work; promotional SMS feels intrusive",
        "college_kids":   "SMS = 'old people' channel; Gen Z ignores business SMS",
        "working_women":  "TRAI DND restrictions; promotional SMS blocked; compliance risk",
        "solo_diners":    "Transactional only; no relationship depth for promotional SMS",
    },
}

# Instagram creative direction per strongest fitness dimension
# Source: DIM_CREATIVE_ANGLES from research
DIM_CREATIVE_ANGLES: dict[str, dict[str, str]] = {
    "fitness_for_social_dwell": {
        "what":      "Ambiance shots: soft lighting, intimate seating, candlelit tables, cozy corners. Slow pan across dining room. Couples in frame.",
        "avoid":     "Crowded loud scenes; bright fluorescent lighting; group tables; kitchen chaos",
        "audio":     "Soft jazz, lo-fi, or ambient sound. Avoid trending loud music.",
        "rationale": "Bitner servicescape: environmental intimacy cues drive approach behavior. Mattila: emotional bonding requires privacy ambiance.",
    },
    "fitness_for_destination_visit": {
        "what":      "Hero shot of signature dish + exterior facade. Journey narrative: arriving → ambiance → dish → satisfaction. Aerial/establishing shots.",
        "avoid":     "Generic food shots without context; interior-only without exterior identity; process videos (too utilitarian)",
        "audio":     "Trending audio with energy build. Cinematic sound design.",
        "rationale": "Kahneman System 1: destination decisions are heuristic, not analytical. Need immediate 'this is special' signal.",
    },
    "fitness_for_group_energy": {
        "what":      "Crowd energy: laughing groups, cheers, shared plates, communal dining. Fast cuts. High energy.",
        "avoid":     "Empty tables; quiet scenes; solo diners; slow-paced content",
        "audio":     "High-energy trending audio. Beat drops synchronized with crowd reactions.",
        "rationale": "Cialdini social proof: group behavior signals correctness. Gen Z: 90% prefer communal formats. FOMO drives attendance.",
    },
    "fitness_for_repeat_habit": {
        "what":      "'Your usual' narrative: staff greeting regular by name, consistent table, familiar menu item. Warm, nostalgic tone.",
        "avoid":     "New/unknown dishes; flashy promotions; anything signaling 'this is different'",
        "audio":     "Familiar, comforting audio. Nostalgic tracks. Avoid trending/new sounds.",
        "rationale": "Duhigg habit loop: consistency and reward drive repetition. Kahneman System 1: habitual choices reduce cognitive effort.",
    },
    "fitness_for_office_lunch": {
        "what":      "Speed + value: quick plating, thali spread, lunch combo, 'in and out in 30 min' text overlay. Business district context.",
        "avoid":     "Slow romantic ambiance; elaborate plating; dinner-only dishes; anything signaling 'this takes time'",
        "audio":     "Fast-paced, upbeat. Quick cuts. No slow-motion.",
        "rationale": "Time scarcity = primary constraint. Visual must communicate speed and efficiency.",
    },
    "operational_quality": {
        "what":      "Behind-the-scenes: clean kitchen, ingredient sourcing, chef precision, hygiene protocols. Staff professionalism.",
        "avoid":     "Messy prep areas; unprofessional staff behavior; dark/blurry footage",
        "audio":     "Clean, professional voiceover. No trending audio. Authority signaling.",
        "rationale": "SoDF scale: proper service + cleanliness = trust. For families: safety signal. For solo diners: inconspicuousness requires operational excellence.",
    },
    "retention_strength": {
        "what":      "Customer testimonials; 'been coming here for years' interviews; generational dining (grandparent → parent → child).",
        "avoid":     "First-time visitor reactions; 'limited time' promotional messaging; anything signaling transience",
        "audio":     "Testimonial audio. Authentic, unscripted. Emotional music.",
        "rationale": "Social proof through longevity. Cialdini: consistency principle — long-term customers signal reliability.",
    },
}

# Research-validated copy hooks per segment (3 per segment, fill [Venue] and [Dish] at render time)
# Source: SEG_COPY_TRIGGERS from research
SEG_COPY_HOOKS: dict[str, list[str]] = {
    "office_workers": [
        "Your 30-minute lunch window just got better. [Dish] ready in 8 mins — no waiting, no wondering.",
        "Monday to Friday, 12–3 PM: Office lunch thali + refillable chai. Same time, same table, zero decision fatigue.",
        "Beat the 1 PM rush. Pre-order by 11:30, walk in and eat. Your time is money — we don't waste either.",
    ],
    "college_kids": [
        "Your entire gang's already here. [Venue] tonight — no cover, no drama, just the energy you're looking for.",
        "₹299 unlimited starters + mocktails. Split 4 ways = cheaper than your auto ride. Tag your squad.",
        "This Reel has 12K shares for a reason. [Dish] at [Venue] — see it, want it, get here before it sells out.",
    ],
    "couples": [
        "Table 7. Corner seat. City lights. Just you, them, and a [dish] that takes 3 hours to make and 30 minutes to finish.",
        "They said yes to the date. Now say yes to the corner table with the soft lights. Reserve — it goes fast on Fridays.",
        "Not a dinner. An evening. [Venue] — where the food is just the beginning.",
    ],
    "families": [
        "Same table, same friendly faces, same food your kids actually eat. Sunday lunch at [Venue] — no surprises, just Sunday.",
        "Kids' menu: ₹149. Your peace of mind: priceless. High chairs, clean floors, staff who smile at chaos.",
        "Grandparents approved. Parents relaxed. Kids occupied. [Venue] — where family dinner doesn't feel like work.",
    ],
    "premium": [
        "12 tables. 1 chef. No menu. [Venue] — where dinner is decided by what arrived this morning.",
        "You don't come here because you're hungry. You come because you know. [Venue] — for those who don't need to ask.",
        "Last seating this month: [Date]. Reserve via private link only. Not on Zomato. Not on Instagram. Just here.",
    ],
    "solo_diners": [
        "Table for one. Corner seat. No questions, no pity, just your [dish] and your peace. [Venue] — solo dining, done right.",
        "In and out in 20 minutes. Or stay for 2 hours. No one checks on you twice. Your time, your rules.",
        "Laptop-friendly. Charger-ready. Coffee that stays hot. [Venue] — where solo isn't second-class.",
    ],
    "working_women": [
        "All-women staff. Well-lit entrance. No questions asked. [Venue] — lunch hour is your hour.",
        "The table by the window. The one every regular asks for. [Venue] — where working women don't need an excuse to take a break.",
        "Your colleagues are already here. Join them — or don't. [Venue] — safe, quiet, and nobody's business.",
    ],
}

# Optimal WhatsApp send window per segment
# Source: WhatsApp Business research, optimal timing by segment
SEG_WHATSAPP_TIMING: dict[str, str] = {
    "office_workers": "11:30 AM – 12:30 PM weekdays (pre-lunch decision window)",
    "college_kids":   "6:00 PM – 8:00 PM (evening plans form 2–3 hours before)",
    "couples":        "4:00 PM – 6:00 PM Friday/Saturday (date night planning)",
    "families":       "10:00 AM – 12:00 PM Sunday (weekend lunch decisions made morning)",
    "premium":        "11:00 AM – 1:00 PM Tuesday–Thursday (weekday = less noise for exclusives)",
    "solo_diners":    "11:00 AM – 1:00 PM weekdays (quick lunch, minimal planning)",
    "working_women":  "12:00 PM – 1:00 PM weekdays (lunch break, daylight = comfort)",
}

# ─── Static channel configuration ────────────────────────────────────────────

ACQUISITION_CHANNELS = [
    ("instagram_organic", "environmental_expectation", "#1 RECOMMENDED"),
    ("instagram_ads",     "environmental_expectation", "META & INSTA ADS"),
    ("google_ads",        "intent_capture",            "GOOGLE ADS"),
]

RETENTION_CHANNELS = [
    ("whatsapp", "habit_formation", "PRIMARY"),
    ("email",    "habit_formation", None),
    ("sms",      "habit_formation", None),
]

# Polynovea advises on these but does not execute them
CONSULTING_CHANNELS = [
    ("zomato_swiggy",        "social_proof", "PLATFORM ADVISORY"),
    ("instagram_consulting", "social_proof", "ADVISORY"),
]

NOT_RECOMMENDED = [
    ("facebook",  "Generic targeting misses Mumbai's intent-driven dining culture. "
                  "Reach is high but conversion-to-table is poor for restaurants."),
    ("tiktok",    "TikTok is banned in India. YouTube Shorts is the equivalent, "
                  "but rated LOW for restaurant discovery across all segments — "
                  "best reserved for nightlife venues targeting 18–24."),
]

SEG_TEMPLATE_KEY: dict[str, str] = {
    "office_workers": "office_workers_lunch",
    "college_kids":   "college_kids_weekend",
    "couples":        "couples_date_nights",
    "families":       "families_casual_dining",
    "premium":        "premium_high_income",
}

# Zomato checklist — research-backed ranking factors
_ZOMATO_CHECKLIST = [
    "Ratings & reviews: respond to all reviews within 24 h — image reviews weighted highest by algorithm",
    "Photos: upload 5–8 shots in Zomato's required sequence — facade → ambience → food (AI rejects wrong order)",
    "Photo spec: JPG/PNG, high-res, mobile-optimised; no text overlays, watermarks, or collages",
    "Attribute tags: mark 'couple-friendly', 'group dining', 'vegetarian options', 'fastest delivery' — these drive filter discovery",
    "Menu: keep pricing + items current — stale menu = customer disappointment = negative reviews",
    "Time-based menus: separate breakfast/lunch/dinner menus so the algorithm shows relevant items by time of day",
]


# ─── Helpers ─────────────────────────────────────────────────────────────────

def _why_it_works(channel: str, primary_segment: str, segment_name: str, top_dim: str) -> str:
    """Research-backed rationale from CHANNEL_SEGMENT_RATIONALE, personalised by segment."""
    rationale = CHANNEL_SEGMENT_RATIONALE.get(channel, {}).get(primary_segment)
    if rationale:
        return rationale
    dim_label = DIM_LABELS.get(top_dim, top_dim.replace("_", " ").title())
    return f"Matched to your {dim_label} profile and {segment_name} customer base."


# ─── Route ───────────────────────────────────────────────────────────────────

@router.get("/{venue_id}/marketing", response_model=MarketingResponse)
async def get_marketing(
    venue_id:       int = ...,
    target_segment: str = Query(default=None),
):
    pool = get_pool()

    async with pool.acquire() as conn:
        exists = await conn.fetchval("SELECT id FROM venues WHERE id = $1", venue_id)
        if not exists:
            raise HTTPException(status_code=404, detail="Venue not found")

        seg_rows = await conn.fetch(
            """
            SELECT segment_id, alignment_score, segment_rank
            FROM   venue_demographic_scores
            WHERE  venue_id = $1
            ORDER  BY segment_rank
            LIMIT  3
            """,
            venue_id,
        )

        seg_ids = [r["segment_id"] for r in seg_rows]
        arc_rows = await conn.fetch(
            """
            SELECT DISTINCT ON (segment_id) segment_id, archetype_name
            FROM   demographic_archetype_mapping
            WHERE  segment_id = ANY($1::text[])
            ORDER  BY segment_id, prevalence_percentage DESC
            """,
            seg_ids,
        )
        top_arc_by_seg = {r["segment_id"]: r["archetype_name"] for r in arc_rows}

        all_channels   = [c for c, *_ in ACQUISITION_CHANNELS + RETENTION_CHANNELS + CONSULTING_CHANNELS]
        all_mechanisms = [m for _, m, *_ in ACQUISITION_CHANNELS + RETENTION_CHANNELS + CONSULTING_CHANNELS]
        cmm_rows = await conn.fetch(
            """
            SELECT channel, behavioral_mechanism, effectiveness_score,
                   baseline_roi_lift_min, baseline_roi_lift_max, primary_use_case
            FROM   channel_mechanism_mapping
            WHERE  channel = ANY($1::text[])
              AND  behavioral_mechanism = ANY($2::text[])
            """,
            all_channels, all_mechanisms,
        )
        cmm_map = {(r["channel"], r["behavioral_mechanism"]): r for r in cmm_rows}

        ch_label_rows   = await conn.fetch("SELECT channel_key, label FROM channel_benchmarks")
        mech_label_rows = await conn.fetch("SELECT slug, label FROM behavioral_mechanisms")

        fd = await conn.fetchrow(
            """
            SELECT fitness_for_office_lunch, fitness_for_repeat_habit,
                   fitness_for_social_dwell, fitness_for_group_energy,
                   fitness_for_destination_visit, operational_quality, retention_strength
            FROM venue_fitness_dimensions WHERE venue_id = $1 AND source = 'blended'
            """,
            venue_id,
        )
        fitness_dims = {
            "fitness_for_office_lunch":      _float(fd["fitness_for_office_lunch"])      if fd else 0.0,
            "fitness_for_repeat_habit":      _float(fd["fitness_for_repeat_habit"])      if fd else 0.0,
            "fitness_for_social_dwell":      _float(fd["fitness_for_social_dwell"])      if fd else 0.0,
            "fitness_for_group_energy":      _float(fd["fitness_for_group_energy"])      if fd else 0.0,
            "fitness_for_destination_visit": _float(fd["fitness_for_destination_visit"]) if fd else 0.0,
            "operational_quality":           _float(fd["operational_quality"])           if fd else 0.0,
            "retention_strength":            _float(fd["retention_strength"])            if fd else 0.0,
        }
        top_dim = max(fitness_dims, key=lambda d: fitness_dims[d])

        primary_seg_id   = seg_ids[0] if seg_ids else "office_workers"
        primary_seg_meta = SEGMENT_LABELS.get(primary_seg_id, {})
        primary_seg_name = primary_seg_meta.get("label", primary_seg_id)

        template_key = SEG_TEMPLATE_KEY.get(primary_seg_id)
        tmpl_row = None
        if template_key:
            tmpl_row = await conn.fetchrow(
                """
                SELECT message_template FROM campaign_templates
                WHERE  demographic_segment = $1 AND channel = 'whatsapp'
                ORDER  BY CASE behavioral_mechanism
                    WHEN 'habit_formation'    THEN 1
                    WHEN 'identity_signaling' THEN 2
                    WHEN 'fomo_scarcity'      THEN 3
                    ELSE 4 END
                LIMIT 1
                """,
                template_key,
            )
        if not tmpl_row:
            tmpl_row = await conn.fetchrow(
                """
                SELECT message_template FROM campaign_templates
                WHERE  channel = 'whatsapp' AND behavioral_mechanism = 'habit_formation'
                LIMIT 1
                """
            )

        whatsapp_template = tmpl_row["message_template"] if tmpl_row else None

    ch_labels   = {**CHANNEL_LABELS,   **{r["channel_key"]: r["label"] for r in ch_label_rows}}
    mech_labels = {**MECHANISM_LABELS, **{r["slug"]: r["label"] for r in mech_label_rows}}

    # ── Segment cards ──────────────────────────────────────────────────────────
    segment_cards: list[MarketingSegmentCard] = []
    for sr in seg_rows:
        sid  = sr["segment_id"]
        meta = SEGMENT_LABELS.get(sid, {})
        arc  = top_arc_by_seg.get(sid, SEGMENT_TOP_ARCHETYPES.get(sid, [""])[0])
        segment_cards.append(MarketingSegmentCard(
            segment_id=sid,
            segment_name=meta.get("label", sid),
            demographic_label=meta.get("demographic", ""),
            alignment_pct=round(_float(sr["alignment_score"]) * 100),
            top_archetype=make_archetype_chip(arc),
            visit_time=meta.get("visit_time", ""),
        ))

    # ── Channel card builder ───────────────────────────────────────────────────
    def _make_card(
        channel: str,
        mechanism: str,
        badge: str | None,
        seg_id: str = primary_seg_id,
        seg_name: str = primary_seg_name,
    ) -> ChannelCard:
        cmm   = cmm_map.get((channel, mechanism), {})
        eff   = _float(cmm.get("effectiveness_score"))
        r_min = int(cmm.get("baseline_roi_lift_min") or 0)
        r_max = int(cmm.get("baseline_roi_lift_max") or 0)
        use   = cmm.get("primary_use_case") or "acquisition"

        checklist    = _ZOMATO_CHECKLIST      if channel == "zomato_swiggy" else None
        msg_tmpl     = whatsapp_template      if channel == "whatsapp"      else None

        # Instagram: creative angle from strongest fitness dimension
        creative = DIM_CREATIVE_ANGLES.get(top_dim) if channel == "instagram_organic" else None

        # Instagram: copy hooks for primary segment
        hooks = SEG_COPY_HOOKS.get(seg_id) if channel == "instagram_organic" else None

        # WhatsApp: optimal send timing for primary segment
        timing = SEG_WHATSAPP_TIMING.get(seg_id) if channel == "whatsapp" else None

        return ChannelCard(
            channel=channel,
            channel_label=ch_labels.get(channel, channel),
            mechanism=mechanism,
            mechanism_label=mech_labels.get(mechanism, mechanism),
            effectiveness_score=eff,
            roi_lift_min=r_min,
            roi_lift_max=r_max,
            roi_label=f"+{r_min}–{r_max}% {'new customers' if use == 'acquisition' else 'repeat revenue'}",
            why_it_works=_why_it_works(channel, seg_id, seg_name, top_dim),
            target_segments=[s.segment_id for s in segment_cards],
            primary_use_case=use,
            badge=badge,
            message_template=msg_tmpl,
            action_checklist=checklist,
            creative_angle=creative,
            copy_hooks=hooks,
            send_timing=timing,
        )

    acquisition_cards = [_make_card(c, m, b) for c, m, b in ACQUISITION_CHANNELS]
    retention_cards   = [_make_card(c, m, b) for c, m, b in RETENTION_CHANNELS]
    consulting_cards  = [_make_card(c, m, b) for c, m, b in CONSULTING_CHANNELS]

    not_recommended = [
        NotRecommendedItem(
            channel=c,
            channel_label=CHANNEL_LABELS.get(c, c),
            reason=reason,
        )
        for c, reason in NOT_RECOMMENDED
    ]

    # ── Growth target section ─────────────────────────────────────────────────
    growth_target: GrowthTargetSection | None = None
    if target_segment and target_segment in SEGMENT_LABELS:
        tgt_meta = SEGMENT_LABELS[target_segment]
        tgt_name = tgt_meta.get("label", target_segment)
        tgt_demo = tgt_meta.get("demographic", "")

        tgt_acq = [
            _make_card("instagram_organic", "environmental_expectation", "#1 for Growth", target_segment, tgt_name),
            _make_card("zomato_swiggy",     "social_proof",              "#2 for Growth", target_segment, tgt_name),
        ]
        tgt_ret = _make_card("whatsapp", "habit_formation", "Conversion", target_segment, tgt_name)

        growth_target = GrowthTargetSection(
            target_segment_id=target_segment,
            target_segment_name=tgt_name,
            demographic_label=tgt_demo,
            acquisition_channels=tgt_acq,
            retention_channel=tgt_ret,
        )

    return MarketingResponse(
        top_segments=segment_cards,
        acquisition_channels=acquisition_cards,
        retention_channels=retention_cards,
        consulting_channels=consulting_cards,
        not_recommended=not_recommended,
        growth_target=growth_target,
    )


# ═══════════════════════════════════════════════════════════════════════════════
# AD BRIEF GENERATOR
# Research: india_fb_ad_brief_generator_research.md (Kimi, 2026)
# ═══════════════════════════════════════════════════════════════════════════════

# Map archetype display name (from demographic_archetype_mapping) → archetype_key
_ARCHETYPE_NAME_TO_KEY: dict[str, str] = {
    "Party Seeker":        "party_seeker",
    "Scene Seeker":        "scene_seeker",
    "Trend Hunter":        "trend_hunter",
    "Premium Prioritizer": "premium_prioritizer",
    "Habit Former":        "habit_former",
    "Lifestyle Regular":   "lifestyle_regular",
    "Quiet Discoverer":    "quiet_discoverer",
    "Power Regular":       "power_regular",
    "Trusted Regular":     "trusted_regular",
    "Social Butterfly":    "social_butterfly",
    "Comfort Dweller":     "comfort_dweller",
}

# Per-archetype creative brief data — validated against India F&B research (Kimi 2026)
# india_verdict: CONFIRMED | ADJUST
_ARCHETYPE_BRIEF: dict[str, dict] = {
    "party_seeker": {
        "tone": "High energy, crowd-signal, celebratory — frame as celebration hub not party venue for families",
        "emotional_driver": "social_proof + fomo",
        "hook": "Lead with crowd energy and social proof. Occasion-bound urgency ('Diwali weekend') not time-bound ('tonight only').",
        "cta": "Tag your squad. Book before [occasion].",
        "visual": "Laughing groups, cheers, shared plates, fast cuts, high energy. Festival-specific variants for occasions.",
        "india_verdict": "ADJUST",
        "india_note": "CONFIRMED for college_kids and working_women. For families: 'celebration hub', never 'party venue'. Always add festival/occasion anchor.",
        "trust_first": False,
        "language_rec": "Hinglish",
        "dont": [
            "Never 'party venue' framing for family segments — use 'celebration' instead",
            "Avoid generic time-bound urgency ('tonight only') — use occasion-bound ('Diwali weekend filling fast')",
            "Don't lead with alcohol imagery for family or working_women segments",
        ],
    },
    "scene_seeker": {
        "tone": "Trending, community-first — 'where everyone goes' not 'where cool people go'",
        "emotional_driver": "identity_signaling + fomo",
        "hook": "Trend signal over exclusivity. 'Mumbai's been talking about this' > 'The scene is here'.",
        "cta": "Come see why [Venue] won't leave your recommendations.",
        "visual": "Aspirational but warm Indian palette. Diverse groups. Trending visual language — never cold or minimalist.",
        "india_verdict": "ADJUST",
        "india_note": "Works for premium and couples. WRONG for mass market — 'scene' reads as elitist. Use 'trending' not 'scene'.",
        "trust_first": False,
        "language_rec": "Hinglish",
        "dont": [
            "Never 'where the scene is' or 'where the cool people go' for mass-market segments",
            "Avoid Western minimalist/cold aesthetic — warm, vibrant visuals only",
            "Don't use class-signaling language for non-premium audiences",
        ],
    },
    "trend_hunter": {
        "tone": "Discovery-first, 'first to try' — not exclusivity, not gatekeeping",
        "emotional_driver": "fomo + identity_signaling",
        "hook": "'First to try' > 'Only ones who can'. Frame as discovery, especially for value-conscious millennials.",
        "cta": "Come before it becomes the thing everyone orders.",
        "visual": "New dish reveal. Behind-the-scenes kitchen. 'What we're prepping today' UGC format.",
        "india_verdict": "ADJUST",
        "india_note": "CONFIRMED for Gen Z (72% seek new experiences). For millennials: 'discovery' not 'exclusivity' — Indian millennials are value-conscious even when affluent.",
        "trust_first": False,
        "language_rec": "Hinglish",
        "dont": [
            "Never 'invite only' or 'exclusive access' — reads as gatekeeping for Indian market",
            "Avoid 'only for the few' framing — Indian value-consciousness rejects this",
            "Don't ignore price signals even for trend-hunters — 'worth it' framing always needed",
        ],
    },
    "premium_prioritizer": {
        "tone": "Quality-first, worth-it — 'premium ingredients, honest prices', never 'luxury'",
        "emotional_driver": "anchoring + identity_signaling",
        "hook": "Reference pricing before the offer. Quality anchor before cost. 'Worth ₹1,200. Yours for ₹899'.",
        "cta": "Reserve via private link. Limited covers.",
        "visual": "Aspirational lifestyle + food anchor. Chef pedigree. Award recognition. Not cold minimalist.",
        "india_verdict": "ADJUST",
        "india_note": "Quality signal confirmed. Must add value-consciousness — Indian HNIs are value-aware. 'Worth the price' not 'price is irrelevant'. Use reference pricing.",
        "trust_first": False,
        "language_rec": "English-ok",
        "dont": [
            "Never 'luxury dining' — 'quality' works, 'luxury' reads as pretentious to new-money India",
            "Never 'for the discerning few' or 'not for everyone' — classist framing backfires",
            "Avoid price-irrelevance signals — always frame as 'worth every rupee'",
            "Don't use social proof numbers for premium — use recognition (awards, chef pedigree) instead",
        ],
    },
    "habit_former": {
        "tone": "Recognition, familiarity, consistency as comfort — 'your usual' language",
        "emotional_driver": "habit_formation + reciprocity",
        "hook": "Staff recognition + 'your usual' cue. Social value drives loyalty progression in Indian QSR research.",
        "cta": "Your table is ready. Reply YES.",
        "visual": "'Your usual' narrative. Staff greeting by name. Consistent table. Warm, nostalgic tone.",
        "india_verdict": "CONFIRMED",
        "india_note": "Strong validation. 'Your usual' language is culturally resonant. Nostalgia increases dwell time and spend in Indian dining.",
        "trust_first": False,
        "language_rec": "Hinglish",
        "dont": [
            "Never 'this is different' or flashy promotions — disrupts the habit loop",
            "Avoid urgency framing — this archetype plans, not impulse-buys",
            "Never introduce new/unfamiliar dishes as the hook — comfort is the product",
        ],
    },
    "lifestyle_regular": {
        "tone": "Warm social, belonging, community-centric — 'your group' not 'you'",
        "emotional_driver": "reciprocity + social_proof",
        "hook": "'Your group loves it here' > 'You love it here'. Community > individual in Indian dining context.",
        "cta": "Bring the group. We'll handle the rest.",
        "visual": "Social groups. Community warmth. Generational dining. Staff who know your table.",
        "india_verdict": "CONFIRMED",
        "india_note": "Strong validation. Indian dining is deeply social. Community-centric messaging is critical — 'your group' always outperforms 'you'.",
        "trust_first": False,
        "language_rec": "Hinglish",
        "dont": [
            "Never individual-focused copy — always community/group framing",
            "Avoid transactional language — relationship framing always wins",
            "Don't use urgency — lifestyle regulars are planners",
        ],
    },
    "quiet_discoverer": {
        "tone": "Trust-first, scarcity as earned natural limitation — low pressure",
        "emotional_driver": "loss_aversion",
        "hook": "Trust THEN scarcity. '200+ diners this month. Only 4 tables left.' Never scarcity without proof.",
        "cta": "Reserve quietly. No fanfare.",
        "visual": "Clean, understated. Operational excellence. Hygiene signals. Empty but beautiful space.",
        "india_verdict": "ADJUST",
        "india_note": "CONFIRMED for solo_diners and couples. For families: 'hidden gem' signals risk — use 'trusted by those who know' + scarcity. Trust must precede scarcity always.",
        "trust_first": True,
        "language_rec": "English-ok",
        "dont": [
            "Never lead with scarcity for new venues — build trust first",
            "Avoid crowd/noise signals — this archetype seeks quieter spaces",
            "Don't use FOMO language — opposite of this archetype's motivation",
        ],
    },
    "power_regular": {
        "tone": "Earned status, VIP as achievement not purchase",
        "emotional_driver": "reciprocity + identity_signaling",
        "hook": "Seating is status. Window seat, chef acknowledgment, private access = earned privilege.",
        "cta": "Table 4 is being held for you until [Time].",
        "visual": "Best table in the room. Window seat. Chef acknowledgment. Private access signal.",
        "india_verdict": "CONFIRMED",
        "india_note": "Strong validation. Indian seating psychology: 'seating is closely linked to status'. VIP framing works when it signals earned status not purchased status.",
        "trust_first": False,
        "language_rec": "English-ok",
        "dont": [
            "Never imply status is purchased — it must feel earned through loyalty",
            "Avoid 'exclusive' without the 'earned' qualifier",
            "Don't use generic loyalty points language — personal recognition only",
        ],
    },
    "trusted_regular": {
        "tone": "Loyalty, nostalgia, 'welcome back' — deepest relationship framing",
        "emotional_driver": "habit_formation + reciprocity",
        "hook": "Nostalgia + personalisation. 'Your [Dish] misses you. Three years, same table.'",
        "cta": "Welcome back. Your table is free tonight.",
        "visual": "Generational dining. Familiar staff faces. 'Been coming here for years' testimonials.",
        "india_verdict": "CONFIRMED",
        "india_note": "Strong validation. Nostalgia increases dwell time and spend in Indian dining research. 'Your usual' language is highly effective.",
        "trust_first": False,
        "language_rec": "Hinglish",
        "dont": [
            "Never promotional language — feels transactional, breaks the relationship",
            "Avoid 'new' or 'limited time' — consistency is the product",
            "Don't send generic broadcasts — personal recognition or nothing",
        ],
    },
    "social_butterfly": {
        "tone": "Group consensus, specific social proof — 'your friends are going'",
        "emotional_driver": "social_proof + fomo",
        "hook": "Specific social proof > generic crowd signals. 'Your friends are already here' > 'Everyone's here'.",
        "cta": "Your group is waiting. Book the table.",
        "visual": "Communal formats. Sharing platters. Group laughter. Pitcher rounds.",
        "india_verdict": "CONFIRMED",
        "india_note": "Strong validation. Gen Z: 90% enjoy communal formats. Specific social proof beats generic. '58% choose independent restaurants' — named friends > anonymous crowd.",
        "trust_first": False,
        "language_rec": "Hinglish",
        "dont": [
            "Avoid generic crowd signals — 'everyone is here' lands flat. Always be specific.",
            "Never solo-dining framing in any creative piece",
            "Don't lead with food — lead with the group experience",
        ],
    },
    "comfort_dweller": {
        "tone": "Safety, no surprises — familiar environment is the draw, not the food",
        "emotional_driver": "environmental_expectation + habit_formation",
        "hook": "Environment confidence + consistency. 'Quiet corner. Your usual. No surprises.'",
        "cta": "Your regular table is waiting.",
        "visual": "Quiet corner. Soft lighting. Consistent plating. Clean, safe, visible hygiene.",
        "india_verdict": "CONFIRMED",
        "india_note": "Strong validation. Post-pandemic: 61% prefer familiar environments. Safety and familiarity are primary drivers. Women: 71% cautious — safety signal essential.",
        "trust_first": True,
        "language_rec": "Hinglish",
        "dont": [
            "NEVER FOMO or urgency language — directly contradicts the mechanism and repels this archetype",
            "Avoid crowd/noise/energy signals — comfort dwellers avoid these venues",
            "Never 'new' or 'experimental' framing",
            "Don't show busy/crowded visuals — empty, calm space is the signal",
        ],
    },
}

# Platform-specific brief rules — India-validated (Kimi 2026)
_PLATFORM_BRIEF_RULES: dict[str, dict] = {
    "whatsapp": {
        "format": "Under 1,024 chars. 2–3 emojis max. Always include food image. Text-only underperforms by 35%.",
        "hook_style": "Conversational for repeat visitors (personal tone 2–3x better than deal-first). Deal-first only for lapsed customers (60+ days no visit).",
        "cta": "Soft for repeat: 'Reply YES to reserve your table'. Direct for lapsed: 'Book now — table is free tonight'.",
        "dont": [
            "Never send before 9 AM or after 9 PM",
            "Max 1–2 broadcasts/week for couples — over-messaging triggers opt-out",
            "Always include 'Reply STOP to unsubscribe' — spam reports get accounts banned",
            "Avoid generic personalisation ('Only for you') — use real name/dish or none at all",
        ],
    },
    "instagram_reels": {
        "format": "15–30 seconds. UGC-style (shot-on-iPhone) outperforms studio production 2–3x for dining.",
        "hook_style": "First 2 seconds: food close-up with sizzle/sound, OR Hinglish text overlay, OR chef looking at camera. Food-first for mass market. Atmosphere-first for premium.",
        "cta": "'Save for your next visit' > 'Order now'. Regional language CTA 1.5–2x engagement.",
        "dont": [
            "Never polished studio production for mass-market segments — reads as ad, gets skipped",
            "Avoid English-only copy — Hinglish or regional language gets 1.5–2x engagement",
            "Don't lead with venue exterior — food or people first",
            "Never 6.5x engagement claim — UNSUBSTANTIATED (no India citation)",
        ],
    },
    "instagram_ads": {
        "format": "Carousel for menu showcase (4.2x ROAS vs 3.1x single image). UGC-style video under 15s for engagement. Single image for retargeting.",
        "hook_style": "Local radius targeting 3–5km. Run 1–2 hours before meal-decision window (lunch: 10–12 AM, dinner: 5–7 PM). Hinglish for mass market.",
        "cta": "Warm retargeting: 'Still thinking? Here's what you're missing.' Hot: 'Only 3 tables left for tonight.'",
        "dont": [
            "English-only copy limits reach to premium only — use Hinglish for mass market",
            "Avoid Western minimalist aesthetic for non-premium segments",
            "Never run all-day — time to meal-decision windows only",
        ],
    },
    "google_ads": {
        "format": "Intent-capture. Near-me search. Local radius. Functional copy over emotional.",
        "hook_style": "'Best [cuisine] near [area]'. For office_workers: 'Ready in 8 mins'. Run during lunch (11 AM–1 PM) and dinner (6–8 PM) decision windows.",
        "cta": "Book table / Get directions. Single low-friction action.",
        "dont": [
            "Avoid emotional or branding copy — Google is intent-capture, not discovery",
            "Don't run outside meal-decision windows — wasted spend",
        ],
    },
    "sms": {
        "format": "Under 160 characters (single SMS only). No split messages.",
        "hook_style": "Urgent, time-sensitive, transactional only. Not for relationship-building. Evening (5–8 PM) for dine-in.",
        "cta": "Direct booking link. One action. Nothing else.",
        "dont": [
            "SMS is last-resort in India — DND regulations block promotional SMS without explicit opt-in",
            "WhatsApp has replaced SMS for F&B promotions in India",
            "Never use for relationship-building — transactional alerts only",
            "Never send for working_women segment — TRAI DND compliance risk",
        ],
    },
    "zomato_swiggy": {
        "format": "Platform listing optimisation. Photo sequence: facade → ambience → food. Attribute tags drive algorithm.",
        "hook_style": "Ratings, review response speed, correct attribute tags drive algorithmic visibility — not copy.",
        "cta": "Not copy-driven — algorithmic placement. Focus on listing quality.",
        "dont": [
            "Never text overlays or watermarks on photos — platform AI rejects them",
            "Don't leave stale menus — triggers negative reviews which suppress visibility",
            "Never ignore image review responses — they are weighted highest by the algorithm",
        ],
    },
}

# Default channel per segment (best match from research)
_SEGMENT_DEFAULT_CHANNEL: dict[str, str] = {
    "office_workers": "whatsapp",
    "college_kids":   "instagram_reels",
    "couples":        "whatsapp",
    "families":       "whatsapp",
    "premium":        "instagram_ads",
    "solo_diners":    "google_ads",
    "working_women":  "whatsapp",
}

# Channels valid for content generation (excludes platform-consulting channels like zomato_swiggy)
_CONTENT_CHANNELS = {"whatsapp", "instagram_reels", "instagram_ads", "google_ads", "sms"}

# Archetype-specific copy hooks — India-adjusted (Kimi 2026)
_ARCHETYPE_COPY_HOOKS: dict[str, list[str]] = {
    "party_seeker": [
        "The whole crew is already here. [Venue] tonight — no cover, no drama, just the energy you're looking for.",
        "Diwali plans sorted: group bookings open. ₹299/head starters + pitchers. Tag your squad.",
        "Your table is being claimed by someone else right now. [Venue] — book before it's gone this weekend.",
    ],
    "scene_seeker": [
        "Mumbai's been talking about [Venue] since [Month]. The food is why. The vibe is why you'll stay.",
        "This is where [Area] actually goes right now. [Dish] at [Venue] — trending for good reason.",
        "Your feed is already full of it. Come see why [Venue] won't leave your recommendations.",
    ],
    "trend_hunter": [
        "We just launched [Dish]. Nobody's had it yet. [Venue] — this week only before it becomes the thing everyone orders.",
        "Staff pick this week: [Dish]. Not on the main menu yet. First 30 orders get the launch price.",
        "What we're testing in the kitchen this weekend. [Venue] — come before it goes mainstream.",
    ],
    "premium_prioritizer": [
        "₹1,800 elsewhere. ₹899 here. Same quality, different philosophy. [Venue] — worth every rupee.",
        "12 covers. Chef [Name] cooks what arrived this morning. No set menu. Reserve via link only.",
        "Our [Dish] takes 3 hours to prepare. We make 20 a night. [Venue] — quality has a limit, and it's intentional.",
    ],
    "habit_former": [
        "It's been a while. Your usual table's waiting. [Venue] — same people, same quality, always.",
        "Monday to Friday, same table, same order. [Venue] — where lunch isn't a decision anymore.",
        "Your usual: [Dish]. Your table: corner. Ready when you are. Reply YES to confirm.",
    ],
    "lifestyle_regular": [
        "Your group hasn't been here since [Month]. Time to fix that. [Date] is open.",
        "[Venue] — the place your whole group agrees on. No debate, just dinner. Reserve [Date].",
        "Treat the group. Same spot, same energy. Let us handle the rest.",
    ],
    "quiet_discoverer": [
        "200+ diners this month. Still 4 tables left for this weekend. [Venue] — the one your friends recommended.",
        "They don't advertise much. That's the point. [Venue] — trusted by those who know [Area].",
        "Not on every food blogger's list. On every regular's shortlist. [Venue] — try it once.",
    ],
    "power_regular": [
        "Table 4 is yours tonight. No questions, no waiting. [Venue] — the best seat in the room, held for you.",
        "Our regulars get first reservation rights for the chef's table. [Date] — yours if you want it.",
        "The window table. The one everyone notices. It's being held for you until [Time].",
    ],
    "trusted_regular": [
        "Welcome back. Your usual is waiting. [Dish] at [Venue] — some things shouldn't change.",
        "Three years, same table, same smiles. [Venue] — where being a regular actually means something.",
        "It's been [X] days. Your [Dish] misses you. The table by the window is free tonight.",
    ],
    "social_butterfly": [
        "Your friends are already talking about going to [Venue] this weekend. Don't be the last to know.",
        "Sharing platter for [X]. Pitchers on the table. [Venue] — your group will thank you.",
        "The group chat is about to suggest somewhere average. Beat them to it. [Venue] tonight.",
    ],
    "comfort_dweller": [
        "Quiet corner. Your usual. Nobody rushes you here. [Venue] — exactly what you'd expect, done right.",
        "The [Dish] you've been craving. The table you always ask for. [Venue] — tonight, as usual.",
        "No surprises. No strangers at the next table. Just your meal, your pace. [Venue].",
    ],
}

# India rules that apply universally (always injected into any brief)
_INDIA_UNIVERSAL_RULES = [
    "Value-consciousness applies at ALL price points — even premium segments want 'worth it' not 'expensive'",
    "Food as social currency: 80–85% of Indian diners share food experiences online — design for shareability",
    "Festival/occasion anchoring outperforms generic 'weekend special' — tie to Diwali, Eid, birthdays, anniversaries",
    "Scarcity must be EARNED not GATED: 'Limited covers tonight. Regulars book first.' not 'Not for everyone.'",
    "Family decisions are collective — ads must speak to the provider AND the family experience",
]

# Additional India rules per archetype (appended on top of universal)
_ARCHETYPE_INDIA_RULES: dict[str, list[str]] = {
    "quiet_discoverer": [
        "Trust-first sequencing: establish social proof ('booked by 200+ this month') BEFORE any scarcity signal",
    ],
    "comfort_dweller": [
        "Safety-first framing: safety and hygiene signals must appear in first impression — especially for women diners",
        "Consistency is the feature: 'exactly what you'd expect' is a benefit, not a limitation",
    ],
    "premium_prioritizer": [
        "Indian premium market is new money — 'old money' framing ('for the discerning few') backfires",
        "Reference pricing required: '₹1,800 elsewhere, ₹899 here' even for premium positioning",
    ],
    "scene_seeker": [
        "Mass market: 'where everyone goes' > 'where the cool people go' — social inclusion beats exclusion",
    ],
    "party_seeker": [
        "Occasion-bound FOMO ('Diwali weekend filling fast') outperforms time-bound ('Tonight only') for most segments",
    ],
}


def _detect_anti_patterns(archetype_key: str, channel: str, segment_id: str) -> list[str]:
    flags = []

    if archetype_key in ("scene_seeker", "trend_hunter") and segment_id != "premium":
        flags.append(
            "RISK: Identity-signaling for non-premium segment can read as classist — "
            "use 'trending/community' framing, avoid 'exclusive/scene' language"
        )

    fomo_archetypes = {"party_seeker", "scene_seeker", "trend_hunter", "social_butterfly"}
    if archetype_key in fomo_archetypes and segment_id == "families":
        flags.append(
            "RISK: FOMO mechanism conflicts with families segment — "
            "switch to occasion anchoring (Diwali, birthday) not time-bound urgency"
        )

    mass_market = {"college_kids", "office_workers", "working_women", "families"}
    if segment_id in mass_market and channel in ("instagram_reels", "instagram_ads"):
        flags.append(
            "RISK: Western minimalist/cold aesthetic underperforms for this segment — "
            "warm, vibrant Indian visual language required"
        )

    if segment_id == "working_women" and channel == "sms":
        flags.append(
            "RISK: SMS for Working Women blocked by TRAI DND regulations — "
            "switch to WhatsApp"
        )

    if archetype_key == "quiet_discoverer":
        flags.append(
            "RULE: Trust-first sequencing mandatory — "
            "social proof must appear BEFORE any scarcity or urgency signal"
        )

    if archetype_key == "comfort_dweller":
        flags.append(
            "RULE: Never use urgency, FOMO, or scarcity language — "
            "this archetype is repelled by pressure. Consistency and safety only."
        )

    if archetype_key == "premium_prioritizer" and channel in ("instagram_reels", "sms"):
        flags.append(
            "RISK: Premium Prioritizer is poorly served by Reels/SMS — "
            "Instagram Ads or email newsletter is stronger for this archetype"
        )

    return flags


@router.get("/{venue_id}/marketing/brief", response_model=AdBrief)
async def get_ad_brief(
    venue_id: int,
    channel:  str = Query(default=None),
):
    pool = get_pool()

    async with pool.acquire() as conn:
        exists = await conn.fetchval("SELECT id FROM venues WHERE id = $1", venue_id)
        if not exists:
            raise HTTPException(status_code=404, detail="Venue not found")

        venue_row = await conn.fetchrow(
            "SELECT name, area FROM venues WHERE id = $1", venue_id
        )

        seg_row = await conn.fetchrow(
            """
            SELECT segment_id, alignment_score
            FROM   venue_demographic_scores
            WHERE  venue_id = $1
            ORDER  BY segment_rank
            LIMIT  1
            """,
            venue_id,
        )

        primary_seg_id = seg_row["segment_id"] if seg_row else "office_workers"

        arc_row = await conn.fetchrow(
            """
            SELECT archetype_name
            FROM   demographic_archetype_mapping
            WHERE  segment_id = $1
            ORDER  BY prevalence_percentage DESC
            LIMIT  1
            """,
            primary_seg_id,
        )

    archetype_name = arc_row["archetype_name"] if arc_row else "Habit Former"
    archetype_key  = _ARCHETYPE_NAME_TO_KEY.get(archetype_name, "habit_former")
    brief_data     = _ARCHETYPE_BRIEF.get(archetype_key, _ARCHETYPE_BRIEF["habit_former"])

    seg_meta    = SEGMENT_LABELS.get(primary_seg_id, {})
    seg_label   = seg_meta.get("label", primary_seg_id)

    resolved_channel = channel or _SEGMENT_DEFAULT_CHANNEL.get(primary_seg_id, "whatsapp")
    platform_data    = _PLATFORM_BRIEF_RULES.get(resolved_channel, _PLATFORM_BRIEF_RULES["whatsapp"])
    ch_label         = CHANNEL_LABELS.get(resolved_channel, resolved_channel)

    india_rules = list(_INDIA_UNIVERSAL_RULES) + _ARCHETYPE_INDIA_RULES.get(archetype_key, [])
    anti_flags  = _detect_anti_patterns(archetype_key, resolved_channel, primary_seg_id)
    copy_hooks  = _ARCHETYPE_COPY_HOOKS.get(archetype_key, _ARCHETYPE_COPY_HOOKS["habit_former"])

    platform_rules = PlatformBriefRules(
        format=platform_data["format"],
        hook_style=platform_data["hook_style"],
        cta=platform_data["cta"],
        dont=platform_data["dont"],
    )

    return AdBrief(
        venue_name=venue_row["name"],
        venue_area=venue_row["area"],
        target_segment=seg_label,
        target_archetype=archetype_name,
        channel=resolved_channel,
        channel_label=ch_label,
        tone=brief_data["tone"],
        emotional_driver=brief_data["emotional_driver"],
        hook=brief_data["hook"],
        cta=brief_data["cta"],
        visual_direction=brief_data["visual"],
        india_rules=india_rules,
        trust_first=brief_data["trust_first"],
        language_rec=brief_data["language_rec"],
        occasion_anchor="Festival/occasion anchoring recommended — tie to Diwali, Eid, Onam, birthdays, anniversaries for 2–3x engagement lift",
        dont_say=brief_data["dont"],
        anti_pattern_flags=anti_flags,
        platform_rules=platform_rules,
        copy_hooks=copy_hooks,
        data_confidence="MED",
    )


# ═══════════════════════════════════════════════════════════════════════════════
# BRIEF CONTENT GENERATOR  (streaming)
# POST /{venue_id}/marketing/brief/generate?channel=
# Generates 3 ready-to-use content pieces grounded in the structured brief.
# ═══════════════════════════════════════════════════════════════════════════════

_CHANNEL_CONTENT_TYPE: dict[str, str] = {
    "whatsapp":        "WhatsApp broadcast messages",
    "instagram_reels": "Instagram Reels scripts (hook + body + CTA)",
    "instagram_ads":   "Meta/Instagram ad copy variations",
    "google_ads":      "Google search ad headlines + descriptions",
    "sms":             "SMS messages (under 160 chars each)",
    "zomato_swiggy":   "Zomato/Swiggy listing description variants",
}


def _build_brief_system_prompt(
    venue_name: str,
    venue_area: str,
    seg_label: str,
    archetype_name: str,
    archetype_key: str,
    resolved_channel: str,
    ch_label: str,
    brief_data: dict,
    platform_data: dict,
    india_rules: list[str],
    anti_flags: list[str],
) -> str:
    content_type = _CHANNEL_CONTENT_TYPE.get(resolved_channel, "content pieces")
    donts_str    = "\n".join(f"- {d}" for d in brief_data["dont"])
    india_str    = "\n".join(f"- {r}" for r in india_rules)
    platform_donts = "\n".join(f"- {d}" for d in platform_data["dont"])
    flags_str    = ("\n\nAUTO-DETECTED RISKS:\n" + "\n".join(f"- {f}" for f in anti_flags)) if anti_flags else ""
    trust_note   = "\n\nMANDATORY: Establish trust/social proof BEFORE any scarcity or urgency." if brief_data.get("trust_first") else ""

    return f"""You are an expert India F&B ad copywriter working for Polynovea. Your job is to generate exactly 3 ready-to-use {content_type} for {venue_name} in {venue_area}.

IDENTITY GUARDRAIL: Never mention Polynovea's internal systems, file names, research documents, loader names, Python modules, or any technical implementation details in your output. Never reference how you were trained or what data sources you use. Output only the content pieces themselves.

VENUE BRIEF:
- Venue: {venue_name}, {venue_area}
- Target segment: {seg_label}
- Dominant archetype: {archetype_name}
- India research verdict: {brief_data.get("india_verdict", "CONFIRMED")} — {brief_data.get("india_note", "")}

CREATIVE DIRECTION:
- Tone: {brief_data["tone"]}
- Emotional driver: {brief_data["emotional_driver"]}
- Hook formula: {brief_data["hook"]}
- CTA style: {brief_data["cta"]}
- Visual direction: {brief_data["visual"]}
- Language: {brief_data["language_rec"]}{trust_note}

{ch_label.upper()} PLATFORM RULES:
- Format: {platform_data["format"]}
- Hook style: {platform_data["hook_style"]}
- CTA: {platform_data["cta"]}
- Platform don'ts:
{platform_donts}

INDIA RULES — ALWAYS APPLY:
{india_str}

NEVER WRITE / NEVER DO:
{donts_str}{flags_str}

OUTPUT FORMAT:
Return exactly 3 numbered {content_type}. Use "{venue_name}" as the venue name. Use [Dish] as a placeholder for specific dishes. No preamble, no explanation, no headings — just the 3 pieces numbered 1, 2, 3."""


async def _log_brief_to_supabase(
    venue_id: int,
    channel: str,
    archetype: str,
    segment: str,
    direction: str,
    response: str,
) -> None:
    import httpx
    supabase_url = os.getenv("SUPABASE_URL", "").rstrip("/")
    supabase_key = os.getenv("SUPABASE_SECRET_KEY") or os.getenv("SUPABASE_ANON_KEY", "")
    if not supabase_url or not supabase_key:
        return
    try:
        url     = f"{supabase_url}/rest/v1/venue_chat_logs"
        payload = {
            "venue_id":         str(venue_id),
            "tab":              "marketing_brief",
            "question":         direction or f"Generate {channel} content",
            "context_snapshot": {"channel": channel, "archetype": archetype, "segment": segment},
            "response":         response,
            "model_version":    "brief-generator-v1",
            "source_type":      "brief_generated",
            "schema_version":   1,
        }
        headers = {
            "apikey":        supabase_key,
            "Authorization": f"Bearer {supabase_key}",
            "Content-Type":  "application/json",
            "Prefer":        "return=minimal",
        }
        async with httpx.AsyncClient(timeout=10) as client:
            await client.post(url, json=payload, headers=headers)
    except Exception as e:
        print(f"Brief Supabase logging failed: {e}")


async def _stream_brief_content(system_prompt: str, user_message: str):
    try:
        from openai import AsyncOpenAI

        if not _NVIDIA_KEY:
            yield "[Error: NVIDIA_API_KEY_CREATIVE not configured]"
            return

        client = AsyncOpenAI(api_key=_NVIDIA_KEY, base_url=_NVIDIA_API_BASE)
        stream = await client.chat.completions.create(
            model=_NVIDIA_MODEL,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user",   "content": user_message},
            ],
            temperature=0.85,
            max_tokens=1500,
            stream=True,
        )

        async for chunk in stream:
            if chunk.choices and chunk.choices[0].delta.content:
                yield chunk.choices[0].delta.content

    except Exception as e:
        yield f"\n\n[Error: {str(e)}]"


@router.post("/{venue_id}/marketing/brief/generate")
async def generate_brief_content(
    venue_id:  int,
    request:   BriefGenerateRequest,
    channel:   str = Query(default=None),
):
    pool = get_pool()

    async with pool.acquire() as conn:
        venue_row = await conn.fetchrow(
            "SELECT name, area FROM venues WHERE id = $1", venue_id
        )
        if not venue_row:
            raise HTTPException(status_code=404, detail="Venue not found")

        seg_row = await conn.fetchrow(
            """
            SELECT segment_id FROM venue_demographic_scores
            WHERE  venue_id = $1
            ORDER  BY segment_rank
            LIMIT  1
            """,
            venue_id,
        )
        primary_seg_id = seg_row["segment_id"] if seg_row else "office_workers"

        arc_row = await conn.fetchrow(
            """
            SELECT archetype_name FROM demographic_archetype_mapping
            WHERE  segment_id = $1
            ORDER  BY prevalence_percentage DESC
            LIMIT  1
            """,
            primary_seg_id,
        )

    archetype_name   = arc_row["archetype_name"] if arc_row else "Habit Former"
    archetype_key    = _ARCHETYPE_NAME_TO_KEY.get(archetype_name, "habit_former")
    brief_data       = _ARCHETYPE_BRIEF.get(archetype_key, _ARCHETYPE_BRIEF["habit_former"])
    seg_meta         = SEGMENT_LABELS.get(primary_seg_id, {})
    seg_label        = seg_meta.get("label", primary_seg_id)

    resolved_channel = channel or _SEGMENT_DEFAULT_CHANNEL.get(primary_seg_id, "whatsapp")
    if resolved_channel not in _CONTENT_CHANNELS:
        raise HTTPException(
            status_code=400,
            detail=f"'{resolved_channel}' is a platform-consulting channel — content generation not applicable.",
        )

    platform_data    = _PLATFORM_BRIEF_RULES.get(resolved_channel, _PLATFORM_BRIEF_RULES["whatsapp"])
    ch_label         = CHANNEL_LABELS.get(resolved_channel, resolved_channel)
    india_rules      = list(_INDIA_UNIVERSAL_RULES) + _ARCHETYPE_INDIA_RULES.get(archetype_key, [])
    anti_flags       = _detect_anti_patterns(archetype_key, resolved_channel, primary_seg_id)

    system_prompt = _build_brief_system_prompt(
        venue_name=venue_row["name"],
        venue_area=venue_row["area"],
        seg_label=seg_label,
        archetype_name=archetype_name,
        archetype_key=archetype_key,
        resolved_channel=resolved_channel,
        ch_label=ch_label,
        brief_data=brief_data,
        platform_data=platform_data,
        india_rules=india_rules,
        anti_flags=anti_flags,
    )

    content_type = _CHANNEL_CONTENT_TYPE.get(resolved_channel, "content pieces")
    user_message = (
        request.direction.strip()
        if request.direction.strip()
        else f"Generate 3 {content_type} for {venue_row['name']}."
    )

    async def _stream_and_log():
        buffer: list[str] = []
        async for chunk in _stream_brief_content(system_prompt, user_message):
            buffer.append(chunk)
            yield chunk
        asyncio.create_task(_log_brief_to_supabase(
            venue_id=venue_id,
            channel=resolved_channel,
            archetype=archetype_name,
            segment=seg_label,
            direction=request.direction,
            response="".join(buffer),
        ))

    return StreamingResponse(_stream_and_log(), media_type="text/plain")
