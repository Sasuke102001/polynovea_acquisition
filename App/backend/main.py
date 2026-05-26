"""
main.py
FastAPI application entry point.

Run:
    uvicorn main:app --reload --port 8000

Endpoints:
    GET /api/venues/search                     Screen 1
    GET /api/venues/{id}/overview              Screen 5
    GET /api/venues/{id}/similar               Screen 2
    GET /api/venues/{id}/transform             Screen 3
    GET /api/venues/{id}/marketing             Screen 4
    GET /api/venues/{id}/intelligence          Screen 6
    GET /api/venues/{id}/risk                  Screen 6 — Risk tab
    GET /api/venues/{id}/primitives            Screen 6 — Primitives tab
    GET /api/venues/{id}/benchmarks            Screen 6 — Benchmarks tab
    GET /api/venues/{id}/trends                Screen 6 — Trends tab
"""

from dotenv import load_dotenv

load_dotenv()  # Load .env BEFORE importing routers (so Supabase client can initialize)

from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from database import init_pool, close_pool
from routers import venues, overview, competitors, transform, marketing, intelligence, risk, primitives_tab, benchmarks, trends_tab, audience, chat, demo
from routers.providers import nvidia_key_count, mistral_available, mistral_model
from routers.council import _NEMOTRON, _DEEPSEEK, _MISTRAL_OR_QWEN


@asynccontextmanager
async def lifespan(app: FastAPI):
    await init_pool()
    from database import get_pool
    async with get_pool().acquire() as _conn:
        for _t in ("venue_similarity_deltas", "fitness_delta_rules", "venue_similarity",
                   "venue_demographic_scores", "venue_fitness_dimensions"):
            await _conn.execute(f"ANALYZE {_t}")
    yield
    await close_pool()


app = FastAPI(
    title="Polynovea Acquisition System API",
    version="1.0.0",
    description="Venue intelligence API — Module 2",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],   # Next.js dev server
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(venues.router,       prefix="/api/venues", tags=["venues"])
app.include_router(overview.router,     prefix="/api/venues", tags=["overview"])
app.include_router(competitors.router,  prefix="/api/venues", tags=["competitors"])
app.include_router(transform.router,    prefix="/api/venues", tags=["transform"])
app.include_router(marketing.router,    prefix="/api/venues", tags=["marketing"])
app.include_router(intelligence.router,   prefix="/api/venues", tags=["intelligence"])
app.include_router(risk.router,           prefix="/api/venues", tags=["risk"])
app.include_router(primitives_tab.router, prefix="/api/venues", tags=["primitives"])
app.include_router(benchmarks.router,     prefix="/api/venues", tags=["benchmarks"])
app.include_router(trends_tab.router,     prefix="/api/venues", tags=["trends"])
app.include_router(audience.router,       prefix="/api/venues", tags=["audience"])
app.include_router(chat.router,           prefix="/api/venues", tags=["chat"])
app.include_router(demo.router,           prefix="/api/demo",   tags=["demo"])


@app.get("/health")
async def health():
    return {"status": "ok", "service": "polynovea-acquisition-api"}


@app.get("/api/providers")
async def providers():
    return {
        "nvidia": {
            "keys_active": nvidia_key_count(),
            "models": {
                "nemotron": _NEMOTRON["model"],
                "deepseek":  _DEEPSEEK["model"],
                "council_third": _MISTRAL_OR_QWEN["model"],
            },
        },
        "mistral": {
            "configured": mistral_available(),
            "model": mistral_model() if mistral_available() else None,
        },
    }


