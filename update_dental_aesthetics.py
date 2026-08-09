import requests, sys, io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
from dotenv import load_dotenv
import os
load_dotenv(r'c:\Users\Ciaran\Desktop\Dental_Directory\.env')
MGMT_KEY = os.environ['SUPABASE_MANAGEMENT_KEY']
SUPABASE_URL = os.environ['SUPABASE_URL']
JWT = os.environ['SUPABASE_JWT']
BUCKET = f'{SUPABASE_URL}/storage/v1/object/public/practitioner-photos/practitioners'

HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36',
    'Accept': 'text/html,application/xhtml+xml,*/*;q=0.8',
}

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

BASE = 'https://www.dentalaesthetics.co.nz'

# 1. Clinic — fix website URL + add description
desc = "A full-service dental laboratory based in Nelson, with over 15 years of experience. Combines traditional craftsmanship with advanced digital technology to deliver restorations of exceptional quality and precision for dentists across New Zealand. Services include implants, All-on-X, crowns and bridges, CAD/CAM design, shade matching, clear aligners, nightguards, and surgical guides."
print(q(f"""UPDATE dental_clinics
    SET website = '{BASE}/',
        description = $${desc}$$
    WHERE id = 1655 RETURNING id"""))

# 2. Clinic photo
print('\nClinic photo:')
clinic_photo = upload(f'{BASE}/wp-content/uploads/2025/10/aboutimg.png', 'dental-aesthetics-nelson-clinic')
if clinic_photo:
    print(q(f"UPDATE dental_clinics SET photo_url = '{clinic_photo}' WHERE id = 1655 RETURNING id"))

# 3. Team photos — team1 + team2 appear in order on the page alongside bios
# Order on page: Sanya Shabnam (id 712), Hadrien Loubat (id 713), Ingo Haan (id 714)
print('\nteam1 photo:')
t1 = upload(f'{BASE}/wp-content/uploads/2025/11/team1.webp', 'sanya-shabnam-dental-aesthetics')
if t1:
    print(q(f"UPDATE clinic_practitioners SET photo_url = '{t1}' WHERE id = 712 RETURNING id, name"))

print('\nteam2 photo:')
t2 = upload(f'{BASE}/wp-content/uploads/2025/11/team2.webp', 'hadrien-loubat-dental-aesthetics')
if t2:
    print(q(f"UPDATE clinic_practitioners SET photo_url = '{t2}' WHERE id = 713 RETURNING id, name"))

print('\nDone.')
