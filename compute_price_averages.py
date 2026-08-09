import sys, json, re, urllib.request
sys.stdout.reconfigure(encoding='utf-8')

KEY = os.environ['SUPABASE_ANON_KEY']
SUPABASE_URL = 'https://ankyjpgcocsvvtyyymys.supabase.co'

def fetch_paginated(path):
    rows, offset = [], 0
    while True:
        req = urllib.request.Request(f'{SUPABASE_URL}/rest/v1/{path}')
        req.add_header('apikey', KEY)
        req.add_header('Authorization', 'Bearer ' + KEY)
        req.add_header('Range-Unit', 'items')
        req.add_header('Range', f'{offset}-{offset+999}')
        with urllib.request.urlopen(req) as r:
            batch = json.loads(r.read())
        rows.extend(batch)
        if len(batch) < 1000: break
        offset += 1000
    return rows

CHECKUP_KW = ['checkup','check-up','exam','examination','consult','assessment']
CHECKUP_EX = ['hygien','scale','clean','polish','x-ray','xray','filling','extraction','crown','root canal']

def is_checkup(row):
    t = (row.get('treatment') or '').lower()
    return any(k in t for k in CHECKUP_KW) and not any(e in t for e in CHECKUP_EX)

def extract_price(row):
    if row.get('price_nzd') and float(row['price_nzd']) > 0:
        return float(row['price_nzd'])
    m = re.search(r'\$(\d+)', row.get('price_label') or '')
    return float(m.group(1)) if m else None

SANITY_MIN, SANITY_MAX = 50, 400

print('Fetching clinics...')
clinics = fetch_paginated('dental_clinics?select=id,city,region')
print(f'  {len(clinics)} clinics')

print('Fetching scraped_prices...')
prices = fetch_paginated('scraped_prices?select=clinic_id,treatment,price_nzd,price_label')
print(f'  {len(prices)} price rows')

clinic_map = {c['id']: c for c in clinics}

# Lowest valid checkup price per clinic
clinic_min = {}
for row in prices:
    if not is_checkup(row): continue
    p = extract_price(row)
    if p is None or p < SANITY_MIN or p > SANITY_MAX: continue
    cid = row['clinic_id']
    if cid not in clinic_min or p < clinic_min[cid]:
        clinic_min[cid] = p

print(f'  {len(clinic_min)} clinics with valid checkup prices')

# Group by city and region
city_prices, region_prices = {}, {}
for cid, price in clinic_min.items():
    c = clinic_map.get(cid)
    if not c: continue
    city = (c.get('city') or '').strip()
    region = (c.get('region') or '').strip()
    if city and city != 'NA':
        city_prices.setdefault(city, []).append(price)
    if region:
        region_prices.setdefault(region, []).append(price)

MIN_CLINICS = 1

cities = {city: {'avg': round(sum(p)/len(p), 1), 'clinics': len(p)}
          for city, p in city_prices.items() if len(p) >= MIN_CLINICS}
regions = {region: {'avg': round(sum(p)/len(p), 1), 'clinics': len(p)}
           for region, p in region_prices.items() if len(p) >= MIN_CLINICS}

out = {'cities': cities, 'regions': regions}
path = r'docs\assets\data\price-averages.json'
with open(path, 'w', encoding='utf-8') as f:
    json.dump(out, f, indent=2, ensure_ascii=False)

print(f'\nWrote {path}')
print(f'  {len(cities)} cities, {len(regions)} regions')

print(f'\nAll cities (sorted by avg price):')
for city, d in sorted(cities.items(), key=lambda x: x[1]['avg']):
    print(f'  ${d["avg"]:>6.1f}  {d["clinics"]:>3} clinics  {city}')

print(f'\nAll regions:')
for region, d in sorted(regions.items(), key=lambda x: x[1]['avg']):
    print(f'  ${d["avg"]:>6.1f}  {d["clinics"]:>3} clinics  {region}')
