#!/usr/bin/env python3
"""
Scrape dental clinics in the Canterbury region using the Google Places API (New).
Covers Christchurch city suburbs and the wider Canterbury/South Canterbury region.
Outputs results to dental_clinics_canterbury.csv

Requires:
    GOOGLE_PLACES_API_KEY environment variable to be set.

Usage:
    python3 scrape_canterbury.py
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
OUTPUT_FILE = "dental_clinics_canterbury.csv"
REGION = "Canterbury"

TOWNS = [
    # Christchurch City
    "Christchurch CBD",
    "Addington Christchurch",
    "Avonhead Christchurch",
    "Beckenham Christchurch",
    "Belfast Christchurch",
    "Bishopdale Christchurch",
    "Bryndwr Christchurch",
    "Burnside Christchurch",
    "Cashmere Christchurch",
    "Fendalton Christchurch",
    "Halswell Christchurch",
    "Harewood Christchurch",
    "Hornby Christchurch",
    "Ilam Christchurch",
    "Linwood Christchurch",
    "Lyttelton Christchurch",
    "Merivale Christchurch",
    "New Brighton Christchurch",
    "Northcote Christchurch",
    "Opawa Christchurch",
    "Papanui Christchurch",
    "Parklands Christchurch",
    "Rangiora Christchurch",
    "Redwood Christchurch",
    "Riccarton Christchurch",
    "Richmond Christchurch",
    "Shirley Christchurch",
    "Sockburn Christchurch",
    "Spreydon Christchurch",
    "St Albans Christchurch",
    "Sumner Christchurch",
    "Sydenham Christchurch",
    "Upper Riccarton Christchurch",
    "Wainoni Christchurch",
    "Waltham Christchurch",
    "Wigram Christchurch",
    "Woolston Christchurch",
    # Wider Canterbury / Selwyn / Waimakariri
    "Kaiapoi",
    "Rangiora",
    "Amberley",
    "Oxford",
    "Cheviot",
    "Kaikōura",
    "Rolleston",
    "Lincoln",
    "Prebbleton",
    "Darfield",
    "Leeston",
    "Broadfield",
    # South Canterbury
    "Ashburton",
    "Methven",
    "Geraldine",
    "Timaru",
    "Temuka",
    "Pleasant Point",
    # Mackenzie District
    "Twizel",
    "Lake Tekapo",
    # Hanmer / Lewis Pass
    "Hanmer Springs",
]

# Address fragments used to keep only Canterbury-region results
CANTERBURY_REGION_MARKERS = [
    "Christchurch",
    "Canterbury",
    "Kaiapoi",
    "Rangiora",
    "Amberley",
    "Oxford",
    "Cheviot",
    "Kaikōura",
    "Kaikoura",
    "Rolleston",
    "Lincoln",
    "Prebbleton",
    "Darfield",
    "Leeston",
    "Broadfield",
    "Ashburton",
    "Methven",
    "Geraldine",
    "Timaru",
    "Temuka",
    "Twizel",
    "Tekapo",
    "Hanmer Springs",
    "Selwyn",
    "Waimakariri",
    "Lyttelton",
]

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

        next_page_token = data.get("nextPageToken")
        if not next_page_token:
            break

        payload = {"textQuery": query, "pageSize": 20, "pageToken": next_page_token}
        time.sleep(1)

    return results


def extract_hours(place: dict) -> str:
    hours = place.get("regularOpeningHours", {})
    return "; ".join(hours.get("weekdayDescriptions", []))


def in_region(address: str) -> bool:
    return any(marker in address for marker in CANTERBURY_REGION_MARKERS)


def clean_town(town_query: str) -> str:
    """Strip location qualifier suffixes to get a clean town name for the CSV."""
    return (
        town_query
        .replace(" Christchurch", "")
        .replace(" New Zealand", "")
        .strip()
    )


def main():
    all_rows = []
    seen = set()  # deduplicate by google_maps_url

    for town in TOWNS:
        query = f"dental clinic {town} New Zealand"
        print(f"Searching: {query!r}")
        try:
            places = search_all_places(query)
        except requests.HTTPError as e:
            print(f"  ERROR: {e}")
            time.sleep(2)
            continue

        new_count = 0
        for place in places:
            maps_url = place.get("googleMapsUri", "")
            if maps_url in seen:
                continue
            seen.add(maps_url)

            address = place.get("formattedAddress", "")
            if not in_region(address):
                continue

            row = {
                "name": place.get("displayName", {}).get("text", ""),
                "address": address,
                "phone_national": place.get("nationalPhoneNumber", ""),
                "phone_international": place.get("internationalPhoneNumber", ""),
                "website": place.get("websiteUri", ""),
                "rating": place.get("rating", ""),
                "total_ratings": place.get("userRatingCount", ""),
                "business_status": place.get("businessStatus", ""),
                "google_maps_url": maps_url,
                "opening_hours": extract_hours(place),
                "category": "dental_clinic",
                "region": REGION,
                "town": clean_town(town),
                "price": "no_prices",
            }
            all_rows.append(row)
            new_count += 1

        print(f"  -> {new_count} new clinics (total: {len(all_rows)})")
        time.sleep(0.5)

    fieldnames = [
        "name", "address", "phone_national", "phone_international",
        "website", "rating", "total_ratings", "business_status",
        "google_maps_url", "opening_hours", "category", "region", "town", "price",
    ]

    with open(OUTPUT_FILE, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(all_rows)

    print(f"\nDone! {len(all_rows)} clinics saved to {OUTPUT_FILE}")


if __name__ == "__main__":
    main()
