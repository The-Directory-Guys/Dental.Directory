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
    
    # Fix Mt Wellington Dental Centre
    for row in rows:
        if row["name"] == "Mt Wellington Dental Centre":
            row["region"] = "Auckland"
            row["town"] = "Mount Wellington Auckland"
    
    # Remove UK entries
    rows = [r for r in rows if r["name"] not in uk_names]
    
    with open("dental_clinics_all.csv", "w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)
    
    print("Fixed: Mt Wellington Dental Centre -> Auckland")
    print("Removed: 2 UK-based entries (Deveron Dental Centre, Huntly Dental Practice)")

if __name__ == "__main__":
    main()
