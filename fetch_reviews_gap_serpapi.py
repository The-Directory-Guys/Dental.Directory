"""
Fetch Google Maps reviews via SerpAPI for clinics that have a rating but
zero reviews scraped yet (the "gap" clinics, nationwide -- not just one city).

Two-step process per clinic (2 API calls):
  1. Google Maps search by name, biased to the clinic's own lat/lng -> data_id
  2. Google Maps Reviews search using data_id -> review text

Capped to stay within SerpAPI's free tier (250 searches/month) across however
many runs it takes -- LIMIT below controls how many clinics this run processes.

Setup:
  SERPAPI_API_KEY must be set in .env (free tier: https://serpapi.com/)

Input:
  reviews_gap_clinics.json -- list of {id, name, address, lat, lng, google_maps_url, ...}

Output:
  reviews_gap_serpapi.json -- one entry per clinic with review text, rating, date, author
  (resumable -- already-fetched clinics are skipped on re-run)
"""

import json
import os
import re
import sys
import time

import requests
from dotenv import load_dotenv

sys.stdout.reconfigure(encoding="utf-8")
load_dotenv()

SERP_API_KEY = os.getenv("SERPAPI_API_KEY")
if not SERP_API_KEY:
    print("ERROR: SERPAPI_API_KEY not set in .env")
    sys.exit(1)

INPUT_FILE = "reviews_gap_clinics.json"
OUTPUT_FILE = "reviews_gap_serpapi.json"
DELAY = 0.5

# 250 free searches/month, 2 calls/clinic -> safely under the cap with room
# for retries. Re-run later (after results carry over via resume) for the rest.
LIMIT = int(os.environ.get("GAP_SERPAPI_LIMIT", "125"))


def get(params):
    r = requests.get("https://serpapi.com/search.json", params={**params, "api_key": SERP_API_KEY}, timeout=30)
    r.raise_for_status()
    return r.json()


def main():
    with open(INPUT_FILE, encoding="utf-8") as f:
        clinics = json.load(f)

    if os.path.exists(OUTPUT_FILE):
        with open(OUTPUT_FILE, encoding="utf-8") as f:
            results = json.load(f)
        print(f"Resuming -- {len(results)} already fetched")
    else:
        results = {}

    def save():
        with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
            json.dump(results, f, ensure_ascii=False, indent=2)

    # Prioritise clinics with the most Google reviews so richest data lands first
    clinics_sorted = sorted(clinics, key=lambda c: c.get("total_ratings") or 0, reverse=True)
    todo = [c for c in clinics_sorted if str(c["id"]) not in results]
    batch = todo[:LIMIT]
    print(f"Gap clinics total: {len(clinics)}, already done: {len(clinics) - len(todo)}, this run: {len(batch)}")

    for i, clinic in enumerate(batch, 1):
        cid = str(clinic["id"])
        name = clinic["name"]
        lat, lng = clinic.get("lat"), clinic.get("lng")

        cid_match = re.search(r"cid=(\d+)", clinic.get("google_maps_url", "") or "")
        expected_cid = cid_match.group(1) if cid_match else None

        print(f"[{i}/{len(batch)}] {name}...", end=" ", flush=True)

        try:
            search_params = {"engine": "google_maps", "q": name, "hl": "en"}
            if lat and lng:
                search_params["ll"] = f"@{lat},{lng},14z"

            search = get(search_params)
            time.sleep(DELAY)

            place = search.get("place_results")
            if not place:
                local = search.get("local_results", [])
                if expected_cid:
                    place = next((r for r in local if str(r.get("data_cid", "")) == expected_cid), None)
                if not place and local:
                    place = local[0]

            if not place:
                print("no place found")
                results[cid] = {"name": name, "error": "place not found", "reviews": []}
                save()
                continue

            data_id = place.get("data_id")
            if not data_id:
                print("no data_id")
                results[cid] = {"name": name, "error": "no data_id", "reviews": []}
                save()
                continue

            rev_data = get({
                "engine": "google_maps_reviews",
                "data_id": data_id,
                "hl": "en",
                "sort_by": "ratingHigh",
            })
            time.sleep(DELAY)

            reviews = rev_data.get("reviews", [])
            place_info = rev_data.get("place_info", {})

            results[cid] = {
                "name": name,
                "data_id": data_id,
                "rating": place_info.get("rating") or clinic.get("rating"),
                "total_ratings": place_info.get("reviews") or clinic.get("total_ratings"),
                "reviews": [
                    {
                        "author": rv.get("user", {}).get("name"),
                        "rating": rv.get("rating"),
                        "date": rv.get("date"),
                        "snippet": rv.get("snippet"),
                    }
                    for rv in reviews
                ],
            }
            print(f"{len(reviews)} reviews")

        except Exception as e:
            print(f"ERROR: {e}")
            results[cid] = {"name": name, "error": str(e), "reviews": []}

        save()

    print(f"\nDone this run. Total fetched so far: {len(results)} of {len(clinics)}")
    total_reviews = sum(len(v.get("reviews", [])) for v in results.values())
    print(f"Total reviews collected so far: {total_reviews}")


if __name__ == "__main__":
    main()
