import requests, os, re
from dotenv import load_dotenv
load_dotenv(r"c:\Users\Ciaran\Desktop\Dental_Directory\.env")
MGMT_KEY = os.environ["SUPABASE_MANAGEMENT_KEY"]

def q(sql):
    r = requests.post("https://api.supabase.com/v1/projects/ankyjpgcocsvvtyyymys/database/query",
        headers={"Authorization": f"Bearer {MGMT_KEY}", "Content-Type": "application/json"},
        json={"query": sql}, timeout=60, verify=False)
    return r.json()

def extract_price(label):
    # Remove thousand-separating commas before parsing
    clean = re.sub(r'(\d),(\d{3})', r'\1\2', label)
    m = re.search(r'\$([0-9]+(?:\.[0-9]+)?)', clean)
    if not m:
        return None
    val = float(m.group(1))
    if val < 5 or val > 80000:   # skip per-unit cosmetic prices and outliers
        return None
    return int(val) if val == int(val) else round(val, 2)

# Treatments to skip — payment methods, fees, and non-price rows
SKIP_TREATMENTS = [
    'afterpay','winz','acc','q card','credit','eftpos','cash','southern cross',
    'payment','laybuy','humm','gem','visa','mastercard','insurance','gold card',
    'supergold','nib','cancellation','corporate','referral','scrape error',
    'other','dysport','botox','xeomin','lip filler',
]

def should_skip(treatment):
    t = treatment.lower()
    return any(s in t for s in SKIP_TREATMENTS)

def should_skip_label(label):
    l = label.lower()
    # Skip installment/per-unit pricing
    return any(s in l for s in ['per unit', 'per week', 'a week', '/week', 'pw', 'per month'])

# Fetch all candidates (no row limit)
print("Fetching rows...")
rows = q("""
    SELECT sp.id, sp.treatment, sp.price_label
    FROM scraped_prices sp
    WHERE sp.price_nzd IS NULL
      AND sp.price_label ~ '\\$[0-9]'
    ORDER BY sp.id
""")
print(f"  {len(rows)} candidate rows")

# Parse prices
updates = {}
skipped_treatment = 0
skipped_label = 0
skipped_no_price = 0

for r in rows:
    if should_skip(r['treatment']):
        skipped_treatment += 1
        continue
    if should_skip_label(r['price_label']):
        skipped_label += 1
        continue
    price = extract_price(r['price_label'])
    if price is None:
        skipped_no_price += 1
        continue
    updates[r['id']] = price

print(f"  Skipped (payment method): {skipped_treatment}")
print(f"  Skipped (installment pricing): {skipped_label}")
print(f"  Skipped (no extractable price): {skipped_no_price}")
print(f"  To update: {len(updates)}")

# Sample check
print("\nSample of updates (first 20):")
for id_, price in list(updates.items())[:20]:
    row = next(r for r in rows if r['id'] == id_)
    print(f"  [{id_}] {row['treatment'][:40]:40s} | {row['price_label'][:50]:50s} → ${price}")

# Batch update in chunks of 500
ids = list(updates.keys())
chunk_size = 500
total_updated = 0

for i in range(0, len(ids), chunk_size):
    chunk = ids[i:i+chunk_size]
    sql = "UPDATE scraped_prices SET price_nzd = CASE id\n"
    for id_ in chunk:
        sql += f"  WHEN {id_} THEN {updates[id_]}\n"
    sql += f"END WHERE id IN ({','.join(str(i) for i in chunk)});"
    result = q(sql)
    total_updated += len(chunk)
    print(f"  Batch {i//chunk_size + 1}: updated {len(chunk)} rows")

print(f"\nDone. Total rows updated: {total_updated}")
