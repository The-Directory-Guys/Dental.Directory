import requests
import os
import sys
import urllib3
from dotenv import load_dotenv

urllib3.disable_warnings()
sys.stdout.reconfigure(encoding='utf-8')
load_dotenv()

SUPABASE_URL = os.getenv('SUPABASE_URL')
SUPABASE_KEY = os.getenv('SUPABASE_SERVICE_KEY')
HEADERS = {'apikey': SUPABASE_KEY, 'Authorization': f'Bearer {SUPABASE_KEY}'}

# Name keywords that indicate non-general-dental practices to exclude
EXCLUDE_KEYWORDS = [
    'periodontic', 'periodontist', 'aucklandperio', 'periocare', 'nsperio',
    'orthodont', 'ortho ', 'orthodontics', ' ortho',
    'oral surgery', 'maxillofacial', ' oms', 'oral surgeon',
    'endodont',
    'prosthodont',
    'denture', 'dentures',
    'implant centre', 'implant center',
    'whitening', 'teeth whitening',
    'hygien',
    'teeth movers',
    'support office',
    'children',
    'the fono',
    'paediatric',
]

def is_excluded(name):
    n = name.lower()
    for kw in EXCLUDE_KEYWORDS:
        if kw in n:
            return True
    return False

# Fetch all Auckland clinics
clinics = []
offset = 0
while True:
    r = requests.get(f'{SUPABASE_URL}/rest/v1/dental_clinics', headers=HEADERS,
        params={'region': 'eq.Auckland', 'select': 'id,name,city,address,website',
                'order': 'name', 'offset': offset, 'limit': 1000}, verify=False)
    batch = r.json()
    clinics.extend(batch)
    if len(batch) < 1000:
        break
    offset += 1000

# Fetch priced IDs
ids = ','.join(str(c['id']) for c in clinics)
r = requests.get(f'{SUPABASE_URL}/rest/v1/scraped_prices', headers=HEADERS,
    params={'clinic_id': f'in.({ids})', 'select': 'clinic_id'}, verify=False)
priced = {row['clinic_id'] for row in r.json()}

no_price = [c for c in clinics if c['id'] not in priced]
filtered = [c for c in no_price if not is_excluded(c['name'])]

print(f'Total Auckland: {len(clinics)} | Without prices: {len(no_price)} | After filtering: {len(filtered)}')

lines = [
    'Auckland clinics needing phone verification for checkup prices',
    f'Generated 21/05/26 — {len(no_price) - len(filtered)} excluded (specialists, denture labs, whitening, hygienist-only, community)',
    '',
]
for i, c in enumerate(filtered, 1):
    addr = (c.get('address') or '').replace(', New Zealand', '').strip().rstrip(',')
    lines.append(f'{i}. {c["name"]}')
    if c.get('website'):
        lines.append(f'   {c["website"]}')
    if addr:
        lines.append(f'   {addr}')
    lines.append('')

lines.append(f'Total: {len(filtered)} clinics')

output = '\n'.join(lines)
with open('auckland_need_checkup.txt', 'w', encoding='utf-8') as f:
    f.write(output)

print('Written to auckland_need_checkup.txt')
