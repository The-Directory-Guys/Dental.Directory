#!/usr/bin/env python3
"""
Remove non-dental rows from dental_clinics_all.csv:
  - Supermarket / grocery chains (website domain)
  - Pharmacies / chemists (website domain and/or name heuristics)

Run from repo root: python remove_false_listings.py
"""
import csv
import re
import shutil
from pathlib import Path

ROOT = Path(__file__).resolve().parent
CSV_PATH = ROOT / "dental_clinics_all.csv"

GROCERY_DENYLIST = (
    "newworld.co.nz",
    "paknsave.co.nz",
    "woolworths.co.nz",
    "countdown.co.nz",
    "foursquare.co.nz",
    "freshchoice.co.nz",
    "supervalue.co.nz",
)

PHARMACY_DENYLIST = (
    "chemistwarehouse.co.nz",
    "bargainchemist.co.nz",
    "lifepharmacy.co.nz",
    "lifepharmacy",  # e.g. lifepharmacyorewa.co.nz
    "unichem.co.nz",
    "healthpoint.co.nz/pharmacy",
    "nzpharmacy.co.nz",
    "d1p.co.nz",
)

# Name looks like a pharmacy / chemist (not a dental practice name)
PHARMACY_NAME = re.compile(
    r"\b(pharmacy|chemist|unichem)\b",
    re.IGNORECASE,
)


def website_matches(website: str, denylist) -> bool:
    w = (website or "").lower()
    return any(d in w for d in denylist)


def is_false_listing(row: dict) -> bool:
    site = row.get("website", "") or ""
    name = row.get("name", "") or ""

    if website_matches(site, GROCERY_DENYLIST):
        return True
    if website_matches(site, PHARMACY_DENYLIST):
        return True
    if PHARMACY_NAME.search(name):
        return True
    return False


def main() -> None:
    backup = CSV_PATH.with_suffix(CSV_PATH.suffix + ".bak")
    shutil.copy2(CSV_PATH, backup)
    print(f"Backup: {backup}")

    with CSV_PATH.open(newline="", encoding="utf-8") as f:
        rows = list(csv.DictReader(f))
    fieldnames = rows[0].keys() if rows else []

    removed = [r for r in rows if is_false_listing(r)]
    kept = [r for r in rows if not is_false_listing(r)]

    with CSV_PATH.open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=fieldnames)
        w.writeheader()
        w.writerows(kept)

    print(f"Rows before: {len(rows)}")
    print(f"Removed:     {len(removed)}")
    print(f"Rows after:  {len(kept)}")
    for r in removed[:20]:
        print(f"  - {r.get('name', '')}")
    if len(removed) > 20:
        print(f"  ... and {len(removed) - 20} more")


if __name__ == "__main__":
    main()
