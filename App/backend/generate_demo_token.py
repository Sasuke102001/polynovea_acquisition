#!/usr/bin/env python3
"""
generate_demo_token.py
CLI script to create a signed Polynovea demo token.

Usage:
  python generate_demo_token.py --venue-id 223 --prospect "John Smith"
  python generate_demo_token.py --venue-id 223 --prospect "The Kapoor Group" --hours 168

The generated URL goes to /demo/<token> on the frontend.
Send it to the prospect — they get a real AI preview of their venue's intelligence.
"""

import argparse
import os
import sys
import time
from datetime import datetime, timezone

from dotenv import load_dotenv

load_dotenv()

try:
    import jwt
except ImportError:
    print("ERROR: PyJWT not installed. Run: pip install PyJWT>=2.8.0")
    sys.exit(1)


DEFAULT_EXPIRES_HOURS = 720
MAX_EXPIRES_HOURS = 24 * 365


def _generate(venue_id: int, prospect_name: str, expires_hours: int, demo_level: int) -> dict:
    secret = os.getenv("DEMO_JWT_SECRET", "")
    if not secret:
        print("ERROR: DEMO_JWT_SECRET not set in .env")
        sys.exit(1)
    if expires_hours < 1 or expires_hours > MAX_EXPIRES_HOURS:
        print(f"ERROR: --hours must be between 1 and {MAX_EXPIRES_HOURS}")
        sys.exit(1)
    if demo_level not in (1, 2, 3, 4):
        print("ERROR: --demo-level must be 1, 2, 3, or 4")
        sys.exit(1)

    now = int(time.time())
    payload = {
        "venue_id":      venue_id,
        "prospect_name": prospect_name,
        "demo_level":    demo_level,
        "exp":           now + expires_hours * 3600,
        "iat":           now,
    }
    token      = jwt.encode(payload, secret, algorithm="HS256")
    expires_at = datetime.fromtimestamp(payload["exp"], tz=timezone.utc).strftime(
        "%Y-%m-%d %H:%M UTC"
    )
    frontend   = os.getenv("FRONTEND_URL", "http://localhost:3000").rstrip("/")
    demo_url   = f"{frontend}/demo/{token}"

    return {
        "token":      token,
        "expires_at": expires_at,
        "demo_url":   demo_url,
    }


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Generate a Polynovea demo token for a prospect"
    )
    parser.add_argument(
        "--venue-id", type=int, required=True,
        help="Venue ID from the database (e.g. 223 for Aphrodite)"
    )
    parser.add_argument(
        "--prospect", type=str, required=True,
        help='Prospect name — shown in the AI chat CTA (e.g. "John Smith")'
    )
    parser.add_argument(
        "--hours", type=int, default=DEFAULT_EXPIRES_HOURS,
        help=f"How long the link stays valid in hours (default: {DEFAULT_EXPIRES_HOURS})"
    )
    parser.add_argument(
        "--demo-level", type=int, default=1,
        help="Demo mode: 1=single model, 2=council, 3=prism, 4=council+prism"
    )
    args = parser.parse_args()

    result = _generate(args.venue_id, args.prospect, args.hours, args.demo_level)

    print()
    print("Demo token generated")
    print(f"  Prospect  : {args.prospect}")
    print(f"  Venue ID  : {args.venue_id}")
    print(f"  Mode      : {args.demo_level}")
    print(f"  Expires   : {result['expires_at']}  ({args.hours}h)")
    print()
    print("Demo URL (send this to the prospect):")
    print(f"  {result['demo_url']}")
    print()
