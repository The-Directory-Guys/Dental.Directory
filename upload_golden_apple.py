import requests
import os
from dotenv import load_dotenv

load_dotenv(r"c:\Users\Ciaran\Desktop\Dental_Directory\.env")

SUPABASE_URL = os.environ["SUPABASE_URL"]
SUPABASE_JWT = os.environ['SUPABASE_JWT']
MGMT_KEY = os.environ["SUPABASE_MANAGEMENT_KEY"]
BUCKET = "practitioner-photos"
CLINIC_IDS = [1516, 1530]  # Hastings + Napier
SOURCE_URL = "https://gadental.co.nz/our-team/"

HEADERS_DL = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/124.0.0.0 Safari/537.36",
    "Referer": "https://gadental.co.nz/",
}

def db(sql):
    r = requests.post(
        "https://api.supabase.com/v1/projects/ankyjpgcocsvvtyyymys/database/query",
        headers={"Authorization": f"Bearer {MGMT_KEY}", "Content-Type": "application/json"},
        json={"query": sql}, timeout=30, verify=False,
    )
    if r.status_code not in (200, 201):
        print(f"    DB ERROR: {r.text[:300]}")
    return r.status_code

practitioners = [
    {
        "filename": "dr-isha-woodhams-gadental.jpg",
        "name": "Dr Isha Woodhams",
        "gender": "F",
        "specialties": "General Dentist",
        "experience": "BDS (Otago), MBA",
        "photo_url": "https://gadental.co.nz/wp-content/uploads/2026/02/Dr-Isha-Woodhams-683x1024.jpg",
    },
    {
        "filename": "adrian-woodhams-gadental.jpg",
        "name": "Adrian Woodhams",
        "gender": "M",
        "specialties": "Director",
        "experience": None,
        "photo_url": "https://gadental.co.nz/wp-content/uploads/2024/04/CP27195-Edit-683x1024.jpg",
    },
    {
        "filename": "lucy-vlnasova-gadental.jpg",
        "name": "Lucy Vlnasova",
        "gender": "F",
        "specialties": "Practice Manager",
        "experience": None,
        "photo_url": "https://gadental.co.nz/wp-content/uploads/2022/09/Dental-b-683x1024.jpg",
    },
    {
        "filename": "dr-pop-wattanakulachart-gadental.jpg",
        "name": "Dr Pop Wattanakulachart",
        "gender": "M",
        "specialties": "General Dentist",
        "experience": "BDS (Otago)",
        "photo_url": "https://gadental.co.nz/wp-content/uploads/2022/08/Dr-Pop-Wattanakulachart-683x1024.jpg",
    },
    {
        "filename": "dr-imran-cassim-gadental.jpg",
        "name": "Dr Imran Cassim",
        "gender": "M",
        "specialties": "General Dentist",
        "experience": "BDS",
        "photo_url": "https://gadental.co.nz/wp-content/uploads/2024/04/CP27249-Edit-683x1024.jpg",
    },
    {
        "filename": "dr-jack-saunders-gadental.jpg",
        "name": "Dr Jack Saunders",
        "gender": "M",
        "specialties": "General Dentist",
        "experience": "BSc, BDS (Otago)",
        "photo_url": "https://gadental.co.nz/wp-content/uploads/2024/04/CP27304-Edit-683x1024.jpg",
    },
    {
        "filename": "dr-vineetha-jenson-gadental.jpg",
        "name": "Dr Vineetha Jenson",
        "gender": "F",
        "specialties": "General Dentist",
        "experience": "BDS (Otago)",
        "photo_url": "https://gadental.co.nz/wp-content/uploads/2024/04/CP27272-Edit-scaled-e1714357117302-683x1024.jpg",
    },
    {
        "filename": "dr-micah-lepaio-gadental.jpg",
        "name": "Dr Micah Lepaio",
        "gender": "M",
        "specialties": "General Dentist",
        "experience": "BDS",
        "photo_url": "https://gadental.co.nz/wp-content/uploads/2026/02/Dr-Micah-Lepaio-683x1024.jpg",
    },
    {
        "filename": "dr-charlotta-hillberg-gadental.jpg",
        "name": "Dr Charlotta Hillberg",
        "gender": "F",
        "specialties": "General Dentist",
        "experience": "BDS (Otago)",
        "photo_url": "https://gadental.co.nz/wp-content/uploads/2026/02/Dr-Charlotta-Hillberg-683x1024.jpg",
    },
    {
        "filename": "dr-tazeem-chaudhry-gadental.jpg",
        "name": "Dr Tazeem Chaudhry",
        "gender": "M",
        "specialties": "General Dentist",
        "experience": "BDS",
        "photo_url": "https://gadental.co.nz/wp-content/uploads/2026/02/Dr-Tazeem-Chaudhry-683x1024.jpg",
    },
    {
        "filename": "dr-tegan-bennik-gadental.jpg",
        "name": "Dr Tegan Bennik",
        "gender": "F",
        "specialties": "General Dentist",
        "experience": "BDS (Otago)",
        "photo_url": "https://gadental.co.nz/wp-content/uploads/2026/02/Dr-Tegan-Bennick-683x1024.jpg",
    },
    {
        "filename": "kate-fairweather-gadental.jpg",
        "name": "Kate Fairweather",
        "gender": "F",
        "specialties": "Oral Health Therapist",
        "experience": None,
        "photo_url": "https://gadental.co.nz/wp-content/uploads/2022/08/Kate-e1663128474717-683x1024.jpg",
    },
    {
        "filename": "maggey-shin-gadental.jpg",
        "name": "Maggey Shin",
        "gender": "F",
        "specialties": "Dental Hygienist",
        "experience": "OHT (AUT)",
        "photo_url": "https://gadental.co.nz/wp-content/uploads/2024/04/CP27234-Edit-683x1024.jpg",
    },
    {
        "filename": "simeon-wilson-gadental.jpg",
        "name": "Simeon Wilson",
        "gender": "M",
        "specialties": "Oral Health Therapist",
        "experience": None,
        "photo_url": "https://gadental.co.nz/wp-content/uploads/2026/02/Simeon-Wilson-683x1024.jpg",
    },
]

# Upload each photo once, then insert a row per clinic
for p in practitioners:
    print(f"\n--- {p['name']} ---")

    # Download photo
    r = requests.get(p["photo_url"], headers=HEADERS_DL, timeout=30, verify=False)
    print(f"  Download: {r.status_code}, {len(r.content)} bytes")
    if r.status_code != 200 or len(r.content) < 5000:
        print("  SKIP (bad download)")
        continue

    # Upload once
    file_path = f"practitioners/{p['filename']}"
    up = requests.post(
        f"{SUPABASE_URL}/storage/v1/object/{BUCKET}/{file_path}",
        headers={"Authorization": f"Bearer {SUPABASE_JWT}", "Content-Type": "image/jpeg", "x-upsert": "true"},
        data=r.content, timeout=30, verify=False,
    )
    print(f"  Upload: {up.status_code}")

    public_url = f"{SUPABASE_URL}/storage/v1/object/public/{BUCKET}/{file_path}"
    exp_val = f"$${p['experience']}$$" if p["experience"] else "NULL"

    # Insert for each clinic
    for clinic_id in CLINIC_IDS:
        sql = f"""
            INSERT INTO clinic_practitioners (clinic_id, name, gender, specialties, experience, photo_url, source_url)
            VALUES ({clinic_id}, $${p['name']}$$, '{p['gender']}', $${p['specialties']}$$, {exp_val}, '{public_url}', '{SOURCE_URL}');
        """
        status = db(sql)
        print(f"  Clinic {clinic_id}: {status}")

print("\nDone.")
