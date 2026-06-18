#!/usr/bin/env python3
"""
Merge the 72 new genuine Wellington-area dental clinics (found by
filter_wellington_raw.py) into dental_clinics_all.csv, matching the existing
column schema and suburb_town/city/region conventions.
"""
import csv
import re
from datetime import date

with open("dental_clinics_all.csv", encoding="utf-8-sig", newline="") as f:
    existing = list(csv.DictReader(f))
    fieldnames = list(existing[0].keys())

# Drop a pre-existing stray duplicate-header row (line 2 of the file is
# literally the header repeated, which DictReader reads as a junk data row)
existing = [r for r in existing if r.get("name") != "name"]

existing_names = {r["name"].strip().lower() for r in existing}
existing_urls = {r["google_maps_url"].strip() for r in existing if r["google_maps_url"].strip()}

# Build suburb_town -> (city, region) lookup from already-known Wellington/Wairarapa rows
suburb_map = {}
for r in existing:
    if r["region"] in ("Wellington", "Wairarapa"):
        suburb_map[r["suburb_town"].strip().lower()] = (r["city"], r["region"])

EXCLUDE_NAME = re.compile(
    r"\b(pharmacy|chemist|unichem|vet|veterinary|animates|hospital|"
    r"medical centre|medical practice|medical care|medical limited|after.?hours|"
    r"school dental|bee healthy|nzda|dental council|sedation in dentistry|"
    r"laboratory|dental lab\b|dentocast|institute of digital dentistry|"
    r"new world|pak.?nsave|freshchoice|countdown|woolworths|the warehouse|"
    r"laser clinics|sleep matters|healthcare essentials|community vaccination|"
    r"vaccination centre|health hub|health centre)\b",
    re.IGNORECASE,
)
EXCLUDE_EXACT = {
    "kelvin house",
    "dental surgery",
    "dental corporation (nz) limited",
    "verve @ connolly",
    "ashley aesthetics",  # cosmetic/beauty, not dental
    "brooklyn central health",  # generic health centre, not dental-specific
    "wong kevin b",  # duplicate of existing "Kevin Wong Dental Surgery"
    "dentist wellington dental surgery tooth fillings tawa lower hutt",  # spammy/keyword-stuffed GMB name
    "paraparaumu dental hub clinic",  # website is info.health.nz/BeeHealthy - same free community service we exclude elsewhere
}

# Manual suburb -> (city, region) overrides for suburbs not yet in the existing dataset
MANUAL_SUBURB_MAP = {
    "fairfield": ("Lower Hutt", "Wellington"),
    "waterloo": ("Lower Hutt", "Wellington"),
    "stokes valley": ("Lower Hutt", "Wellington"),
    "waikanae": ("Waikanae", "Wellington"),
}

WHITENING_NAME = re.compile(r"whiten", re.IGNORECASE)


def is_excluded(r):
    return bool(EXCLUDE_NAME.search(r["name"])) or r["name"].strip().lower() in EXCLUDE_EXACT


def parse_suburb(address: str) -> str:
    parts = [p.strip() for p in address.split(",")]
    if len(parts) < 3:
        return ""
    city_postcode = parts[-2]
    suburb = parts[-3]
    # Small-town addresses have no separate suburb level, e.g.
    # "8 Mahara Place, Waikanae 5036, New Zealand" (3 parts) -- here
    # parts[-3] is actually the street, not a suburb. Detect this by
    # checking whether parts[-3] looks like a street (starts with a digit).
    if re.match(r"^\d", suburb):
        town = re.sub(r"\s*\d{4}$", "", city_postcode).strip()
        return town
    if suburb.upper() == "CBD":
        return "Wellington Central"
    return suburb


with open("dental_clinics_wellington.csv", encoding="utf-8", newline="") as f:
    raw = list(csv.DictReader(f))

kept = [r for r in raw if not is_excluded(r)]
# Exclude by name AND by google_maps_url -- the same physical place can come back
# from a fresh Places search with a slightly different display name, and matching
# only on name would create a duplicate row that collides with (and overwrites)
# the existing clinic on import (both share the same google_maps_url / cid).
new_clinics = [
    r for r in kept
    if r["name"].strip().lower() not in existing_names
    and r.get("google_maps_url", "").strip() not in existing_urls
]
same_place_diff_name = [
    r for r in kept
    if r["name"].strip().lower() not in existing_names
    and r.get("google_maps_url", "").strip() in existing_urls
]

today = date.today().isoformat()
merged_rows = []
unmapped = []

for r in new_clinics:
    suburb = parse_suburb(r["address"])
    lookup = suburb_map.get(suburb.strip().lower()) or MANUAL_SUBURB_MAP.get(suburb.strip().lower())
    if not lookup:
        unmapped.append((r["name"], r["address"], suburb))
        continue
    city, region = lookup

    new_row = {fn: "" for fn in fieldnames}
    new_row.update({
        "name": r["name"],
        "address": r["address"],
        "phone_national": r.get("phone_national", ""),
        "phone_international": r.get("phone_international", ""),
        "email": "",
        "website": r.get("website", ""),
        "rating": r.get("rating", ""),
        "total_ratings": r.get("total_ratings", ""),
        "business_status": r.get("business_status", "") or "OPERATIONAL",
        "google_maps_url": r.get("google_maps_url", ""),
        "opening_hours": r.get("opening_hours", ""),
        "category": "teeth_whitening" if WHITENING_NAME.search(r["name"]) else "dentist",
        "region": region,
        "suburb_town": suburb,
        "city": city,
        "price": "no_prices",
        "date_scraped": today,
        "description": "",
        "services": "General Dentistry",
    })
    merged_rows.append(new_row)

if same_place_diff_name:
    print(f"Skipped (same place as existing, different name string): {len(same_place_diff_name)}")
    for r in same_place_diff_name:
        print(f"  {r['name']!r}")

print(f"New clinics found: {len(new_clinics)}")
print(f"Successfully mapped to a suburb/city/region: {len(merged_rows)}")
print(f"Could not map (unknown suburb): {len(unmapped)}")
for n, a, s in unmapped:
    print(f"  UNMAPPED: {n} | suburb={s!r} | {a}")

if merged_rows:
    with open("dental_clinics_all.csv", "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames, quoting=csv.QUOTE_ALL)
        writer.writeheader()
        writer.writerows(existing + merged_rows)
    print(f"\nWrote {len(existing) + len(merged_rows)} total rows to dental_clinics_all.csv")
