#!/usr/bin/env python3
"""Fix region errors in dental_clinics_all.csv"""

import csv


def main():
    with open("dental_clinics_all.csv", "r", encoding="utf-8", newline="") as f:
        reader = csv.DictReader(f)
        fieldnames = reader.fieldnames
        rows = list(reader)

    # Rows to remove (UK - not NZ clinics)
    uk_names = {"Deveron Dental Centre, Huntly", "Huntly Dental Practice"}

    nelson_merged = 0
    australia_removed = 0

    # Fix Mt Wellington Dental Centre
    for row in rows:
        if row["name"] == "Mt Wellington Dental Centre":
            row["region"] = "Auckland"
            row["suburb_town"] = "Mount Wellington Auckland"

    # Merge Nelson/Tasman -> Nelson
    for row in rows:
        if row.get("region") == "Nelson/Tasman":
            row["region"] = "Nelson"
            nelson_merged += 1

    # Remove UK entries
    before_uk = len(rows)
    rows = [r for r in rows if r["name"] not in uk_names]
    uk_removed = before_uk - len(rows)

    # Remove non-NZ clinics (e.g. Tasmania / Australia)
    before_au = len(rows)
    rows = [
        r
        for r in rows
        if "Australia" not in (r.get("address") or "")
    ]
    australia_removed = before_au - len(rows)

    with open("dental_clinics_all.csv", "w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)

    print("Fixed: Mt Wellington Dental Centre -> Auckland (if present)")
    if uk_removed:
        print(f"Removed: {uk_removed} UK-based entries")
    if nelson_merged:
        print(f"Merged region: Nelson/Tasman -> Nelson ({nelson_merged} rows)")
    if australia_removed:
        print(f"Removed: {australia_removed} Australia-based entries")


if __name__ == "__main__":
    main()
