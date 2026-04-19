"""
Upload scraper CSV results to Supabase scraped_prices table.

Reads all_regions_pricing.csv (and auckland_bay_of_plenty_pricing.csv),
inserts rows for clinics with has_pricing=True, and sets prices_last_updated.
Skips clinics that already have manual:* entries (already verified).
"""

import csv
import os
import re
import requests
from pathlib import Path
from urllib.parse import urlparse
from datetime import date
from dotenv import load_dotenv

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

SCRAPER_CSVS = ["all_regions_pricing.csv", "auckland_bay_of_plenty_pricing.csv"]

# Map CSV column → treatment label
COLUMN_TREATMENTS = {
    "checkup":        "Checkup / exam",
    "scale_and_polish": "Scale and polish",
    "filling":        "Filling",
    "extraction":     "Extraction",
    "whitening":      "Whitening",
    "new_patient":    "New patient offer",
}


def domain(url: str) -> str:
    try:
        return urlparse(url).netloc.lstrip("www.") or url
    except Exception:
        return url


def fetch_manual_clinic_ids() -> set:
    """Return clinic_ids that already have manual:* entries."""
    resp = requests.get(
        f"{SUPABASE_URL}/rest/v1/scraped_prices?select=clinic_id&source=like.manual:*&limit=10000",
        headers=HEADERS, timeout=15,
    )
    resp.raise_for_status()
    return {r["clinic_id"] for r in resp.json()}


def delete_existing_scraper_rows(clinic_id: int):
    """Remove old scraper:* rows for this clinic before re-inserting."""
    resp = requests.delete(
        f"{SUPABASE_URL}/rest/v1/scraped_prices?clinic_id=eq.{clinic_id}&source=like.scraper:*",
        headers=HEADERS, timeout=15,
    )
    resp.raise_for_status()


def insert_rows(rows: list[dict]):
    resp = requests.post(
        f"{SUPABASE_URL}/rest/v1/scraped_prices",
        headers=HEADERS, json=rows, timeout=15,
    )
    resp.raise_for_status()


def update_clinic(clinic_id: int, open_to_new_patients):
    payload = {"prices_last_updated": TODAY}
    if open_to_new_patients is not None:
        payload["open_to_new_patients"] = open_to_new_patients
    resp = requests.patch(
        f"{SUPABASE_URL}/rest/v1/dental_clinics?id=eq.{clinic_id}",
        headers=HEADERS, json=payload, timeout=15,
    )
    resp.raise_for_status()


def build_rows(clinic_id: int, row: dict) -> list[dict]:
    """Convert a CSV row into scraped_prices insert dicts."""
    src = f"scraper:{domain(row.get('website', ''))}"
    source_url = (row.get("pages_crawled") or "").split(",")[0].strip() or row.get("website", "")
    price_rows = []

    # Structured columns
    for col, treatment in COLUMN_TREATMENTS.items():
        val = (row.get(col) or "").strip()
        if not val:
            continue
        price_rows.append({
            "clinic_id":   clinic_id,
            "source":      src,
            "treatment":   treatment,
            "price_nzd":   None,
            "price_label": val,
            "source_url":  source_url,
            "notes":       None,
        })

    # Other field — pipe-separated, each entry may be "Treatment: price" or just info
    other = (row.get("other") or "").strip()
    if other:
        for entry in other.split(" | "):
            entry = entry.strip()
            if not entry:
                continue
            if ": " in entry:
                treatment, price_label = entry.split(": ", 1)
            else:
                treatment, price_label = "Other", entry
            price_rows.append({
                "clinic_id":   clinic_id,
                "source":      src,
                "treatment":   treatment.strip(),
                "price_nzd":   None,
                "price_label": price_label.strip(),
                "source_url":  source_url,
                "notes":       None,
            })

    return price_rows


def load_csvs() -> list[dict]:
    seen_ids = set()
    all_rows = []
    for path in SCRAPER_CSVS:
        if not Path(path).exists():
            print(f"  Skipping {path} (not found)")
            continue
        with open(path, newline="", encoding="utf-8") as f:
            for row in csv.DictReader(f):
                pid = row.get("place_id", "")
                if pid in seen_ids:
                    continue
                seen_ids.add(pid)
                all_rows.append(row)
        print(f"  Loaded {path}")
    return all_rows


def main():
    print("Loading CSVs...")
    all_rows = load_csvs()
    has_pricing = [r for r in all_rows if r.get("has_pricing") == "True"]
    print(f"  {len(all_rows)} total clinics, {len(has_pricing)} with pricing")

    print("Fetching manually verified clinic IDs...")
    manual_ids = fetch_manual_clinic_ids()
    print(f"  {len(manual_ids)} clinics already manually verified (will skip)")

    to_upload = [r for r in has_pricing if int(r["place_id"]) not in manual_ids]
    print(f"  {len(to_upload)} clinics to upload")

    inserted = 0
    skipped = 0
    for row in to_upload:
        clinic_id = int(row["place_id"])
        price_rows = build_rows(clinic_id, row)
        if not price_rows:
            skipped += 1
            continue

        try:
            otnp_raw = row.get("open_to_new_patients", "")
            open_to_new_patients = True if otnp_raw == "True" else (False if otnp_raw == "False" else None)
            delete_existing_scraper_rows(clinic_id)
            insert_rows(price_rows)
            update_clinic(clinic_id, open_to_new_patients)
            inserted += 1
            name = row['name'].encode('ascii', 'replace').decode()
            print(f"  + {name} ({len(price_rows)} rows)")
        except Exception as e:
            name = row['name'].encode('ascii', 'replace').decode()
            print(f"  ERR {name}: {e}")

    print(f"\nDone. Uploaded: {inserted}, Skipped (no rows): {skipped}")


if __name__ == "__main__":
    main()
