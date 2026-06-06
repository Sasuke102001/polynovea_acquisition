# M2 Tiered Demo Implementation — Complete

**Status:** ✅ Ready for testing  
**Date:** 2026-06-07  
**Scope:** M2 admin demo extended to support 3 capability levels with gated DB/research/AI routing

---

## What's Implemented

### 1. **Database Layer** (`App/backend/database.py`)
- ✅ Added `get_m3_pool()` — separate asyncpg connection pool for M3 RDS
- ✅ Added `init_m3_pool()` — initializes on startup (graceful degradation if M3 not configured)
- ✅ Added `close_m3_pool()` — cleanup on shutdown
- ✅ `M3_PG_*` env vars required in `.env` (optional)

### 2. **Main App** (`App/backend/main.py`)
- ✅ Imported `init_m3_pool`, `close_m3_pool`
- ✅ Calls `init_m3_pool()` on startup, `close_m3_pool()` on shutdown

### 3. **Demo API Endpoints** (`App/backend/routers/demo.py`)

#### POST /api/demo/generate
- ✅ Added `demo_level: int` (1, 2, or 3) to `GenerateRequest`
- ✅ Validates demo_level in [1, 2, 3]
- ✅ Encodes demo_level into JWT payload
- ✅ Returns demo_level in response

#### GET /api/demo/verify/{token}
- ✅ Returns `demo_level` in `VerifyResponse`
- ✅ Extracts from JWT payload

#### POST /api/demo/{token}/chat
- ✅ Extracts demo_level from JWT
- ✅ Routes to appropriate AI:
  - **Level 1:** M2 Council only
  - **Level 2:** M2 Council + M3 Prism Agent 1 (side-by-side)
  - **Level 3:** Full M3 Prism (all 7 agents)
- ✅ Added `call_m3_prism()` helper to call M3's `/api/prism` endpoint

### 4. **Context Fetching** (`App/backend/routers/chat.py`)

#### fetch_venue_context(venue_id, tab, demo_level=1)
- ✅ Added `demo_level` parameter
- ✅ **Level 1+:** M2 data (existing behavior)
- ✅ **Level 2+:** M3 summary data (recent sessions, avg KPI)
  - Queries `m3_sessions`, `m3_kpi_assessments`
  - Returns `m3_recent_sessions`, `m3_kpi_summary`
- ✅ **Level 3+:** M3 full data (show plans, outcomes)
  - Queries `m3_show_plans`, `m3_show_outcomes`
  - Returns `m3_show_plans`, `m3_show_outcomes`
- ✅ Gracefully degrades if M3 pool unavailable

### 5. **Research Files & Prompts** (`App/backend/prompts.py`)

#### Research Loading
- ✅ Added `_RESEARCH_M3_DIR` → `research_m3/` (28 files)
- ✅ Added `_RESEARCH_SE_DIR` → `research_se/` (24 files)
- ✅ Added `_load_all_from_dir()` helper to load all `.md` files from directory
- ✅ Cached at startup: `_M3_RESEARCH_CACHE`, `_SE_RESEARCH_CACHE`

#### get_demo_system_prompt(venue_context, prospect_name, demo_level=1)
- ✅ Added `demo_level` parameter
- ✅ **Level 1:** M2 guardrail + M2 venue prompt (existing behavior)
- ✅ **Level 2:** + M3 research section (music psychology, neuropsych, environmental)
- ✅ **Level 3:** + SE research section (neuroacoustics, show engineering, frequency psychology)

### 6. **Frontend — Admin Panel** (`App/frontend/components/AdminDemoPanel.tsx`)
- ✅ Added `demoLevel` state (1 | 2 | 3)
- ✅ Added level selector UI with descriptions
- ✅ Passes `demo_level` to `POST /api/demo/generate`

### 7. **Frontend — Demo Chat** (`App/frontend/app/demo/[token]/DemoChat.tsx`)
- ✅ Updated `VenueMetadata` type to include `demo_level: number`
- ✅ Added level badge in header (blue/purple/gold for levels 1/2/3)

### 8. **API Types** (`App/frontend/lib/demo-api.ts`)
- ✅ Added `demo_level: number` to `VenueMetadata` interface

### 9. **Deployment** (`.github/workflows/deploy-backend.yml`)
- ✅ Updated to clone `polynovea-research` and extract `m2/`, `m3/`, `se/` folders
- ✅ Creates `App/backend/research`, `research_m3`, `research_se` on deploy
- ✅ Gracefully handles missing folders

### 10. **Configuration** (`App/backend/.env.example`)
- ✅ Added M3 RDS variables: `M3_PG_HOST`, `M3_PG_USER`, `M3_PG_PASSWORD`, `M3_PG_DB`
- ✅ Added `M3_API_URL` for cross-repo Prism calls

---

## Data Flow

```
1. Admin generates token with level selector (1/2/3)
   └→ POST /api/demo/generate with demo_level in body

2. Token encoded with demo_level claim in JWT
   └→ /demo/{token} shared with prospect

3. Prospect visits link
   └→ GET /api/demo/verify/{token} returns demo_level badge info

4. Prospect asks question
   └→ POST /api/demo/{token}/chat with demo_level from JWT

5. Backend:
   a) fetch_venue_context(venue_id, tab, demo_level)
      - Level 1: M2 only
      - Level 2: M2 + M3 summary
      - Level 3: M2 + M3 full + SE
   
   b) get_demo_system_prompt(context, prospect, demo_level)
      - Level 1: M2 research only
      - Level 2: + M3 research
      - Level 3: + SE research
   
   c) Route to AI:
      - Level 1: stream_from_nvidia() → M2 Council
      - Level 2: M2 Council + call_m3_prism(agent=1)
      - Level 3: call_m3_prism(agent=None) → Full Prism 1–7

6. Frontend displays:
   - Venue header with Level badge
   - Separator between responses (level 2)
   - Full Prism output (level 3)
```

---

## Testing Checklist

- [ ] **Level 1 token:**
  - Generates with demo_level=1
  - Returns M2 context only
  - Shows M2 Council response only
  - Badge shows "Level 1"

- [ ] **Level 2 token:**
  - Generates with demo_level=2
  - Returns M2 + M3 summary (sessions, avg KPI)
  - Shows M2 Council + M3 Prism Agent 1 side-by-side
  - Badge shows "Level 2"
  - M3 API call succeeds (or fails gracefully)

- [ ] **Level 3 token:**
  - Generates with demo_level=3
  - Returns M2 + M3 full + SE (show plans, outcomes)
  - Shows full Prism pipeline (all 7 agents)
  - Badge shows "Level 3"
  - M3 API call succeeds (or fails gracefully)

- [ ] **Graceful degradation:**
  - If M3 pool unavailable, levels 2/3 still work (M3 context empty, M3 calls fail with friendly message)
  - If M3 API down, falls back to "M3 Prism unavailable" message
  - Research folders missing → load defaults gracefully

- [ ] **Admin panel:**
  - Level selector visible and functional
  - Demo URL includes correct token
  - History tracks demo_level

- [ ] **Credentials:**
  - M3_PG_* env vars optional (not required for level 1)
  - M3_API_URL optional (not required for level 1)

---

## Files Modified

| File | Changes |
|------|---------|
| `App/backend/database.py` | M3 pool init/close + get_m3_pool() |
| `App/backend/main.py` | init_m3_pool() call in lifespan |
| `App/backend/routers/demo.py` | demo_level in token gen/verify/chat + M3 routing |
| `App/backend/routers/chat.py` | Level-gated context fetch from M2/M3 |
| `App/backend/prompts.py` | Research loading + level-gated prompt building |
| `App/frontend/components/AdminDemoPanel.tsx` | Level selector UI |
| `App/frontend/app/demo/[token]/DemoChat.tsx` | Level badge in header |
| `App/frontend/lib/demo-api.ts` | demo_level in VenueMetadata type |
| `.github/workflows/deploy-backend.yml` | M3/SE research cloning |
| `App/backend/.env.example` | M3 credentials + M3_API_URL |

---

## Next Steps

### M2 Side (COMPLETE ✅)
All wiring done. Ready for:
1. **Local testing** — verify level 1 works without M3 (graceful fallback)
2. **M3 credential setup** — add M3 RDS access + M3_API_URL when M3 is ready
3. **Integration testing** — once M3 `/api/prism` endpoint is available

### M3 Side (PENDING)
- [ ] Create `/api/prism` endpoint in `App/backend/routers/show.py`
- [ ] Accepts: `system_prompt`, `message`, `agent` (1–7 or None), `venue_id`
- [ ] Returns: SSE stream of Prism response
- [ ] Error handling for agent failures

### Research Files (READY)
- [ ] Upload M3 research (28 files from Module 3) → `polynovea-research/m3/`
- [ ] Upload SE research (24 files) → `polynovea-research/se/`
- [ ] Deploy script will auto-extract on next push

---

## Env Vars Required

### For Level 1 (M2 only)
```
# Existing M2 vars (required)
PG_HOST=...
PG_PORT=5432
PG_DB=polynovea_module2
PG_USER=...
PG_PASSWORD=...
DEMO_JWT_SECRET=...
ADMIN_KEY=...
```

### For Level 2+ (with M3)
```
# Add to above:
M3_PG_HOST=...
M3_PG_PORT=5432
M3_PG_DB=polynovea_module3
M3_PG_USER=...
M3_PG_PASSWORD=...
M3_API_URL=http://m3-backend:9000
```

If M3 vars missing, levels 2/3 gracefully degrade to level 1 (M2 only).

---

## Architecture Diagram

```
┌─────────────────────────────────────────────────────────────┐
│                       M2 Backend                             │
├─────────────────────────────────────────────────────────────┤
│                                                               │
│  POST /api/demo/generate (admin creates token with level)   │
│       ↓                                                       │
│  JWT encode: {venue_id, prospect_name, demo_level, exp}    │
│       ↓                                                       │
│  GET /api/demo/verify/{token} (frontend shows level badge) │
│       ↓                                                       │
│  POST /api/demo/{token}/chat (prospect asks question)       │
│       ↓                                                       │
│  ┌───────────────────────────────────┐                      │
│  │ fetch_venue_context(level)        │                      │
│  ├───────────────────────────────────┤                      │
│  │ Level 1: M2 only                  │                      │
│  │ Level 2: M2 + M3 summary          │ ←─ get_m3_pool()    │
│  │ Level 3: M2 + M3 full + SE        │                      │
│  └───────────────────────────────────┘                      │
│       ↓                                                       │
│  ┌───────────────────────────────────┐                      │
│  │ get_demo_system_prompt(level)     │                      │
│  ├───────────────────────────────────┤                      │
│  │ Level 1: M2 research              │                      │
│  │ Level 2: M2 + M3 research         │ ←─ _M3_RESEARCH_*  │
│  │ Level 3: M2 + M3 + SE research    │     _SE_RESEARCH_*  │
│  └───────────────────────────────────┘                      │
│       ↓                                                       │
│  ┌───────────────────────────────────┐                      │
│  │ Route by level:                   │                      │
│  ├───────────────────────────────────┤                      │
│  │ Level 1: stream_from_nvidia()     │                      │
│  │          ↓                         │                      │
│  │          M2 Council                │                      │
│  │                                    │                      │
│  │ Level 2: stream_from_nvidia()     │                      │
│  │          +                         │                      │
│  │          call_m3_prism(agent=1)   │ ←──────┐             │
│  │                                    │        │             │
│  │ Level 3: call_m3_prism(agent=None)│        │             │
│  │          (all 7 agents)            │        │             │
│  └───────────────────────────────────┘        │             │
│       ↓                                        │             │
│  StreamingResponse (SSE)                     │             │
│                                               │             │
└─────────────────────────────────────────────┼─────────────┘
                                              │
                  ┌──────────────────────────┘
                  │
              ┌───▼──────────────────────────┐
              │     M3 Backend               │
              ├──────────────────────────────┤
              │                              │
              │  POST /api/prism            │
              │  (accepts system_prompt,    │
              │   message, agent, venue_id) │
              │                              │
              │  Runs Prism agents 1–7      │
              │  Returns SSE stream         │
              │                              │
              └──────────────────────────────┘
```

---

## Notes

- **M3 DB is optional:** If M3 pool fails to init, graceful degradation — levels 2/3 still work but return empty M3 context
- **M3 API is optional:** If M3 API unreachable, falls back to friendly error message in response
- **Research files:** All loaded once at startup and cached. Missing files don't crash — they log and return placeholder text
- **Security:** demo_level embedded in JWT, can't be forged without `DEMO_JWT_SECRET`
- **Backwards compatible:** Existing level 1 behavior unchanged if M3 not configured

