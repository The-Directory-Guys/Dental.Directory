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
    "Referer": "https://www.nelsonortho.nz/",
}

# ids: (Richmond 1674, Nelson 2403)
practitioners = [
    {
        "ids": [747, 772],
        "filename": "andrew-lush.jpg",
        "photo_url": "https://images.squarespace-cdn.com/content/v1/593f16e8ff7c50ca377498a2/1566430986401-STGJ16QFKAK57XKFQX9T/190623_Gusto_NelsonOrthodontics_Photos_Tim_0860.jpg",
    },
    {
        "ids": [748, 773],
        "filename": "ana-low.jpg",
        "photo_url": "https://images.squarespace-cdn.com/content/v1/593f16e8ff7c50ca377498a2/1565929184903-YAWS96V787S9UQ2XNYEE/190623_Gusto_NelsonOrthodontics_Photos_Tim_0834.jpg",
    },
    {
        "ids": [749, 774],
        "filename": "andrew-marriott.jpg",
        "photo_url": "https://images.squarespace-cdn.com/content/v1/593f16e8ff7c50ca377498a2/1566431026709-EGOM2GYNI0QB9NPB6G4U/190623_Gusto_NelsonOrthodontics_Photos_Tim_0849.jpg",
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
        headers={"Authorization": f"Bearer {SUPABASE_JWT}", "Content-Type": "image/jpeg", "x-upsert": "true"},
        data=r.content, timeout=30, verify=False,
    )
    print(f"  Upload: {up.status_code}")

    public_url = f"{SUPABASE_URL}/storage/v1/object/public/{BUCKET}/{file_path}"
    ids_list = ", ".join(str(i) for i in p["ids"])
    resp = requests.post(
        "https://api.supabase.com/v1/projects/ankyjpgcocsvvtyyymys/database/query",
        headers={"Authorization": f"Bearer {MGMT_KEY}", "Content-Type": "application/json"},
        json={"query": f"UPDATE clinic_practitioners SET photo_url = '{public_url}' WHERE id IN ({ids_list});"},
        timeout=30, verify=False,
    )
    print(f"  DB: {resp.status_code}")

print("\nDone.")
