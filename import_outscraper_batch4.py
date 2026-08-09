import csv
import json
import os
import time
import requests
from datetime import datetime
from dotenv import load_dotenv

load_dotenv()

OUTSCRAPER_API_KEY = os.getenv('OUTSCRAPER_API_KEY')
SUPABASE_URL = os.getenv('SUPABASE_URL')
SUPABASE_KEY = os.getenv('SUPABASE_SERVICE_KEY')

HEADERS_SB = {
    'apikey': SUPABASE_KEY,
    'Authorization': f'Bearer {SUPABASE_KEY}',
    'Content-Type': 'application/json',
    'Prefer': 'return=minimal'
}

CSV_PATH = os.path.join(os.path.dirname(__file__), 'outscraper_batch4.csv')
PROGRESS_PATH = os.path.join(os.path.dirname(__file__), 'outscraper_progress_batch4.json')
RAW_PATH = os.path.join(os.path.dirname(__file__), 'outscraper_raw_responses_batch4.jsonl')

BATCH_SIZE = 10


def load_progress():
    if os.path.exists(PROGRESS_PATH):
        with open(PROGRESS_PATH) as f:
            return json.load(f)
    return {'done_ids': []}


def save_progress(progress):
    with open(PROGRESS_PATH, 'w') as f:
        json.dump(progress, f)


def load_clinics():
    clinics = []
    with open(CSV_PATH, newline='', encoding='utf-8-sig') as f:
        reader = csv.DictReader(f)
        for row in reader:
            clinics.append({
                'id': int(row['clinic_id']),
                'name': row['name'],
                'url': row['google_maps_url']
            })
    return clinics


def fetch_reviews(urls):
    params = {
        'query': urls,
        'reviewsLimit': 20,
        'language': 'en',
        'sort': 'most_relevant',
        'async': False,
    }
    resp = requests.get(
        'https://api.app.outscraper.com/maps/reviews-v3',
        headers={'X-API-KEY': OUTSCRAPER_API_KEY},
        params=params,
        timeout=300
    )
    resp.raise_for_status()
    raw = resp.json().get('data', [])
    places = []
    for item in raw:
        if isinstance(item, list):
            places.append(item[0] if item else {})
        elif isinstance(item, dict):
            places.append(item)
        else:
            places.append({})
    return places


def get_existing_reviews(clinic_id):
    resp = requests.get(
        f'{SUPABASE_URL}/rest/v1/google_reviews',
        headers=HEADERS_SB,
        params={'clinic_id': f'eq.{clinic_id}', 'select': 'author,date_text'}
    )
    data = resp.json()
    if not isinstance(data, list):
        raise RuntimeError(f'Supabase error {resp.status_code}: {data}')
    return {(r['author'], r['date_text']) for r in data}


def insert_reviews(rows):
    if not rows:
        return 0
    resp = requests.post(
        f'{SUPABASE_URL}/rest/v1/google_reviews',
        headers=HEADERS_SB,
        json=rows
    )
    resp.raise_for_status()
    return len(rows)


def process_place(clinic, place_data):
    reviews_raw = place_data.get('reviews_data', [])
    if not reviews_raw:
        return 0

    existing = get_existing_reviews(clinic['id'])
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

        rows.append({
            'clinic_id': clinic['id'],
            'author': author,
            'rating': int(rating) if rating else None,
            'date_text': date_text,
            'snippet': snippet,
            'fetched_at': now
        })

    return insert_reviews(rows)


def main():
    clinics = load_clinics()
    progress = load_progress()
    done_ids = set(progress['done_ids'])

    remaining = [c for c in clinics if c['id'] not in done_ids]
    print(f"{len(clinics)} total clinics, {len(done_ids)} already done, {len(remaining)} remaining")

    total_inserted = 0
    batches = [remaining[i:i+BATCH_SIZE] for i in range(0, len(remaining), BATCH_SIZE)]

    for batch_num, batch in enumerate(batches, 1):
        urls = [c['url'] for c in batch]
        print(f"\nBatch {batch_num}/{len(batches)} — fetching {len(urls)} clinics...")

        try:
            places = fetch_reviews(urls)
        except Exception as e:
            print(f"  ERROR fetching batch: {e}")
            print("  Stopping.")
            progress['done_ids'] = list(done_ids)
            save_progress(progress)
            break

        with open(RAW_PATH, 'a', encoding='utf-8') as f:
            for i, place in enumerate(places):
                clinic_id = batch[i]['id'] if i < len(batch) else None
                f.write(json.dumps({'clinic_id': clinic_id, 'data': place}) + '\n')

        for i, place_data in enumerate(places):
            if i >= len(batch):
                break
            clinic = batch[i]
            try:
                inserted = process_place(clinic, place_data)
                print(f"  {clinic['name']}: {inserted} new reviews")
                total_inserted += inserted
            except Exception as e:
                print(f"  ERROR inserting {clinic['name']}: {e}")
                continue

            done_ids.add(clinic['id'])

        progress['done_ids'] = list(done_ids)
        save_progress(progress)
        time.sleep(2)

    print(f"\nDone. {total_inserted} new reviews inserted across {len(done_ids)} clinics.")


if __name__ == '__main__':
    main()
