"""
Fetch Google Maps reviews for Christchurch clinics via Google Places API.
Gets up to 5 reviews per clinic. Skips clinics already in christchurch_reviews.json.
Results are saved in the same format as fetch_reviews_chch.py so the same
import_google_reviews.ts script handles both sources.

Prerequisites:
  1. Enable "Places API" in Google Cloud Console
  2. Add to .env:  GOOGLE_PLACES_API_KEY=your_key_here
  Get a key at: https://console.cloud.google.com/ → APIs & Services → Credentials

Cost: ~$0.034 per clinic (Find Place $0.017 + Place Details $0.017)
      134 clinics ≈ $4.60 — well within the $200/month free credit

Usage:
  python fetch_reviews_places.py

After running, import with:
  $env:NODE_OPTIONS="--use-system-ca"; web\\node_modules\\.bin\\tsx.cmd supabase\\import_google_reviews.ts
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

OUTPUT_FILE = 'christchurch_reviews.json'
DELAY = 0.2  # seconds between requests
CHCH_BIAS = 'circle:20000@-43.5321,172.6362'  # 20km radius around Christchurch

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


def find_place(name):
    """Step 1: Find Place ID by clinic name, biased to Christchurch."""
    r = requests.get(
        'https://maps.googleapis.com/maps/api/place/findplacefromtext/json',
        params={
            'input': name,
            'inputtype': 'textquery',
            'fields': 'place_id,name',
            'locationbias': CHCH_BIAS,
            'key': API_KEY,
        },
        timeout=30,
    )
    r.raise_for_status()
    data = r.json()
    candidates = data.get('candidates', [])
    return candidates[0]['place_id'] if candidates else None


def get_place_reviews(place_id):
    """Step 2: Get Place Details including up to 5 reviews."""
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


# --- Fetch Christchurch clinics from Supabase ---
print('Fetching clinic list from Supabase...')
clinics = fetch_supabase('dental_clinics?select=id,name,suburb_town&business_status=eq.OPERATIONAL&region=eq.Canterbury')
chch_clinics = [c for c in clinics if c.get('suburb_town') in CHCH_SUBURBS]

todo = [c for c in chch_clinics if c['name'] not in results or results[c['name']].get('error')]
print(f'Christchurch clinics in DB: {len(chch_clinics)}')
print(f'Already scraped: {len(chch_clinics) - len(todo)}')
print(f'To fetch: {len(todo)}')
print(f'Estimated cost: ~${len(todo) * 0.034:.2f} (within $200 free credit)')
print()

api_calls = 0

for i, clinic in enumerate(todo, 1):
    name = clinic['name']
    print(f'[{i}/{len(todo)}] {name}...', end=' ', flush=True)

    try:
        # Step 1: Find Place ID
        place_id = find_place(name)
        api_calls += 1
        time.sleep(DELAY)

        if not place_id:
            print('not found')
            results[name] = {'error': 'place not found', 'reviews': []}
            save()
            continue

        # Step 2: Get reviews
        details = get_place_reviews(place_id)
        api_calls += 1
        time.sleep(DELAY)

        raw_reviews = details.get('reviews', [])

        # Normalise to same format as SerpAPI output
        reviews = [
            {
                'author': rv.get('author_name'),
                'rating': rv.get('rating'),
                'date': rv.get('relative_time_description'),
                'snippet': rv.get('text'),
            }
            for rv in raw_reviews
        ]

        results[name] = {
            'place_id': place_id,
            'source': 'places_api',
            'rating': details.get('rating'),
            'total_ratings': details.get('user_ratings_total'),
            'reviews': reviews,
        }

        print(f'{len(reviews)} reviews (of {details.get("user_ratings_total", "?")} total)')

    except Exception as e:
        print(f'ERROR: {e}')
        results[name] = {'error': str(e), 'reviews': []}

    save()

print(f'\nDone. API calls used: {api_calls}')
print(f'Total clinics in file: {len(results)}')
print(f'Total reviews: {sum(len(v.get("reviews", [])) for v in results.values())}')
print()
print('Next step — run the SQL constraint (once only), then import:')
print('  1. Supabase dashboard → SQL Editor → run supabase/add_review_unique_constraint.sql')
print('  2. $env:NODE_OPTIONS="--use-system-ca"; web\\node_modules\\.bin\\tsx.cmd supabase\\import_google_reviews.ts')
