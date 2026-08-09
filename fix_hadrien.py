import requests, os
from dotenv import load_dotenv
load_dotenv(r'c:\Users\Ciaran\Desktop\Dental_Directory\.env')
MGMT_KEY = os.environ['SUPABASE_MANAGEMENT_KEY']
SUPABASE_URL = os.environ['SUPABASE_URL']
JWT = os.environ['SUPABASE_JWT']
BUCKET = f'{SUPABASE_URL}/storage/v1/object/public/practitioner-photos/practitioners'

HEADERS = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36'}

r = requests.get('https://www.dentalaesthetics.co.nz/wp-content/uploads/2025/11/imag-22.webp',
    timeout=20, verify=False, headers=HEADERS)
print(f'Download: {r.status_code}, {len(r.content)} bytes')

up = requests.post(f'{SUPABASE_URL}/storage/v1/object/practitioner-photos/practitioners/hadrien-loubat-dental-aesthetics.webp',
    headers={'Authorization': f'Bearer {JWT}', 'Content-Type': 'image/webp', 'x-upsert': 'true'},
    data=r.content, timeout=30, verify=False)
print(f'Upload: {up.status_code}')

photo_url = f'{BUCKET}/hadrien-loubat-dental-aesthetics.webp'
res = requests.post('https://api.supabase.com/v1/projects/ankyjpgcocsvvtyyymys/database/query',
    headers={'Authorization': f'Bearer {MGMT_KEY}', 'Content-Type': 'application/json'},
    json={'query': f"UPDATE clinic_practitioners SET photo_url = '{photo_url}' WHERE id = 713 RETURNING id, name"},
    verify=False)
print(res.json())
