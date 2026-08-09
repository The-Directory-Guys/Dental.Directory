import requests, os
from dotenv import load_dotenv
load_dotenv(r'c:\Users\Ciaran\Desktop\Dental_Directory\.env')
MGMT_KEY = os.environ['SUPABASE_MANAGEMENT_KEY']

def q(sql):
    r = requests.post('https://api.supabase.com/v1/projects/ankyjpgcocsvvtyyymys/database/query',
        headers={'Authorization': f'Bearer {MGMT_KEY}', 'Content-Type': 'application/json'},
        json={'query': sql}, verify=False)
    return r.json()

# Johnsonville Dental Centre — online booking
rows = q("SELECT id, name FROM dental_clinics WHERE name ILIKE '%johnsonville dental%'")
print(rows)
if rows:
    print(q(f"UPDATE clinic_amenities SET online_booking = TRUE WHERE clinic_id = {rows[0]['id']} RETURNING clinic_id"))

# Spotless White — category
rows2 = q("SELECT id, name, category FROM dental_clinics WHERE name ILIKE '%spotless white%'")
print(rows2)
if rows2:
    print(q(f"UPDATE dental_clinics SET category = 'teeth_whitening' WHERE id = {rows2[0]['id']} RETURNING id, name, category"))
