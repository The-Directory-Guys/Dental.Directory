"""
Merge manually verified Supabase prices with the scraper CSV.

Fetches all manual:* rows from scraped_prices, pivots them into the same
per-clinic column format as auckland_bay_of_plenty_pricing.csv, then
concatenates both sources into merged_pricing.csv.
"""

import csv
import json
import os
import re
import requests
from pathlib import Path
from collections import defaultdict
from dotenv import load_dotenv

load_dotenv()

SUPABASE_URL = os.environ["SUPABASE_URL"]
SUPABASE_KEY = os.environ["SUPABASE_SERVICE_KEY"]

# All scraper CSVs to merge (add new ones here, or they're auto-detected below)
SCRAPER_CSVS  = None   # None = auto-detect all *_pricing.csv files except merged
OUTPUT_CSV    = "merged_pricing.csv"

HEADERS = {
    "apikey": SUPABASE_KEY,
    "Authorization": f"Bearer {SUPABASE_KEY}",
}

# ---------------------------------------------------------------------------
# Treatment → column mapping
# ---------------------------------------------------------------------------
# Each pattern is checked (case-insensitive) against the treatment name.
# First match wins. Unmatched treatments go into "other".

COLUMN_PATTERNS = [
    # new_patient — must come before checkup to avoid "new patient exam" going to checkup
    ("new_patient",     r"new.patient"),

    # checkup
    ("checkup",         r"\b(exam|examination|check.?up|check.?in|consultation|full.mouth.exam|recall|full.dental.check)\b"),

    # scale_and_polish
    ("scale_and_polish", r"\b(scale.and.polish|scale.&.polish|scale.and.clean|clean.and.polish|hygien|clean(?!ing kit)|routine.clean|dental.clean|teeth.clean)\b"),

    # filling
    ("filling",         r"\bfilling\b"),

    # extraction
    ("extraction",      r"\b(extract|tooth.remov|wisdom)\b"),

    # whitening
    ("whitening",       r"\b(whiten|bleach|zoom)\b"),
]

SKIP_TREATMENTS = re.compile(
    r"\b(payment|q card|q mastercard|afterpay|genoapay|laybuy|zip|oxipay|"
    r"southern cross|nib|winz|acc\b|studylink|farmers|gem visa|finance|"
    r"interest.free|discount|supergold|grey power|healthnow|loan haus|"
    r"mtf finance|alipay|wechat|refer.reward|gift.voucher|credit.card|"
    r"community.services|capital.coast|university|ara |otago|institute|"
    r"student free|free.teen|free.adolescent|free.dental.care|ministry.funded|"
    r"under.18|adolescent.care|teen.basic)\b",
    re.IGNORECASE,
)


def classify_treatment(treatment: str) -> str:
    if SKIP_TREATMENTS.search(treatment):
        return "skip"
    t = treatment.lower()
    for col, pattern in COLUMN_PATTERNS:
        if re.search(pattern, t, re.IGNORECASE):
            return col
    return "other"


def label(price_nzd, price_label):
    """Return the best human-readable price string."""
    if price_label and str(price_label).strip():
        return str(price_label).strip()
    if price_nzd is not None:
        return f"${price_nzd}"
    return ""


# ---------------------------------------------------------------------------
# Fetch from Supabase
# ---------------------------------------------------------------------------

def fetch_all_manual_prices():
    """Fetch all manual:* scraped_prices rows with clinic info, paged."""
    all_rows = []
    page_size = 1000
    offset = 0
    while True:
        url = (
            f"{SUPABASE_URL}/rest/v1/scraped_prices"
            f"?select=clinic_id,treatment,price_nzd,price_label,source_url,notes,source,"
            f"dental_clinics(id,name,website,region,suburb_town,prices_last_updated)"
            f"&source=like.manual:*"
            f"&order=clinic_id.asc"
            f"&limit={page_size}&offset={offset}"
        )
        resp = requests.get(url, headers=HEADERS, timeout=20)
        resp.raise_for_status()
        rows = resp.json()
        all_rows.extend(rows)
        if len(rows) < page_size:
            break
        offset += page_size
    print(f"Fetched {len(all_rows)} manual scraped_price rows")
    return all_rows


def pivot_to_clinics(rows):
    """
    Group rows by clinic_id, classify treatments, and build per-clinic dicts
    in the same format as the scraper CSV.
    """
    by_clinic = defaultdict(list)
    clinic_meta = {}

    for row in rows:
        cid = row["clinic_id"]
        by_clinic[cid].append(row)
        if cid not in clinic_meta:
            dc = row.get("dental_clinics") or {}
            clinic_meta[cid] = {
                "place_id":    str(cid),
                "name":        dc.get("name", ""),
                "website":     dc.get("website", ""),
                "region":      dc.get("region", ""),
                "suburb_town": dc.get("suburb_town", ""),
            }

    clinics = []
    for cid, price_rows in by_clinic.items():
        meta = clinic_meta[cid]

        buckets = defaultdict(list)
        for r in price_rows:
            col = classify_treatment(r["treatment"])
            if col == "skip":
                continue
            val = label(r.get("price_nzd"), r.get("price_label"))
            if val:
                entry = f"{r['treatment']}: {val}"
            else:
                entry = r["treatment"]
            buckets[col].append(entry)

        def join(col):
            return " | ".join(buckets[col]) if buckets[col] else ""

        has_pricing = any(
            buckets[c] for c in ("checkup", "scale_and_polish", "filling", "extraction", "whitening", "new_patient", "other")
        )

        clinics.append({
            **meta,
            "scrape_status": "manual",
            "fetch_method":  "manual",
            "checkup":        join("checkup"),
            "scale_and_polish": join("scale_and_polish"),
            "filling":        join("filling"),
            "extraction":     join("extraction"),
            "whitening":      join("whitening"),
            "new_patient":    join("new_patient"),
            "other":          join("other"),
            "has_pricing":    str(has_pricing),
            "pages_crawled":  "",
        })

    return clinics


# ---------------------------------------------------------------------------
# Load scraper CSV
# ---------------------------------------------------------------------------

def find_scraper_csvs():
    """Auto-detect all *_pricing.csv files in the current directory, excluding the output."""
    return [
        p for p in Path(".").glob("*_pricing.csv")
        if p.name != OUTPUT_CSV
    ]


def load_scraper_csv(path):
    if not Path(path).exists():
        print(f"Warning: {path} not found, skipping")
        return []
    with open(path, newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

FIELDNAMES = [
    "place_id", "name", "website", "region", "suburb_town",
    "scrape_status", "fetch_method",
    "checkup", "scale_and_polish", "filling", "extraction",
    "whitening", "new_patient", "other",
    "has_pricing", "pages_crawled",
]

def main():
    # 1. Load all scraper CSVs
    csv_paths = SCRAPER_CSVS if SCRAPER_CSVS else find_scraper_csvs()
    scraper_normalised = []
    seen_ids = set()
    for path in csv_paths:
        rows = load_scraper_csv(path)
        for r in rows:
            pid = r.get("place_id", "")
            if pid in seen_ids:
                continue  # deduplicate if a clinic appears in multiple CSVs
            seen_ids.add(pid)
            scraper_normalised.append({k: r.get(k, "") for k in FIELDNAMES})
        print(f"  {path}: {len(rows)} rows")
    print(f"Scraper CSVs total: {len(scraper_normalised)} rows")

    # 2. Fetch and pivot manual Supabase rows
    raw = fetch_all_manual_prices()
    manual_rows = pivot_to_clinics(raw)
    print(f"Manual Supabase: {len(manual_rows)} clinics")

    # 3. Exclude manual rows whose clinic_id already appears in the scraper CSV
    #    (the scraper CSV already covers Auckland + BOP, and manual entries for
    #    those clinics would duplicate them)
    scraper_ids = {r["place_id"] for r in scraper_normalised}
    manual_new = [r for r in manual_rows if r["place_id"] not in scraper_ids]
    print(f"Manual rows not in scraper CSV: {len(manual_new)}")

    # 4. Write merged CSV
    all_rows = scraper_normalised + manual_new
    all_rows.sort(key=lambda r: (r.get("region", ""), r.get("name", "").lower()))

    with open(OUTPUT_CSV, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=FIELDNAMES, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(all_rows)

    print(f"\nWrote {len(all_rows)} rows to {OUTPUT_CSV}")

    # 5. Summary by region
    by_region = defaultdict(lambda: {"total": 0, "with_pricing": 0})
    for r in all_rows:
        reg = r.get("region") or "Unknown"
        by_region[reg]["total"] += 1
        if str(r.get("has_pricing")).lower() == "true":
            by_region[reg]["with_pricing"] += 1

    print("\nRegion summary:")
    for region in sorted(by_region):
        s = by_region[region]
        print(f"  {region.encode('ascii', 'replace').decode()}: {s['with_pricing']}/{s['total']} clinics with pricing")


if __name__ == "__main__":
    main()
