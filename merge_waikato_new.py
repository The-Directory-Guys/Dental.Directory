#!/usr/bin/env python3
"""
Filter dental_clinics_waikato.csv (raw Places API results) down to genuine
new dental clinics and merge into dental_clinics_all.csv, following the same
approach used for the Wellington merge.
"""
import csv
import re
from datetime import date

with open("dental_clinics_all.csv", encoding="utf-8-sig", newline="") as f:
    existing = list(csv.DictReader(f))
    fieldnames = list(existing[0].keys())

existing = [r for r in existing if r.get("name") != "name"]  # drop stray dup header row if present
existing_names = {r["name"].strip().lower() for r in existing}
existing_urls = {r["google_maps_url"].strip() for r in existing if r["google_maps_url"].strip()}

suburb_map = {}
for r in existing:
    if r["region"] == "Waikato":
        suburb_map[r["suburb_town"].strip().lower()] = (r["city"], r["region"])

EXCLUDE_NAME = re.compile(
    r"\b(pharmacy|chemist|unichem|vets?|veterinary|animates|hospital|"
    r"medical centre|medical practice|medical care|medical limited|tui medical|after.?hours|"
    r"school dental|bee healthy|nzda|dental council|sedation in dentistry|"
    r"laboratory|dental lab\b|dentocast|institute of digital dentistry|prosthetic lab|"
    r"new world|pak.?nsave|freshchoice|countdown|woolworths|the warehouse|"
    r"four square|chiropractic|information centre|community services|"
    r"laser clinics|sleep matters|healthcare essentials|community vaccination|"
    r"vaccination centre|health hub|health centre|wellness|urgent care|"
    r"radiology|community dental|diagnostic centre|te whatu ora)\b",
    re.IGNORECASE,
)
EXCLUDE_EXACT: set[str] = {
    "thames",  # bare place-name listing, not a real business
    "contact care",
    "coromandel family health clinic",  # general health clinic, not dental
    "corovets tairua",  # vet clinic
    "health ngatea",  # general health clinic, not dental
    "changing faces",  # cosmetic/plastic surgery clinic, not dental
    "anglesea a & e",  # urgent care / A&E medical clinic
    "john sullivan house",  # building name, not a business
    "the cosmetic clinic centre place",  # cosmetic injectables clinic
    "redicare family practice",  # GP medical practice
    "raukura hauora o tainui - waikato office",  # Maori health provider, general health
    "raukura hauora o tainui - te papanui medical clinic",  # general health clinic
    "te kohao health ltd",  # general health provider (Te Kohao Dental already covered separately)
    "127 peachgrove rd, hamilton",  # no business name, junk listing
    "breathe free clinic",  # breathing/sleep clinic, not general/cosmetic dentistry
    "cambridge family health",  # GP medical practice, not dental
    "dentist",  # no business name, junk listing
}

WHITENING_NAME = re.compile(r"whiten", re.IGNORECASE)


def is_nz(address: str) -> bool:
    return address.strip().endswith("New Zealand")


def is_excluded(r):
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


with open("dental_clinics_waikato.csv", encoding="utf-8", newline="") as f:
    raw = list(csv.DictReader(f))

nz_only = [r for r in raw if is_nz(r["address"])]
kept = [r for r in nz_only if not is_excluded(r)]

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
    lookup = suburb_map.get(suburb.strip().lower())
    if not lookup:
        # Fallback: try the town name (city+postcode, postcode stripped) in case
        # the suburb-level address segment was actually a building/road name.
        parts = [p.strip() for p in r["address"].split(",")]
        if len(parts) >= 3:
            town = re.sub(r"\s*\d{4}$", "", parts[-2]).strip()
            fallback = suburb_map.get(town.lower())
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

print(f"Raw: {len(raw)}  NZ-only: {len(nz_only)}  After noise filter: {len(kept)}")
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
