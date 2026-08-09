import sys, io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

import requests, os
from dotenv import load_dotenv
load_dotenv(r"c:\Users\Ciaran\Desktop\Dental_Directory\.env")
MGMT_KEY = os.environ["SUPABASE_MANAGEMENT_KEY"]
SUPABASE_URL = os.environ["SUPABASE_URL"]
BASE = f"{SUPABASE_URL}/storage/v1/object/public/practitioner-photos/practitioners"

def q(sql):
    r = requests.post("https://api.supabase.com/v1/projects/ankyjpgcocsvvtyyymys/database/query",
        headers={"Authorization": f"Bearer {MGMT_KEY}", "Content-Type": "application/json"},
        json={"query": sql}, timeout=30, verify=False)
    return r.json()

SOURCE = "https://www.dentiq.nz/meet-our-team/"

# 1. Delete the old bare "Aidan Khoo" — "Dr Aidan Khoo" (3741) is the better record
q("DELETE FROM clinic_practitioners WHERE id = 1359")
print("Deleted id 1359 (Aidan Khoo without Dr prefix)")

# 2. Update old staff records with photos + proper data
updates = [
    (1355, "Anu Sundar",        "F", "Executive Director",  "MPhil in Library and Information Science", f"{BASE}/anu-sundar-dentiq.jpg"),
    (1356, "Debra Nabney",      "F", "Oral Health Therapist","Bachelor of Oral Health (AUT, 2010)",       f"{BASE}/debra-nabney-dentiq.jpg"),
    (1357, "Harry Dissanayake", "M", "Practice Manager",    "BDS (Sri Lanka)",                           f"{BASE}/harry-dissanayake-dentiq.jpg"),
    (1358, "Rachel Roberts",    "F", "Dental Assistant",    None,                                        f"{BASE}/rachel-roberts-dentiq.jpg"),
]

for id_, name, gender, specialties, experience, photo_url in updates:
    exp_val = f"$${experience}$$" if experience else "NULL"
    sql = f"""
        UPDATE clinic_practitioners
        SET gender = '{gender}',
            specialties = $${specialties}$$,
            experience = {exp_val},
            photo_url = '{photo_url}',
            source_url = '{SOURCE}'
        WHERE id = {id_}
    """
    result = q(sql)
    print(f"Updated id {id_} ({name}): {result}")

# Verify final state
print()
rows = q("SELECT id, name, specialties, photo_url IS NOT NULL as has_photo FROM clinic_practitioners WHERE clinic_id = 1511 ORDER BY id")
for r in rows:
    print(r)
print(f"Total: {len(rows)}")
