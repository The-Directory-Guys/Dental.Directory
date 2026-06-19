"""
Fetch Google Maps reviews for North Island dental clinics via Google Places API.
Gets up to 5 reviews per clinic. Saves to north_island_reviews.json.

Covers: Auckland, Wellington, Waikato, Bay of Plenty, Manawatu-Whanganui,
        Hawke's Bay, Northland, Taranaki, Gisborne, Wairarapa (~772 clinics)

Import:
  $env:NODE_OPTIONS="--use-system-ca"; web\\node_modules\\.bin\\tsx.cmd supabase\\import_google_reviews.ts north_island_reviews.json
"""

import json
import os
import sys
import time

import requests
from dotenv import load_dotenv

sys.stdout.reconfigure(encoding='utf-8')
load_dotenv()

API_KEY = os.getenv('GOOGLE_PLACES_API_KEY')
if not API_KEY:
    print('ERROR: GOOGLE_PLACES_API_KEY not set in .env')
    sys.exit(1)

SUPABASE_URL = os.getenv('SUPABASE_URL', 'https://ankyjpgcocsvvtyyymys.supabase.co')
SUPABASE_ANON_KEY = os.getenv('SUPABASE_ANON_KEY', 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImFua3lqcGdjb2NzdnZ0eXl5bXlzIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NzM4MTM1MTQsImV4cCI6MjA4OTM4OTUxNH0.SXxTLBdiNVSEDXy95yU0x0ctYFOjIby8hZbJ7B1LPK8')

OUTPUT_FILE = 'north_island_reviews.json'
DELAY = 0.2

# North Island centre, 700km radius covers Northland to Wairarapa
NI_BIAS = 'circle:700000@-38.5,175.8'

SOUTH_ISLAND_REGIONS = {
    'Canterbury', 'Otago', 'Southland', 'Nelson & Tasman', 'Marlborough', 'West Coast',
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


def find_place(name, suburb):
    query = f'{name} {suburb} New Zealand' if suburb else f'{name} New Zealand'
    r = requests.get(
        'https://maps.googleapis.com/maps/api/place/findplacefromtext/json',
        params={
            'input': query,
            'inputtype': 'textquery',
            'fields': 'place_id,name',
            'locationbias': NI_BIAS,
            'key': API_KEY,
        },
        timeout=30,
    )
    r.raise_for_status()
    candidates = r.json().get('candidates', [])
    return candidates[0]['place_id'] if candidates else None


def get_place_reviews(place_id):
    r = requests.get(
        'https://maps.googleapis.com/maps/api/place/details/json',
        params={
            'place_id': place_id,
            'fields': 'name,rating,user_ratings_total,reviews',
            'reviews_sort': 'newest',
            'key': API_KEY,
        },
        timeout=30,
    )
    r.raise_for_status()
    return r.json().get('result', {})


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


print('Fetching clinic list from Supabase...')
all_clinics = fetch_supabase('dental_clinics?select=id,name,suburb_town,region&business_status=eq.OPERATIONAL')

ni_clinics = [c for c in all_clinics if c.get('region') and c['region'] not in SOUTH_ISLAND_REGIONS]
todo = [c for c in ni_clinics if c['name'] not in results]

from collections import Counter
print(f'North Island clinics: {len(ni_clinics)}')
print(f'Already scraped: {len(ni_clinics) - len(todo)}')
print(f'To fetch: {len(todo)}')
print()
regions = Counter(c['region'] for c in todo)
for region, count in sorted(regions.items(), key=lambda x: -x[1]):
    print(f'  {count:3d}  {region}')
print()

api_calls = 0

for i, clinic in enumerate(todo, 1):
    name = clinic['name']
    suburb = clinic.get('suburb_town', '')
    print(f'[{i}/{len(todo)}] {name} ({suburb})...', end=' ', flush=True)

    try:
        place_id = find_place(name, suburb)
        api_calls += 1
        time.sleep(DELAY)

        if not place_id:
            print('not found')
            results[name] = {'error': 'place not found', 'reviews': []}
            save()
            continue

        details = get_place_reviews(place_id)
        api_calls += 1
        time.sleep(DELAY)

        raw_reviews = details.get('reviews', [])
        reviews = [
            {
                'author': rv.get('author_name'),
                'rating': rv.get('rating'),
                'date': rv.get('relative_time_description'),
                'snippet': rv.get('text'),
            }
            for rv in raw_reviews
        ]

        got = len(reviews)
        total = details.get('user_ratings_total')
        results[name] = {
            'place_id': place_id,
            'source': 'places_api',
            'rating': details.get('rating'),
            'total_ratings': total,
            'complete': total is None or total == 0 or got >= total,
            'reviews': reviews,
        }

        print(f'{got} reviews (of {total or "?"} total)')

    except Exception as e:
        print(f'ERROR: {e}')
        results[name] = {'error': str(e), 'reviews': []}

    save()

print(f'\nDone. API calls used: {api_calls}')
print(f'Total clinics in file: {len(results)}')
print(f'Total reviews: {sum(len(v.get("reviews", [])) for v in results.values())}')
complete = sum(1 for v in results.values() if v.get('complete'))
print(f'Complete (all reviews scraped): {complete}/{len(results)}')
print()
print('Next: import to Supabase:')
print('  $env:NODE_OPTIONS="--use-system-ca"; web\\node_modules\\.bin\\tsx.cmd supabase\\import_google_reviews.ts north_island_reviews.json')
