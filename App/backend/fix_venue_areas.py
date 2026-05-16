"""
fix_venue_areas.py
One-time migration: patch venues.name and venues.area using
geo_google.resolved_locality from the step_1_venues_refined.json files.

The DB was populated with the search-area tag (e.g. "Khandeshwar") which was
the query used to discover the venue, not the actual Google-resolved locality.
The correct area sits in geo_google.resolved_locality.

Run:
    python fix_venue_areas.py
"""

import asyncio
import json
import os
import sys
import asyncpg
import ssl
from dotenv import load_dotenv

load_dotenv()

SOURCE_FILES = [
    ("D:/PolyNovea/Module 2/Google Places API/data/navi-mumbai/step_1_venues_refined.json", "Navi Mumbai"),
    ("D:/PolyNovea/Module 2/Google Places API/data/thane/step_1_venues_refined.json",       "Thane"),
    ("D:/PolyNovea/Module 2/Google Places API/data/mumbai/main/step_1_venues_refined.json", "Mumbai"),
    ("D:/PolyNovea/Module 2/Google Places API/data/mumbai/sobo/step_1_venues_refined.json", "Mumbai"),
]


def build_lookup() -> dict:
    """
    Returns {place_id: {name, area, city}} where area = geo_google.resolved_locality.
    If no geo_google data, falls back to the raw area field.
    """
    lookup: dict = {}
    for fpath, city in SOURCE_FILES:
        with open(fpath, encoding="utf-8") as f:
            venues = json.load(f)

        for v in venues:
            pid = v.get("place_id", "").strip()
            if not pid:
                continue

            name = v.get("name", "").strip()
            geo  = v.get("geo_google") or {}
            area = geo.get("resolved_locality") or v.get("area", "")

            # Later files (sobo) may re-add Mumbai venues — last write wins,
            # but since place_ids are unique across cities this shouldn't collide.
            lookup[pid] = {"name": name, "area": area, "city": city}

    return lookup


async def run():
    ssl_ctx = ssl.create_default_context()
    ssl_ctx.check_hostname = False
    ssl_ctx.verify_mode   = ssl.CERT_NONE

    conn = await asyncpg.connect(
        host=os.getenv("PG_HOST"),
        port=int(os.getenv("PG_PORT", 5432)),
        database=os.getenv("PG_DB"),
        user=os.getenv("PG_USER"),
        password=os.getenv("PG_PASSWORD"),
        ssl=ssl_ctx,
    )

    print("Building lookup from JSON files …")
    lookup = build_lookup()
    print(f"  Loaded {len(lookup):,} unique place_ids from JSON\n")

    # Fetch all DB rows
    rows = await conn.fetch("SELECT id, place_id, name, area, city FROM venues")
    print(f"DB has {len(rows):,} venues\n")

    updates = []
    skipped_no_json = 0
    skipped_same    = 0

    for row in rows:
        pid = row["place_id"]
        src = lookup.get(pid)
        if not src:
            skipped_no_json += 1
            continue

        new_name = src["name"]
        new_area = src["area"]

        if new_name == row["name"] and new_area == row["area"]:
            skipped_same += 1
            continue

        updates.append((new_name, new_area, row["id"]))

    print(f"  Venues to update:    {len(updates):,}")
    print(f"  Already correct:     {skipped_same:,}")
    print(f"  Not in JSON (skip):  {skipped_no_json:,}")
    print()

    if not updates:
        print("Nothing to do.")
        await conn.close()
        return

    # Batch update
    print("Applying updates …")
    async with conn.transaction():
        await conn.executemany(
            "UPDATE venues SET name = $1, area = $2 WHERE id = $3",
            updates,
        )

    print(f"Done — {len(updates):,} venues patched.\n")

    # Spot-check Broaster
    row = await conn.fetchrow(
        "SELECT name, area, city FROM venues WHERE place_id = $1",
        "ChIJR9nrEdHA5zsRsG3YqCmSWmo",
    )
    if row:
        print(f"Spot-check Genuine Broaster Chicken → area: {row['area']} (expected: Vashi)")
    else:
        print("Broaster not found in DB (different place_id?)")

    await conn.close()


if __name__ == "__main__":
    asyncio.run(run())
