#!/usr/bin/env python3
"""
Keep listings suitable for private dental price comparison.

Removes: public hospital / school & community dental services, DHB admin
listings, ARDS / DHB community dental sites, GP & medical-centre pins,
urgent-care clinics, university dental schools, and needs_verification
rows that are clearly not dental practices.

Run: python filter_private_price_directory.py
"""
import csv
import re
import shutil
from pathlib import Path

ROOT = Path(__file__).resolve().parent
CSV_PATH = ROOT / "dental_clinics_all.csv"

DENTAL_HINT = re.compile(
    r"dental|dentist|tooth|orthodont|oral care|oral surgery|oral health|"
    r"endodont|periodont|prosthodont|implant|lumino|smile|braces|"
    r"maxillofacial|\boms\b",
    re.IGNORECASE,
)

# Public school / DHB “community dental” (not private fee-for-service listings)
PUBLIC_SCHOOL_COMMUNITY_DENTAL = re.compile(
    r"children'?s community dental|"
    r"intermediate children'?s community dental|"
    r"children community dental clinic|"
    r"primary children'?s community dental|"
    r"child and adolescent community dental|"
    r"child & adolescent community dental|"
    r"child adolescent community dental|"
    r"community dental clinic\b|"
    r"\bintermediate dental clinic\b|"
    r"\bcommunity dental\b",
    re.IGNORECASE,
)

def _is_gp_only_listing(name: str, site: str) -> bool:
    """True if the listing name/site is clearly a GP clinic, not a dental practice."""
    if DENTAL_HINT.search(name):
        return False
    n = (name or "").lower()
    s = (site or "").lower()
    if "tend.nz" in s:
        return True
    if "family doctors" in n or "family doctor" in n:
        return True
    if re.search(r"\bmedical centre\b", n):
        return True
    if "riccarton clinic" in n:
        return True
    return False


# needs_verification rows to drop (not private fee-for-service dental comparison)
NEEDS_VERIF_BAD = re.compile(
    r"community law|radiology|supermarket|remarkables park town|"
    r"lumsden prescriptions|me and mi|"
    r"health new zealand|te whatu ora|"
    r"wairau hospital|nelson hospital|dunedin hospital|southland hospital|"
    r"stewart island health|"
    r"roxburgh area school|otautau school|lumsden school|"
    r"dunedin urgent doctors|arrowtown medical|gardens medical centre|"
    r"the village medical centre|roxburgh medical centre|"
    r"northern southland medical|otautau medical|tuatapere medical|"
    r"te kaika|west otago health|tuapeka community health",
    re.IGNORECASE,
)


def is_price_comparison_listing(row: dict) -> bool:
    """Return True to KEEP the row."""
    name = row.get("name") or ""
    n = name.lower()
    cat = (row.get("category") or "").strip()

    if name.strip() == "Franz Josef Clinic":
        return False
    if name.strip() == "New Al-Dawa Medical & Dental Centre":
        return False

    site = (row.get("website") or "").lower()

    # Veterinary clinic (human dental directory)
    if "animalmedicalcentre.co.nz" in site:
        return False

    # DHB community health org (not a dental practice listing)
    if "countiesmanukau.health.nz" in site and "community health" in n:
        return False

    # Healthpoint pages for GPs / superclinics — not dental practice providers
    if "healthpoint.co.nz" in site:
        if "manukau-superclinic" in site:
            return False
        if (
            "/doctors/gp/" in site
            or "/gps-accident-urgent-medical-care/gp/" in site
        ) and not DENTAL_HINT.search(name):
            return False

    # Public school / DHB community dental websites
    if "ards.co.nz" in site:
        return False
    if "waitematadhb.govt.nz" in site:
        return False
    if "letstalkteeth.co.nz" in site:
        return False
    if "cdhb.health.nz" in site and "community-dental" in site:
        return False
    if "info.health.nz" in site and "community-dental" in site:
        return False
    if "servicefinder.co.nz" in site and "community-dental" in site:
        return False
    # School intermediate clinic misfiled under Healthpoint “general dentist”
    if "healthpoint.co.nz" in site and "intermediate-dental" in site:
        return False

    if PUBLIC_SCHOOL_COMMUNITY_DENTAL.search(name):
        return False

    # GP / medical-centre Google pins (no dental practice name)
    if _is_gp_only_listing(name, site):
        return False

    if cat == "medical_centre":
        return False

    # University teaching clinics (not typical consumer price shopping)
    if "faculty of dentistry" in n:
        return False
    if "auckland dental school" in n:
        return False
    if "university of otago" in n and "dental" in n:
        return False

    # Public / school dental programmes
    if "school dental" in n:
        return False
    if "school & community dental" in n:
        return False
    if "community dental service" in n:
        return False
    if "woolston community dental" in n:
        return False

    # DHB / national org pins (not a practice)
    if "health new zealand" in n or "te whatu ora" in n:
        return False

    # Whole-hospital listings (includes public hospital dental departments)
    if re.search(r"\bhospital\b", n):
        return False

    # GP / urgent care (name field only — not "The Tooth Doctor" at an urgent-care address)
    if "urgent care" in n or "urgentcare" in n.replace(" ", ""):
        if not DENTAL_HINT.search(name):
            return False
    if re.search(r"\bgp\s*&\s*urgent", n) or re.search(r"\bgp\s+and\s+urgent", n):
        return False
    if "tui medical" in n:
        return False
    if "accident and medical clinic" in n and not DENTAL_HINT.search(name):
        return False

    if cat == "needs_verification":
        if NEEDS_VERIF_BAD.search(name):
            return False

    return True


def main() -> None:
    backup = CSV_PATH.with_suffix(CSV_PATH.suffix + ".bak")
    shutil.copy2(CSV_PATH, backup)
    print(f"Backup: {backup}")

    with CSV_PATH.open(newline="", encoding="utf-8") as f:
        rows = list(csv.DictReader(f))
    fieldnames = rows[0].keys() if rows else []

    kept = [r for r in rows if is_price_comparison_listing(r)]
    removed = [r for r in rows if not is_price_comparison_listing(r)]

    with CSV_PATH.open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=fieldnames)
        w.writeheader()
        w.writerows(kept)

    print(f"Rows before: {len(rows)}")
    print(f"Removed:     {len(removed)}")
    print(f"Rows after:  {len(kept)}")
    for r in removed[:35]:
        print(f"  - {r.get('name', '')}")
    if len(removed) > 35:
        print(f"  ... and {len(removed) - 35} more")


if __name__ == "__main__":
    main()
