import psycopg2, os
from dotenv import load_dotenv

load_dotenv()

conn = psycopg2.connect(
    host=os.getenv('PG_HOST'),
    port=int(os.getenv('PG_PORT', 5432)),
    dbname=os.getenv('PG_DB'),
    user=os.getenv('PG_USER'),
    password=os.getenv('PG_PASSWORD'),
    sslmode='require'
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
