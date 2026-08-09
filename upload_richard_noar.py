import requests
import os
from dotenv import load_dotenv

load_dotenv(r"c:\Users\Ciaran\Desktop\Dental_Directory\.env")

SUPABASE_URL = os.environ["SUPABASE_URL"]
SUPABASE_JWT = os.environ['SUPABASE_JWT']
MGMT_KEY = os.environ["SUPABASE_MANAGEMENT_KEY"]
BUCKET = "practitioner-photos"

# Try larger version first, fall back to 200w
base = "https://cdn-asset-mel-2.airsquare.com/gentledental/managed/image/widget/image_list/C853AEF4-8D74-45C4-88E8DAD93D387FCB"
headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/120.0.0.0 Safari/537.36",
    "Referer": "https://www.gentledentalnelson.co.nz/",
}

photo_url = None
for size in ["400w", "200w"]:
    url = f"{base}-{size}.webp?20230614223447"
    r = requests.get(url, headers=headers, timeout=30, verify=False)
    print(f"{size}: {r.status_code}, {len(r.content)} bytes")
    if r.status_code == 200 and len(r.content) > 1000:
        photo_url = url
        content = r.content
        break

if not photo_url:
    print("Could not download photo")
    exit(1)

filename = "richard-noar.webp"
file_path = f"practitioners/{filename}"
up = requests.post(
    f"{SUPABASE_URL}/storage/v1/object/{BUCKET}/{file_path}",
    headers={"Authorization": f"Bearer {SUPABASE_JWT}", "Content-Type": "image/webp", "x-upsert": "true"},
    data=content,
    timeout=30,
    verify=False,
)
print(f"Upload: {up.status_code}")

public_url = f"{SUPABASE_URL}/storage/v1/object/public/{BUCKET}/{file_path}"
resp = requests.post(
    "https://api.supabase.com/v1/projects/ankyjpgcocsvvtyyymys/database/query",
    headers={"Authorization": f"Bearer {MGMT_KEY}", "Content-Type": "application/json"},
    json={"query": f"UPDATE clinic_practitioners SET photo_url = '{public_url}' WHERE id = 783;"},
    timeout=30,
    verify=False,
)
print(f"DB update: {resp.status_code} — {public_url}")
