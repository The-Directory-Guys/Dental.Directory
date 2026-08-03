import sys, io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

import requests, os, re
from dotenv import load_dotenv

load_dotenv(r"c:\Users\Ciaran\Desktop\Dental_Directory\.env")

SUPABASE_URL = os.environ["SUPABASE_URL"]
SUPABASE_JWT = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImFua3lqcGdjb2NzdnZ0eXl5bXlzIiwicm9sZSI6InNlcnZpY2Vfcm9sZSIsImlhdCI6MTc3MzgxMzUxNCwiZXhwIjoyMDg5Mzg5NTE0fQ.9wfSt-mM39fqQbihr8sTCPB80k3UhoAnMX5LQv8Q9VU"
MGMT_KEY = os.environ["SUPABASE_MANAGEMENT_KEY"]
BUCKET = "practitioner-photos"
CLINIC_ID = 1511
SOURCE_URL = "https://www.dentiq.nz/meet-our-team/"

HEADERS_DL = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/124.0.0.0 Safari/537.36",
    "Referer": "https://www.dentiq.nz/",
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

def ext_from_url(url):
    return url.split("?")[0].rsplit(".", 1)[-1].lower()

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
        "name": "Dr Sundar Jagadeesan",
        "gender": "M",
        "specialties": "General Dentist",
        "experience": "BDS (TN Dr MGR Medical University, 2002), PG Cert Oral Implantology (Manipal, 2007), NZDREX (Otago, 2008), FICOI (2016), Kois Center Graduate (Seattle, 2018)",
        "photo_url": "https://www.dentiq.nz/wp-content/uploads/2025/09/Dr-Sundar-Jagadeesan.jpg",
    },
    {
        "name": "Dr Aidan Khoo",
        "gender": "M",
        "specialties": "General Dentist",
        "experience": "BDS (Otago, 2025)",
        "photo_url": "https://www.dentiq.nz/wp-content/uploads/2026/01/aidan-khoo.jpg",
    },
    {
        "name": "Debra Nabney",
        "gender": "F",
        "specialties": "Oral Health Therapist",
        "experience": "Bachelor of Oral Health (AUT, 2010)",
        "photo_url": "https://www.dentiq.nz/wp-content/uploads/2025/08/debra-nabney-1.jpg",
    },
    {
        "name": "Harry Dissanayake",
        "gender": "M",
        "specialties": "Practice Manager",
        "experience": "BDS (Sri Lanka)",
        "photo_url": "https://www.dentiq.nz/wp-content/uploads/2025/08/harry-dissanayake.jpg",
    },
    {
        "name": "Anu Sundar",
        "gender": "F",
        "specialties": "Executive Director",
        "experience": "MPhil in Library and Information Science",
        "photo_url": "https://www.dentiq.nz/wp-content/uploads/2025/08/anu-sundar.jpg",
    },
    {
        "name": "Rachel Roberts",
        "gender": "F",
        "specialties": "Dental Assistant",
        "experience": None,
        "photo_url": "https://www.dentiq.nz/wp-content/uploads/2025/08/rachel-roberts.jpg",
    },
]

for p in TEAM:
    print(f"\n--- {p['name']} ---")
    ext = ext_from_url(p["photo_url"])
    filename = f"{name_slug(p['name'])}-dentiq.{ext}"

    try:
        r = requests.get(p["photo_url"], headers=HEADERS_DL, timeout=30, verify=False)
        print(f"  Download: {r.status_code}, {len(r.content)} bytes")
        if r.status_code != 200 or len(r.content) < 3000:
            print("  SKIP (bad download)")
            continue
        data = r.content
    except Exception as e:
        print(f"  SKIP (error: {e})")
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
