#!/usr/bin/env python3
"""
Collapse duplicate Google Business listings that share the same street address and phone
(e.g. practitioner profile vs practice profile). Keeps one row per (address, phone) using
heuristics: prefer Lumino/practice websites, non-'Dr …' names, ratings, etc.

Run: python dedupe_same_address_phone.py
"""
import csv
import re
import shutil
from pathlib import Path

ROOT = Path(__file__).resolve().parent
CSV_PATH = ROOT / "dental_clinics_all.csv"


def norm_addr(a: str) -> str:
    if not a:
        return ""
    a = a.lower().replace(",", " ")
    a = a.split("new zealand")[0].strip()
    a = re.sub(r"\s+", " ", a)
    return a


def norm_phone(ph: str) -> str:
    if not ph:
        return ""
    d = re.sub(r"[^\d]", "", ph)
    if d.startswith("64"):
        d = d[2:]
    if d.startswith("0"):
        d = d[1:]
    return d[-9:] if len(d) >= 9 else d


def total_ratings_val(r: dict) -> int:
    t = r.get("total_ratings") or ""
    try:
        return int(float(str(t).strip()))
    except (ValueError, TypeError):
        return 0


def score_row(r: dict) -> float:
    """Higher = better candidate to keep as the canonical practice row."""
    name = (r.get("name") or "").strip()
    website = (r.get("website") or "").lower()

    s = 0.0
    s += total_ratings_val(r) * 3
    s += min(len(website), 200) * 0.5

    if "lumino.co.nz" in website:
        s += 400
    elif website:
        s += 120

    if "|" in name:
        s += 80
    if "lumino" in name.lower():
        s += 60

    # Deprioritise lone practitioner listings
    if re.match(r"^Dr\.?\s", name, re.I):
        s -= 150
    if re.search(r"\bDentist\s*$", name) and len(name) < 45:
        s -= 90
    if name.count(" ") <= 2 and re.search(r"Dentist", name, re.I):
        s -= 50

    return s


def pick_kept_row(group):
    return max(group, key=lambda r: (score_row(r), len(r.get("name") or "")))


def main() -> None:
    backup = CSV_PATH.with_suffix(CSV_PATH.suffix + ".bak")
    shutil.copy2(CSV_PATH, backup)
    print(f"Backup: {backup}")

    with CSV_PATH.open(newline="", encoding="utf-8") as f:
        rows = list(csv.DictReader(f))
    fieldnames = list(rows[0].keys()) if rows else []

    # Group by (address, phone); skip groups with empty phone (cannot dedupe safely)
    groups = {}
    no_phone: list[dict] = []
    for r in rows:
        addr = norm_addr(r.get("address", ""))
        ph = norm_phone(r.get("phone_national", "") or "")
        if not addr or not ph:
            no_phone.append(r)
            continue
        key = (addr, ph)
        groups.setdefault(key, []).append(r)

    kept: list[dict] = []
    removed: list[tuple[str, str]] = []

    for key, grp in groups.items():
        if len(grp) == 1:
            kept.extend(grp)
            continue
        winner = pick_kept_row(grp)
        kept.append(winner)
        for r in grp:
            if r is not winner:
                removed.append((r.get("name", ""), winner.get("name", "")))

    kept.extend(no_phone)

    # Original order is lost; sort by region then name for stable CSV
    kept.sort(key=lambda r: ((r.get("region") or ""), (r.get("name") or "").lower()))

    with CSV_PATH.open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=fieldnames)
        w.writeheader()
        w.writerows(kept)

    print(f"Rows before: {len(rows)}")
    print(f"Removed (duplicate address+phone): {len(removed)}")
    print(f"Rows after:  {len(kept)}")
    print()
    print("Sample merges (removed -> kept):")
    for a, b in removed[:25]:
        print(f"  − {a[:65]}")
        print(f"    + kept: {b[:65]}")
    if len(removed) > 25:
        print(f"  ... and {len(removed) - 25} more")


if __name__ == "__main__":
    main()
