"""
Fetch Google Maps reviews for South Island dental clinics (excluding Christchurch)
via Google Places API. Gets up to 5 reviews per clinic.

Covers: Canterbury (non-Chch), Otago, Southland, Nelson & Tasman, Marlborough, West Coast.
Saves to south_island_reviews.json for import via import_google_reviews.ts.

Cost: ~$0.034 per clinic (Find Place + Place Details)
      ~114 clinics ≈ $3.90 — well within the $200/month free credit

Usage:
  python fetch_reviews_south_island.py

Import:
  $env:NODE_OPTIONS="--use-system-ca"; web\\node_modules\\.bin\\tsx.cmd supabase\\import_google_reviews.ts south_island_reviews.json
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
SUPABASE_ANON_KEY = os.getenv('SUPABASE_ANON_KEY', os.environ['SUPABASE_ANON_KEY'])

OUTPUT_FILE = 'south_island_reviews.json'
DELAY = 0.2  # seconds between API requests

# South Island centre, 700km radius covers everything from Nelson to Bluff
SI_BIAS = 'circle:700000@-44.0,170.5'

# Christchurch suburbs already scraped — exclude them
CHCH_SUBURBS = {
    'Christchurch Central', 'Papanui', 'Riccarton', 'Strowan', 'Merivale',
    'St Albans', 'Sydenham', 'Bishopdale', 'Linwood', 'Shirley', 'Spreydon',
    'Hornby', 'Burnside', 'Woolston', 'Avonhead', 'Hillmorton', 'Cashmere',
    'Sockburn', 'Halswell', 'Bryndwr', 'Richmond', 'Redwood', 'Somerfield',
    'Hoon Hay', 'Addington', 'Fendalton', 'Kaiapoi', 'Prebbleton', 'Rangiora',
    'Rolleston', 'Lincoln', 'CBD', 'Northcote', 'Casebrook', 'North New Brighton',
    'Redcliffs', 'Yaldhurst', 'Waltham', 'Ilam', 'Ferrymead', 'Phillipstown',
}

SOUTH_ISLAND_REGIONS = {
    'Canterbury',
    'Otago',
    'Southland',
    'Nelson & Tasman',
    'Marlborough',
    'West Coast',
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
    """Find Place ID. Include suburb for disambiguation."""
    query = f'{name} {suburb} New Zealand' if suburb else f'{name} New Zealand'
    r = requests.get(
        'https://maps.googleapis.com/maps/api/place/findplacefromtext/json',
        params={
            'input': query,
            'inputtype': 'textquery',
            'fields': 'place_id,name',
            'locationbias': SI_BIAS,
            'key': API_KEY,
        },
        timeout=30,
    )
    r.raise_for_status()
    candidates = r.json().get('candidates', [])
    return candidates[0]['place_id'] if candidates else None


def get_place_reviews(place_id):
    """Get Place Details including up to 5 reviews."""
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


# --- Fetch South Island clinics from Supabase ---
print('Fetching clinic list from Supabase...')
all_clinics = fetch_supabase('dental_clinics?select=id,name,suburb_town,region&business_status=eq.OPERATIONAL')

si_clinics = [
    c for c in all_clinics
    if c.get('region') in SOUTH_ISLAND_REGIONS
    and c.get('suburb_town') not in CHCH_SUBURBS
]

todo = [c for c in si_clinics if c['name'] not in results]

print(f'South Island clinics (non-Chch): {len(si_clinics)}')
print(f'Already scraped: {len(si_clinics) - len(todo)}')
print(f'To fetch: {len(todo)}')
print(f'Estimated cost: ~${len(todo) * 0.034:.2f}')
print()

# Show breakdown by region
from collections import Counter
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
print('Next step — import to Supabase:')
print('  $env:NODE_OPTIONS="--use-system-ca"; web\\node_modules\\.bin\\tsx.cmd supabase\\import_google_reviews.ts south_island_reviews.json')
