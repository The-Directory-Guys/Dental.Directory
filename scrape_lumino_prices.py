#!/usr/bin/env python3
"""
Lumino scraped-prices helper (CSV count + optional Supabase push).

National Lumino promos (Q Card, $99 new patient, etc.) are not stored in
scraped_prices — users should check lumino.co.nz for current offers. This
script returns an empty scrape list so --push-supabase does not re-insert them.

Usage:
  python scrape_lumino_prices.py --count-lumino-csv
  python scrape_lumino_prices.py              # prints []
  python scrape_lumino_prices.py --push-supabase   # no-op insert (0 rows)

Optional: SUPABASE_URL and SUPABASE_SERVICE_KEY in .env for --push-supabase.
"""
from __future__ import annotations

import argparse
import csv
import json
import os
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import requests


def load_env_from_dotenv() -> None:
    """Load KEY=value pairs from .env or .env.txt in the project root (same idea as supabase/import.ts)."""
    root = Path(__file__).resolve().parent
    for name in (".env", ".env.txt"):
        path = root / name
        if not path.is_file():
            continue
        for line in path.read_text(encoding="utf-8").splitlines():
            t = line.strip()
            if not t or t.startswith("#"):
                continue
            if "=" not in t:
                continue
            key, _, val = t.partition("=")
            key = key.strip()
            val = val.strip().strip('"').strip("'")
            if key and key not in os.environ:
                os.environ[key] = val
        break


def scrape_lumino() -> list[dict[str, Any]]:
    """No national Lumino promo rows in the directory (see module docstring)."""
    return []


def count_lumino_clinics_csv(csv_path: Path) -> int:
    with csv_path.open(newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        n = 0
        for row in reader:
            name = (row.get("name") or "").lower()
            web = (row.get("website") or "").lower()
            if "lumino" in name or "lumino.co.nz" in web:
                n += 1
    return n


def push_supabase(rows: list[dict[str, Any]]) -> None:
    base = (os.environ.get("SUPABASE_URL") or "").rstrip("/")
    key = os.environ.get("SUPABASE_SERVICE_KEY") or ""
    if not base or not key:
        print("Missing SUPABASE_URL or SUPABASE_SERVICE_KEY", file=sys.stderr)
        sys.exit(1)
    if not rows:
        print("Nothing to insert (0 rows).", file=sys.stderr)
        return
    endpoint = f"{base}/rest/v1/scraped_prices"
    headers = {
        "apikey": key,
        "Authorization": f"Bearer {key}",
        "Content-Type": "application/json",
        "Prefer": "return=minimal",
    }
    now = datetime.now(timezone.utc).isoformat()
    payload = [
        {
            "clinic_id": r["clinic_id"],
            "source": r["source"],
            "treatment": r["treatment"],
            "price_nzd": r["price_nzd"],
            "price_label": r["price_label"],
            "source_url": r["source_url"],
            "notes": r.get("notes"),
            "scraped_at": now,
        }
        for r in rows
    ]
    r = requests.post(endpoint, headers=headers, json=payload, timeout=60)
    if not r.ok:
        print(r.text[:2000], file=sys.stderr)
        r.raise_for_status()
    print(f"Inserted {len(payload)} row(s) into scraped_prices.", file=sys.stderr)


def main() -> None:
    ap = argparse.ArgumentParser(description="Lumino CSV count / empty scraped_prices push")
    ap.add_argument("--json-out", type=Path, help="Write JSON array to this file")
    ap.add_argument(
        "--push-supabase",
        action="store_true",
        help="POST rows to Supabase scraped_prices (service role)",
    )
    ap.add_argument(
        "--count-lumino-csv",
        action="store_true",
        help="Print count of Lumino-related rows in dental_clinics_all.csv and exit",
    )
    args = ap.parse_args()
    load_env_from_dotenv()

    root = Path(__file__).resolve().parent
    csv_path = root / "dental_clinics_all.csv"

    if args.count_lumino_csv:
        if not csv_path.is_file():
            print("CSV not found:", csv_path, file=sys.stderr)
            sys.exit(1)
        print(count_lumino_clinics_csv(csv_path))
        return

    rows = scrape_lumino()
    text = json.dumps(rows, indent=2, ensure_ascii=False)
    print(text)
    if args.json_out:
        args.json_out.write_text(text, encoding="utf-8")
    if args.push_supabase:
        push_supabase(rows)


if __name__ == "__main__":
    main()
