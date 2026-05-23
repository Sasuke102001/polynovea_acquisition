"""
routers/demo.py
JWT-gated demo mode — shareable links for prospect presentations.

Token payload:  venue_id | prospect_name | exp | iat
Algorithm:      HS256 using DEMO_JWT_SECRET env var

Endpoints:
  POST /api/demo/generate           Create a signed token (CLI / internal use only)
  GET  /api/demo/verify/{token}     Validate token + return venue metadata
  POST /api/demo/{token}/chat       Demo chat (teaser mode, logged with is_demo=True)
"""

import asyncio
import os
import time
from datetime import datetime, timezone
from typing import AsyncGenerator

import httpx
import jwt  # PyJWT
from fastapi import APIRouter, Header, HTTPException
from fastapi.responses import StreamingResponse
from pydantic import BaseModel

from database import get_pool
from prompts import get_demo_system_prompt
from routers.chat import fetch_venue_context, stream_from_nvidia

router = APIRouter()

_DEFAULT_EXPIRES_HOURS = 72


# ─── Supabase demo logging ─────────────────────────────────────────────────────

async def log_demo_chat(
    venue_id: int,
    venue_name: str,
    prospect_name: str,
    question: str,
    response: str,
) -> None:
    """Fire-and-forget: log demo chat exchange to demo_chat_logs table."""
    try:
        supabase_url = os.getenv("SUPABASE_URL", "").rstrip("/")
        supabase_key = os.getenv("SUPABASE_SECRET_KEY") or os.getenv("SUPABASE_ANON_KEY", "")
        if not supabase_url or not supabase_key:
            return

        headers = {
            "apikey":        supabase_key,
            "Authorization": f"Bearer {supabase_key}",
            "Content-Type":  "application/json",
        }
        payload = {
            "venue_id":      str(venue_id),
            "venue_name":    venue_name,
            "prospect_name": prospect_name,
            "question":      question,
            "response":      response,
        }
        async with httpx.AsyncClient(timeout=10) as client:
            await client.post(
                f"{supabase_url}/rest/v1/demo_chat_logs",
                json=payload,
                headers=headers,
            )
    except Exception as e:
        print(f"[demo] Supabase logging failed: {e}")


def _secret() -> str:
    s = os.getenv("DEMO_JWT_SECRET", "")
    if not s:
        raise HTTPException(
            status_code=503,
            detail="Demo feature not configured — set DEMO_JWT_SECRET in .env",
        )
    return s


def _decode(token: str) -> dict:
    """Decode and validate JWT. Raises HTTPException on any failure."""
    try:
        return jwt.decode(token, _secret(), algorithms=["HS256"])
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=410, detail="This demo link has expired.")
    except jwt.InvalidTokenError as exc:
        raise HTTPException(status_code=401, detail=f"Invalid demo link: {exc}")


# ─── Token generation ─────────────────────────────────────────────────────────

class GenerateRequest(BaseModel):
    venue_id: int
    prospect_name: str
    expires_hours: int = _DEFAULT_EXPIRES_HOURS


class GenerateResponse(BaseModel):
    token: str
    expires_at: str
    demo_url: str


def _check_admin(x_admin_key: str | None) -> None:
    """Validate the admin key header. Raises 403 if wrong."""
    required = os.getenv("ADMIN_KEY", "")
    if required and x_admin_key != required:
        raise HTTPException(status_code=403, detail="Invalid admin key.")


@router.post("/generate", response_model=GenerateResponse)
async def generate_token(
    req: GenerateRequest,
    x_admin_key: str | None = Header(default=None),
):
    """
    Generate a signed JWT demo token.
    Requires X-Admin-Key header matching ADMIN_KEY env var.
    """
    _check_admin(x_admin_key)
    now = int(time.time())
    payload = {
        "venue_id":      req.venue_id,
        "prospect_name": req.prospect_name,
        "exp":           now + req.expires_hours * 3600,
        "iat":           now,
    }
    token = jwt.encode(payload, _secret(), algorithm="HS256")
    expires_at = datetime.fromtimestamp(int(payload["exp"]), tz=timezone.utc).isoformat()

    frontend_base = os.getenv("FRONTEND_URL", "http://localhost:3000").rstrip("/")
    return GenerateResponse(
        token=token,
        expires_at=expires_at,
        demo_url=f"{frontend_base}/demo/{token}",
    )


# ─── Token verification ───────────────────────────────────────────────────────

class VerifyResponse(BaseModel):
    venue_id: int
    prospect_name: str
    expires_at: str
    venue_name: str
    venue_area: str
    venue_city: str


@router.get("/verify/{token}", response_model=VerifyResponse)
async def verify_token(token: str):
    """
    Validate a demo token and return venue metadata.
    Called by the frontend on page load to display venue info before chat starts.
    """
    payload  = _decode(token)
    venue_id = int(payload["venue_id"])

    pool = get_pool()
    async with pool.acquire() as conn:
        venue = await conn.fetchrow(
            "SELECT name, area, city FROM venues WHERE id = $1",
            venue_id,
        )
    if not venue:
        raise HTTPException(status_code=404, detail="Venue not found")

    expires_at = datetime.fromtimestamp(int(payload["exp"]), tz=timezone.utc).isoformat()
    return VerifyResponse(
        venue_id=venue_id,
        prospect_name=str(payload["prospect_name"]),
        expires_at=expires_at,
        venue_name=venue["name"],
        venue_area=venue["area"] or "",
        venue_city=venue["city"] or "",
    )


# ─── Demo chat ────────────────────────────────────────────────────────────────

class DemoChatRequest(BaseModel):
    question: str


@router.post("/{token}/chat")
async def demo_chat(token: str, req: DemoChatRequest):
    """
    Demo-mode chat — validates token, fetches real venue context,
    applies teaser system prompt, streams response, logs with is_demo=True.
    """
    payload  = _decode(token)
    venue_id = int(payload["venue_id"])
    prospect = str(payload["prospect_name"])

    try:
        context = await fetch_venue_context(venue_id, "overview")
    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Context error: {exc}")

    system_prompt = get_demo_system_prompt(context, prospect)

    async def _generate() -> AsyncGenerator[str, None]:
        buffer: list[str] = []
        try:
            async for chunk in stream_from_nvidia(system_prompt, req.question, "overview"):
                buffer.append(chunk)
                yield chunk
        except Exception as exc:
            yield f"\n\n[Error: {exc}]"
        finally:
            full_response = "".join(buffer)
            if full_response:
                asyncio.create_task(
                    log_demo_chat(
                        venue_id,
                        context["venue_name"],
                        prospect,
                        req.question,
                        full_response,
                    )
                )

    return StreamingResponse(_generate(), media_type="text/event-stream")
