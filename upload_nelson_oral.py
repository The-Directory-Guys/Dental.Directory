import requests, sys, io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
from dotenv import load_dotenv
import os
load_dotenv(r'c:\Users\Ciaran\Desktop\Dental_Directory\.env')
MGMT_KEY = os.environ['SUPABASE_MANAGEMENT_KEY']
SUPABASE_URL = os.environ['SUPABASE_URL']
JWT = os.environ['SUPABASE_JWT']
BUCKET = f'{SUPABASE_URL}/storage/v1/object/public/practitioner-photos/practitioners'

def q(sql):
    r = requests.post('https://api.supabase.com/v1/projects/ankyjpgcocsvvtyyymys/database/query',
        headers={'Authorization': f'Bearer {MGMT_KEY}', 'Content-Type': 'application/json'},
        json={'query': sql}, verify=False)
    return r.json()

rows = q("SELECT id, name FROM dental_clinics WHERE name ILIKE '%nelson oral%'")
print(rows)
cid = rows[0]['id']

r = requests.get('https://www.nelsonoralsurgery.co.nz/images/main-img.jpg',
    timeout=20, verify=False, headers={'User-Agent': 'Mozilla/5.0'})
print(f'Download: {r.status_code}, {len(r.content)} bytes')

up = requests.post(f'{SUPABASE_URL}/storage/v1/object/practitioner-photos/practitioners/nelson-oral-surgery-clinic.jpg',
    headers={'Authorization': f'Bearer {JWT}', 'Content-Type': 'image/jpeg', 'x-upsert': 'true'},
    data=r.content, timeout=30, verify=False)
print(f'Upload: {up.status_code}')

photo_url = f'{BUCKET}/nelson-oral-surgery-clinic.jpg'
print(q(f"UPDATE dental_clinics SET photo_url = '{photo_url}' WHERE id = {cid} RETURNING id, name, photo_url"))
