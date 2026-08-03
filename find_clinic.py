import sys, io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

import requests, os
from dotenv import load_dotenv
load_dotenv(r"c:\Users\Ciaran\Desktop\Dental_Directory\.env")
MGMT_KEY = os.environ["SUPABASE_MANAGEMENT_KEY"]

def q(sql):
    r = requests.post("https://api.supabase.com/v1/projects/ankyjpgcocsvvtyyymys/database/query",
        headers={"Authorization": f"Bearer {MGMT_KEY}", "Content-Type": "application/json"},
        json={"query": sql}, timeout=30, verify=False)
    return r.json()

row = q("SELECT description FROM dental_clinics WHERE id = 1509")
print(row[0]['description'][:200])
