#!/usr/bin/env python3
"""
Scrape dental clinics in the Wellington region using the Google Places API (New).
Outputs results to dental_clinics_wellington.csv

Covers: Wellington City, Porirua, Lower Hutt, Upper Hutt, Kapiti Coast, Wairarapa.

Requires:
    GOOGLE_PLACES_API_KEY environment variable to be set.

Usage:
    python3 scrape_wellington.py
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
OUTPUT_FILE = "dental_clinics_wellington.csv"
REGION = "Wellington"

TOWNS = [
    # Wellington City
    "Wellington CBD",
    "Newtown Wellington",
    "Johnsonville Wellington",
    "Karori Wellington",
    "Miramar Wellington",
    "Kilbirnie Wellington",
    "Island Bay Wellington",
    "Tawa Wellington",
    "Churton Park Wellington",
    "Newlands Wellington",
    "Khandallah Wellington",
    "Ngaio Wellington",
    "Brooklyn Wellington",
    "Thorndon Wellington",
    "Hataitai Wellington",
    # Porirua
    "Porirua",
    "Whitby Porirua",
    "Titahi Bay Porirua",
    "Plimmerton Porirua",
    # Lower Hutt
    "Lower Hutt",
    "Petone Lower Hutt",
    "Naenae Lower Hutt",
    "Stokes Valley Lower Hutt",
    "Wainuiomata Lower Hutt",
    # Upper Hutt
    "Upper Hutt",
    # Kapiti Coast
    "Paraparaumu",
    "Waikanae",
    "Otaki",
    "Raumati",
    # Wairarapa
    "Masterton",
    "Carterton",
    "Greytown Wairarapa",
    "Martinborough",
    "Featherston Wairarapa",
]

# Address fragments used to keep only Wellington-region results
WELLINGTON_REGION_MARKERS = [
    "Wellington", "Porirua", "Lower Hutt", "Upper Hutt", "Hutt City",
    "Paraparaumu", "Waikanae", "Otaki", "Raumati", "Paekakariki",
    "Masterton", "Carterton", "Greytown", "Martinborough", "Featherston",
    "Tawa", "Porirua", "Wainuiomata",
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
    return any(marker in address for marker in WELLINGTON_REGION_MARKERS)


def town_label(town_query: str) -> str:
    """Strip location qualifier to get clean town name for the CSV."""
    return town_query.split()[0] if " " not in town_query.replace(" Wellington", "").replace(" Porirua", "").replace(" Lower Hutt", "").replace(" Wairarapa", "") else town_query.replace(" New Zealand", "")


def main():
    all_rows = []
    seen = set()

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
                "town": town,
                "price": "no_prices",
            }
            all_rows.append(row)
            new_count += 1
            print(f"    {row['name']} — {address}")

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
