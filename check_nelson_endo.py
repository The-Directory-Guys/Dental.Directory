import requests, sys, io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
from dotenv import load_dotenv
import os
load_dotenv(r'c:\Users\Ciaran\Desktop\Dental_Directory\.env')
MGMT_KEY = os.environ['SUPABASE_MANAGEMENT_KEY']

def q(sql):
    r = requests.post('https://api.supabase.com/v1/projects/ankyjpgcocsvvtyyymys/database/query',
        headers={'Authorization': f'Bearer {MGMT_KEY}', 'Content-Type': 'application/json'},
        json={'query': sql}, verify=False)
    return r.json()

rows = q("SELECT id, name, address, website, phone_national, region FROM dental_clinics WHERE name ILIKE '%nelson endodontic%' OR name ILIKE '%waimea dental%'")
for r in rows: print(r)

print()
# Check practitioners for Nelson Endodontic Centre
for row in rows:
    print(f"\n=== Practitioners for {row['name']} (id {row['id']}) ===")
    for p in q(f"SELECT id, name, experience FROM clinic_practitioners WHERE clinic_id = {row['id']}"): print(p)
