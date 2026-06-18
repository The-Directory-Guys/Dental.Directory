#!/usr/bin/env python3
"""
Filter dental_clinics_otago_fresh.csv (raw Places API results) down to
genuine new dental clinics and merge into dental_clinics_all.csv, following
the same approach used for the Wellington, Waikato, and Bay of Plenty merges.
"""
import csv
import re
from datetime import date

with open("dental_clinics_all.csv", encoding="utf-8-sig", newline="") as f:
    existing = list(csv.DictReader(f))
    fieldnames = list(existing[0].keys())

existing = [r for r in existing if r.get("name") != "name"]
existing_names = {r["name"].strip().lower() for r in existing}
existing_urls = {r["google_maps_url"].strip() for r in existing if r["google_maps_url"].strip()}

suburb_map = {}
for r in existing:
    if r["region"] == "Otago":
        suburb_map[r["suburb_town"].strip().lower()] = (r["city"], r["region"])

EXCLUDE_NAME = re.compile(
    r"\b(pharmacy|chemist|unichem|vets?|veterinary|animates|hospital|"
    r"medical centre|medical practice|medical care|medical limited|medical store|"
    r"medical & health|tui medical|after.?hours|urgent care|"
    r"school dental|bee healthy|nzda|dental council|sedation in dentistry|"
    r"laboratory|dental lab\b|dentocast|institute of digital dentistry|prosthetic lab|"
    r"new world|pak.?nsave|freshchoice|countdown|woolworths|the warehouse|mitre 10|"
    r"four square|chiropractic|information centre|community services|community kindergarten|"
    r"laser clinics|sleep matters|healthcare essentials|community vaccination|"
    r"vaccination centre|health hub|health centre|wellness|wellbeing hub|"
    r"radiology|community dental|community oral health|diagnostic centre|te whatu ora|"
    r"birthing centre|elder abuse|beauty|urban retreat|mall\b|college\b|"
    r"community library|cosmetic clinic|whitening co)\b",
    re.IGNORECASE,
)
EXCLUDE_EXACT: set[str] = {
    "dunedin urgent doctors & accident centre",  # urgent care / GP, not dental
    "waverley health",  # general health practice, not dental
    "maori hill clinic",  # generic GP-style clinic name, not confirmed dental
    "west otago health limited",  # general regional health provider
    "vetsouth tapanui",  # vet clinic
    "healthcentral",  # generic GP-style practice, not dental
    "vetlife st kilda",  # vet clinic (no word-boundary match for "vetlife")
    "central dental - cromwell",  # duplicate Google listing of existing "Central Dental" (same phone/hours/address)
}

# Unambiguous dental brand signals -- never exclude a listing carrying one of
# these, even if its name also matches a generic "health/medical" pattern
# (e.g. "Milton Health Centre - Lumino The Dentists" is a real Lumino practice
# that happens to be located inside a building called "Milton Health Centre").
# Deliberately excludes bare "dental" -- that alone still shows up in lab/
# equipment-supplier names ("Dental Laboratory") that should stay excluded.
DENTAL_OVERRIDE = re.compile(r"\b(lumino|dentist)\b", re.IGNORECASE)

# Manual suburb -> (city, region) overrides / aliases
MANUAL_SUBURB_MAP = {
    "central dunedin": ("Dunedin", "Otago"),  # same place as "Dunedin Central", different word order
    "maori hill": ("Dunedin", "Otago"),
}

WHITENING_NAME = re.compile(r"whiten", re.IGNORECASE)


def is_excluded(r):
    if DENTAL_OVERRIDE.search(r["name"]):
        return False
    return bool(EXCLUDE_NAME.search(r["name"])) or r["name"].strip().lower() in EXCLUDE_EXACT


def parse_suburb(address: str) -> str:
    parts = [p.strip() for p in address.split(",")]
    if len(parts) < 3:
        return ""
    city_postcode = parts[-2]
    suburb = parts[-3]
    if re.match(r"^\d", suburb):
        town = re.sub(r"\s*\d{4}$", "", city_postcode).strip()
        return town
    return suburb


with open("dental_clinics_otago_fresh.csv", encoding="utf-8", newline="") as f:
    raw = list(csv.DictReader(f))

# "Frankton" is ambiguous (a Hamilton suburb as well as a Queenstown one) --
# the OTAGO_REGION_MARKERS match in scrape_otago.py let a Hamilton clinic
# leak through. Drop anything whose address isn't actually in Otago.
raw = [r for r in raw if "Hamilton" not in r["address"]]

kept = [r for r in raw if not is_excluded(r)]

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

SUBURB_NORMALIZE = {
    "central dunedin": "Dunedin Central",
}

for r in new_clinics:
    suburb = parse_suburb(r["address"])
    suburb = SUBURB_NORMALIZE.get(suburb.strip().lower(), suburb)
    lookup = suburb_map.get(suburb.strip().lower()) or MANUAL_SUBURB_MAP.get(suburb.strip().lower())
    if not lookup:
        parts = [p.strip() for p in r["address"].split(",")]
        if len(parts) >= 3:
            town = re.sub(r"\s*\d{4}$", "", parts[-2]).strip()
            fallback = suburb_map.get(town.lower()) or MANUAL_SUBURB_MAP.get(town.lower())
            if fallback:
                suburb = town
                lookup = fallback
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

print(f"Raw: {len(raw)}  After noise filter: {len(kept)}")
if same_place_diff_name:
    print(f"Skipped (same place as existing, different name): {len(same_place_diff_name)}")
    for r in same_place_diff_name:
        print(f"  {r['name']!r}")
print(f"New clinics found: {len(new_clinics)}")
print(f"Mapped: {len(merged_rows)}  Unmapped: {len(unmapped)}")
for n, a, s in unmapped:
    print(f"  UNMAPPED: {n} | suburb={s!r} | {a}")

if merged_rows:
    with open("dental_clinics_all.csv", "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames, quoting=csv.QUOTE_ALL)
        writer.writeheader()
        writer.writerows(existing + merged_rows)
    print(f"\nWrote {len(existing) + len(merged_rows)} total rows to dental_clinics_all.csv")
