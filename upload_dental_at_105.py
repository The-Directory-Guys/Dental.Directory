import sys, io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

import requests, os
from dotenv import load_dotenv
load_dotenv(r'c:\Users\Ciaran\Desktop\Dental_Directory\.env')
MGMT_KEY = os.environ['SUPABASE_MANAGEMENT_KEY']
SUPABASE_URL = os.environ['SUPABASE_URL']
STORAGE_JWT = os.environ['SUPABASE_JWT']
BUCKET_BASE = f'{SUPABASE_URL}/storage/v1/object/public/practitioner-photos/practitioners'

def q(sql):
    r = requests.post('https://api.supabase.com/v1/projects/ankyjpgcocsvvtyyymys/database/query',
        headers={'Authorization': f'Bearer {MGMT_KEY}', 'Content-Type': 'application/json'},
        json={'query': sql}, timeout=30, verify=False)
    return r.json()

def upload_photo(img_url, filename):
    try:
        resp = requests.get(img_url, timeout=15, verify=False, headers={'User-Agent': 'Mozilla/5.0'})
        if not resp.ok:
            print(f'  Download failed {resp.status_code}')
            return None
        ext = img_url.split('.')[-1].split('?')[0].lower()
        fname = f'{filename}.{ext}'
        content_type = {'webp': 'image/webp', 'jpg': 'image/jpeg', 'jpeg': 'image/jpeg',
                        'png': 'image/png', 'avif': 'image/avif'}.get(ext, 'image/jpeg')
        up = requests.post(
            f'{SUPABASE_URL}/storage/v1/object/practitioner-photos/practitioners/{fname}',
            headers={'Authorization': f'Bearer {STORAGE_JWT}', 'Content-Type': content_type, 'x-upsert': 'true'},
            data=resp.content, timeout=30, verify=False)
        if up.ok:
            print(f'  Uploaded: {fname}')
            return f'{BUCKET_BASE}/{fname}'
        print(f'  Upload failed {up.status_code}: {up.text[:80]}')
        return None
    except Exception as e:
        print(f'  Error: {e}')
        return None

CLINIC_ID = 1510
SOURCE = 'https://dentalat105.co.nz/the-team/'

# Existing records to update
existing = [
    {
        'id': 1389,
        'name': 'Ian Rosenberg',
        'gender': 'M',
        'specialties': 'Dental Surgeon',
        'photo_url': 'https://dentalat105.co.nz/wp-content/uploads/2021/06/IMG_9088.jpg',
        'filename': 'ian-rosenberg-dental-at-105',
    },
    {
        'id': 1390,
        'name': 'Gunilla Karlson',
        'gender': 'F',
        'specialties': 'Dental Surgeon',
        'photo_url': 'https://dentalat105.co.nz/wp-content/uploads/2021/06/IMG_9066.jpg',
        'filename': 'gunilla-karlson-dental-at-105',
    },
    {
        'id': 1391,
        'name': "Bill O'Connor",
        'gender': 'M',
        'specialties': 'Dental Surgeon',
        'photo_url': None,
        'filename': None,
    },
]

# New staff to insert
new_staff = [
    {'name': 'Leah Palmer',    'gender': 'F', 'specialties': 'Practice Manager'},
    {'name': 'Kat Wong',       'gender': 'F', 'specialties': 'Dental Assistant'},
    {'name': 'Jo Crisp',       'gender': 'F', 'specialties': 'Dental Assistant'},
    {'name': 'Sian Veerkamp',  'gender': 'F', 'specialties': 'Receptionist'},
    {'name': 'Zaviah Tuinier', 'gender': 'F', 'specialties': 'Dental Assistant'},
]

print('Updating existing practitioners...')
for p in existing:
    print(f'\n{p["name"]}')
    photo_url = upload_photo(p['photo_url'], p['filename']) if p['photo_url'] else None
    photo_val = f"'{photo_url}'" if photo_url else 'NULL'
    sql = f"""
        UPDATE clinic_practitioners SET
            gender = '{p['gender']}',
            specialties = $${p['specialties']}$$,
            photo_url = {photo_val},
            source_url = '{SOURCE}'
        WHERE id = {p['id']}
    """
    res = q(sql)
    print(f'  Updated: {res}')

print('\nInserting new staff...')
current_names = {r['name'].lower() for r in q(f'SELECT name FROM clinic_practitioners WHERE clinic_id = {CLINIC_ID}')}
for p in new_staff:
    if p['name'].lower() in current_names:
        print(f'  Skipping (exists): {p["name"]}')
        continue
    print(f'\n{p["name"]}')
    sql = f"""
        INSERT INTO clinic_practitioners (clinic_id, name, gender, specialties, source_url)
        VALUES ({CLINIC_ID}, $${p['name']}$$, '{p['gender']}', $${p['specialties']}$$, '{SOURCE}')
    """
    res = q(sql)
    print(f'  Inserted: {res}')

print('\nFinal list:')
rows = q(f'SELECT name, specialties, photo_url IS NOT NULL as has_photo FROM clinic_practitioners WHERE clinic_id = {CLINIC_ID} ORDER BY id')
for r in rows:
    print(r)
