"""
Import the national amenities-scrape results (from scrape_amenities_claude.py)
into the clinic_amenities and clinic_practitioners Supabase tables.

Reads every amenities_*.json file from this session, skips entries that
errored (no "data" key), and upserts the rest. Re-runnable: clears any
existing rows for a clinic_id before inserting fresh ones, so this can be
re-run safely after a re-scrape without creating duplicates.

Usage:
    python supabase/import_amenities.py                # preview, 5 clinics
    python supabase/import_amenities.py --apply         # import everything
"""

import json
import os
import sys
from datetime import date
from urllib.parse import urlparse

import requests
from dotenv import load_dotenv

sys.stdout.reconfigure(encoding="utf-8")
load_dotenv()

SUPABASE_URL = os.environ["SUPABASE_URL"]
SUPABASE_KEY = os.environ["SUPABASE_SERVICE_KEY"]
TODAY = str(date.today())

HEADERS = {
    "apikey": SUPABASE_KEY,
    "Authorization": f"Bearer {SUPABASE_KEY}",
    "Content-Type": "application/json",
    "Prefer": "return=minimal",
}

AMENITIES_FILES = [
    "amenities_test_christchurch.json",
    "amenities_south_island_rest.json",
    "amenities_wellington.json",
    "amenities_wairarapa_gisborne.json",
    "amenities_manawatu_taranaki_hawkesbay.json",
    "amenities_auckland.json",
    "amenities_bay_of_plenty.json",
    "amenities_waikato.json",
    "amenities_northland.json",
]

AMENITY_COLS = [
    "parking_access", "wheelchair_accessible", "same_day_emergency",
    "saturday_evening_hours", "in_house_specialists", "practice_size",
    "sedation_options", "calming_amenities", "dental_anxiety_friendly",
    "years_open", "awards", "professional_memberships", "before_after_gallery",
    "online_booking", "new_patient_forms_online", "payment_partners",
    "membership_plans", "kids_family_friendly",
]

# These are `boolean` columns in clinic_amenities, but Claude sometimes
# returns a descriptive sentence instead of strict true/false/null (e.g.
# same_day_emergency: "Emergency treatment within 25 hours"). Postgres
# rejects free text as an invalid boolean literal, so coerce any non-empty
# string to True (the detail text itself isn't stored in this scalar table).
BOOL_COLS = {
    "wheelchair_accessible", "same_day_emergency", "saturday_evening_hours",
    "dental_anxiety_friendly", "before_after_gallery", "online_booking",
    "new_patient_forms_online",
}


def domain(url: str) -> str:
    try:
        return urlparse(url).netloc.lstrip("www.") or url
    except Exception:
        return url


def load_all_clinics() -> list[dict]:
    """Read every amenities file, dedupe by clinic id (last write wins, so a
    re-scrape's results in a later file override an earlier failed attempt)."""
    by_id = {}
    for fn in AMENITIES_FILES:
        if not os.path.exists(fn):
            print(f"  (skipping missing file: {fn})")
            continue
        with open(fn, encoding="utf-8") as f:
            entries = json.load(f)
        for e in entries:
            if "data" in e:
                by_id[e["id"]] = e
    return list(by_id.values())


def build_amenity_row(entry: dict) -> dict:
    data = entry["data"]
    row = {"clinic_id": entry["id"], "source": f"scraper:{domain(entry['url'])}",
           "source_url": entry["url"], "scraped_at": TODAY}
    for col in AMENITY_COLS:
        val = data.get(col)
        if val in ([], ""):
            val = None
        if col in BOOL_COLS and val is not None and not isinstance(val, bool):
            val = True
        row[col] = val
    return row


def build_practitioner_rows(entry: dict) -> list[dict]:
    rows = []
    for p in entry["data"].get("practitioners") or []:
        name = (p.get("name") or "").strip()
        if not name:
            continue
        rows.append({
            "clinic_id": entry["id"],
            "name": name,
            "photo_url": p.get("photo_url") or None,
            "experience": p.get("experience") or None,
            "specialties": p.get("specialties") or None,
            "bio": p.get("bio") or None,
            "languages": p.get("languages") or None,
            "source_url": entry["url"],
            "scraped_at": TODAY,
        })
    return rows


def delete_existing(clinic_id: int):
    for table in ("clinic_amenities", "clinic_practitioners"):
        resp = requests.delete(
            f"{SUPABASE_URL}/rest/v1/{table}?clinic_id=eq.{clinic_id}",
            headers=HEADERS, timeout=15,
        )
        resp.raise_for_status()


def insert_rows(table: str, rows: list[dict]):
    if not rows:
        return
    resp = requests.post(
        f"{SUPABASE_URL}/rest/v1/{table}", headers=HEADERS, json=rows, timeout=15,
    )
    resp.raise_for_status()


def main():
    apply = "--apply" in sys.argv[1:]

    clinics = load_all_clinics()
    print(f"Loaded {len(clinics)} successfully-scraped clinics across {len(AMENITIES_FILES)} files")

    if not apply:
        clinics = clinics[:5]
        print("Preview mode: showing first 5 clinics. Use --apply to import everything.\n")

    total_practitioners = 0
    errors = 0

    for i, entry in enumerate(clinics, 1):
        amenity_row = build_amenity_row(entry)
        practitioner_rows = build_practitioner_rows(entry)
        filled = sum(1 for c in AMENITY_COLS if amenity_row.get(c) is not None)

        print(f"  [{i:4d}/{len(clinics)}] {entry['name'][:50]:50s} "
              f"{filled}/{len(AMENITY_COLS)} fields, {len(practitioner_rows)} practitioners")

        if apply:
            try:
                delete_existing(entry["id"])
                insert_rows("clinic_amenities", [amenity_row])
                insert_rows("clinic_practitioners", practitioner_rows)
                total_practitioners += len(practitioner_rows)
            except Exception as e:
                print(f"    DB error: {e}")
                errors += 1

    print(f"\n{'='*60}")
    print(f"Clinics processed: {len(clinics)}, practitioners inserted: {total_practitioners}, errors: {errors}")
    if not apply:
        print("Run with --apply to write to Supabase.")


if __name__ == "__main__":
    main()
