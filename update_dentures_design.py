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

def upload(img_url, slug):
    r = requests.get(img_url, timeout=20, verify=False, headers={'User-Agent': 'Mozilla/5.0'})
    if not r.ok: print(f'  Download failed {r.status_code}'); return None
    ext = img_url.split('.')[-1].lower()
    if ext not in ('jpg','jpeg','png','webp'): ext = 'jpg'
    fname = f'{slug}.{ext}'
    ct = 'image/jpeg' if ext in ('jpg','jpeg') else 'image/png'
    up = requests.post(f'{SUPABASE_URL}/storage/v1/object/practitioner-photos/practitioners/{fname}',
        headers={'Authorization': f'Bearer {JWT}', 'Content-Type': ct, 'x-upsert': 'true'},
        data=r.content, timeout=30, verify=False)
    if up.ok: print(f'  Uploaded {fname}'); return f'{BUCKET}/{fname}'
    print(f'  Upload failed: {up.text[:80]}'); return None

# 1. Clinic — description, website HTTPS
desc = "A denture clinic based in Motueka, run by Clinical Dental Technician Felicity Hart. Offers a range of denture solutions including full denture replacements, immediate dentures, partial dentures, and free initial consultations. Open Monday to Thursday, 9am to 5pm, with appointments available outside these hours on request."
print(q(f"""UPDATE dental_clinics
    SET description = $${desc}$$,
        website = 'https://www.denturesbydesignnz.com/'
    WHERE id = 2925 RETURNING id"""))

# 2. Clinic photo (banner/hero image)
print('\nClinic photo:')
clinic_photo = upload('https://www.denturesbydesignnz.com/images/headers/slide2.jpg', 'dentures-by-design-nz-clinic')
if clinic_photo:
    print(q(f"UPDATE dental_clinics SET photo_url = '{clinic_photo}' WHERE id = 2925 RETURNING id"))

# 3. Felicity Hart photo (id 698) — hp-profile.jpg is the headshot
print('\nFelicity Hart photo:')
f_photo = upload('https://www.denturesbydesignnz.com/images/hp-profile.jpg', 'felicity-hart-dentures-by-design')
if f_photo:
    print(q(f"""UPDATE clinic_practitioners
        SET photo_url = '{f_photo}',
            experience = 'Clinical Dental Technician (Otago University), Dental and Orthodontic Technician'
        WHERE id = 698 RETURNING id, name"""))

print('\nDone.')
