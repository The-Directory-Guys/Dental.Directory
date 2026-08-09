import sys, io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

import requests, os, re
from dotenv import load_dotenv

load_dotenv(r"c:\Users\Ciaran\Desktop\Dental_Directory\.env")

SUPABASE_URL = os.environ["SUPABASE_URL"]
SUPABASE_JWT = os.environ['SUPABASE_JWT']
MGMT_KEY = os.environ["SUPABASE_MANAGEMENT_KEY"]
BUCKET = "practitioner-photos"
CLINIC_ID = 1509
SOURCE_URL = "https://dentalonraffles.co.nz/our-team/"

HEADERS_DL = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/124.0.0.0 Safari/537.36",
    "Referer": "https://dentalonraffles.co.nz/",
}

def db_exec(sql):
    r = requests.post(
        "https://api.supabase.com/v1/projects/ankyjpgcocsvvtyyymys/database/query",
        headers={"Authorization": f"Bearer {MGMT_KEY}", "Content-Type": "application/json"},
        json={"query": sql}, timeout=30, verify=False,
    )
    if r.status_code not in (200, 201):
        print(f"    DB ERROR: {r.text[:300]}")
    return r.status_code

def name_slug(name):
    return re.sub(r"[^a-z0-9]+", "-", name.lower()).strip("-")

def full_size_url(thumb_url):
    return re.sub(r"-\d+x\d+(\.[a-z]+)$", r"\1", thumb_url)

def ext_from_url(url):
    return url.split("?")[0].rsplit(".", 1)[-1].lower()

def download(url):
    try:
        r = requests.get(url, headers=HEADERS_DL, timeout=30, verify=False)
        if r.status_code == 200 and len(r.content) >= 3000:
            return r.content
    except Exception:
        pass
    return None

def upload(filename, data, ext):
    ctype = "image/png" if ext == "png" else "image/jpeg"
    file_path = f"practitioners/{filename}"
    r = requests.post(
        f"{SUPABASE_URL}/storage/v1/object/{BUCKET}/{file_path}",
        headers={"Authorization": f"Bearer {SUPABASE_JWT}", "Content-Type": ctype, "x-upsert": "true"},
        data=data, timeout=60, verify=False,
    )
    return r.status_code, f"{SUPABASE_URL}/storage/v1/object/public/{BUCKET}/{file_path}"

TEAM = [
    {
        "name": "Dr Gary Winter",
        "gender": "M",
        "specialties": "General Dentist",
        "experience": "UCLA Master Clinician Program in Implant Dentistry",
        "thumb": "https://dentalonraffles.co.nz/wp-content/uploads/2015/08/Doctor-Gary-Winter-2-175x175.jpg",
    },
    {
        "name": "Dr Swati Bajaj",
        "gender": "F",
        "specialties": "General Dentist",
        "experience": "BDS (India, 2005)",
        "thumb": "https://dentalonraffles.co.nz/wp-content/uploads/2020/07/Dr-Swati-Bajaj-175x175.jpg",
    },
    {
        "name": "Dr Ankush Bajaj",
        "gender": "M",
        "specialties": "General Dentist",
        "experience": "BDS (India, 2005)",
        "thumb": "https://dentalonraffles.co.nz/wp-content/uploads/2015/08/Dr-Ankush-Bajaj-175x175.jpg",
    },
    {
        "name": "Dr Tabetha Lindsay",
        "gender": "F",
        "specialties": "General Dentist",
        "experience": None,
        "thumb": "https://dentalonraffles.co.nz/wp-content/uploads/2015/08/Tabatha-1-175x175.jpg",
    },
    {
        "name": "Dr Jason Lee",
        "gender": "M",
        "specialties": "General Dentist",
        "experience": "BDS with First Class Honours (Otago)",
        "thumb": "https://dentalonraffles.co.nz/wp-content/uploads/2020/06/JL-e1783372314982-175x175.png",
    },
    {
        "name": "Dr Carly Wu",
        "gender": "F",
        "specialties": "General Dentist",
        "experience": "BDS (Otago)",
        "thumb": "https://dentalonraffles.co.nz/wp-content/uploads/2026/05/Qinze-Wu-2-scaled-e1778619648322-175x175.jpg",
    },
    {
        "name": "Maddie Beserra",
        "gender": "F",
        "specialties": "Dental Hygienist",
        "experience": None,
        "thumb": "https://dentalonraffles.co.nz/wp-content/uploads/2020/03/Maddie-175x175.jpg",
    },
    {
        "name": "Marie Davis",
        "gender": "F",
        "specialties": "Dental Hygienist",
        "experience": "Bachelor of Oral Health (BOH)",
        "thumb": "https://dentalonraffles.co.nz/wp-content/uploads/2020/03/MarieDavis-1-175x175.jpg",
    },
]

for p in TEAM:
    print(f"\n--- {p['name']} ---")
    ext = ext_from_url(p["thumb"])
    filename = f"{name_slug(p['name'])}-raffles.{ext}"

    # Try full-size first, fall back to thumbnail
    full_url = full_size_url(p["thumb"])
    data = download(full_url)
    if data:
        print(f"  Downloaded full-size: {len(data)} bytes ({full_url.split('/')[-1]})")
    else:
        data = download(p["thumb"])
        if data:
            print(f"  Downloaded thumbnail: {len(data)} bytes")
        else:
            print("  SKIP (download failed)")
            continue

    up_status, public_url = upload(filename, data, ext)
    print(f"  Upload: {up_status} → {filename}")

    exp_val = f"$${p['experience']}$$" if p["experience"] else "NULL"
    sql = f"""
        INSERT INTO clinic_practitioners
          (clinic_id, name, gender, specialties, experience, photo_url, source_url)
        VALUES
          ({CLINIC_ID}, $${p['name']}$$, '{p["gender"]}', $${p["specialties"]}$$,
           {exp_val}, '{public_url}', '{SOURCE_URL}');
    """
    status = db_exec(sql)
    print(f"  DB insert: {status}")

print("\nDone.")
