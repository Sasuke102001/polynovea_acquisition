"""
Temporary script: extract individual reviews from genuine_broaster_chicken.jsonl blobs.
Run once to understand review content, then delete.
"""
import json, re, sys
sys.stdout.reconfigure(encoding='utf-8')

path = r"D:\PolyNovea\Module 2\Google Raw Scrapper\output\genuine_broaster_chicken.jsonl"

# Collect all unique text blobs that look like they start with a real review
# (reviewer name at the start)
NAME_PREFIX = re.compile(
    r'^([A-Z][a-zA-Z\s()\.]+?)\s+'
    r'(?:Local Guide[^\n]*?\s+)?'
    r'(\d+ (?:years?|months?|weeks?|days?) ago|Edited \d+ (?:years?|months?) ago)'
)

all_lines = []
with open(path, encoding='utf-8') as f:
    for line in f:
        try:
            obj = json.loads(line)
        except Exception:
            continue
        text = obj.get('review_text', '').strip()
        if not text or len(text) < 40:
            continue
        all_lines.append(text)

# Find the longest blob — it likely has all reviews concatenated
longest = max(all_lines, key=len)

# Parse individual reviews from the longest blob
# Pattern: Name + (Local Guide badge optional) + time_ago + optional meal/price + review text
REVIEW_BLOCK = re.compile(
    r'([A-Z][a-zA-Z\s()\.\']+?)\s+'           # reviewer name
    r'(?:Local Guide[^·\n]*?·\s*)?'            # optional badge
    r'(\d+ (?:years?|months?|weeks?|days?) ago|Edited \d+ (?:years?|months?) ago)'  # time
    r'([^\n]{0,100}?\n?)'                      # optional meal/price line
    r'(.+?)(?=(?:[A-Z][a-zA-Z\s()\.\']+?\s+(?:Local Guide|(?:\d+ (?:year|month|week|day)s? ago)))|\Z)',
    re.DOTALL
)

matches = REVIEW_BLOCK.findall(longest)
print(f"Reviews found in longest blob: {len(matches)}\n")
for i, (name, when, meta, body) in enumerate(matches, 1):
    body_clean = re.sub(r'\s+', ' ', body.strip())
    # Remove owner replies
    body_clean = re.sub(r'Genuine Broaster Chicken \(owner\).*', '', body_clean, flags=re.DOTALL).strip()
    # Remove emoji/reaction noise
    body_clean = re.sub(r'[^\x00-\x7F]+', '', body_clean).strip()
    if len(body_clean) < 20:
        continue
    print(f"=== {i}. {name.strip()} | {when.strip()} ===")
    if meta.strip():
        print(f"    [{meta.strip()}]")
    print(f"    {body_clean[:400]}")
    print()
