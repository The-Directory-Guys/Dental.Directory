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
    "Referer": "https://www.nelsondental.co.nz/",
}

def db(sql):
    r = requests.post(
        "https://api.supabase.com/v1/projects/ankyjpgcocsvvtyyymys/database/query",
        headers={"Authorization": f"Bearer {MGMT_KEY}", "Content-Type": "application/json"},
        json={"query": sql}, timeout=30, verify=False,
    )
    return r.status_code

practitioners = [
    {
        "id": 751,
        "filename": "janette-wilcox.jpg",
        "content_type": "image/jpeg",
        "photo_url": "https://images.squarespace-cdn.com/content/v1/62fb0dafcb84e0517fe5b9f0/1663065615930-0M1ZH6BGNDPVHC31FHDN/VWPhoto-8975-min.jpg",
        "experience": "Graduated Guys Hospital, London (1987). Credentialed in forensic dentistry.",
        "bio": "Practised in the UK before immigrating to New Zealand in 2004, becoming a partner in 2007. Former Nelson Dental Association President. Received a citation medal for forensic services after the Christchurch earthquake. Volunteer dental missions to Nepal and India with Rotary.",
        "specialties": "Principal Dentist, Forensic dentistry",
    },
    {
        "id": 752,
        "filename": "pierre-gill.jpg",
        "content_type": "image/jpeg",
        "photo_url": "https://images.squarespace-cdn.com/content/v1/62fb0dafcb84e0517fe5b9f0/5c2cf54c-8881-4a33-85ba-6912696863f4/VWPhoto-8958-min.jpg",
        "experience": "BDS (Otago, 1999), MSc Dental Implantology with distinction (University of Salford, 2012).",
        "bio": "Spent 17 years in the UK developing expertise in general dentistry, endodontics, and implantology before relocating to New Zealand.",
        "specialties": "Principal Dentist, Endodontics, implantology",
    },
    {
        "id": 753,
        "filename": "evonne-phua.jpg",
        "content_type": "image/jpeg",
        "photo_url": "https://images.squarespace-cdn.com/content/v1/62fb0dafcb84e0517fe5b9f0/6d72c7ef-edf9-4762-991b-9086f52c0137/evonne+web+picture.jpg",
        "experience": "BDS (Otago, 2021) with First Class Honours. OMRF Scholarship recipient (2020).",
        "bio": None,
        "specialties": "Dentist, Digital dentistry, restorative dentistry, oral surgery, facial aesthetics, IV sedation",
    },
    {
        "id": 754,
        "filename": "ben-mar.png",
        "content_type": "image/png",
        "photo_url": "https://images.squarespace-cdn.com/content/v1/62fb0dafcb84e0517fe5b9f0/dd864be5-0eff-4729-8395-8280b857e9ec/Ben+web+photo.png",
        "experience": "BDS (Otago, 2021) with First Class Honours. NZ Dental Research Foundation Scholarship and OMRF Scholarship recipient.",
        "bio": None,
        "specialties": "Dentist, Endodontics, composite resin artistry, digital dentistry, implantology, oral surgery",
    },
    {
        "id": 755,
        "filename": "olivia-partridge.png",
        "content_type": "image/png",
        "photo_url": "https://images.squarespace-cdn.com/content/v1/62fb0dafcb84e0517fe5b9f0/755f0898-373d-4650-8c68-a48ca5d79c81/Olivia+web+photo.png",
        "experience": None,
        "bio": None,
        "specialties": "Oral Health Therapist",
    },
    {
        "id": 756,
        "filename": "indi-alsop.jpg",
        "content_type": "image/jpeg",
        "photo_url": "https://images.squarespace-cdn.com/content/v1/62fb0dafcb84e0517fe5b9f0/bcd245e0-86d2-4f61-8502-d9b723197c8c/Indi+web+photo.jpg",
        "experience": None,
        "bio": None,
        "specialties": "Oral Health Therapist",
    },
]

for p in practitioners:
    print(f"\n--- {p['filename']} ---")
    r = requests.get(p["photo_url"], headers=HEADERS_DL, timeout=30, verify=False)
    print(f"  Download: {r.status_code}, {len(r.content)} bytes")
    if r.status_code != 200:
        print("  SKIP")
        continue

    file_path = f"practitioners/{p['filename']}"
    up = requests.post(
        f"{SUPABASE_URL}/storage/v1/object/{BUCKET}/{file_path}",
        headers={"Authorization": f"Bearer {SUPABASE_JWT}", "Content-Type": p["content_type"], "x-upsert": "true"},
        data=r.content, timeout=30, verify=False,
    )
    print(f"  Upload: {up.status_code}")

    public_url = f"{SUPABASE_URL}/storage/v1/object/public/{BUCKET}/{file_path}"
    bio_sql = f", bio = $${p['bio']}$$" if p["bio"] else ""
    exp_sql = f", experience = $${p['experience']}$$" if p["experience"] else ""
    sql = f"UPDATE clinic_practitioners SET photo_url = '{public_url}', specialties = $${p['specialties']}$${exp_sql}{bio_sql} WHERE id = {p['id']};"
    print(f"  DB: {db(sql)}")

# Fix payment_partners — keep ACC only, Southern Cross covered by scraped entry
print("\n--- Payment fix ---")
sql_pay = "UPDATE clinic_amenities SET payment_partners = 'ACC' WHERE clinic_id = 1669;"
print(f"  {db(sql_pay)}")

print("\nDone.")
