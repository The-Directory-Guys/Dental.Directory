import json
import csv
import requests
import os
from dotenv import load_dotenv

load_dotenv(r"c:\Users\Ciaran\Desktop\Dental_Directory\.env")
MGMT_KEY = os.environ["SUPABASE_MANAGEMENT_KEY"]

done_ids = set()
for fname in ["outscraper_progress.json", "outscraper_progress_batch2.json",
              "outscraper_progress_batch3.json", "outscraper_progress_batch4.json",
              "outscraper_progress_batch5.json"]:
    path = os.path.join(r"c:\Users\Ciaran\Desktop\Dental_Directory", fname)
    with open(path) as f:
        data = json.load(f)
    done_ids.update(data.get("done_ids", []))

print(f"Already done: {len(done_ids)} clinics")

id_list = ",".join(str(i) for i in sorted(done_ids))
query = f"SELECT id, name, google_maps_url FROM dental_clinics WHERE id NOT IN ({id_list}) AND google_maps_url IS NOT NULL ORDER BY id;"

r = requests.post(
    "https://api.supabase.com/v1/projects/ankyjpgcocsvvtyyymys/database/query",
    headers={"Authorization": f"Bearer {MGMT_KEY}", "Content-Type": "application/json"},
    json={"query": query},
    timeout=30,
)
clinics = r.json()
print(f"Fetched {len(clinics)} clinics for batch 6")

csv_path = r"c:\Users\Ciaran\Desktop\Dental_Directory\outscraper_batch6.csv"
with open(csv_path, "w", newline="", encoding="utf-8-sig") as f:
    writer = csv.DictWriter(f, fieldnames=["clinic_id", "name", "google_maps_url"])
    writer.writeheader()
    for c in clinics:
        writer.writerow({"clinic_id": c["id"], "name": c["name"], "google_maps_url": c["google_maps_url"]})

print(f"Written to {csv_path}")
