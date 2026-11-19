"""
Pulls the current review set from Google (via SerpAPI) for one or more
clinics and writes the result to Supabase: inserts reviews we don't have
yet, fills in the owner's Google reply on reviews we already have if one
has since appeared, and refreshes dental_clinics.rating/total_ratings.

Replaces the old one-off scripts (refresh_prestige_reviews.py,
refresh_reviews_batch.py, fetch_reviews_gap_serpapi.py, and their matching
write/import scripts) with a single reusable tool.

Setup:
  SERPAPI_API_KEY, SUPABASE_URL, SUPABASE_SERVICE_KEY must be set in .env.

Usage:
  python refresh_clinic_reviews.py <clinic_id> [<clinic_id> ...]
"""
import json
import math
import os
import re
import sys
import time

import requests
import truststore
from dotenv import load_dotenv

truststore.inject_into_ssl()
sys.stdout.reconfigure(encoding="utf-8")
load_dotenv()

SUPABASE_URL = os.environ["SUPABASE_URL"]
SERVICE_KEY = os.environ["SUPABASE_SERVICE_KEY"]
SERP_API_KEY = os.environ["SERPAPI_API_KEY"]

DB_HEADERS = {
    "apikey": SERVICE_KEY,
    "Authorization": f"Bearer {SERVICE_KEY}",
    "Content-Type": "application/json",
}

MAX_PAGES = 15
DELAY = 1.0
FAR_WARNING_M = 500


def serp_get(params):
    r = requests.get("https://serpapi.com/search.json", params={**params, "api_key": SERP_API_KEY}, timeout=30)
    r.raise_for_status()
    return r.json()


def haversine_m(lat1, lng1, lat2, lng2):
    R = 6371000
    p1, p2 = math.radians(lat1), math.radians(lat2)
    dphi = math.radians(lat2 - lat1)
    dlambda = math.radians(lng2 - lng1)
    a = math.sin(dphi / 2) ** 2 + math.cos(p1) * math.cos(p2) * math.sin(dlambda / 2) ** 2
    return 2 * R * math.asin(math.sqrt(a))


def fetch_clinic_row(clinic_id):
    r = requests.get(
        f"{SUPABASE_URL}/rest/v1/dental_clinics",
        headers=DB_HEADERS,
        params={"select": "id,name,lat,lng,google_maps_url", "id": f"eq.{clinic_id}"},
    )
    r.raise_for_status()
    rows = r.json()
    if not rows:
        print(f"ERROR: no clinic with id={clinic_id}")
        return None
    return rows[0]


def expected_cid_from_url(google_maps_url):
    if not google_maps_url:
        return None
    m = re.search(r"cid=(\d+)", google_maps_url)
    return m.group(1) if m else None


def find_place(clinic):
    name, lat, lng = clinic["name"], clinic["lat"], clinic["lng"]
    expected_cid = expected_cid_from_url(clinic.get("google_maps_url"))

    search = serp_get({"engine": "google_maps", "q": name, "ll": f"@{lat},{lng},14z", "hl": "en"})
    candidates = ([search["place_results"]] if search.get("place_results") else []) + search.get("local_results", [])
    if not candidates:
        return None

    place = None
    if expected_cid:
        place = next((c for c in candidates if str(c.get("data_cid", "")) == expected_cid), None)
    if not place:
        place = candidates[0]
        if expected_cid:
            print(f"  WARNING: no candidate matched expected cid {expected_cid}, falling back to top result")

    gps = place.get("gps_coordinates")
    if gps:
        dist = haversine_m(lat, lng, gps["latitude"], gps["longitude"])
        if dist > FAR_WARNING_M:
            print(f"  WARNING: matched place is {dist:.0f}m from clinic's stored coordinates - verify this is correct")

    return place


def fetch_reviews(data_id):
    all_reviews = []
    seen_ids = set()
    next_page_token = None
    place_info = None

    for page in range(1, MAX_PAGES + 1):
        params = {"engine": "google_maps_reviews", "data_id": data_id, "hl": "en", "sort_by": "newestFirst"}
        if next_page_token:
            params["next_page_token"] = next_page_token

        data = serp_get(params)
        if place_info is None:
            place_info = data.get("place_info", {})

        reviews = data.get("reviews", [])
        new_count = 0
        for rv in reviews:
            rid = rv.get("review_id") or rv.get("link")
            if rid and rid in seen_ids:
                continue
            if rid:
                seen_ids.add(rid)
            response = rv.get("response") or {}
            all_reviews.append({
                "author": (rv.get("user") or {}).get("name") or "Anonymous",
                "rating": rv.get("rating"),
                "date_text": rv.get("date") or "",
                "snippet": (rv.get("snippet") or "").strip(),
                "google_reply": (response.get("snippet") or "").strip() or None,
                "google_reply_date_text": response.get("date"),
            })
            new_count += 1

        print(f"  page {page}: {len(reviews)} reviews ({new_count} new), running total {len(all_reviews)}")

        next_page_token = data.get("serpapi_pagination", {}).get("next_page_token")
        if not next_page_token or new_count == 0:
            break
        time.sleep(DELAY)

    return all_reviews, place_info


def fetch_existing(clinic_id):
    r = requests.get(
        f"{SUPABASE_URL}/rest/v1/google_reviews",
        headers=DB_HEADERS,
        params={"select": "id,author,snippet,google_reply", "clinic_id": f"eq.{clinic_id}"},
    )
    r.raise_for_status()
    return {(row["author"] or "", row["snippet"] or ""): row for row in r.json()}


def fetch_all_snippets_elsewhere(clinic_id):
    """Every non-empty snippet already in the table for a DIFFERENT clinic -
    guards against re-introducing cross-clinic review contamination."""
    seen = set()
    offset, page = 0, 1000
    while True:
        r = requests.get(
            f"{SUPABASE_URL}/rest/v1/google_reviews",
            headers=DB_HEADERS,
            params={"select": "snippet,clinic_id", "offset": offset, "limit": page, "order": "id"},
        )
        r.raise_for_status()
        chunk = r.json()
        for row in chunk:
            if row["clinic_id"] != clinic_id and row["snippet"]:
                seen.add(row["snippet"].strip())
        if len(chunk) < page:
            break
        offset += page
    return seen


def process_clinic(clinic_id):
    clinic = fetch_clinic_row(clinic_id)
    if not clinic:
        return

    print(f"\n=== {clinic['name']} (id={clinic_id}) ===")
    place = find_place(clinic)
    if not place:
        print("  ERROR: could not find this clinic on Google Maps via SerpAPI")
        return

    data_id = place.get("data_id")
    print(f"  Matched: {place.get('title')} | {place.get('address')}")

    reviews, place_info = fetch_reviews(data_id)
    existing = fetch_existing(clinic_id)
    contamination_guard = fetch_all_snippets_elsewhere(clinic_id)

    to_insert = []
    to_update_reply = []
    skipped_contamination = 0

    for rv in reviews:
        key = (rv["author"], rv["snippet"])
        existing_row = existing.get(key)

        if existing_row is not None:
            if rv["google_reply"] and not existing_row.get("google_reply"):
                to_update_reply.append((existing_row["id"], rv["google_reply"], rv["google_reply_date_text"]))
            continue

        if rv["snippet"] and len(rv["snippet"]) >= 20 and rv["snippet"] in contamination_guard:
            skipped_contamination += 1
            continue

        to_insert.append({
            "clinic_id": clinic_id,
            "author": rv["author"],
            "rating": round(rv["rating"]) if rv["rating"] is not None else None,
            "date_text": rv["date_text"],
            "snippet": rv["snippet"],
            "is_curated": bool(rv["snippet"] and len(rv["snippet"]) >= 20),
            "is_curated_rating": True,
            "google_reply": rv["google_reply"],
            "google_reply_date_text": rv["google_reply_date_text"],
        })

    if to_insert:
        r = requests.post(f"{SUPABASE_URL}/rest/v1/google_reviews", headers={**DB_HEADERS, "Prefer": "return=minimal"},
                           data=json.dumps(to_insert, ensure_ascii=False).encode("utf-8"))
        r.raise_for_status()

    for review_id, reply, reply_date in to_update_reply:
        r = requests.patch(f"{SUPABASE_URL}/rest/v1/google_reviews", headers={**DB_HEADERS, "Prefer": "return=minimal"},
                            params={"id": f"eq.{review_id}"},
                            data=json.dumps({"google_reply": reply, "google_reply_date_text": reply_date}, ensure_ascii=False).encode("utf-8"))
        r.raise_for_status()

    if place_info:
        update = {"rating": place_info.get("rating"), "total_ratings": place_info.get("reviews")}
        r = requests.patch(f"{SUPABASE_URL}/rest/v1/dental_clinics", headers={**DB_HEADERS, "Prefer": "return=minimal"},
                            params={"id": f"eq.{clinic_id}"}, data=json.dumps(update).encode("utf-8"))
        r.raise_for_status()
        print(f"  Google reports {update['total_ratings']} total reviews (rating {update['rating']})")

    print(f"  Inserted {len(to_insert)} new review(s), filled in {len(to_update_reply)} new Google reply(ies), "
          f"skipped {skipped_contamination} as likely cross-clinic duplicates")


def main():
    if len(sys.argv) < 2:
        print("Usage: python refresh_clinic_reviews.py <clinic_id> [<clinic_id> ...]")
        sys.exit(1)

    for arg in sys.argv[1:]:
        process_clinic(int(arg))


if __name__ == "__main__":
    main()
