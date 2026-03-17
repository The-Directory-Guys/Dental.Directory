#!/usr/bin/env python3
"""
Scrape dental clinics in the Auckland region using the Google Places API (New).
Outputs results to dental_clinics_auckland.csv

Covers: Auckland City (all suburbs), North Shore, Waitākere, Manukau,
Papakura, Franklin, Rodney, and Waitematā districts.

Requires:
    GOOGLE_PLACES_API_KEY environment variable to be set.

Usage:
    python3 scrape_auckland.py
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
OUTPUT_FILE = "dental_clinics_auckland.csv"
REGION = "Auckland"

TOWNS = [
    # Auckland CBD / Inner City
    "Auckland CBD",
    "Newmarket Auckland",
    "Parnell Auckland",
    "Ponsonby Auckland",
    "Grey Lynn Auckland",
    "Freemans Bay Auckland",
    "Grafton Auckland",
    "Karangahape Road Auckland",
    "Eden Terrace Auckland",
    "Kingsland Auckland",

    # Auckland Inner East
    "Remuera Auckland",
    "Epsom Auckland",
    "Mount Eden Auckland",
    "Balmoral Auckland",
    "Sandringham Auckland",
    "Three Kings Auckland",
    "Royal Oak Auckland",

    # Auckland Eastern Suburbs
    "Mission Bay Auckland",
    "St Heliers Auckland",
    "Kohimarama Auckland",
    "Glendowie Auckland",
    "Ellerslie Auckland",
    "Panmure Auckland",
    "Glen Innes Auckland",
    "Point England Auckland",
    "Pakuranga Auckland",
    "Howick Auckland",
    "Botany Auckland",
    "Flat Bush Auckland",
    "Bucklands Beach Auckland",
    "Half Moon Bay Auckland",
    "Beachlands Auckland",

    # Auckland South / Manukau
    "Onehunga Auckland",
    "Penrose Auckland",
    "Mount Wellington Auckland",
    "Otahuhu Auckland",
    "Mangere Auckland",
    "Mangere Bridge Auckland",
    "Papatoetoe Auckland",
    "Manukau Auckland",
    "Manurewa Auckland",
    "Clendon Auckland",
    "Wiri Auckland",
    "Ōtara Auckland",
    "Clover Park Auckland",

    # Papakura / Franklin
    "Papakura",
    "Pukekohe",
    "Waiuku",
    "Tuakau",
    "Pokeno",
    "Huntly Waikato",  # border area already in Waikato but some may appear

    # Auckland West / Waitākere
    "New Lynn Auckland",
    "Glen Eden Auckland",
    "Henderson Auckland",
    "Massey Auckland",
    "West Harbour Auckland",
    "Ranui Auckland",
    "Swanson Auckland",
    "Titirangi Auckland",
    "Avondale Auckland",
    "Blockhouse Bay Auckland",
    "Green Bay Auckland",

    # Auckland Northwest
    "Kumeu Auckland",
    "Huapai Auckland",
    "Helensville Auckland",
    "Warkworth Auckland",
    "Wellsford Auckland",

    # North Shore
    "Takapuna Auckland",
    "Devonport Auckland",
    "Milford Auckland",
    "Forrest Hill Auckland",
    "Glenfield Auckland",
    "Northcote Auckland",
    "Birkenhead Auckland",
    "Beach Haven Auckland",
    "Birkdale Auckland",
    "Browns Bay Auckland",
    "Mairangi Bay Auckland",
    "Torbay Auckland",
    "Long Bay Auckland",
    "Albany Auckland",
    "Rosedale Auckland",
    "Unsworth Heights Auckland",

    # Hibiscus Coast / Rodney
    "Orewa Auckland",
    "Red Beach Auckland",
    "Silverdale Auckland",
    "Whangaparaoa Auckland",
    "Gulf Harbour Auckland",
    "Manly Auckland",
    "Stanmore Bay Auckland",
    "Snells Beach Auckland",
    "Algies Bay Auckland",
    "Matakana Auckland",
    "Leigh Auckland",

    # Islands
    "Waiheke Island Auckland",
    "Great Barrier Island Auckland",
]

AUCKLAND_REGION_MARKERS = [
    "Auckland",
    "Pukekohe",
    "Waiuku",
    "Tuakau",
    "Pokeno",
    "Papakura",
    "Manurewa",
    "Manukau",
    "Papatoetoe",
    "Otahuhu",
    "Mangere",
    "Onehunga",
    "Panmure",
    "Howick",
    "Pakuranga",
    "Botany",
    "Flat Bush",
    "Kumeu",
    "Helensville",
    "Warkworth",
    "Wellsford",
    "Orewa",
    "Silverdale",
    "Whangaparaoa",
    "Takapuna",
    "Devonport",
    "Glenfield",
    "Northcote",
    "Birkenhead",
    "Albany",
    "Waiheke",
    "Ostend",
    "Oneroa",
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
    return any(marker in address for marker in AUCKLAND_REGION_MARKERS)


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
