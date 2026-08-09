import sys
import json
import urllib.request
sys.stdout.reconfigure(encoding='utf-8')

SUPABASE_URL = 'https://ankyjpgcocsvvtyyymys.supabase.co'
SUPABASE_KEY = os.environ['SUPABASE_ANON_KEY']

HYGIENIST_KEYWORDS = ['hygienist', 'hygiene', 'scale', 'clean', 'polish', 'periodontal', 'perio']
EXCLUDE_KEYWORDS = ['exam', 'checkup', 'check-up', 'x-ray', 'xray', 'consult', 'extraction', 'filling', 'crown', 'whitening', 'bleach']

def fetch_paginated(table, select='*', filters=''):
    all_rows = []
    offset = 0
    while True:
        sep = '&' if filters else ''
        path = f'{table}?select={select}{sep}{filters}'
        url = SUPABASE_URL + '/rest/v1/' + path
        req = urllib.request.Request(url)
        req.add_header('apikey', SUPABASE_KEY)
        req.add_header('Authorization', 'Bearer ' + SUPABASE_KEY)
        req.add_header('Accept', 'application/json')
        req.add_header('Range-Unit', 'items')
        req.add_header('Range', f'{offset}-{offset+999}')
        with urllib.request.urlopen(req) as resp:
            batch = json.loads(resp.read().decode('utf-8'))
        all_rows.extend(batch)
        if len(batch) < 1000:
            break
        offset += 1000
    return all_rows

def is_hygienist_row(row):
    t = (row.get('treatment') or '').lower()
    label = (row.get('price_label') or '').lower()
    combined = t + ' ' + label
    if any(kw in combined for kw in HYGIENIST_KEYWORDS):
        if not any(ex in t for ex in EXCLUDE_KEYWORDS):
            return True
    return False

def extract_price(row):
    if row.get('price_nzd') and row['price_nzd'] > 0:
        return float(row['price_nzd'])
    import re
    label = row.get('price_label') or ''
    m = re.search(r'\$(\d+)', label)
    if m:
        return float(m.group(1))
    return None

print("Fetching all scraped_prices...")
all_prices = fetch_paginated('scraped_prices', 'id,clinic_id,treatment,price_nzd,price_label')
print(f"  {len(all_prices)} total price rows")

print("Fetching all clinics...")
all_clinics = fetch_paginated('dental_clinics', 'id,name,city,region')
print(f"  {len(all_clinics)} clinics")

clinic_map = {c['id']: c for c in all_clinics}

# For each clinic, find the lowest valid hygienist price
SANITY_MIN = 50
SANITY_MAX = 400

clinic_min_price = {}
for row in all_prices:
    if not is_hygienist_row(row):
        continue
    price = extract_price(row)
    if price is None or price < SANITY_MIN or price > SANITY_MAX:
        continue
    cid = row['clinic_id']
    if cid not in clinic_min_price or price < clinic_min_price[cid]:
        clinic_min_price[cid] = price

print(f"  {len(clinic_min_price)} clinics with valid hygienist prices")

# Group by city and region
city_prices = {}
region_prices = {}

for cid, price in clinic_min_price.items():
    clinic = clinic_map.get(cid)
    if not clinic:
        continue
    city = clinic.get('city') or ''
    region = clinic.get('region') or ''
    if city:
        city_prices.setdefault(city, []).append(price)
    if region:
        region_prices.setdefault(region, []).append(price)

def compute_avg(prices):
    return round(sum(prices) / len(prices), 1)

# Build output
MIN_CLINICS = 1
cities = {}
for city, prices in city_prices.items():
    if len(prices) >= MIN_CLINICS:
        cities[city] = {'avg': compute_avg(prices), 'clinics': len(prices)}

regions = {}
for region, prices in region_prices.items():
    if len(prices) >= MIN_CLINICS:
        regions[region] = {'avg': compute_avg(prices), 'clinics': len(prices)}

result = {'cities': cities, 'regions': regions}

out_path = r'docs\assets\data\hygienist-averages.json'
with open(out_path, 'w', encoding='utf-8') as f:
    json.dump(result, f, indent=2, ensure_ascii=False)

print(f"\nWrote {out_path}")
print(f"  Cities: {len(cities)}, Regions: {len(regions)}")
print(f"\nKey cities:")
for city in ['Wellington', 'Auckland City', 'Christchurch']:
    if city in cities:
        e = cities[city]
        print(f"  {city}: ${e['avg']} avg ({e['clinics']} clinics)")

print(f"\nKey regions:")
for region in ['Wellington', 'Canterbury', 'Auckland']:
    if region in regions:
        e = regions[region]
        print(f"  {region}: ${e['avg']} avg ({e['clinics']} clinics)")
