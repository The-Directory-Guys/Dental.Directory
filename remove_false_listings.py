#!/usr/bin/env python3
"""
Remove non-dental rows from dental_clinics_all.csv:
  - Supermarket / grocery chains (website domain)
  - Pharmacies / chemists (website domain and/or name heuristics)
  - Big-box / general retail (The Warehouse, Mitre 10, Bunnings, etc.)
  - Veterinary clinics (website domain and/or name)
  - Pet stores / pet supply retail (Animates shops, Petstock, etc.)
  - Schools, finance companies, physiotherapy, medical imaging, pathology
  - Dental laboratories (technician labs, not patient-facing clinics)
  - Teeth-whitening kiosks / non-dentist whitening services
  - Denture + hearing clinics (Clinico chain)
  - Online dental supply stores
  - Non-dental wellness / health centres

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

# Department / hardware / variety retail (NZ chains that often appear in "dental" searches)
RETAIL_DENYLIST = (
    "thewarehouse.co.nz",
    "mitre10.co.nz",
    "bunnings.co.nz",
    "kmart.co.nz",
    "farmers.co.nz",
    "smithscity.co.nz",
    "pbtech.co.nz",
    "noelleeming.co.nz",
    "briscoes.co.nz",
    "rebel.co.nz",
    "huntingandfishing.co.nz",
    "spotlightstores.co.nz",
    "placemakers.co.nz",
    "jaycar.co.nz",
)

# Name looks like a pharmacy / chemist (not a dental practice name)
PHARMACY_NAME = re.compile(
    r"\b(pharmacy|chemist|unichem)\b",
    re.IGNORECASE,
)

# Retail chain names if website is missing or unusual
RETAIL_NAME = re.compile(
    r"^(The Warehouse|Mitre 10|Mitre10)\b",
    re.IGNORECASE,
)

# NZ veterinary clinic websites (substring match)
VET_DENYLIST = (
    "animatesvetcare.co.nz",
    "bbvet.co.nz",
    "carevets.co.nz",
    "franklinvets.co.nz",
    "vetforpet.co.nz",
    "orewabeachvetclinic.co.nz",
    "shorevets.co.nz",
    "stlukesvet.co.nz",
    "vetcentre.co.nz",
    "bayvets.net.nz",
    "coastalpetvet.co.nz",
    "vetora.co.nz",
    "avonheadvets.co.nz",
    "mypetfirst.co.nz",
    "harewoodvet.co.nz",
    "kowhaivet.co.nz",
    "ncvets.co.nz",
    "ourvetsparklands.co.nz",
    "rangioravetcentre.co.nz",
    "vetlife.co.nz",
    "wigramvet.co.nz",
    "clivevets.co.nz",
    "cahillanimalhospital.co.nz",
    "centralvetspalmerstonnorth.co.nz",
    "remarkablevets.co.nz",
    "vetsouth.co.nz",
    "nsvets.co.nz",
    "otautauvets.co.nz",
    "bop.vetora.co.nz",
    "haurakivets.co.nz",
    "thevet.co.nz",
    "yourvet.co.nz",
    "corovets.co.nz",
    "swvs.co.nz",
    "cenvet.co.nz",
    "vshb.co.nz",
    "anexa.co.nz",
    "petdoctors",
)

# Names / brands for vet clinics (Animates Vetcare uses animates.co.nz for some branches)
VET_NAME = re.compile(
    r"Animates Vetcare|"
    r"\b(veterinary|veterinarian|animal hospital|vetlife|vetora|carevets|vetsouth|"
    r"nsvets|remarkable vets|ourvets|coastal pet vet|cahill animal|franklin vets|"
    r"shore vets|bay vets|the vet centre|central vets|rangiora vet centre|"
    r"otautau vets|mangere veterinary|bucklands beach veterinary|"
    r"orewa beach veterinary|st lukes veterinary|north canterbury veterinary|"
    r"clive cottage vet|farmfirst and petfirst veterinary|harewood veterinary|"
    r"wigram vet|kowhai vet|vet clinic|vets limited|vet centre|pet vet|"
    r"the vet|vet services|yourvet|anexa vets|corovets|south waikato vet|"
    r"central vet hospital|pet doctors)\b|"
    r"\sVets$",
    re.IGNORECASE,
)

# Pet supply / pet store chains (not veterinary clinics; vet uses separate domains)
PET_STORE_DENYLIST = (
    "animates.co.nz",
    "petstock.co.nz",
    "thepetcentre.co.nz",
    "petbarn.co.nz",
    "petdirect.co.nz",
    "petpost.co.nz",
)

PET_STORE_NAME = re.compile(
    r"^Animates\b|"
    r"\bPetstock\b|"
    r"^The Pet Centre\b",
    re.IGNORECASE,
)

# Dental laboratories — technician labs, not patient-facing clinics
DENTAL_LAB_NAME = re.compile(
    r"\bdental\s+lab(oratory|oratories)?\b|"
    r"\bprosthetic\s+lab\b|"
    r"^Dentocast\b",
    re.IGNORECASE,
)

# Teeth-whitening kiosks / non-dentist whitening services
TEETH_WHITENING_NAME = re.compile(
    r"sparkle?\s*white\s+teeth|"
    r"sparkling\s+white\s+smile|"
    r"\bteeth\s+whitening\s+(lab|studio|lounge|bar|kiosk)\b",
    re.IGNORECASE,
)

# Exact name matches for one-off non-dental businesses
NON_DENTAL_NAMES = frozenset({
    # Schools
    "Papakura Normal Primary School",
    "Edgecumbe College",
    "Marton School",
    "Opunake Primary School",
    # Finance
    "Instant Finance Mangere",
    # Physiotherapy
    "Waihi Beach Physiotherapy & Acupuncture",
    # Medical imaging & pathology
    "Canopy Imaging Palmerston North",
    "Medlab Central - The Palms",
    # Non-dental wellness / health
    "Essence Wellness Clinic",
    "Te Kohao Health - Taakiri Tuu Wellness and Diagnostic Centre",
    # Online dental supply (not a clinic)
    "OralCare+ Online Dental Supply Store",
    # Denture + hearing clinics (Clinico chain)
    "Clinico Denture & Hearing - Rotorua",
    "Clinico Denture & Hearing - Hamilton",
    "Clinico Denture & Hearing - Te Awamutu",
    "Clinico Denture & Hearing - Thames",
    "Clinico Denture & Hearing - Tokoroa",
    "Clinico Denture & Hearing - Waihi",
    # Dental labs not matched by DENTAL_LAB_NAME regex
    "ConfiDental Laboratory and Clinic",
    "Oamaru Denture Clinic/Oamaru Dental Laboratory",
    "Seaside Dental Laboratory & Denture Clinic",
    "Hauraki Smiles Dental Laboratory Ltd.",
    "Life Dental previously known as Timaru Dental Laboratory",
    "The Teeth Whitening Lab - Christchurch Former Dental Therapist",
})


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
    if website_matches(site, RETAIL_DENYLIST):
        return True
    if website_matches(site, VET_DENYLIST):
        return True
    if PHARMACY_NAME.search(name):
        return True
    if RETAIL_NAME.search(name):
        return True
    if VET_NAME.search(name):
        return True
    if website_matches(site, PET_STORE_DENYLIST):
        return True
    if PET_STORE_NAME.search(name):
        return True
    if name in NON_DENTAL_NAMES:
        return True
    if DENTAL_LAB_NAME.search(name):
        return True
    if TEETH_WHITENING_NAME.search(name):
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
