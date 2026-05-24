import os, sys, psycopg2
sys.stdout.reconfigure(encoding='utf-8')

DB = {
    'host': 'polynovea-module2.cxeo8066g8t2.ap-south-1.rds.amazonaws.com',
    'port': 5432, 'dbname': 'polynovea_module2',
    'user': 'polynovea_admin', 'password': '07586277012Luna', 'sslmode': 'require'
}
conn = psycopg2.connect(**DB)
cur = conn.cursor()

cur.execute("""
    SELECT
        COUNT(*) FILTER (WHERE fitness_for_social_dwell > 0 OR fitness_for_office_lunch > 0
                              OR fitness_for_group_energy > 0 OR fitness_for_destination_visit > 0
                              OR fitness_for_repeat_habit > 0) AS has_signal,
        COUNT(*) FILTER (WHERE fitness_for_social_dwell = 0 AND fitness_for_office_lunch = 0
                              AND fitness_for_group_energy = 0 AND fitness_for_destination_visit = 0
                              AND fitness_for_repeat_habit = 0) AS all_zeros,
        COUNT(*) AS total
    FROM venue_fitness_dimensions WHERE source = 'google_reviews'
""")
r = cur.fetchone()
print(f"google_reviews — has_signal: {r[0]}  all_zero: {r[1]}  total: {r[2]}")

cur.execute("""
    SELECT
        ROUND(AVG(fitness_for_social_dwell)::numeric,3)  AS social,
        ROUND(AVG(fitness_for_office_lunch)::numeric,3)  AS office,
        ROUND(AVG(fitness_for_group_energy)::numeric,3)  AS group_e,
        ROUND(AVG(fitness_for_destination_visit)::numeric,3) AS dest,
        ROUND(AVG(fitness_for_repeat_habit)::numeric,3)  AS repeat
    FROM venue_fitness_dimensions WHERE source = 'google_reviews'
""")
r = cur.fetchone()
print(f"Avg scores — social:{r[0]}  office:{r[1]}  group:{r[2]}  dest:{r[3]}  repeat:{r[4]}")

# Compare with google averages for same venues
cur.execute("""
    SELECT
        ROUND(AVG(fitness_for_social_dwell)::numeric,3)  AS social,
        ROUND(AVG(fitness_for_office_lunch)::numeric,3)  AS office,
        ROUND(AVG(fitness_for_group_energy)::numeric,3)  AS group_e,
        ROUND(AVG(fitness_for_destination_visit)::numeric,3) AS dest,
        ROUND(AVG(fitness_for_repeat_habit)::numeric,3)  AS repeat
    FROM venue_fitness_dimensions
    WHERE source = 'google'
      AND venue_id IN (SELECT venue_id FROM venue_fitness_dimensions WHERE source = 'google_reviews')
""")
r = cur.fetchone()
print(f"Google avg (same venues) — social:{r[0]}  office:{r[1]}  group:{r[2]}  dest:{r[3]}  repeat:{r[4]}")

cur.close(); conn.close()
