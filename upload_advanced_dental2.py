import requests
import os
from dotenv import load_dotenv

load_dotenv(r"c:\Users\Ciaran\Desktop\Dental_Directory\.env")

SUPABASE_URL = os.environ["SUPABASE_URL"]
SUPABASE_JWT = os.environ['SUPABASE_JWT']
MGMT_KEY = os.environ["SUPABASE_MANAGEMENT_KEY"]
BUCKET = "practitioner-photos"
CLINIC_ID = 1651

HEADERS_DL = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/120.0.0.0 Safari/537.36",
    "Referer": "https://www.advanceddental.co.nz/",
}

def db(sql):
    r = requests.post(
        "https://api.supabase.com/v1/projects/ankyjpgcocsvvtyyymys/database/query",
        headers={"Authorization": f"Bearer {MGMT_KEY}", "Content-Type": "application/json"},
        json={"query": sql}, timeout=30, verify=False,
    )
    if r.status_code not in (200, 201):
        print(f"    ERROR: {r.text[:200]}")
    return r.status_code

staff = [
    {
        "filename": "debbie-advanced-dental.jpg",
        "name": "Debbie",
        "gender": "F",
        "specialties": "Practice Manager",
        "experience": None,
        "bio": "Practice manager at Advanced Dental for 19 years.",
        "photo_url": "https://images.squarespace-cdn.com/content/v1/597925aacd39c3750038d54c/1ff465af-5de3-42d0-bb71-86ed5fbc2968/IMG_0357.jpg",
    },
    {
        "filename": "jaz-advanced-dental.jpg",
        "name": "Jaz",
        "gender": "F",
        "specialties": "Receptionist",
        "experience": None,
        "bio": "Has been with the practice for 9 years, initially as a dental assistant for 5 years before moving into reception.",
        "photo_url": "https://images.squarespace-cdn.com/content/v1/597925aacd39c3750038d54c/4e9fa2d4-0633-4fd5-a039-3e10ab654a78/IMG_9115.jpg",
    },
    {
        "filename": "bronnie-advanced-dental.jpg",
        "name": "Bronnie",
        "gender": "F",
        "specialties": "Receptionist",
        "experience": None,
        "bio": "Multi-role team member for 5 years, working across reception, hygienist assistance, and sterilisation.",
        "photo_url": "https://images.squarespace-cdn.com/content/v1/597925aacd39c3750038d54c/24bfdeef-270a-4f69-a2fc-5bd81b84ee19/IMG_9098+%281%29.jpg",
    },
    {
        "filename": "courtney-advanced-dental.jpg",
        "name": "Courtney",
        "gender": "F",
        "specialties": "Dental Assistant",
        "experience": "Certificate in Dental Assisting (2018)",
        "bio": "Has been with the practice for over 5 years. Also trained in advanced skin assessment and treatments.",
        "photo_url": "https://images.squarespace-cdn.com/content/v1/597925aacd39c3750038d54c/c1ad27f3-4e95-45f6-b46b-80661a38e0cf/IMG_0872.jpg",
    },
    {
        "filename": "brooklynn-advanced-dental.jpg",
        "name": "Brooklynn",
        "gender": "F",
        "specialties": "Dental Assistant",
        "experience": None,
        "bio": "Experienced dental assistant skilled in implant procedures and surgical extractions. Also manages practice supply ordering.",
        "photo_url": "https://images.squarespace-cdn.com/content/v1/597925aacd39c3750038d54c/07276387-a473-4c89-9fc2-2460468da626/IMG_3035.jpeg",
    },
    {
        "filename": "chris-advanced-dental.jpg",
        "name": "Chris",
        "gender": "M",
        "specialties": "Dental Assistant",
        "experience": "Certificate in Dental Assisting (2019)",
        "bio": "Has been with the practice for over 7 years, starting out as a hygienist's assistant.",
        "photo_url": "https://images.squarespace-cdn.com/content/v1/597925aacd39c3750038d54c/b0cca6ef-1320-481c-98ae-02fcf06d9472/IMG_0894.jpg",
    },
    {
        "filename": "emma-advanced-dental.jpg",
        "name": "Emma",
        "gender": "F",
        "specialties": "Dental Assistant",
        "experience": "Dental Assisting Certificate (2024)",
        "bio": None,
        "photo_url": "https://images.squarespace-cdn.com/content/v1/597925aacd39c3750038d54c/037172f4-3cce-4c27-be09-d1f572cb8633/IMG_8551.jpg",
    },
    {
        "filename": "chloe-advanced-dental.jpg",
        "name": "Chloe",
        "gender": "F",
        "specialties": "Dental Assistant",
        "experience": None,
        "bio": None,
        "photo_url": "https://images.squarespace-cdn.com/content/v1/597925aacd39c3750038d54c/299d8d31-b473-48d0-a9bf-da11297475f2/unnamed.jpg",
    },
    {
        "filename": "mae-advanced-dental.jpg",
        "name": "Mae",
        "gender": "F",
        "specialties": "Dental Assistant",
        "experience": "Dental Assistant training (2023)",
        "bio": "Works across both public and private practice. A multilingual interpreter who supports patients from diverse backgrounds.",
        "photo_url": "https://images.squarespace-cdn.com/content/v1/597925aacd39c3750038d54c/3b2b8c23-c610-4f31-af01-973d5e6f0b3a/M+Hla.jpg",
    },
    {
        "filename": "chanel-advanced-dental.jpg",
        "name": "Chanel",
        "gender": "F",
        "specialties": "Dental Assistant",
        "experience": None,
        "bio": None,
        "photo_url": "https://images.squarespace-cdn.com/content/v1/597925aacd39c3750038d54c/669d33ba-40f9-4790-a33a-12dc7579d7fc/IMG_4801.jpg",
    },
]

for p in staff:
    print(f"\n--- {p['name']} ---")
    r = requests.get(p["photo_url"], headers=HEADERS_DL, timeout=30, verify=False)
    print(f"  Download: {r.status_code}, {len(r.content)} bytes")
    if r.status_code != 200 or len(r.content) < 1000:
        print("  SKIP (bad download)")
        continue

    file_path = f"practitioners/{p['filename']}"
    up = requests.post(
        f"{SUPABASE_URL}/storage/v1/object/{BUCKET}/{file_path}",
        headers={"Authorization": f"Bearer {SUPABASE_JWT}", "Content-Type": "image/jpeg", "x-upsert": "true"},
        data=r.content, timeout=30, verify=False,
    )
    print(f"  Upload: {up.status_code}")

    public_url = f"{SUPABASE_URL}/storage/v1/object/public/{BUCKET}/{file_path}"
    exp_val = f"$${p['experience']}$$" if p["experience"] else "NULL"
    bio_val = f"$${p['bio']}$$" if p["bio"] else "NULL"

    sql = f"""
        INSERT INTO clinic_practitioners (clinic_id, name, gender, specialties, experience, bio, photo_url, source_url)
        VALUES (
            {CLINIC_ID},
            $${p['name']}$$,
            '{p['gender']}',
            $${p['specialties']}$$,
            {exp_val},
            {bio_val},
            '{public_url}',
            'https://www.advanceddental.co.nz/dentists-copy'
        );
    """
    print(f"  DB: {db(sql)}")

print("\nDone.")
