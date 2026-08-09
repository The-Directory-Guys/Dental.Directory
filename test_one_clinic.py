from dotenv import load_dotenv
load_dotenv()
import csv, requests, os, json
from datetime import datetime

OUTSCRAPER_API_KEY = os.getenv('OUTSCRAPER_API_KEY', 'c2MjZjIwNzgxMTFmMDIwNDkxMGFlNjE1Nzk3ZDMzNmIzMmN8YTg3M2NjMDJhZQ')
SUPABASE_URL = os.getenv('SUPABASE_URL', 'https://ankyjpgcocsvvtyyymys.supabase.co')
SUPABASE_KEY = os.getenv('SUPABASE_SERVICE_KEY', '')
HEADERS_SB = {'apikey': SUPABASE_KEY, 'Authorization': 'Bearer ' + SUPABASE_KEY, 'Content-Type': 'application/json', 'Prefer': 'return=minimal'}

with open('outscraper_under20_reviews.csv', newline='', encoding='utf-8-sig') as f:
    row = next(csv.DictReader(f))
clinic = {'id': int(row['clinic_id']), 'name': row['name'], 'url': row['google_maps_url']}
print('Testing with:', clinic['name'], '(id:', clinic['id'], ')')

resp = requests.get('https://api.app.outscraper.com/maps/reviews-v3',
    headers={'X-API-KEY': OUTSCRAPER_API_KEY},
    params={'query': clinic['url'], 'reviewsLimit': 0, 'language': 'en', 'sort': 'most_relevant', 'async': False},
    timeout=120)
raw = resp.json().get('data', [])
item = raw[0] if raw else {}
place = item[0] if isinstance(item, list) and item else (item if isinstance(item, dict) else {})
reviews_raw = place.get('reviews_data', [])
print('Reviews fetched:', len(reviews_raw))

cid = clinic['id']
existing_resp = requests.get(SUPABASE_URL + '/rest/v1/google_reviews', headers=HEADERS_SB,
    params={'clinic_id': 'eq.' + str(cid), 'select': 'author,date_text'})
existing_data = existing_resp.json()
print('Existing in DB:', len(existing_data) if isinstance(existing_data, list) else existing_data)
existing = {(r['author'], r['date_text']) for r in existing_data} if isinstance(existing_data, list) else set()

now = datetime.utcnow().isoformat()
rows = []
for r in reviews_raw:
    author = (r.get('author_title') or '').strip()
    date_text = (r.get('review_datetime_utc') or r.get('review_pagination_id') or '')[:10]
    snippet = (r.get('review_text') or '').strip()
    rating = r.get('review_rating')
    if not author or not snippet:
        continue
    if (author, date_text) in existing:
        continue
    rows.append({'clinic_id': cid, 'author': author, 'rating': int(rating) if rating else None,
                 'date_text': date_text, 'snippet': snippet, 'fetched_at': now})
print('New rows to insert:', len(rows))

if rows:
    ins = requests.post(SUPABASE_URL + '/rest/v1/google_reviews', headers=HEADERS_SB, json=rows)
    print('Insert status:', ins.status_code)
    if ins.status_code not in (200, 201):
        print('Error:', ins.text[:300])
    else:
        print('SUCCESS — inserted', len(rows), 'reviews for', clinic['name'])
