import requests, sys, io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
from dotenv import load_dotenv
import os
load_dotenv(r'c:\Users\Ciaran\Desktop\Dental_Directory\.env')
MGMT_KEY = os.environ['SUPABASE_MANAGEMENT_KEY']
SUPABASE_URL = os.environ['SUPABASE_URL']
JWT = os.environ['SUPABASE_JWT']
BUCKET = f'{SUPABASE_URL}/storage/v1/object/public/practitioner-photos/practitioners'

HEADERS = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36'}

def q(sql):
    r = requests.post('https://api.supabase.com/v1/projects/ankyjpgcocsvvtyyymys/database/query',
        headers={'Authorization': f'Bearer {MGMT_KEY}', 'Content-Type': 'application/json'},
        json={'query': sql}, verify=False)
    return r.json()

def upload(img_url, slug):
    r = requests.get(img_url, timeout=20, verify=False, headers=HEADERS)
    if not r.ok: print(f'  Download failed {r.status_code}'); return None
    ext = img_url.split('?')[0].split('.')[-1].lower()
    if ext not in ('jpg','jpeg','png','webp'): ext = 'jpg'
    ct = {'jpg':'image/jpeg','jpeg':'image/jpeg','png':'image/png','webp':'image/webp'}.get(ext,'image/jpeg')
    fname = f'{slug}.{ext}'
    up = requests.post(f'{SUPABASE_URL}/storage/v1/object/practitioner-photos/practitioners/{fname}',
        headers={'Authorization': f'Bearer {JWT}', 'Content-Type': ct, 'x-upsert': 'true'},
        data=r.content, timeout=30, verify=False)
    if up.ok: print(f'  Uploaded {fname}'); return f'{BUCKET}/{fname}'
    print(f'  Upload failed: {up.text[:80]}'); return None

BASE = 'https://www.dentalaesthetics.co.nz/wp-content/uploads/2025/11'

photos = [
    (714, 'Ingo Haan',          f'{BASE}/imag-18.png',   'ingo-haan-dental-aesthetics'),
    (715, 'Marianne Miranda',   f'{BASE}/team1.webp',    'marianne-miranda-dental-aesthetics'),
    (716, 'Veronika Fitzgerald',f'{BASE}/team2.webp',    'veronika-fitzgerald-dental-aesthetics'),
    (712, 'Sanya Shabnam',      f'{BASE}/imag-23.webp',  'sanya-shabnam-dental-aesthetics'),
]

for pid, name, url, slug in photos:
    print(f'\n{name}:')
    photo = upload(url, slug)
    if photo:
        print(q(f"UPDATE clinic_practitioners SET photo_url = '{photo}' WHERE id = {pid} RETURNING id, name"))

# Clear Hadrien — no photo provided
print('\nClearing Hadrien Loubat photo (no photo provided):')
print(q("UPDATE clinic_practitioners SET photo_url = NULL WHERE id = 713 RETURNING id, name"))

print('\nDone.')
