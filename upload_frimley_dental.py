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
        content_type = {'jpg': 'image/jpeg', 'jpeg': 'image/jpeg', 'png': 'image/png', 'webp': 'image/webp'}.get(ext, 'image/jpeg')
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

print('Diane Rowe')
photo_url = upload_photo(
    'https://static.wixstatic.com/media/4af9af_e07f062679f543468cf05fb95e0edd0e~mv2.jpg',
    'diane-rowe-frimley-dental'
)
photo_val = f"'{photo_url}'" if photo_url else 'NULL'

sql = f"""
    UPDATE clinic_practitioners SET
        gender = 'F',
        specialties = $$Principal Dentist$$,
        experience = $$BDS Otago$$,
        bio = $$Diane graduated from Otago University in 1992. She worked in Wairoa before moving to Auckland, where she owned practices in Papakura and Mt Eden. In 2019 she and her family relocated to Hawke's Bay, fulfilling a long-held dream. Diane enjoys all aspects of general dentistry and loves building long-term relationships with her clients. Quality care is always her primary focus.$$,
        photo_url = {photo_val},
        source_url = 'https://www.frimleydental.co.nz/'
    WHERE id = 1393
"""
res = q(sql)
print(f'  Updated: {res}')

print('\nFinal:')
rows = q('SELECT name, specialties, experience, photo_url IS NOT NULL as has_photo FROM clinic_practitioners WHERE clinic_id = 1514')
for r in rows: print(r)
