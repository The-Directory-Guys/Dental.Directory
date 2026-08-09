"""
Fetch Google Maps reviews for ALL Christchurch dental clinics via SerpAPI.

Reads clinic list directly from Supabase so it covers every clinic in the DB,
not just the original 40. Skips any clinic already in christchurch_reviews.json.
Appends results to the same file so import_google_reviews.ts picks them up.

Usage:
  python fetch_reviews_chch.py

Cost: ~2 SerpAPI calls per clinic (search + reviews). 250 free/month.
"""

import json
import os
import re
import sys
import time

import requests
from dotenv import load_dotenv

sys.stdout.reconfigure(encoding='utf-8')
load_dotenv()

SERP_API_KEY = os.getenv('SERPAPI_API_KEY')
if not SERP_API_KEY:
    print('ERROR: SERPAPI_API_KEY not set in .env')
    sys.exit(1)

SUPABASE_URL = os.getenv('SUPABASE_URL', 'https://ankyjpgcocsvvtyyymys.supabase.co')
SUPABASE_ANON_KEY = os.getenv('SUPABASE_ANON_KEY', os.environ['SUPABASE_ANON_KEY'])

OUTPUT_FILE = 'christchurch_reviews.json'
DELAY = 0.5
CHCH_LL = '@-43.5321,172.6362,12z'

CHCH_SUBURBS = {
    'Christchurch Central', 'Papanui', 'Riccarton', 'Strowan', 'Merivale',
    'St Albans', 'Sydenham', 'Bishopdale', 'Linwood', 'Shirley', 'Spreydon',
    'Hornby', 'Burnside', 'Woolston', 'Avonhead', 'Hillmorton', 'Cashmere',
    'Sockburn', 'Halswell', 'Bryndwr', 'Richmond', 'Redwood', 'Somerfield',
    'Hoon Hay', 'Addington', 'Fendalton', 'Kaiapoi', 'Prebbleton', 'Rangiora',
    'Rolleston', 'Lincoln', 'CBD', 'Northcote', 'Casebrook', 'North New Brighton',
    'Redcliffs', 'Yaldhurst', 'Waltham', 'Ilam', 'Ferrymead', 'Phillipstown',
}


def fetch_supabase(path):
    headers = {'apikey': SUPABASE_ANON_KEY, 'Authorization': f'Bearer {SUPABASE_ANON_KEY}'}
    all_rows = []
    offset = 0
    while True:
        r = requests.get(f'{SUPABASE_URL}/rest/v1/{path}&limit=1000&offset={offset}', headers=headers, timeout=30)
        r.raise_for_status()
        page = r.json()
        all_rows.extend(page)
        if len(page) < 1000:
            break
        offset += 1000
    return all_rows


def serp(params):
    r = requests.get('https://serpapi.com/search.json', params={**params, 'api_key': SERP_API_KEY}, timeout=30)
    r.raise_for_status()
    return r.json()


# --- Load existing results ---
if os.path.exists(OUTPUT_FILE):
    with open(OUTPUT_FILE, encoding='utf-8') as f:
        results = json.load(f)
    print(f'Loaded {len(results)} existing entries from {OUTPUT_FILE}')
else:
    results = {}


def save():
    with open(OUTPUT_FILE, 'w', encoding='utf-8') as f:
        json.dump(results, f, ensure_ascii=False, indent=2)


# --- Fetch Christchurch clinics from Supabase ---
print('Fetching clinic list from Supabase...')
clinics = fetch_supabase('dental_clinics?select=id,name,suburb_town,google_maps_url&business_status=eq.OPERATIONAL&region=eq.Canterbury')
chch_clinics = [c for c in clinics if c.get('suburb_town') in CHCH_SUBURBS]
print(f'Christchurch clinics in DB: {len(chch_clinics)}')

# Skip already-scraped
todo = [c for c in chch_clinics if c['name'] not in results]
print(f'To scrape: {len(todo)}')
print(f'Estimated SerpAPI calls: ~{len(todo) * 2} (of 250/month free)')
print()

api_calls = 0

for i, clinic in enumerate(todo, 1):
    name = clinic['name']
    cid_match = re.search(r'cid=(\d+)', clinic.get('google_maps_url') or '')
    expected_cid = cid_match.group(1) if cid_match else None

    print(f'[{i}/{len(todo)}] {name}...', end=' ', flush=True)

    try:
        # Step 1: Find the place to get data_id
        search = serp({'engine': 'google_maps', 'q': name, 'll': CHCH_LL, 'hl': 'en'})
        api_calls += 1
        time.sleep(DELAY)

        place = search.get('place_results')
        if not place:
            local = search.get('local_results', [])
            if expected_cid:
                place = next((r for r in local if str(r.get('data_cid', '')) == expected_cid), None)
            if not place and local:
                place = local[0]

        if not place:
            print('no place found')
            results[name] = {'error': 'place not found', 'reviews': []}
            save()
            continue

        data_id = place.get('data_id')
        if not data_id:
            print('no data_id')
            results[name] = {'error': 'no data_id', 'reviews': []}
            save()
            continue

        # Step 2: Fetch reviews
        rev_data = serp({'engine': 'google_maps_reviews', 'data_id': data_id, 'hl': 'en', 'sort_by': 'newestFirst'})
        api_calls += 1
        time.sleep(DELAY)

        reviews = rev_data.get('reviews', [])
        place_info = rev_data.get('place_info', {})

        results[name] = {
            'data_id': data_id,
            'rating': place_info.get('rating'),
            'total_ratings': place_info.get('reviews'),
            'reviews': [
                {
                    'author': rv.get('user', {}).get('name'),
                    'rating': rv.get('rating'),
                    'date': rv.get('date'),
                    'snippet': rv.get('snippet'),
                }
                for rv in reviews
            ],
        }

        print(f'{len(reviews)} reviews')

    except Exception as e:
        print(f'ERROR: {e}')
        results[name] = {'error': str(e), 'reviews': []}

    save()

print(f'\nDone. API calls used: {api_calls}')
print(f'Total clinics in file: {len(results)}')
print(f'Total reviews: {sum(len(v.get("reviews", [])) for v in results.values())}')
print()
print('Next step: run the import to push to Supabase:')
print('  $env:NODE_OPTIONS="--use-system-ca"; web\\node_modules\\.bin\\tsx.cmd supabase\\import_google_reviews.ts')
