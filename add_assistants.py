import sys, io, requests
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

URL = "https://ankyjpgcocsvvtyyymys.supabase.co/rest/v1/clinic_practitioners"
JWT = os.environ['SUPABASE_JWT']
HEADERS = {"apikey": JWT, "Authorization": f"Bearer {JWT}", "Content-Type": "application/json", "Prefer": "return=representation"}

for name in ["Shanae", "Liarna", "Siri", "Lindsay", "Maddie"]:
    r = requests.post(URL, headers=HEADERS, verify=False, json={
        "clinic_id": 1679,
        "name": name,
        "gender": "F",
        "specialties": "Dental Assistant",
        "source_url": "https://www.stephwillsdental.co.nz/our-team"
    })
    d = r.json()
    print(f"{name} -> id {d[0]['id']}")
