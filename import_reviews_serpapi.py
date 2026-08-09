"""
Import reviews from reviews_gap_serpapi.json into Supabase google_reviews table.

Skips reviews already present (matched by clinic_id + author + date_text).
Uses service key to bypass RLS.
"""

import json
import os
import sys
import urllib.request
import urllib.parse
from datetime import datetime, timezone

sys.stdout.reconfigure(encoding='utf-8')

from dotenv import load_dotenv
load_dotenv()

SERVICE_KEY = os.getenv('SUPABASE_SERVICE_KEY')
if not SERVICE_KEY:
    print("ERROR: SUPABASE_SERVICE_KEY not set in .env")
    sys.exit(1)

BASE = 'https://ankyjpgcocsvvtyyymys.supabase.co/rest/v1'
INPUT_FILE = 'reviews_gap_serpapi.json'


def get_existing(clinic_id):
    """Return set of (author, date_text) tuples already in DB for this clinic."""
    url = f'{BASE}/google_reviews?clinic_id=eq.{clinic_id}&select=author,date_text'
    req = urllib.request.Request(url)
    req.add_header('apikey', SERVICE_KEY)
    req.add_header('Authorization', 'Bearer ' + SERVICE_KEY)
    with urllib.request.urlopen(req) as r:
        rows = json.loads(r.read())
    return {(row['author'], row['date_text']) for row in rows}


def insert_reviews(rows):
    body = json.dumps(rows, ensure_ascii=False).encode('utf-8')
    req = urllib.request.Request(f'{BASE}/google_reviews', data=body, method='POST')
    req.add_header('apikey', SERVICE_KEY)
    req.add_header('Authorization', 'Bearer ' + SERVICE_KEY)
    req.add_header('Content-Type', 'application/json')
    req.add_header('Prefer', 'return=minimal')
    with urllib.request.urlopen(req) as r:
        return r.status


def main():
    with open(INPUT_FILE, encoding='utf-8') as f:
        results = json.load(f)

    now = datetime.now(timezone.utc).isoformat()

    total_inserted = 0
    total_skipped = 0
    clinics_with_reviews = 0
    clinics_no_reviews = 0

    for cid_str, data in results.items():
        reviews = data.get('reviews', [])
        if not reviews:
            clinics_no_reviews += 1
            continue

        clinic_id = int(cid_str)
        name = data.get('name', '')

        try:
            existing = get_existing(clinic_id)
        except Exception as e:
            print(f"  ERROR fetching existing for {name}: {e}")
            continue

        to_insert = []
        for rv in reviews:
            author = rv.get('author') or 'Anonymous'
            date_text = rv.get('date') or ''
            snippet = rv.get('snippet') or ''
            rating = rv.get('rating')

            if not snippet:
                continue
            if (author, date_text) in existing:
                total_skipped += 1
                continue

            to_insert.append({
                'clinic_id': clinic_id,
                'author': author,
                'rating': int(rating) if rating is not None else None,
                'date_text': date_text,
                'snippet': snippet,
                'fetched_at': now,
            })

        if to_insert:
            try:
                insert_reviews(to_insert)
                total_inserted += len(to_insert)
                clinics_with_reviews += 1
                print(f"  {name}: inserted {len(to_insert)}, skipped {len(reviews) - len(to_insert)}")
            except Exception as e:
                print(f"  ERROR inserting for {name}: {e}")
        else:
            print(f"  {name}: all {len(reviews)} already in DB")

    print(f"\nDone.")
    print(f"  Reviews inserted: {total_inserted}")
    print(f"  Reviews skipped (already existed): {total_skipped}")
    print(f"  Clinics with new reviews: {clinics_with_reviews}")
    print(f"  Clinics with no reviews from SerpAPI: {clinics_no_reviews}")


if __name__ == '__main__':
    main()
