"""
Fetch Google Maps reviews for Christchurch dental clinics via SerpAPI.

Two-step process per clinic:
  1. Google Maps search by name → get data_id
  2. Google Maps Reviews search using data_id → get review text

Uses ~2 API calls per clinic (144 total for 72 clinics; free tier = 250/month).

Setup:
  Add to .env:  SERPAPI_API_KEY=your_key_here
  Sign up free at https://serpapi.com/ (250 searches/month free)

Output:
  christchurch_reviews.json — one entry per clinic with review text, rating, date, author
"""

import csv
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

OUTPUT_FILE = 'christchurch_reviews.json'
DELAY = 0.5  # seconds between requests
CHRISTCHURCH_LL = '@-43.5321,172.6362,12z'  # central Christchurch

# --- Load clinic names from christchurch_prices.txt ---
with open('christchurch_prices.txt', encoding='utf-8') as f:
    content = f.read()

parts = re.split(r'\n\n\n(?=\d+\. )', content.lstrip('\n'))
names_in_txt = set()
for p in parts:
    first_line = p.split('\n')[0]
    name = re.sub(r'^\d+\.\s+', '', first_line).split(' [')[0].strip()
    names_in_txt.add(name)

# --- Load clinic data from CSV ---
with open('dental_clinics_all.csv', encoding='utf-8', newline='') as f:
    rows = list(csv.DictReader(f))

clinics = [r for r in rows if r['name'] in names_in_txt and r.get('google_maps_url')]

# De-duplicate by name
seen = set()
deduped = []
for c in clinics:
    if c['name'] not in seen:
        seen.add(c['name'])
        deduped.append(c)

print(f'Clinics to fetch: {len(deduped)}')

# --- Load existing results to allow resuming ---
if os.path.exists(OUTPUT_FILE):
    with open(OUTPUT_FILE, encoding='utf-8') as f:
        results = json.load(f)
    print(f'Resuming — {len(results)} already fetched')
else:
    results = {}

def save():
    with open(OUTPUT_FILE, 'w', encoding='utf-8') as f:
        json.dump(results, f, ensure_ascii=False, indent=2)

def get(params):
    r = requests.get('https://serpapi.com/search.json', params={**params, 'api_key': SERP_API_KEY}, timeout=30)
    r.raise_for_status()
    return r.json()

# --- Fetch reviews ---
for i, clinic in enumerate(deduped, 1):
    name = clinic['name']
    if name in results:
        print(f'[{i}/{len(deduped)}] Skipping: {name}')
        continue

    cid_match = re.search(r'cid=(\d+)', clinic.get('google_maps_url', ''))
    expected_cid = cid_match.group(1) if cid_match else None

    print(f'[{i}/{len(deduped)}] {name}...', end=' ', flush=True)

    try:
        # Step 1: Find the place to get data_id
        search = get({
            'engine': 'google_maps',
            'q': name,
            'll': CHRISTCHURCH_LL,
            'hl': 'en',
        })
        time.sleep(DELAY)

        # Try place_results first (direct match), then local_results
        place = search.get('place_results')
        if not place:
            local = search.get('local_results', [])
            # Match by CID if possible
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
        rev_data = get({
            'engine': 'google_maps_reviews',
            'data_id': data_id,
            'hl': 'en',
            'sort_by': 'ratingHigh',
        })
        time.sleep(DELAY)

        reviews = rev_data.get('reviews', [])
        place_info = rev_data.get('place_info', {})

        results[name] = {
            'data_id': data_id,
            'address': clinic.get('address', ''),
            'rating': place_info.get('rating') or clinic.get('rating'),
            'total_ratings': place_info.get('reviews') or clinic.get('total_ratings'),
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

print(f'\nDone. Results saved to {OUTPUT_FILE}')
print(f'Total clinics: {len(results)}')
total_reviews = sum(len(v.get("reviews", [])) for v in results.values())
print(f'Total reviews fetched: {total_reviews}')
