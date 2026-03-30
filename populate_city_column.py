#!/usr/bin/env python3
"""One-off: add `city` to dental_clinics_all.csv (after suburb_town). Re-run if rules change."""

import csv

CSV_PATH = "dental_clinics_all.csv"


def infer_city(region: str, suburb_town: str, address: str) -> str:
    r = (region or "").strip()
    st = (suburb_town or "").lower()
    ad = (address or "").lower()
    blob = f"{st} {ad}"

    if r == "Auckland":
        return "Auckland"
    if r == "Wellington":
        return "Wellington"
    if r == "Canterbury":
        return "Christchurch" if "christchurch" in blob else "NA"
    if r == "Waikato":
        return "Hamilton" if "hamilton" in blob else "NA"
    if r == "Bay of Plenty":
        if "tauranga" in blob:
            return "Tauranga"
        if "rotorua" in blob:
            return "Rotorua"
        return "NA"
    if r == "Otago":
        if "dunedin" in blob:
            return "Dunedin"
        if "queenstown" in blob:
            return "Queenstown"
        return "NA"
    if r == "Southland":
        return "Invercargill" if "invercargill" in blob else "NA"
    if r == "Taranaki":
        return "New Plymouth" if "new plymouth" in blob or "newplymouth" in ad else "NA"
    if r in ("Manawatū-Whanganui", "Manawatu-Whanganui"):
        if "palmerston" in blob:
            return "Palmerston North"
        if "whanganui" in blob or "wanganui" in blob:
            return "Whanganui"
        return "NA"
    if r == "Hawke's Bay":
        if "napier" in blob:
            return "Napier"
        if "hastings" in blob:
            return "Hastings"
        return "NA"
    if r == "Northland":
        return "Whangārei" if "whangarei" in blob or "whangārei" in suburb_town else "NA"
    if r in ("Nelson", "Nelson/Tasman"):
        return "Nelson" if "nelson" in blob or "richmond" in blob or "motueka" in blob else "NA"
    if r == "Marlborough":
        return "Blenheim" if "blenheim" in blob else "NA"
    if r == "Gisborne":
        return "Gisborne" if "gisborne" in blob else "NA"
    if r == "West Coast":
        if "greymouth" in blob:
            return "Greymouth"
        if "westport" in blob:
            return "Westport"
        return "NA"

    return "NA"


def main():
    with open(CSV_PATH, encoding="utf-8", newline="") as f:
        reader = csv.DictReader(f)
        fieldnames = list(reader.fieldnames or [])
        rows = list(reader)

    if "city" in fieldnames:
        print("Column `city` already exists; re-populating values.")
    else:
        if "suburb_town" not in fieldnames:
            raise SystemExit("Expected column suburb_town in CSV")
        idx = fieldnames.index("suburb_town") + 1
        fieldnames = fieldnames[:idx] + ["city"] + fieldnames[idx:]

    for row in rows:
        row["city"] = infer_city(
            row.get("region", ""),
            row.get("suburb_town", ""),
            row.get("address", ""),
        )

    with open(CSV_PATH, "w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)

    print(f"Wrote {len(rows)} rows with city column.")


if __name__ == "__main__":
    main()
