#!/usr/bin/env python3
"""
Filter dental_clinics_auckland.csv (raw Places API results) down to genuine
new dental clinics and merge into dental_clinics_all.csv, following the same
approach used for the previous region merges. Also checks new entries for
same-address + same-phone-number collisions against already-existing
clinics (an individual dentist's personal GMB listing for an already-listed
practice is not a new clinic).
"""
import csv
import re
from collections import defaultdict
from datetime import date

with open("dental_clinics_all.csv", encoding="utf-8-sig", newline="") as f:
    existing = list(csv.DictReader(f))
    fieldnames = list(existing[0].keys())

existing = [r for r in existing if r.get("name") != "name"]
existing_names = {r["name"].strip().lower() for r in existing}
existing_urls = {r["google_maps_url"].strip() for r in existing if r["google_maps_url"].strip()}
existing_addr_phone = {
    (r["address"].strip(), r["phone_national"].strip())
    for r in existing
    if r["phone_national"].strip()
}

suburb_map = {}
for r in existing:
    if r["region"] == "Auckland":
        suburb_map[r["suburb_town"].strip().lower()] = (r["city"], r["region"])

EXCLUDE_NAME = re.compile(
    r"\b(pharmacy|chemist|unichem|vets?|veterinary|animates|hospital|"
    r"medical centre|medical practice|medical care|medical limited|medical store|"
    r"medical & health|family healthcare|tui medical|after.?hours|urgent care|accident (&|and) medical|"
    r"family doctors|doctors at|clinical centre|dental marketing|"
    r"school dental clinic|bee healthy|nzda|dental council|sedation in dentistry|"
    r"laboratory|dental lab\b|dentocast|institute of digital dentistry|prosthetic lab|"
    r"new world|pak.?nsave|freshchoice|countdown|woolworths|supermarket|the warehouse|mitre 10|mcdonald|"
    r"four square|chiropractic|information centre|community services|community kindergarten|community centre|"
    r"laser clinics|sleep matters|healthcare essentials|community vaccination|"
    r"vaccination centre|health hub|health centre|health care|natural health|wellness|wellbeing hub|"
    r"radiology|community oral health|community dental|diagnostic centre|te whatu ora|"
    r"birthing centre|elder abuse|beauty|urban retreat|mall\b|college\b|"
    r"community library|cosmetic clinic|whitening co|polyclinic|skin clinic|"
    r"law centre|family centre|family health|health network|imaging|plunket|"
    r"laundromat|health enterprise|health trust|community clinic|whanau ora|"
    r"family care centre|hauora|animal bedding|fono\b|taiwhenua|"
    r"fallen soldiers|memorial hospital|carefirst|rural healthcare|district health board|"
    r"hungry pet|motel\b|aged residential care|kindergarten|care village|"
    r"the doctors|church\b|community health centre|optometrist|health center|healthcare nz)\b",
    re.IGNORECASE,
)
EXCLUDE_EXACT: set[str] = {
    "dentist",  # no business name, junk listing
    "wiri family doctors",  # GP practice, not dental
    "devonport naval dental clinic",  # military facility, not open to the public
    "beach haven clinic",  # vague generic clinic name, not confirmed dental
    "the hemp store",  # not a dental business
    "dominion road surgery",  # GP practice, not dental
    "dental surgeon",  # no business name, junk listing
    "smilepath - new zealand",  # at-home clear-aligner company, not a physical clinic
    "southern cross dental nz (auckland office)",  # dental laboratory (scdlab.co.nz), not a patient clinic
    "ards childrens dental clinic ponsonby",  # ARDS free community children's dental service
    "auckland regional dental service",  # ARDS free community children's dental service
    "may road children's dental clinic",  # ARDS free community children's dental service
    "lynfield shopping centre",  # shopping centre, not a business
    "local doctors mount roskill",  # GP practice chain
    "lynfield medical clinic",  # GP practice
    "eastridge shopping centre",  # shopping centre, not a business
    "onehunga",  # bare place-name listing, not a real business
    "mangere town centre",  # shopping centre, not a business
    "east tamaki healthcare mangere town centre",  # GP/healthcare provider
    "dental clinic",  # no business name, junk listing
    "manurewa intermediate dental clinic",  # school dental clinic
    "parking child dental clinic",  # data-quality artifact / community child dental clinic
    "manukau superclinic",  # public hospital outpatient facility, not a private dental clinic
    "auckland dental school",  # duplicate of "Auckland Dental Facility, University of Otago" (same address, no website)
    "pukekohe intermediate dental clinic",  # school dental clinic
    "carevets glen eden",  # vet clinic (no word-boundary match for "carevets")
    "carevets te atatu",  # vet clinic (no word-boundary match for "carevets")
    "titirangi library",  # library, not a business
    "peninsula medical",  # GP practice
    "te atatu health and physiotherapy",  # GP/physiotherapy practice
    "shorecare",  # vague generic name, GP/urgent-care-style branding
    "petstock takapuna",  # pet store
    "denture clinic",  # no business name, junk listing
    "henry schein new zealand",  # dental equipment/supply company, not a patient clinic
    "all health medical",  # GP practice
    "oralcare+ online dental supply store",  # online supply store, not a patient clinic
    "osstem implant new zealand",  # dental implant manufacturer/supplier
    "silverdale medical",  # GP practice
    "auckland dental association",  # professional association, not a clinic
    "oraltec - a division of pharmaco (nz) ltd",  # dental equipment/supply company
    "ards",  # ARDS free community children's dental service
    "new al-dawa medical & dental centre",  # GP/urgent-care practice (healthpoint-listed as GP)
    "auckland dentists",  # third-party directory/marketing site, not a standalone clinic
    "white cross - henderson 24/7",  # White Cross urgent-care/GP chain, not dental
}

DENTAL_OVERRIDE = re.compile(r"\b(lumino|dentist|dentists)\b", re.IGNORECASE)

# Manual suburb -> (city, region) overrides for suburbs not yet represented
# in the existing dataset, following the established city conventions
# (south Auckland growth towns -> Manukau, inner suburbs -> Auckland City)
MANUAL_SUBURB_MAP = {
    "wesley": ("Auckland City", "Auckland"),
    "drury": ("Manukau", "Auckland"),
    "point chevalier": ("Auckland City", "Auckland"),
    "hillsborough": ("Auckland City", "Auckland"),
    "golflands": ("Manukau", "Auckland"),
    "karaka": ("Manukau", "Auckland"),
}
# Malformed address fix -- Google returned "2 Mount Albert, Auckland 1025"
# (no real street name) for a clinic that's actually in Mount Albert
SUBURB_NORMALIZE = {
    "the dental suite, mt albert": "Mount Albert",
}


def is_excluded(r):
    name_lower = r["name"].strip().lower()
    if name_lower in EXCLUDE_EXACT:
        return True
    if DENTAL_OVERRIDE.search(r["name"]):
        return False
    return bool(EXCLUDE_NAME.search(r["name"]))


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


with open("dental_clinics_auckland.csv", encoding="utf-8", newline="") as f:
    raw = list(csv.DictReader(f))

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

# Same address + same phone as an EXISTING clinic -> not a new clinic
# (e.g. an individual dentist's personal listing for an already-listed practice)
dup_of_existing = [
    r for r in new_clinics
    if (r["address"].strip(), r["phone_national"].strip()) in existing_addr_phone
    and r["phone_national"].strip()
]
new_clinics = [r for r in new_clinics if r not in dup_of_existing]

# Same address + same phone shared between two NEW entries -> keep only one
by_addr_phone = defaultdict(list)
for r in new_clinics:
    key = (r["address"].strip(), r["phone_national"].strip())
    if key[1]:
        by_addr_phone[key].append(r)
mutual_dups_dropped = []
final_new = []
seen_keys = set()
for r in new_clinics:
    key = (r["address"].strip(), r["phone_national"].strip())
    if key[1] and len(by_addr_phone[key]) > 1:
        if key in seen_keys:
            mutual_dups_dropped.append(r)
            continue
        seen_keys.add(key)
    final_new.append(r)
new_clinics = final_new

today = date.today().isoformat()
merged_rows = []
unmapped = []

for r in new_clinics:
    if r["name"].strip().lower() in SUBURB_NORMALIZE:
        suburb = SUBURB_NORMALIZE[r["name"].strip().lower()]
    else:
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

print(f"Raw: {len(raw)}  After noise filter: {len(kept)}")
print(f"Skipped (same place as existing, different name via URL): {len(same_place_diff_name)}")
print(f"Skipped (same address+phone as existing -- not actually new): {len(dup_of_existing)}")
for r in dup_of_existing:
    print(f"  {r['name']!r} @ {r['address']}")
print(f"Skipped (mutual duplicate among new entries): {len(mutual_dups_dropped)}")
for r in mutual_dups_dropped:
    print(f"  {r['name']!r} @ {r['address']}")
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
