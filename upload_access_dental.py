import requests
import os
from dotenv import load_dotenv

load_dotenv(r"c:\Users\Ciaran\Desktop\Dental_Directory\.env")

SUPABASE_URL = os.environ["SUPABASE_URL"]
SUPABASE_JWT = os.environ['SUPABASE_JWT']
MGMT_KEY = os.environ["SUPABASE_MANAGEMENT_KEY"]
BUCKET = "practitioner-photos"

HEADERS_DL = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/120.0.0.0 Safari/537.36",
    "Referer": "https://www.accessdental.co.nz/",
}

practitioners = [
    {
        "id": 760,
        "name": "Paula Palmer",
        "filename": "paula-palmer.jpg",
        "photo_url": "https://www.accessdental.co.nz/wp-content/uploads/elementor/thumbs/pp-pics-qjc7hbt8frw8hdhohozu0pkj65uxlm01w84d29fi7w.jpg",
        "specialties": "Dental Hygienist, Whitening",
        "experience": "25+ years experience",
        "bio": "Dental Hygienist of the Year 2019. Trained as both a Dental Assistant and Dental Therapist before becoming a hygienist. Former President of the NZ Dental Hygiene Association. Special interest in whitening.",
    },
    {
        "id": 761,
        "name": "Dr Lindsay Carlier-Boedels",
        "filename": "lindsay-carlier-boedels.jpg",
        "photo_url": "https://www.accessdental.co.nz/wp-content/uploads/elementor/thumbs/Lindsay-qjc7hbt8frw8hdhohozu0pkj65uxlm01w84d29fi7w.jpg",
        "specialties": "Registered Dentist",
        "experience": None,
        "bio": None,
    },
    {
        "id": 762,
        "name": "Dr Sam Schroder",
        "filename": "sam-schroder.jpg",
        "photo_url": "https://www.accessdental.co.nz/wp-content/uploads/2024/06/sam-schroeder-pic-e1718859432803.jpg",
        "specialties": "Dentist, BDS, PhD, BSc",
        "experience": None,
        "bio": None,
    },
]

for p in practitioners:
    print(f"\n--- {p['name']} ---")

    # Download photo
    r = requests.get(p["photo_url"], headers=HEADERS_DL, timeout=30, verify=False)
    print(f"  Download: {r.status_code}, {len(r.content)} bytes")
    if r.status_code != 200:
        print("  SKIP — download failed")
        continue

    # Upload to storage
    file_path = f"practitioners/{p['filename']}"
    up = requests.post(
        f"{SUPABASE_URL}/storage/v1/object/{BUCKET}/{file_path}",
        headers={"Authorization": f"Bearer {SUPABASE_JWT}", "Content-Type": "image/jpeg", "x-upsert": "true"},
        data=r.content,
        timeout=30,
        verify=False,
    )
    print(f"  Upload: {up.status_code}")

    public_url = f"{SUPABASE_URL}/storage/v1/object/public/{BUCKET}/{file_path}"

    # Build update fields
    set_parts = [
        f"photo_url = '{public_url}'",
        f"specialties = '{p['specialties']}'",
    ]
    if p["experience"]:
        set_parts.append(f"experience = '{p['experience']}'")
    if p["bio"]:
        bio_escaped = p["bio"].replace("'", "''")
        set_parts.append(f"bio = '{bio_escaped}'")

    sql = f"UPDATE clinic_practitioners SET {', '.join(set_parts)} WHERE id = {p['id']};"
    resp = requests.post(
        "https://api.supabase.com/v1/projects/ankyjpgcocsvvtyyymys/database/query",
        headers={"Authorization": f"Bearer {MGMT_KEY}", "Content-Type": "application/json"},
        json={"query": sql},
        timeout=30,
        verify=False,
    )
    print(f"  DB update: {resp.status_code}")

print("\nDone.")
