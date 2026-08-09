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

SOURCE = 'https://www.pearlofahuriri.co.nz/ourteam'

team = [
    {
        'id': 1406,
        'name': 'Dr Martin Langford',
        'gender': 'M',
        'specialties': 'Dental Surgeon',
        'experience': 'BDS',
        'bio': "Originally from the UK, Martin has been a dental surgeon for over 30 years, with experience in NHS hospitals, the Royal Air Force, and private practice in New Zealand. He was on the board of a Hawke's Bay medical and dental trust for 15 years. Provides all aspects of general dental treatment including examinations, restorations, extractions, root canal therapy, and whitening.",
        'photo_url': 'https://images.squarespace-cdn.com/content/v1/619d626a4012a442c7c164c6/cd6018c8-2f2f-40a1-bb96-f928373bf801/IMG_0013.JPG',
        'filename': 'martin-langford-pearl-of-ahuriri',
    },
    {
        'id': 1407,
        'name': 'Dr Josh Stening',
        'gender': 'M',
        'specialties': 'Dental Surgeon',
        'experience': 'BDS Otago',
        'bio': 'A University of Otago graduate with a genuine passion for dentistry. Skilled at making patients feel at ease regardless of dental anxieties, Josh takes the time to explain all your options and strives for excellence in dental health, function, and aesthetics. Outside the practice he enjoys tennis and walks in the Hawke\'s Bay sun.',
        'photo_url': 'https://images.squarespace-cdn.com/content/v1/619d626a4012a442c7c164c6/bff9e64a-d6fb-4b84-b449-7167f851a076/20240916_143315.jpg',
        'filename': 'josh-stening-pearl-of-ahuriri',
    },
]

for p in team:
    print(f'\n{p["name"]}')
    photo_url = upload_photo(p['photo_url'], p['filename'])
    photo_val = f"'{photo_url}'" if photo_url else 'NULL'
    sql = f"""
        UPDATE clinic_practitioners SET
            gender = '{p['gender']}',
            specialties = $${p['specialties']}$$,
            experience = $${p['experience']}$$,
            bio = $${p['bio']}$$,
            photo_url = {photo_val},
            source_url = '{SOURCE}'
        WHERE id = {p['id']}
    """
    res = q(sql)
    print(f'  Updated: {res}')

print('\nFinal list:')
rows = q('SELECT name, specialties, experience, photo_url IS NOT NULL as has_photo FROM clinic_practitioners WHERE clinic_id = 1535 ORDER BY id')
for r in rows: print(r)
