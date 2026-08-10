import requests, os
from dotenv import load_dotenv
load_dotenv(r'c:\Users\Ciaran\Desktop\Dental_Directory\.env')
MGMT = os.environ['SUPABASE_MANAGEMENT_KEY']

def q(sql):
    r = requests.post('https://api.supabase.com/v1/projects/ankyjpgcocsvvtyyymys/database/query',
        headers={'Authorization': f'Bearer {MGMT}', 'Content-Type': 'application/json'},
        json={'query': sql}, verify=False)
    return r.json()

rows = q("SELECT id, name, category, services FROM dental_clinics WHERE name ILIKE '%spotless white%'")
print('Before:', rows)

for r in rows:
    print(q(f"UPDATE dental_clinics SET category = 'teeth_whitening', services = 'Teeth Whitening' WHERE id = {r['id']} RETURNING id, name, category, services"))
