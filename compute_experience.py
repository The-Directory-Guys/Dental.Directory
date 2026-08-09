import sys, json, re, urllib.request
sys.stdout.reconfigure(encoding='utf-8')

KEY = os.environ['SUPABASE_ANON_KEY']
BASE = 'https://ankyjpgcocsvvtyyymys.supabase.co/rest/v1/clinic_practitioners'
CURRENT_YEAR = 2026

def fetch_all():
    rows, offset = [], 0
    while True:
        req = urllib.request.Request(f'{BASE}?select=clinic_id,experience')
        req.add_header('apikey', KEY)
        req.add_header('Authorization', 'Bearer ' + KEY)
        req.add_header('Range-Unit', 'items')
        req.add_header('Range', f'{offset}-{offset+999}')
        with urllib.request.urlopen(req) as r:
            batch = json.loads(r.read())
        rows.extend(batch)
        if len(batch) < 1000:
            break
        offset += 1000
    return rows

def parse_years(text):
    if not text:
        return None
    t = text.lower()

    # "over/more than a decade"
    if re.search(r'(?:over|more\s+than)\s+a\s+decade', t):
        return 10

    # explicit "X years of/in/as experience/practice/dentistry"
    m = re.search(r'(?:over|more\s+than|nearly|almost|around)?\s*(\d+)\+?\s*years?\s*(?:of\s*)?(?:experience|exp|in\b|as\b|practicing|practice)', t)
    if m:
        return int(m.group(1))

    # "X+ years" anywhere
    m = re.search(r'(\d+)\+\s*years?', t)
    if m:
        return int(m.group(1))

    # graduation year patterns
    m = re.search(r'graduated\D{0,40}?(19[6-9]\d|20[0-2]\d)', t)
    if m:
        return max(0, CURRENT_YEAR - int(m.group(1)))

    # "graduated in YEAR" with year before "from"
    m = re.search(r'graduated\s+(?:in\s+)?(19[6-9]\d|20[0-2]\d)', t)
    if m:
        return max(0, CURRENT_YEAR - int(m.group(1)))

    # started/began career
    m = re.search(r'(?:started|began|career|qualified|practice)\D{0,20}?(19[6-9]\d|20[0-2]\d)', t)
    if m:
        return max(0, CURRENT_YEAR - int(m.group(1)))

    # any standalone 4-digit year 1965-2021
    m = re.search(r'\b(19[6-9]\d|200\d|201\d|202[01])\b', t)
    if m:
        return max(0, CURRENT_YEAR - int(m.group(1)))

    return None

print('Fetching practitioners...')
rows = fetch_all()
print(f'  {len(rows)} rows')

# Max parsed years per clinic
clinic_max = {}
parsed_count = 0
for row in rows:
    cid = row.get('clinic_id')
    if not cid:
        continue
    yrs = parse_years(row.get('experience'))
    if yrs is None:
        continue
    if yrs < 1 or yrs > 60:  # sanity
        continue
    parsed_count += 1
    if cid not in clinic_max or yrs > clinic_max[cid]:
        clinic_max[cid] = yrs

print(f'  {parsed_count} rows with parseable years')
print(f'  {len(clinic_max)} clinics with experience data')

# Distribution
thresholds = [5, 10, 15, 20, 25, 30]
for t in thresholds:
    n = sum(1 for v in clinic_max.values() if v >= t)
    print(f'  {n} clinics with {t}+ years')

out_path = r'docs\assets\data\clinic-experience.json'
with open(out_path, 'w', encoding='utf-8') as f:
    json.dump(clinic_max, f, separators=(',', ':'))

print(f'\nWrote {out_path}')
