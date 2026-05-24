"""
debug_blend_diff.py
For thane/navi-mumbai venues that have both google + google_reviews,
compare blended vs google-only vs google_reviews scores to see if
the blend actually shifted anything meaningful.
"""
import os, sys
import psycopg2

sys.stdout.reconfigure(encoding='utf-8')

DB_CONFIG = {
    'host':     os.getenv('PG_HOST',     'polynovea-module2.cxeo8066g8t2.ap-south-1.rds.amazonaws.com'),
    'port':     int(os.getenv('PG_PORT', 5432)),
    'dbname':   os.getenv('PG_DB',       'polynovea_module2'),
    'user':     os.getenv('PG_USER',     'polynovea_admin'),
    'password': os.getenv('PG_PASSWORD', 'REDACTED_DB_PASSWORD'),
    'sslmode':  'require',
}

conn   = psycopg2.connect(**DB_CONFIG)
cursor = conn.cursor()

# Find venues that have all 3: google, google_reviews, and blended
cursor.execute("""
    SELECT v.name, v.area,
           g.fitness_for_social_dwell  AS g_social,
           gr.fitness_for_social_dwell AS gr_social,
           b.fitness_for_social_dwell  AS b_social,
           g.fitness_for_office_lunch  AS g_office,
           gr.fitness_for_office_lunch AS gr_office,
           b.fitness_for_office_lunch  AS b_office,
           ABS(g.fitness_for_social_dwell - gr.fitness_for_social_dwell) AS delta
    FROM venues v
    JOIN venue_fitness_dimensions g  ON g.venue_id  = v.id AND g.source  = 'google'
    JOIN venue_fitness_dimensions gr ON gr.venue_id = v.id AND gr.source = 'google_reviews'
    JOIN venue_fitness_dimensions b  ON b.venue_id  = v.id AND b.source  = 'blended'
    WHERE v.area IN ('Thane', 'Navi Mumbai', 'Thane West', 'Navi-Mumbai')
    ORDER BY ABS(g.fitness_for_social_dwell - gr.fitness_for_social_dwell) DESC
    LIMIT 15
""")

rows = cursor.fetchall()
print(f"\nTop venues where google vs google_reviews diverge most (social_dwell):\n")
print(f"{'Venue':<35} {'Area':<15} {'G':>6} {'GR':>6} {'BLD':>6} | {'G_off':>6} {'GR_off':>6} {'BLD_off':>6}  delta")
print("-"*110)
for r in rows:
    name, area, gs, grs, bs, go, gro, bo, delta = r
    print(f"{str(name)[:34]:<35} {str(area)[:14]:<15} {gs:>6.3f} {grs:>6.3f} {bs:>6.3f} | {go:>6.3f} {gro:>6.3f} {bo:>6.3f}  {delta:.3f}")

# Also check: are blended scores identical to google scores for any venues?
cursor.execute("""
    SELECT COUNT(*) FROM venues v
    JOIN venue_fitness_dimensions g  ON g.venue_id  = v.id AND g.source  = 'google'
    JOIN venue_fitness_dimensions gr ON gr.venue_id = v.id AND gr.source = 'google_reviews'
    JOIN venue_fitness_dimensions b  ON b.venue_id  = v.id AND b.source  = 'blended'
    WHERE ROUND(g.fitness_for_social_dwell::numeric, 4) = ROUND(b.fitness_for_social_dwell::numeric, 4)
      AND ROUND(g.fitness_for_office_lunch::numeric, 4) = ROUND(b.fitness_for_office_lunch::numeric, 4)
""")
identical = cursor.fetchone()[0]
print(f"\nVenues where blended == google exactly (all dims): {identical}")

cursor.close()
conn.close()
