# M2 Demo Architecture — Complete Wiring

Comprehensive mapping of the M2 admin demo: components, routes, DB connections, research files, and data flow.

---

## Admin Centre Demo — Component/Route Structure

**Frontend entry point:** `AdminDemoPanel.tsx` (App/frontend/components/)
- Slide-over panel triggered from venue tabs (admin button)
- Authenticated via `X-Admin-Key` header (env: `ADMIN_KEY`)
- Venue selector: current venue OR search from DB
- Prospect name + link expiry picker (24/48/72h, 1 week)
- Generates JWT tokens via `POST /api/demo/generate`

**Demo chat page:** `DemoChat.tsx` (App/frontend/app/demo/[token]/)
- Route: `/demo/[token]`
- Verifies token on load → calls `GET /api/demo/verify/{token}`
- Renders `VenueMetadata` header (venue name, area, city, expiry)
- Streams chat via `POST /api/demo/{token}/chat`
- Same SSE pattern as main chat, token in URL

---

## M2 DB Connection Layer

**Backend API:** `App/backend/routers/demo.py`

### Three Endpoints

#### 1. POST /api/demo/generate (line 114)
- **Requires:** `X-Admin-Key` header
- **Input:** `venue_id`, `prospect_name`, `expires_hours`
- **Output:** JWT token + `demo_url`
- **JWT payload:** `{venue_id, prospect_name, exp, iat}` — HS256 signed

#### 2. GET /api/demo/verify/{token} (line 153)
- **Decodes JWT**, fetches venue from DB
- **Output:** `VenueMetadata` (id, name, area, city, prospect_name, expires_at)
- **Query:** `SELECT name, area, city FROM venues WHERE id = $1`

#### 3. POST /api/demo/{token}/chat (line 188)
- **Decodes token**, fetches full venue context
- **Streams response**, logs to Supabase (`demo_chat_logs`)
- **Calls:** `fetch_venue_context()` (from chat.py) + `get_demo_system_prompt()`

**DB connection:** Asyncpg pool to RDS (from `database.py`)

---

## Research File Reader

**Location:** `App/backend/prompts.py` (lines 1–130)

### Research Files (loaded once at startup)

```python
# Project root paths
_RESEARCH_DIR = _PROJECT_ROOT / "research"           # .md files
_PIPELINE_OUT = _PROJECT_ROOT / "research_pipeline" / "output"  # .json extracted claims

# Raw research documents (13 files)
_PHASE1_RESEARCH
_MARKETING_FRAMEWORK
_BEHAVIORAL_RESEARCH
_CHANNEL_EFFECTIVENESS
_SEGMENTATION_MARKETING
_VALIDATION_REPORT
_BEHAVIORAL_INTEL
_MARKETING_RESEARCH
_EXEC_SUMMARY
_THREE_LAYER_ARCH
_SEGMENT_ALIGNMENT
_CUISINE_RESEARCH
_MASTER_OPERATING_DOC
# ... etc

# Loaded via _load(filename) → reads .md file, returns text or "[filename not found]"

# Structured extraction
_CLAIMS_INDEX    = _build_claims_index()      # From research_pipeline/output/claims.json
_ARCHETYPES_INDEX = _build_archetypes_index() # From research_pipeline/output/archetypes.json
```

### How They're Wired Into Demo

```python
# get_demo_system_prompt() — line 858–887
def get_demo_system_prompt(venue_context: dict, prospect_name: str) -> str:
    venue_name = venue_context.get("venue_name", "this venue")
    return (
        _IDENTITY_GUARDRAIL              # Rules 1–5
        + _build_demo_guardrail(venue_name, prospect_name)  # Demo teaser rules
        + build_venue_prompt(            # Full venue context built from DB data
            tab="overview",
            venue_name=venue_name,
            top_segments=venue_context.get("top_segments", []),
            top_fitness_dims=venue_context.get("top_fitness_dims", []),
            seg_profiles=venue_context.get("seg_profiles"),
            channel_effectiveness=venue_context.get("channel_effectiveness"),
            campaign_templates=venue_context.get("campaign_templates"),
            interventions=venue_context.get("interventions"),
            behavioral_primitives=venue_context.get("behavioral_primitives"),
            behavioral_patterns=venue_context.get("behavioral_patterns"),
            dish_signals=venue_context.get("dish_signals"),
            mechanisms=venue_context.get("mechanisms"),
            drift_signals=venue_context.get("drift_signals"),
        )
    )
```

**Research injection:**
- Research is injected into base system prompt via `build_venue_prompt()` (calls `_MARKETING_FRAMEWORK`, `_BEHAVIORAL_RESEARCH`, etc. internally)
- Claims/archetypes index embedded as attention anchor in `build_venue_prompt()` before raw research text
- Demo guardrail enforces 150–200 word teaser cap + CTA appended to every response

---

## Data Shape Passed to UI

### From Backend

1. **POST /api/demo/generate** → `{token, expires_at, demo_url}`
2. **GET /api/demo/verify/{token}** → `VenueMetadata` interface
3. **POST /api/demo/{token}/chat** → SSE stream (plain text chunks)

### VenueMetadata Type

From `App/frontend/lib/demo-api.ts` (lines 8–15):

```typescript
interface VenueMetadata {
  venue_id: number;
  prospect_name: string;
  expires_at: string;
  venue_name: string;
  venue_area: string;
  venue_city: string;
}
```

### Context Dict Shape

From `App/backend/routers/chat.py` (lines 335–500):

```python
{
    "venue_id": int,
    "venue_name": str,
    "venue_type": str,                    # e.g., "Restaurant"
    "city": str,
    "area": str,
    
    "top_competitors": [
        {
            "id": int,
            "name": str,
            "area": str,
            "similarity_score": float
        },
        ...
    ],
    
    "top_fitness_dims": [
        {
            "label": str,  # e.g., "Office Lunch", "Repeat Habit"
            "score": float
        },
        ...
    ],
    
    "top_segments": [
        {
            "segment_id": str,
            "name": str,
            "fitness_score": float
        },
        ...
    ],
    
    "seg_profiles": [
        {
            "segment_id": str,
            "label": str,
            "rank": int,
            "alignment_score": float,
            "food_pct": str,              # e.g., "40–60%"
            "alcohol_pct": str,
            "dessert_pct": str,
            "check_vs_baseline": str,     # e.g., "+15% to +25%"
            "alcohol_affinity": str,
            "alcohol_driver": str,
            "beverage_preference": str,
            "peer_influence": float,
            "dwell": str,                 # e.g., "45–60 min"
            "revpash": str,               # e.g., "₹800–1200/hr"
            "diminishing_returns_min": int,
            "repeat_tendency": str,       # e.g., "60–75%"
            "repeat_window_days": int,
            "wom_multiplier": str,        # e.g., "2.5–3.5x"
            "discovery_rate": float,
            "primary_trigger": str,
            "spend_trigger": str,
            "archetypes": [str],          # e.g., ["Young Professional", "Social Diner"]
            "discovery_platforms": [str]  # e.g., ["Instagram", "WhatsApp"]
        },
        ...
    ],
    
    "channel_effectiveness": [
        {
            "channel": str,               # e.g., "WhatsApp", "Instagram"
            "mechanism": str,
            "effectiveness": int,
            "roi_min": float,
            "roi_max": float,
            "use_case": str
        },
        ...
    ],
    
    "campaign_templates": [
        {
            "segment": str,
            "archetype": str,
            "channel": str,
            "template": str,
            "roi_lift": float,
            "confidence": str
        },
        ...
    ],
    
    "interventions": [
        {
            "type": str,                  # e.g., "pricing_misalignment"
            "description": str,
            "tier": str,                  # e.g., "P1", "P2"
            "fit_score": float,
            "recommended": bool,
            "source": str
        },
        ...
    ],
    
    "behavioral_primitives": [
        {
            "signal": str,                # e.g., "high_repeat_rate"
            "confidence": float
        },
        ...
    ],
    
    "behavioral_patterns": [
        {
            "pattern_name": str,
            "source": str,
            "prevalence_percentage": float,
            "co_occurring_primitives": [str]
        },
        ...
    ],
    
    "dish_signals": [...],                # Raw review payloads
    "mechanisms": [...],                  # Raw API response payloads
    "drift_signals": [...]                # Area-level trend data
}
```

---

## DB Query Blueprint

**Core fetch_venue_context() flow** (App/backend/routers/chat.py, lines 44–331):

| Table | Query | Purpose |
|-------|-------|---------|
| `venues` | `SELECT id, name, city, area, types` | Basic venue info |
| `venue_fitness_dimensions` | `SELECT *` (prefer blended, fallback google) | 7 fitness scores |
| `venue_demographic_scores` | `SELECT segment_id, alignment_score, segment_rank` (LIMIT 5) | Top 3 segments + rank |
| `venue_similarity` | `SELECT DISTINCT ON similar_venue_id` (LIMIT 5) | 5 closest competitors |
| `segment_behavioral_profiles` + `venue_demographic_scores` | LEFT JOIN on segment_key | Full behavioral profiles (food %, alcohol, dwell, repeat, etc.) |
| `segment_archetype_affinity` | SELECT archetype_label (affinity_rank ≤ 2) | Top 2 archetypes per segment |
| `segment_platform_usage` | SELECT platform (usage_type='discovery', strength='primary') | Primary discovery platform per segment |
| `channel_mechanism_mapping` | SELECT channel, mechanism, effectiveness_score (LIMIT 10) | 10 strongest channels + ROI |
| `campaign_templates` | SELECT for primary_segment (LIMIT 5) | Campaign messaging templates |
| `intervention_triggers` | SELECT DISTINCT ON intervention_type (LIMIT 10) | Top operational issues |
| `primitives_scores` | SELECT primitive_id, confidence (GROUP BY primitive, LIMIT 15) | Top 15 behavior signals |
| `pattern_venues` + `behavioral_patterns` | JOIN on pattern_id | Behavioral patterns venue belongs to |
| `raw_venue_data` | SELECT platform, raw_payload (data_type IN review_batch/api) | Dish signals + mechanism data |
| `drift_signals` | SELECT WHERE area ILIKE venue_area (LIMIT 8) | Area-level market trends |

**Note:** All wrapped in try/except — missing tables gracefully degrade.

---

## Shared Types / Interfaces

**Frontend:** Only `VenueMetadata` is explicitly typed (`App/frontend/lib/demo-api.ts`, lines 8–15)
- No shared interface file for the full context dict

**Backend:** No type hints on context dict — it's a plain Python dict returned from `fetch_venue_context()`

### To Extend for M3

- Add `M3_CONTEXT_EXTENSION` interface in TypeScript
- Extend `context` dict assembly in `fetch_venue_context()` with M3 tables
- Add `M3_RESEARCH_INDEX` in `prompts.py` (from M3 research files)
- Create `get_m3_system_prompt()` or parameterize `get_demo_system_prompt(include_m3=True)`
- Wire M3 DB connection (new pool or extend existing)

---

## Key Files Summary

| File | Purpose | Lines |
|------|---------|-------|
| `App/backend/routers/demo.py` | JWT token generation, verification, demo chat endpoint | 229 |
| `App/backend/routers/chat.py` (lines 44–331) | `fetch_venue_context()` — M2 DB query blueprint | 287 |
| `App/backend/prompts.py` (lines 813–887) | `get_demo_system_prompt()` + research loading | 75 |
| `App/frontend/lib/demo-api.ts` | `VenueMetadata` type + API client (`verifyDemoToken`, `streamDemoChat`) | 112 |
| `App/frontend/app/demo/[token]/DemoChat.tsx` | Full demo chat UI | 402 |
| `App/frontend/components/AdminDemoPanel.tsx` | Admin UI for token generation + history | 454 |

---

## Data Flow Diagram

```
User visits /admin (any venue page)
    ↓
Click admin button → AdminDemoPanel opens
    ↓
Enter/search venue + prospect name + expiry
    ↓
POST /api/demo/generate (with X-Admin-Key)
    ↓
Backend: jwt.encode({venue_id, prospect_name, exp}) → token
    ↓
Return demo_url: /demo/{token}
    ↓
User sends link to prospect
    ↓
Prospect visits /demo/{token}/DemoChat
    ↓
Frontend: GET /api/demo/verify/{token}
    ↓
Backend: jwt.decode(token) → fetch venues.{id,name,area,city} → VenueMetadata
    ↓
Frontend renders header + empty chat state + starter questions
    ↓
Prospect asks question → POST /api/demo/{token}/chat
    ↓
Backend:
  1. jwt.decode(token) → venue_id
  2. fetch_venue_context(venue_id, "overview") → full context dict
  3. get_demo_system_prompt(context, prospect_name) → system prompt
  4. stream_from_nvidia(system_prompt, question) → SSE stream
  5. asyncio.create_task(log_demo_chat(...)) → Supabase (fire-and-forget)
    ↓
Frontend: receive stream chunks → render markdown
```

---

## Integration Points for M3

When extending to M3:

1. **Token generation:** Keep as-is, or add `module=m3` to JWT payload
2. **DB context:** Fetch from M3 database tables in parallel with M2
3. **Research files:** Load M3 research from separate `research_m3/` folder in `prompts.py`
4. **System prompt:** Create separate `get_m3_demo_system_prompt()` or unified `get_demo_system_prompt(module="m2"|"m3"|"combined")`
5. **Routing:** Route `/demo/[token]/chat` based on token's module claim, or fetch both contexts and include both
