import psycopg2, os

conn = psycopg2.connect(
    host=os.getenv('PG_HOST', 'polynovea-module2.cxeo8066g8t2.ap-south-1.rds.amazonaws.com'),
    port=5432, dbname='polynovea_module2',
    user='polynovea_admin', password='9167032236Subro', sslmode='require'
)
cur = conn.cursor()
cur.execute("SELECT tablename FROM pg_tables WHERE schemaname='public' ORDER BY tablename")
tables = [r[0] for r in cur.fetchall()]
print()
print('  TABLE                                   ROWS')
print('  ' + '-' * 50)
for t in tables:
    cur.execute(f'SELECT COUNT(*) FROM {t}')
    n = cur.fetchone()[0]
    print(f'  {t:<42} {n:>7,}')
print()
cur.close()
conn.close()
