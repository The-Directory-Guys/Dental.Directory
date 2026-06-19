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
HEADERS = {
    'apikey': SUPABASE_KEY,
    'Authorization': f'Bearer {SUPABASE_KEY}',
}

# Fetch all Wellington clinics
def fetch_clinics():
    clinics = []
    offset = 0
    limit = 1000
    while True:
        r = requests.get(
            f'{SUPABASE_URL}/rest/v1/dental_clinics',
            headers=HEADERS,
            params={
                'region': 'eq.Wellington',
                'select': 'id,name,city,address,website',
                'order': 'city,name',
                'offset': offset,
                'limit': limit,
            },
            verify=False,
        )
        r.raise_for_status()
        batch = r.json()
        clinics.extend(batch)
        if len(batch) < limit:
            break
        offset += limit
    return clinics

# Fetch clinic IDs that have scraped prices
def fetch_priced_ids(clinic_ids):
    if not clinic_ids:
        return set()
    id_list = ','.join(str(i) for i in clinic_ids)
    r = requests.get(
        f'{SUPABASE_URL}/rest/v1/scraped_prices',
        headers=HEADERS,
        params={
            'clinic_id': f'in.({id_list})',
            'select': 'clinic_id',
        },
        verify=False,
    )
    r.raise_for_status()
    return {row['clinic_id'] for row in r.json()}

clinics = fetch_clinics()
print(f"Total Wellington clinics: {len(clinics)}")

clinic_ids = [c['id'] for c in clinics]
priced_ids = fetch_priced_ids(clinic_ids)

no_price = [c for c in clinics if c['id'] not in priced_ids]
print(f"Without prices: {len(no_price)}\n")

for i, c in enumerate(no_price, 1):
    print(f"{i}. {c['name']}")
    if c.get('website'):
        print(f"   {c['website']}")
    addr = c.get('address') or ''
    city = c.get('city') or ''
    location = ', '.join(x for x in [addr, city] if x)
    if location:
        print(f"   {location}")
    print()
