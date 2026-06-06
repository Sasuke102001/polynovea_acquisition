import psycopg2, json

conn = psycopg2.connect(
    host='polynovea-module2.cxeo8066g8t2.ap-south-1.rds.amazonaws.com',
    port=5432, dbname='polynovea_module2', user='polynovea_admin',
    password='REDACTED_DB_PASSWORD', sslmode='require'
)
cur = conn.cursor()

test_ids = ['ChIJP-sAFgDP5zsRawlT7zljxC0', 'ChIJHyAROpTJ5zsReat7W9I6gmw', 'ChIJ_9R2kvPR5zsR1ENER48S3Iw']
cur.execute('SELECT place_id, id FROM venues WHERE place_id = ANY(%s)', (test_ids,))
rows = cur.fetchall()
print(f'Found {len(rows)} of 3 test place_ids in venues:')
for r in rows: print(' ', r)

# How many sobo place_ids from the patterns file exist in DB
with open(r'D:\PolyNovea\PolyNovea\Docx\Company Docx\Acquistion System\Database\data\raw\google_reviews\sobo\step_4_patterns_recognized.json', encoding='utf-8') as f:
    data = json.load(f)

all_place_ids = set()
for info in data.get('patterns_detected', {}).values():
    for v in info.get('venues', []):
        if isinstance(v, dict) and v.get('place_id'):
            all_place_ids.add(v['place_id'])

print(f'\nUnique place_ids in sobo patterns file: {len(all_place_ids)}')

cur.execute('SELECT place_id FROM venues WHERE place_id = ANY(%s)', (list(all_place_ids),))
found = {r[0] for r in cur.fetchall()}
print(f'Of those, found in venues table:       {len(found)}')
print(f'Missing from venues table:             {len(all_place_ids - found)}')

cur.close(); conn.close()
