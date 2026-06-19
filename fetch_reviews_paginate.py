"""
Fetch remaining review pages for Christchurch clinics with ≤ 40 total reviews.
Uses existing data_ids from christchurch_reviews.json (no step-1 searches needed).
Sorts by relevantFirst for a balanced mix of reviews.
"""

import json
import os
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
DELAY = 0.5
MAX_TOTAL_REVIEWS = 40

with open(OUTPUT_FILE, encoding='utf-8') as f:
    results = json.load(f)

def save():
    with open(OUTPUT_FILE, 'w', encoding='utf-8') as f:
        json.dump(results, f, ensure_ascii=False, indent=2)

def get_reviews(data_id, next_page_token=None):
    params = {
        'engine': 'google_maps_reviews',
        'data_id': data_id,
        'api_key': SERP_API_KEY,
        'hl': 'en',
        'sort_by': 'relevantFirst',
    }
    if next_page_token:
        params['next_page_token'] = next_page_token
    r = requests.get('https://serpapi.com/search.json', params=params, timeout=30)
    r.raise_for_status()
    return r.json()

# Identify clinics that need more pages
targets = [
    (name, v) for name, v in results.items()
    if int(v.get('total_ratings') or 0) <= MAX_TOTAL_REVIEWS
    and int(v.get('total_ratings') or 0) > len(v.get('reviews', []))
    and v.get('data_id')
    and not v.get('error')
]
targets.sort(key=lambda x: int(x[1].get('total_ratings') or 0))

print(f'Clinics needing more pages: {len(targets)}')
api_calls = 0

for i, (name, v) in enumerate(targets, 1):
    total = int(v.get('total_ratings') or 0)
    already = len(v.get('reviews', []))
    data_id = v['data_id']

    print(f'[{i}/{len(targets)}] {name} ({already}/{total})...', end=' ', flush=True)

    # Fetch all pages from the beginning with relevantFirst sort
    all_reviews = []
    next_token = None
    pages = 0

    while True:
        try:
            data = get_reviews(data_id, next_token)
            api_calls += 1
            time.sleep(DELAY)
        except Exception as e:
            print(f'ERROR: {e}')
            break

        page_reviews = data.get('reviews', [])
        all_reviews.extend([
            {
                'author': rv.get('user', {}).get('name'),
                'rating': rv.get('rating'),
                'date': rv.get('date'),
                'snippet': rv.get('snippet'),
            }
            for rv in page_reviews
        ])
        pages += 1

        next_token = data.get('serpapi_pagination', {}).get('next_page_token')
        if not next_token or not page_reviews:
            break

    results[name]['reviews'] = all_reviews
    results[name]['sort'] = 'relevantFirst'
    save()

    print(f'{len(all_reviews)} reviews ({pages} pages)')

print(f'\nDone. API calls used: {api_calls}')
print(f'Total reviews now: {sum(len(v.get("reviews", [])) for v in results.values())}')
