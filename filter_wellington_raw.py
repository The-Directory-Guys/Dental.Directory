#!/usr/bin/env python3
"""
Filter the raw dental_clinics_wellington.csv (231 Places API results) down to
genuine commercial dental clinics, then compare against what's already in
dental_clinics_all.csv to find truly new clinics worth adding.
"""
import csv
import re

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

# Specific noise rows that slip past the name-pattern regex
EXCLUDE_EXACT = {
    "kelvin house",
    "dental surgery",
    "dental corporation (nz) limited",
    "verve @ connolly",
}

with open("dental_clinics_wellington.csv", encoding="utf-8") as f:
    raw = list(csv.DictReader(f))

def is_excluded(r):
    return bool(EXCLUDE_NAME.search(r["name"])) or r["name"].strip().lower() in EXCLUDE_EXACT

kept = [r for r in raw if not is_excluded(r)]
excluded = [r for r in raw if is_excluded(r)]

with open("dental_clinics_all.csv", encoding="utf-8-sig") as f:
    existing = list(csv.DictReader(f))
existing_names = {r["name"].strip().lower() for r in existing}

new_clinics = [r for r in kept if r["name"].strip().lower() not in existing_names]
already_have = [r for r in kept if r["name"].strip().lower() in existing_names]

with open("wellington_filter_report.txt", "w", encoding="utf-8") as out:
    out.write(f"Raw results: {len(raw)}\n")
    out.write(f"Excluded as non-dental: {len(excluded)}\n")
    out.write(f"Kept as dental clinics: {len(kept)}\n")
    out.write(f"  Already in DB: {len(already_have)}\n")
    out.write(f"  NEW: {len(new_clinics)}\n\n")

    out.write("=== EXCLUDED (non-dental) ===\n")
    for r in excluded:
        out.write(f"  {r['name']}\n")

    out.write("\n=== NEW CLINICS TO ADD ===\n")
    for r in new_clinics:
        out.write(f"  {r['name']} | {r['address']} | {r['town']}\n")

print("Report written to wellington_filter_report.txt")
print(f"Raw: {len(raw)}, excluded: {len(excluded)}, kept: {len(kept)}, already have: {len(already_have)}, NEW: {len(new_clinics)}")
