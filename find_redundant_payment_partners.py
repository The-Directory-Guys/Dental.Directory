import requests
import re
import os
from dotenv import load_dotenv

load_dotenv(r"c:\Users\Ciaran\Desktop\Dental_Directory\.env")
MGMT_KEY = os.environ["SUPABASE_MANAGEMENT_KEY"]

def query(sql):
    r = requests.post(
        "https://api.supabase.com/v1/projects/ankyjpgcocsvvtyyymys/database/query",
        headers={"Authorization": f"Bearer {MGMT_KEY}", "Content-Type": "application/json"},
        json={"query": sql}, timeout=30, verify=False,
    )
    return r.json()

# Fetch all amenities with payment_partners
amenities = query("""
    SELECT ca.clinic_id, dc.name, ca.payment_partners
    FROM clinic_amenities ca
    JOIN dental_clinics dc ON dc.id = ca.clinic_id
    WHERE ca.payment_partners IS NOT NULL AND ca.payment_partners != ''
    ORDER BY dc.name
""")

# Fetch all payment-type rows from scraped_prices
PAYMENT_KEYWORDS = [
    'acc','winz','q card','afterpay','zip','laybuy','gem visa','gem finance',
    'southern cross','credit card','visa','mastercard','eftpos','cash',
    'payment plan','supergold','gold card','humm','genoapay','partpay',
    'flexicare','work and income','q mastercard',
]
scraped = query("""
    SELECT clinic_id, LOWER(treatment) AS treatment
    FROM scraped_prices
    WHERE treatment IS NOT NULL
""")

# Build map: clinic_id -> set of scraped payment labels
scraped_map = {}
for row in scraped:
    t = row['treatment']
    if any(kw in t for kw in PAYMENT_KEYWORDS):
        scraped_map.setdefault(row['clinic_id'], set()).add(t)

def is_covered(chip, scraped_labels):
    c = chip.lower().strip()
    return any(c == s or c in s or s in c for s in scraped_labels)

redundant_ids = []
partial_ids = []

for row in amenities:
    cid = row['clinic_id']
    raw = row['payment_partners']
    # Parse chips (same logic as frontend)
    try:
        import json
        chips = [s.strip() for s in json.loads(raw) if s.strip()]
    except Exception:
        chips = [s.strip() for s in re.split(r',(?![^(]*\))', raw) if s.strip()]

    scraped_labels = scraped_map.get(cid, set())
    if not scraped_labels:
        continue  # nothing scraped to compare against

    covered = [is_covered(c, scraped_labels) for c in chips]
    if all(covered):
        redundant_ids.append(cid)
    elif any(covered):
        partial_ids.append((cid, row['name'], raw, chips, scraped_labels))

print(f"Fully redundant payment_partners (safe to clear): {len(redundant_ids)}")
print(f"Partially redundant (keep, frontend handles): {len(partial_ids)}")

if redundant_ids:
    ids = ', '.join(str(i) for i in redundant_ids)
    confirm = input(f"\nClear payment_partners for all {len(redundant_ids)} redundant clinics? (y/n): ")
    if confirm.strip().lower() == 'y':
        result = query(f"UPDATE clinic_amenities SET payment_partners = NULL WHERE clinic_id IN ({ids});")
        print(f"Cleared {len(redundant_ids)} records.")
    else:
        print("Skipped.")
