import requests
import os
from dotenv import load_dotenv

load_dotenv(r"c:\Users\Ciaran\Desktop\Dental_Directory\.env")

SUPABASE_URL = os.environ["SUPABASE_URL"]
SUPABASE_JWT = os.environ['SUPABASE_JWT']
MGMT_KEY = os.environ["SUPABASE_MANAGEMENT_KEY"]
BUCKET = "practitioner-photos"
CLINIC_ID = 1507
SOURCE_URL = "https://www.davidmarriottdental.co.nz/about-us/our-people/"
BASE_URL = "https://www.davidmarriottdental.co.nz"

HEADERS_DL = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/120.0.0.0 Safari/537.36",
    "Referer": BASE_URL,
}

def db(sql):
    r = requests.post(
        "https://api.supabase.com/v1/projects/ankyjpgcocsvvtyyymys/database/query",
        headers={"Authorization": f"Bearer {MGMT_KEY}", "Content-Type": "application/json"},
        json={"query": sql}, timeout=30, verify=False,
    )
    if r.status_code not in (200, 201):
        print(f"    ERROR: {r.text[:300]}")
    return r.status_code, r.json()

practitioners = [
    {
        "filename": "david-marriott.jpg",
        "name": "David Marriott",
        "gender": "M",
        "specialties": "Principal Dentist, Restorative Dentistry",
        "experience": "BDS (Birmingham, 1984), LDSRCS (Edinburgh)",
        "bio": "Graduated from University of Birmingham Dental School in 1984. Practiced in the UK for three years before relocating to New Zealand in 1987. Established his Hastings practice in 1989. Known for his gentle approach to dental treatment with a special interest in restorative dentistry.",
        "photo_path": "/assets/Images/Team-Images/H4A1035.jpg",
    },
    {
        "filename": "aidan-khoo.jpg",
        "name": "Aidan Khoo",
        "gender": "M",
        "specialties": "Associate Dentist",
        "experience": "BDS (Otago), graduated with Distinction",
        "bio": "Graduated from the University of Otago Faculty of Dentistry with Distinction. Originally from Kuala Lumpur, Malaysia; joined the practice in June 2026. Known for his keen ear for patient concerns and empathetic approach to care, with a focus on transparency and clear communication.",
        "photo_path": "/assets/Images/Content-Blocks/Aidan-Khoo.jpeg",
    },
]

# Check existing practitioners to avoid duplicates
_, existing = db(f"SELECT name FROM clinic_practitioners WHERE clinic_id = {CLINIC_ID}")
existing_names = {row['name'].lower() for row in existing}
print(f"Existing practitioners: {existing_names or 'none'}")

for p in practitioners:
    print(f"\n--- {p['name']} ---")
    if p['name'].lower() in existing_names:
        print("  SKIP (already exists)")
        continue

    photo_url = BASE_URL + p["photo_path"]
    r = requests.get(photo_url, headers=HEADERS_DL, timeout=30, verify=False)
    print(f"  Download: {r.status_code}, {len(r.content)} bytes")
    if r.status_code != 200 or len(r.content) < 1000:
        print("  SKIP (bad download)")
        continue

    content_type = "image/jpeg"
    file_path = f"practitioners/{p['filename']}"
    up = requests.post(
        f"{SUPABASE_URL}/storage/v1/object/{BUCKET}/{file_path}",
        headers={"Authorization": f"Bearer {SUPABASE_JWT}", "Content-Type": content_type, "x-upsert": "true"},
        data=r.content, timeout=30, verify=False,
    )
    print(f"  Upload: {up.status_code}")

    public_url = f"{SUPABASE_URL}/storage/v1/object/public/{BUCKET}/{file_path}"

    sql = f"""
        INSERT INTO clinic_practitioners (clinic_id, name, gender, specialties, experience, bio, photo_url, source_url)
        VALUES (
            {CLINIC_ID},
            $${p['name']}$$,
            '{p['gender']}',
            $${p['specialties']}$$,
            $${p['experience']}$$,
            $${p['bio']}$$,
            '{public_url}',
            '{SOURCE_URL}'
        );
    """
    status, resp = db(sql)
    print(f"  DB: {status}")

# Update services to add Cosmetic and Dentures
print("\n--- Updating services ---")
status, resp = db("SELECT services FROM dental_clinics WHERE id = 1507")
print(f"  Current services: {resp}")

update_sql = """
    UPDATE dental_clinics
    SET services = CASE
        WHEN services IS NULL OR services = '' THEN 'Cosmetic, Dentures'
        ELSE services || ', Cosmetic, Dentures'
    END
    WHERE id = 1507
      AND (services IS NULL OR services NOT ILIKE '%cosmetic%' OR services NOT ILIKE '%dentures%');
"""
status, resp = db(update_sql)
print(f"  Update status: {status}")

status, resp = db("SELECT services FROM dental_clinics WHERE id = 1507")
print(f"  New services: {resp}")

print("\nDone.")
