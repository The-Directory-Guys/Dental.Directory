#!/usr/bin/env python3
"""
Scrape dental clinics in Christchurch, New Zealand using the Google Places API.
Outputs results to dental_clinics_christchurch.csv

Requires:
    GOOGLE_PLACES_API_KEY environment variable to be set.

Usage:
    python3 scrape_dental_clinics.py
"""

import csv
import os
import sys
import time
import requests

API_KEY = os.environ.get("GOOGLE_PLACES_API_KEY")
if not API_KEY:
    print("ERROR: GOOGLE_PLACES_API_KEY environment variable is not set.")
    sys.exit(1)

TEXT_SEARCH_URL = "https://maps.googleapis.com/maps/api/place/textsearch/json"
PLACE_DETAILS_URL = "https://maps.googleapis.com/maps/api/place/details/json"
OUTPUT_FILE = "dental_clinics_christchurch.csv"
QUERY = "dental clinic Christchurch New Zealand"

DETAIL_FIELDS = [
    "name",
    "formatted_address",
    "formatted_phone_number",
    "website",
    "rating",
    "user_ratings_total",
    "opening_hours",
    "business_status",
    "url",
]


def search_places(query: str) -> list[dict]:
    """Fetch all pages of text search results for the given query."""
    results = []
    params = {"query": query, "key": API_KEY}

    while True:
        resp = requests.get(TEXT_SEARCH_URL, params=params, timeout=10)
        resp.raise_for_status()
        data = resp.json()

        status = data.get("status")
        if status not in ("OK", "ZERO_RESULTS"):
            print(f"Places API error: {status} — {data.get('error_message', '')}")
            break

        results.extend(data.get("results", []))
        print(f"  Fetched {len(data.get('results', []))} results (total so far: {len(results)})")

        next_page_token = data.get("next_page_token")
        if not next_page_token:
            break

        # Google requires a short delay before the next_page_token is valid
        time.sleep(2)
        params = {"pagetoken": next_page_token, "key": API_KEY}

    return results


def get_place_details(place_id: str) -> dict:
    """Fetch detailed information for a single place."""
    params = {
        "place_id": place_id,
        "fields": ",".join(DETAIL_FIELDS),
        "key": API_KEY,
    }
    resp = requests.get(PLACE_DETAILS_URL, params=params, timeout=10)
    resp.raise_for_status()
    data = resp.json()

    if data.get("status") != "OK":
        return {}
    return data.get("result", {})


def extract_hours(details: dict) -> str:
    """Return a semicolon-separated string of opening hours."""
    opening_hours = details.get("opening_hours", {})
    weekday_text = opening_hours.get("weekday_text", [])
    return "; ".join(weekday_text)


def main():
    print(f"Searching for: {QUERY!r}")
    places = search_places(QUERY)
    print(f"\nFound {len(places)} places. Fetching details...\n")

    rows = []
    for i, place in enumerate(places, 1):
        place_id = place.get("place_id")
        name = place.get("name", "")
        print(f"[{i}/{len(places)}] {name}")

        details = get_place_details(place_id) if place_id else {}

        row = {
            "name": details.get("name") or name,
            "address": details.get("formatted_address") or place.get("formatted_address", ""),
            "phone": details.get("formatted_phone_number", ""),
            "website": details.get("website", ""),
            "rating": details.get("rating", ""),
            "total_ratings": details.get("user_ratings_total", ""),
            "business_status": details.get("business_status") or place.get("business_status", ""),
            "google_maps_url": details.get("url", ""),
            "opening_hours": extract_hours(details),
        }
        rows.append(row)

        # Be polite to the API
        time.sleep(0.1)

    fieldnames = [
        "name",
        "address",
        "phone",
        "website",
        "rating",
        "total_ratings",
        "business_status",
        "google_maps_url",
        "opening_hours",
    ]

    with open(OUTPUT_FILE, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)

    print(f"\nDone! {len(rows)} clinics saved to {OUTPUT_FILE}")


if __name__ == "__main__":
    main()
