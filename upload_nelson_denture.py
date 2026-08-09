import requests
import os
from dotenv import load_dotenv

load_dotenv(r"c:\Users\Ciaran\Desktop\Dental_Directory\.env")

SUPABASE_URL = os.environ["SUPABASE_URL"]
SUPABASE_JWT = os.environ['SUPABASE_JWT']
MGMT_KEY = os.environ["SUPABASE_MANAGEMENT_KEY"]
BUCKET = "practitioner-photos"

photo_url = "https://static.wixstatic.com/media/ce95c3_916ae95ad2004deda29e3337d9a4d1b8~mv2.jpg/v1/fill/w_330,h_492,al_c,q_80,usm_0.66_1.00_0.01,enc_avif,quality_auto/MDCTom.jpg"
filename = "thomas-gu.jpg"
prac_id = 750
clinic_id = 1670

headers_dl = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/120.0.0.0 Safari/537.36",
    "Referer": "https://www.wixstatic.com/",
}

r = requests.get(photo_url, headers=headers_dl, timeout=30, verify=False)
print(f"Download: {r.status_code}, {len(r.content)} bytes")

file_path = f"practitioners/{filename}"
up = requests.post(
    f"{SUPABASE_URL}/storage/v1/object/{BUCKET}/{file_path}",
    headers={"Authorization": f"Bearer {SUPABASE_JWT}", "Content-Type": "image/jpeg", "x-upsert": "true"},
    data=r.content,
    timeout=30,
    verify=False,
)
print(f"Upload: {up.status_code}")

public_url = f"{SUPABASE_URL}/storage/v1/object/public/{BUCKET}/{file_path}"
sql = f"""
UPDATE clinic_practitioners SET photo_url = '{public_url}' WHERE id = {prac_id};
UPDATE clinic_amenities SET payment_partners = NULL WHERE clinic_id = {clinic_id};
"""
resp = requests.post(
    "https://api.supabase.com/v1/projects/ankyjpgcocsvvtyyymys/database/query",
    headers={"Authorization": f"Bearer {MGMT_KEY}", "Content-Type": "application/json"},
    json={"query": sql},
    timeout=30,
    verify=False,
)
print(f"DB update: {resp.status_code}")
print(f"Photo URL: {public_url}")
