import psycopg2

conn = psycopg2.connect(
    host='polynovea-module2.cxeo8066g8t2.ap-south-1.rds.amazonaws.com',
    port=5432, dbname='polynovea_module2', user='polynovea_admin',
    password='REDACTED_DB_PASSWORD', sslmode='require'
)
cur = conn.cursor()

venue_id = 1301

cur.execute("SELECT name, area, city FROM venues WHERE id = %s", (venue_id,))
v = cur.fetchone()
print(f"Venue: {v}\n")

# Get column names
cur.execute("""
    SELECT column_name FROM information_schema.columns
    WHERE table_name = 'venue_fitness_dimensions'
    ORDER BY ordinal_position
""")
cols = [r[0] for r in cur.fetchall()]
print("Columns:", cols)

# Get all rows for this venue
cur.execute("SELECT * FROM venue_fitness_dimensions WHERE venue_id = %s ORDER BY source", (venue_id,))
rows = cur.fetchall()
print(f"\nSources loaded: {[r[cols.index('source')] for r in rows]}\n")
for r in rows:
    row_dict = dict(zip(cols, r))
    print(f"--- {row_dict['source']} ---")
    for k, val in row_dict.items():
        if val is not None and k not in ('id', 'venue_id', 'created_at', 'updated_at'):
            print(f"  {k}: {val}")

cur.close()
conn.close()
