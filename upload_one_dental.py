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
    "Referer": "https://www.onedental.co.nz/",
}

# ids: (mapua, stoke)
practitioners = [
    {
        "ids": [763, 704],
        "filename": "justin-kabir.jpg",
        "content_type": "image/jpeg",
        "photo_url": "https://www.onedental.co.nz/v2/wp-content/uploads/2025/09/One-Dental-About-Dr-Justin-Kabir-v2-788x1024.jpg",
    },
    {
        "ids": [764, 705],
        "filename": "sarah-kueh.jpg",
        "content_type": "image/jpeg",
        "photo_url": "https://www.onedental.co.nz/v2/wp-content/uploads/2025/09/One-Dental-About-Dr-Sarah-Kueh-v2-788x1024.jpg",
    },
    {
        "ids": [765, 706],
        "filename": "charles-fox.jpg",
        "content_type": "image/jpeg",
        "photo_url": "https://www.onedental.co.nz/v2/wp-content/uploads/2026/02/Charlie-Fox-Photo.jpg",
    },
    {
        "ids": [766, 707],
        "filename": "mat-elmhirst.jpg",
        "content_type": "image/jpeg",
        "photo_url": "https://www.onedental.co.nz/v2/wp-content/uploads/2025/09/One-Dental-About-Dr-Mat-Elmhirst-v2-788x1024.jpg",
    },
    {
        "ids": [767, 708],
        "filename": "binnie-ahamat.png",
        "content_type": "image/png",
        "photo_url": "https://www.onedental.co.nz/v2/wp-content/uploads/2026/01/Binnie-edited-photo-768x1024.png",
    },
    {
        "ids": [768, 709],
        "filename": "michelle-johnstone.jpg",
        "content_type": "image/jpeg",
        "photo_url": "https://www.onedental.co.nz/v2/wp-content/uploads/2025/10/Michelle-Johnstone-788x1024.jpg",
    },
    {
        "ids": [769, 710],
        "filename": "siemin-theis.jpg",
        "content_type": "image/jpeg",
        "photo_url": "https://www.onedental.co.nz/v2/wp-content/uploads/2025/09/One-Dental-About-Dr-Siemin-Theis-v2-788x1024.jpg",
    },
    {
        "ids": [770, 711],
        "filename": "nicky-francis.jpg",
        "content_type": "image/jpeg",
        "photo_url": "https://www.onedental.co.nz/v2/wp-content/uploads/2025/09/One-Dental-About-Dr-Nicky-Francis-v2-788x1024.jpg",
    },
]

for p in practitioners:
    print(f"\n--- {p['filename']} ---")

    r = requests.get(p["photo_url"], headers=HEADERS_DL, timeout=30, verify=False)
    print(f"  Download: {r.status_code}, {len(r.content)} bytes")
    if r.status_code != 200:
        print("  SKIP — download failed")
        continue

    file_path = f"practitioners/{p['filename']}"
    up = requests.post(
        f"{SUPABASE_URL}/storage/v1/object/{BUCKET}/{file_path}",
        headers={"Authorization": f"Bearer {SUPABASE_JWT}", "Content-Type": p["content_type"], "x-upsert": "true"},
        data=r.content,
        timeout=30,
        verify=False,
    )
    print(f"  Upload: {up.status_code}")

    public_url = f"{SUPABASE_URL}/storage/v1/object/public/{BUCKET}/{file_path}"
    ids_list = ", ".join(str(i) for i in p["ids"])
    sql = f"UPDATE clinic_practitioners SET photo_url = '{public_url}' WHERE id IN ({ids_list});"
    resp = requests.post(
        "https://api.supabase.com/v1/projects/ankyjpgcocsvvtyyymys/database/query",
        headers={"Authorization": f"Bearer {MGMT_KEY}", "Content-Type": "application/json"},
        json={"query": sql},
        timeout=30,
        verify=False,
    )
    print(f"  DB update: {resp.status_code}")

print("\nDone.")
