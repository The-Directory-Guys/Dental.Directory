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

# Upload photo
img_url = 'https://images.squarespace-cdn.com/content/v1/69c5c1ca49199f1b264f5f10/1561a90b-979e-4d25-b9e7-b4dea0ba5dd9/Todd+photo.jpg'
r = requests.get(img_url, timeout=20, verify=False, headers={'User-Agent': 'Mozilla/5.0'})
print(f'Download: {r.status_code}, {len(r.content)} bytes')
up = requests.post(f'{SUPABASE_URL}/storage/v1/object/practitioner-photos/practitioners/todd-gracia-waimea-dental.jpg',
    headers={'Authorization': f'Bearer {JWT}', 'Content-Type': 'image/jpeg', 'x-upsert': 'true'},
    data=r.content, timeout=30, verify=False)
print(f'Upload: {up.status_code}')
photo_url = f'{BUCKET}/todd-gracia-waimea-dental.jpg'

bio = "Specialist endodontist providing advanced diagnosis and management of dental pain and endodontic conditions. Trusted by referring dentists across Nelson, Richmond and Tasman for complex and difficult cases. Manages both routine and complex cases, including unclear pain and teeth that have not responded as expected to previous treatment. Accepts referrals from dentists as well as self-referrals."

print(q(f"""UPDATE clinic_practitioners
    SET experience = 'BDS, MDSc, MRACDS',
        specialties = 'Endodontics, root canal treatment, endodontic retreatment, dental pain diagnosis, cracked teeth, dental trauma',
        bio = $${bio}$$,
        photo_url = '{photo_url}',
        source_url = 'https://www.waimeadental.co.nz/endodontist-nelson-richmond'
    WHERE id = 675 RETURNING id, name"""))

print('Done.')
