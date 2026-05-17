import asyncio
import asyncpg

VENUE_PLACE_ID = "effbel"

async def main():
    conn = await asyncpg.connect(
        host="polynovea-module2.cxeo8066g8t2.ap-south-1.rds.amazonaws.com",
        port=5432,
        database="polynovea_module2",
        user="polynovea_admin",
        password="REDACTED_DB_PASSWORD",
    )

    venue_id = await conn.fetchval(
        "SELECT id FROM venues WHERE place_id = $1", VENUE_PLACE_ID
    )
    print(f"Venue ID: {venue_id}")

    # Check existing columns on venue_fitness_dimensions
    cols = await conn.fetch(
        """
        SELECT column_name FROM information_schema.columns
        WHERE table_name = 'venue_fitness_dimensions'
        ORDER BY ordinal_position
        """
    )
    col_names = [r["column_name"] for r in cols]
    print(f"Fitness columns: {col_names}")

    has_monetization = "monetization_potential" in col_names

    if has_monetization:
        await conn.execute(
            """
            INSERT INTO venue_fitness_dimensions (
                venue_id,
                fitness_for_social_dwell,
                fitness_for_destination_visit,
                fitness_for_group_energy,
                fitness_for_repeat_habit,
                fitness_for_office_lunch,
                operational_quality,
                retention_strength,
                monetization_potential
            ) VALUES ($1,$2,$3,$4,$5,$6,$7,$8,$9)
            ON CONFLICT (venue_id) DO UPDATE SET
                fitness_for_social_dwell      = EXCLUDED.fitness_for_social_dwell,
                fitness_for_destination_visit = EXCLUDED.fitness_for_destination_visit,
                fitness_for_group_energy      = EXCLUDED.fitness_for_group_energy,
                fitness_for_repeat_habit      = EXCLUDED.fitness_for_repeat_habit,
                fitness_for_office_lunch      = EXCLUDED.fitness_for_office_lunch,
                operational_quality           = EXCLUDED.operational_quality,
                retention_strength            = EXCLUDED.retention_strength,
                monetization_potential        = EXCLUDED.monetization_potential
            """,
            venue_id, 0.82, 0.76, 0.80, 0.72, 0.30, 0.58, 0.74, 0.72,
        )
    else:
        await conn.execute(
            """
            INSERT INTO venue_fitness_dimensions (
                venue_id,
                fitness_for_social_dwell,
                fitness_for_destination_visit,
                fitness_for_group_energy,
                fitness_for_repeat_habit,
                fitness_for_office_lunch,
                operational_quality,
                retention_strength
            ) VALUES ($1,$2,$3,$4,$5,$6,$7,$8)
            ON CONFLICT (venue_id) DO UPDATE SET
                fitness_for_social_dwell      = EXCLUDED.fitness_for_social_dwell,
                fitness_for_destination_visit = EXCLUDED.fitness_for_destination_visit,
                fitness_for_group_energy      = EXCLUDED.fitness_for_group_energy,
                fitness_for_repeat_habit      = EXCLUDED.fitness_for_repeat_habit,
                fitness_for_office_lunch      = EXCLUDED.fitness_for_office_lunch,
                operational_quality           = EXCLUDED.operational_quality,
                retention_strength            = EXCLUDED.retention_strength
            """,
            venue_id, 0.82, 0.76, 0.80, 0.72, 0.30, 0.58, 0.74,
        )
    print("Step 2: fitness dimensions done")

    # Step 3: Demographic scores
    segments = [
        ("college_kids",   0.88, 1),
        ("couples",        0.75, 2),
        ("working_women",  0.55, 3),
        ("premium",        0.52, 4),
        ("families",       0.40, 5),
        ("office_workers", 0.28, 6),
        ("solo_diners",    0.22, 7),
    ]
    for seg_id, score, rank in segments:
        await conn.execute(
            """
            INSERT INTO venue_demographic_scores (venue_id, segment_id, alignment_score, segment_rank)
            VALUES ($1,$2,$3,$4)
            ON CONFLICT (venue_id, segment_id) DO UPDATE SET
                alignment_score = EXCLUDED.alignment_score,
                segment_rank    = EXCLUDED.segment_rank
            """,
            venue_id, seg_id, score, rank,
        )
    print("Step 3: demographic scores done")

    # Step 4: Venue vector
    await conn.execute(
        """
        INSERT INTO venue_vectors (venue_id, fitness_vector, vector_source, last_computed)
        VALUES ($1, $2, 'manual', NOW())
        ON CONFLICT (venue_id) DO UPDATE SET
            fitness_vector = EXCLUDED.fitness_vector,
            vector_source  = EXCLUDED.vector_source,
            last_computed  = EXCLUDED.last_computed
        """,
        venue_id,
        [0.82, 0.76, 0.80, 0.72, 0.30, 0.58, 0.74, 0.72],
    )
    print("Step 4: venue vector done")

    # Verify
    row = await conn.fetchrow(
        """
        SELECT v.id, v.name, v.area, v.city,
               fd.fitness_for_social_dwell, fd.fitness_for_group_energy,
               fd.retention_strength, fd.operational_quality,
               (SELECT COUNT(*) FROM venue_demographic_scores WHERE venue_id = v.id) AS seg_count
        FROM venues v
        JOIN venue_fitness_dimensions fd ON fd.venue_id = v.id
        WHERE v.place_id = $1
        """,
        VENUE_PLACE_ID,
    )
    print(f"\nVERIFY: {dict(row)}")
    await conn.close()

asyncio.run(main())
