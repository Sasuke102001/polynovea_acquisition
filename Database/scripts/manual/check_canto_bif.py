import json

# Check step6 output for Canto
path6 = r'D:\PolyNovea\Module 2\Google Raw Scrapper\Behavioural_Intelligence_Framework\Data\sobo\step_6_output.json'
print('Loading step_6...')
with open(path6, 'r', encoding='utf-8') as f:
    data6 = json.load(f)

print('Top-level keys:', list(data6.keys()))
venues6 = None
for k, v in data6.items():
    if isinstance(v, list) and len(v) > 10:
        venues6 = v
        print(f'Venues list key: "{k}", count: {len(v)}')
        if v:
            print('First item keys:', list(v[0].keys()))
        break

if venues6:
    matches = [v for v in venues6 if
               'canto' in str(v.get('name', '')).lower() or
               v.get('place_id') == 'ChIJSWqkIQ7O5zsRLZHOeXsM5J8']
    print(f'\nCanto in step6: {len(matches)}')
    if matches:
        m = matches[0]
        print('place_id:', m.get('place_id'))
        print('name:', m.get('name'))
        fitness = m.get('fitness_dimensions') or m.get('fitness_scores') or m.get('fitness') or {}
        print('fitness_dimensions:', json.dumps(fitness, indent=2)[:800])

# Also show full step3 behavioral_primitives for Canto
path3 = r'D:\PolyNovea\Module 2\Google Raw Scrapper\Behavioural_Intelligence_Framework\Data\sobo\step_3_signals_extracted.json'
with open(path3, 'r', encoding='utf-8') as f:
    data3 = json.load(f)
venues3 = data3.get('venues', [])
canto = next((v for v in venues3 if v.get('place_id') == 'ChIJSWqkIQ7O5zsRLZHOeXsM5J8'), None)
if canto:
    bp = canto.get('behavioral_primitives', {})
    print('\n--- Full behavioral_primitives ---')
    for cat, signals in bp.items():
        print(f'  {cat}: {[s["signal"] for s in signals]}')
    print('signal_coverage:', canto.get('signal_coverage'))
