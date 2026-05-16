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

from fastapi import APIRouter, HTTPException, Query

from database import get_pool
from models import (
    MarketingResponse, MarketingSegmentCard, ChannelCard,
    NotRecommendedItem, GrowthTargetSection,
)
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
            FROM venue_fitness_dimensions WHERE venue_id = $1
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
