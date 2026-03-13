#!/usr/bin/env python3
"""
Scrape dental clinics in Christchurch, New Zealand using the Google Places API (New).
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

PLACES_SEARCH_URL = "https://places.googleapis.com/v1/places:searchText"
OUTPUT_FILE = "dental_clinics_christchurch.csv"
QUERY = "dental clinic Christchurch New Zealand"

FIELD_MASK = ",".join([
    "places.displayName",
    "places.formattedAddress",
    "places.nationalPhoneNumber",
    "places.internationalPhoneNumber",
    "places.websiteUri",
    "places.rating",
    "places.userRatingCount",
    "places.businessStatus",
    "places.googleMapsUri",
    "places.regularOpeningHours",
    "nextPageToken",
])


def search_all_places(query: str) -> list[dict]:
    """Fetch all pages of text search results for the given query."""
    results = []
    payload = {"textQuery": query, "pageSize": 20}
    headers = {
        "Content-Type": "application/json",
        "X-Goog-Api-Key": API_KEY,
        "X-Goog-FieldMask": FIELD_MASK,
    }

    while True:
        resp = requests.post(PLACES_SEARCH_URL, headers=headers, json=payload, timeout=10)
        resp.raise_for_status()
        data = resp.json()

        batch = data.get("places", [])
        results.extend(batch)
        print(f"  Fetched {len(batch)} results (total so far: {len(results)})")

        next_page_token = data.get("nextPageToken")
        if not next_page_token:
            break

        # Use the page token for the next request
        payload = {"textQuery": query, "pageSize": 20, "pageToken": next_page_token}
        time.sleep(1)

    return results


def extract_hours(place: dict) -> str:
    """Return a semicolon-separated string of opening hours."""
    hours = place.get("regularOpeningHours", {})
    weekday_text = hours.get("weekdayDescriptions", [])
    return "; ".join(weekday_text)


def main():
    print(f"Searching for: {QUERY!r}")
    places = search_all_places(QUERY)
    print(f"\nFound {len(places)} dental clinics. Writing to {OUTPUT_FILE}...\n")

    fieldnames = [
        "name",
        "address",
        "phone_national",
        "phone_international",
        "website",
        "rating",
        "total_ratings",
        "business_status",
        "google_maps_url",
        "opening_hours",
    ]

    rows = []
    for place in places:
        row = {
            "name": place.get("displayName", {}).get("text", ""),
            "address": place.get("formattedAddress", ""),
            "phone_national": place.get("nationalPhoneNumber", ""),
            "phone_international": place.get("internationalPhoneNumber", ""),
            "website": place.get("websiteUri", ""),
            "rating": place.get("rating", ""),
            "total_ratings": place.get("userRatingCount", ""),
            "business_status": place.get("businessStatus", ""),
            "google_maps_url": place.get("googleMapsUri", ""),
            "opening_hours": extract_hours(place),
        }
        rows.append(row)
        print(f"  {row['name']} — {row['address']}")

    with open(OUTPUT_FILE, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)

    print(f"\nDone! {len(rows)} clinics saved to {OUTPUT_FILE}")


if __name__ == "__main__":
    main()
