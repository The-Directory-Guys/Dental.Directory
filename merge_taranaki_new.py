#!/usr/bin/env python3
"""
Filter dental_clinics_taranaki.csv (raw Places API results) down to
genuine new dental clinics and merge into dental_clinics_all.csv, following
the same approach used for the previous region merges.
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
    if r["region"] == "Taranaki":
        suburb_map[r["suburb_town"].strip().lower()] = (r["city"], r["region"])

EXCLUDE_NAME = re.compile(
    r"\b(pharmacy|chemist|unichem|vets?|veterinary|animates|hospital|"
    r"medical centre|medical practice|medical care|medical limited|medical store|"
    r"medical & health|family healthcare|tui medical|after.?hours|urgent care|accident & medical|"
    r"school dental|bee healthy|nzda|dental council|sedation in dentistry|"
    r"laboratory|dental lab\b|dentocast|institute of digital dentistry|prosthetic lab|"
    r"new world|pak.?nsave|freshchoice|countdown|woolworths|supermarket|the warehouse|mitre 10|mcdonald|"
    r"four square|chiropractic|information centre|community services|community kindergarten|"
    r"laser clinics|sleep matters|healthcare essentials|community vaccination|"
    r"vaccination centre|health hub|health centre|health care|natural health|wellness|wellbeing hub|"
    r"radiology|community dental|community oral health|diagnostic centre|te whatu ora|"
    r"birthing centre|elder abuse|beauty|urban retreat|mall\b|college\b|"
    r"community library|cosmetic clinic|whitening co|polyclinic|skin clinic|"
    r"law centre|family centre|family health|health network|imaging|plunket|"
    r"laundromat|health enterprise|health trust|community clinic|whanau ora|"
    r"family care centre|hauora|animal bedding|fono\b|taiwhenua|"
    r"fallen soldiers|memorial hospital|carefirst|rural healthcare|"
    r"hungry pet|motel\b)\b",
    re.IGNORECASE,
)
EXCLUDE_EXACT: set[str] = {
    "dentist",  # no business name, junk listing
    "strandon health",  # generic health practice, not dental
    "co.lab clinic",  # vague generic clinic name, not confirmed dental
    "healthcare hub taranaki",  # generic health hub
    "coastalcare",  # GP/medical practice
    "patea district & community medical trust 2000",  # general community medical trust
    "patea health clinic",  # generic GP-style health clinic, not confirmed dental
    "hamilton dental",  # duplicate Google listing of existing "Kerry Hamilton Dental New Plymouth" (same address/phone)
}

# Manual suburb -> (city, region) overrides for New Plymouth suburbs not yet
# represented in the existing dataset
MANUAL_SUBURB_MAP = {
    "frankleigh park": ("New Plymouth", "Taranaki"),
    "highlands park": ("New Plymouth", "Taranaki"),
    "lynmouth": ("New Plymouth", "Taranaki"),
}

DENTAL_OVERRIDE = re.compile(r"\b(lumino|dentist|dentists)\b", re.IGNORECASE)


def is_excluded(r):
    name_lower = r["name"].strip().lower()
    if name_lower in EXCLUDE_EXACT:
        return True
    if DENTAL_OVERRIDE.search(r["name"]):
        return False
    return bool(EXCLUDE_NAME.search(r["name"]))


def is_nz(address: str) -> bool:
    return address.strip().endswith("New Zealand")


def parse_suburb(address: str) -> str:
    parts = [p.strip() for p in address.split(",")]
    if len(parts) < 2:
        return ""
    if len(parts) == 2:
        return re.sub(r"\s*\d{4}$", "", parts[-2]).strip()
    city_postcode = parts[-2]
    suburb = parts[-3]
    if re.match(r"^\d", suburb):
        town = re.sub(r"\s*\d{4}$", "", city_postcode).strip()
        return town
    return suburb


with open("dental_clinics_taranaki.csv", encoding="utf-8", newline="") as f:
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
        "category": "teeth_whitening" if re.search(r"whiten", r["name"], re.IGNORECASE) else "dentist",
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
