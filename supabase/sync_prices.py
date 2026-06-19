"""
Sync verified checkup/hygienist prices from christchurch_prices.txt and
wellington_prices.txt into the Supabase dental_clinics table.

Only clinic blocks with a "[Checked: Accurate]" or "[Checked: Phone verified ...]"
status are synced. Pulls "Exam / checkup", "Hygienist" and (when there's no
checkup line) "New patient offer" bullets, strips the verification tag, and
writes a normalized price string plus prices_last_updated (from the bullet's
verification date, or today if none is present).

Usage:
  python supabase/sync_prices.py --dry-run     # preview changes only
  python supabase/sync_prices.py               # apply changes
"""

import os
import re
import sys
import json
import urllib.request
import urllib.parse
import argparse
from datetime import date

sys.stdout.reconfigure(encoding="utf-8")


def load_env():
    env_path = os.path.join(os.getcwd(), ".env")
    if not os.path.exists(env_path):
        return
    for line in open(env_path, encoding="utf-8"):
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        k, v = line.split("=", 1)
        os.environ.setdefault(k.strip(), v.strip().strip('"').strip("'"))


load_env()
SUPABASE_URL = os.environ["SUPABASE_URL"]
SERVICE_KEY = os.environ["SUPABASE_SERVICE_KEY"]
HEADERS = {"apikey": SERVICE_KEY, "Authorization": f"Bearer {SERVICE_KEY}"}

DATE_TAG_RE = re.compile(r"\[(?:[^\[\]]*?)(\d{1,2})/(\d{1,2})/(\d{2,4})[^\[\]]*\]")
BRACKET_RE = re.compile(r"\s*\[[^\[\]]*\]")
ENTRY_HEADER_RE = re.compile(r"^\d+\.\s+(.+?)\s*\[[^\]]*\]\s*$")


def parse_date_tag(text):
    m = DATE_TAG_RE.search(text)
    if not m:
        return None
    d, mo, y = m.groups()
    y = int(y)
    if y < 100:
        y += 2000
    return date(y, int(mo), int(d)).isoformat()


def clean_value(text):
    return BRACKET_RE.sub("", text).strip().rstrip(";").strip()


def parse_file(path):
    blocks = []
    current = None
    for raw in open(path, encoding="utf-8"):
        line = raw.rstrip("\n")
        header = ENTRY_HEADER_RE.match(line)
        if header:
            if current:
                blocks.append(current)
            current = {"name": header.group(1).strip(), "status": "", "bullets": []}
            continue
        if current is None:
            continue
        stripped = line.strip()
        if stripped.startswith("Status:"):
            current["status"] = stripped[len("Status:"):].strip()
        elif stripped.startswith("- "):
            current["bullets"].append(stripped[2:].strip())
    if current:
        blocks.append(current)
    return blocks


def is_checked(status):
    return status.startswith("[Checked: Accurate") or status.startswith("[Checked: Phone verified")


def build_price(block):
    checkup_parts, hygienist_parts, offer_parts = [], [], []
    dates = []

    for bullet in block["bullets"]:
        if ":" not in bullet:
            continue
        label, value = bullet.split(":", 1)
        label = label.strip().lower()
        value = value.strip()

        d = parse_date_tag(value)
        if d:
            dates.append(d)
        value_clean = clean_value(value)
        if not value_clean:
            continue

        if label in ("exam / checkup", "exam/checkup", "checkup"):
            checkup_parts.append(f"checkup {value_clean}")
        elif label == "hygienist":
            hygienist_parts.append(f"hygienist {value_clean}")
        elif label == "new patient offer":
            offer_parts.append(f"new patient offer {value_clean}")

    status_date = parse_date_tag(block["status"])
    if status_date:
        dates.append(status_date)

    parts = checkup_parts + hygienist_parts
    if not parts:
        parts = offer_parts

    if not parts:
        return None, None

    price = "; ".join(parts)
    last_updated = max(dates) if dates else date.today().isoformat()
    return price, last_updated


def supabase_get(path):
    req = urllib.request.Request(f"{SUPABASE_URL}{path}", headers=HEADERS)
    with urllib.request.urlopen(req) as r:
        return json.loads(r.read())


def supabase_patch(clinic_id, body):
    data = json.dumps(body).encode()
    req = urllib.request.Request(
        f"{SUPABASE_URL}/rest/v1/dental_clinics?id=eq.{clinic_id}",
        data=data,
        headers={**HEADERS, "Content-Type": "application/json"},
        method="PATCH",
    )
    with urllib.request.urlopen(req) as r:
        return r.status


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()

    files = ["christchurch_prices.txt", "wellington_prices.txt"]
    updates = []
    not_found = []
    unchanged = 0
    skipped_no_price = 0

    for path in files:
        for block in parse_file(path):
            if not is_checked(block["status"]):
                continue
            price, last_updated = build_price(block)
            if not price:
                skipped_no_price += 1
                continue

            enc = urllib.parse.quote(block["name"])
            rows = supabase_get(f"/rest/v1/dental_clinics?select=id,name,price,prices_last_updated&name=eq.{enc}")
            if not rows:
                not_found.append(block["name"])
                continue

            row = rows[0]
            if row["price"] == price and row["prices_last_updated"] == last_updated:
                unchanged += 1
                continue

            updates.append({
                "id": row["id"],
                "name": block["name"],
                "old_price": row["price"],
                "new_price": price,
                "old_date": row["prices_last_updated"],
                "new_date": last_updated,
            })

    print(f"{len(updates)} clinic(s) to update, {unchanged} already up to date, "
          f"{skipped_no_price} checked entries with no parseable checkup/hygienist price, "
          f"{len(not_found)} not found in DB by name.\n")

    for u in updates:
        print(f"- {u['name']} (id {u['id']})")
        print(f"    price: {u['old_price']!r} -> {u['new_price']!r}")
        print(f"    prices_last_updated: {u['old_date']!r} -> {u['new_date']!r}")

    if not_found:
        print("\nNot found in DB (name mismatch?):")
        for n in not_found:
            print(f"  - {n}")

    if args.dry_run:
        print("\nDry run — no changes written.")
        return

    for u in updates:
        supabase_patch(u["id"], {"price": u["new_price"], "prices_last_updated": u["new_date"]})
        print(f"Updated {u['name']}")

    print(f"\nDone. {len(updates)} clinic(s) updated.")


if __name__ == "__main__":
    main()
