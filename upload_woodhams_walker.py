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

SOURCE = 'https://woodhamsandwalker.co.nz/our-team/'
BASE = 'https://woodhamsandwalker.co.nz/wp-content/uploads/2024/04'

team = [
    {
        'id': 1409,
        'name': 'Dr Humphrey Walker',
        'gender': 'M',
        'specialties': 'Dentist',
        'experience': None,
        'bio': "Humphrey is a highly experienced dentist with 30 years of practice. He brings a methodical, meticulous, and detail-oriented approach, and values the long-term relationships he has with his patients. Humphrey has spent most of his life in Havelock North and has been practising in Hawke's Bay for 25 years. Outside of dentistry he enjoys fishing, gardening, clay target shooting, and getting outdoors with his two dogs.",
        'photo_url': f'{BASE}/CP27202-Edit_grey-BG-scaled.jpg',
        'filename': 'humphrey-walker-woodhams-walker',
    },
    {
        'id': 1411,
        'name': 'Mackenzie',
        'gender': 'F',
        'specialties': 'Dental Assistant',
        'experience': None,
        'bio': 'Mackenzie joined the team in February 2023 and has developed into a wonderful dental assistant. She is passionate about patient care and widening her knowledge. Outside of work she enjoys spending time outdoors with her dog and quality time with family and friends.',
        'photo_url': f'{BASE}/CP27217-Edit-Edit_grey-BG-scaled.jpg',
        'filename': 'mackenzie-woodhams-walker',
    },
    {
        'id': 1410,
        'name': 'Kate Fairweather',
        'gender': 'F',
        'specialties': 'Oral Health Therapist',
        'experience': None,
        'bio': 'Kate is an oral health therapist with 11 years of experience, passionate about promoting optimal oral hygiene and dental wellness. She is dedicated to providing exceptional care with a focus on hygiene treatment, prevention, and maintenance. Outside of work, Kate lives on a farm with her husband, three boys, and two dogs, and enjoys reading, yoga, Pilates, painting, and music.',
        'photo_url': f'{BASE}/CP20302-Edit_grey-BG-scaled.jpg',
        'filename': 'kate-fairweather-woodhams-walker',
    },
    {
        'id': 1412,
        'name': 'Annalysa',
        'gender': 'F',
        'specialties': 'Dental Administrator',
        'experience': None,
        'bio': 'The friendly face of Woodhams & Walker\'s dental administration. An avid reader who enjoys quality time with family and her cat.',
        'photo_url': f'{BASE}/CP20252-Edit_grey-BG-scaled.jpg',
        'filename': 'annalysa-woodhams-walker',
    },
]

for p in team:
    print(f'\n{p["name"]}')
    photo_url = upload_photo(p['photo_url'], p['filename'])
    photo_val = f"'{photo_url}'" if photo_url else 'NULL'
    exp_val = f"$${p['experience']}$$" if p['experience'] else 'NULL'
    sql = f"""
        UPDATE clinic_practitioners SET
            gender = '{p['gender']}',
            specialties = $${p['specialties']}$$,
            experience = {exp_val},
            bio = $${p['bio']}$$,
            photo_url = {photo_val},
            source_url = '{SOURCE}'
        WHERE id = {p['id']}
    """
    res = q(sql)
    print(f'  Updated: {res}')

print('\nFinal list:')
rows = q('SELECT name, specialties, photo_url IS NOT NULL as has_photo FROM clinic_practitioners WHERE clinic_id = 1518 ORDER BY id')
for r in rows: print(r)
