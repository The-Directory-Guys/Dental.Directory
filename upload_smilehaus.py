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

SOURCE = 'https://smilehaus.nz/'

team = [
    {
        'id': 1394,
        'name': 'Dr. Wynton',
        'gender': 'M',
        'specialties': 'Principal Dentist',
        'bio': 'His calm and gentle nature combined with complete attention to detail will leave you feeling reassured and at ease. Special interest in cosmetic smile enhancement.',
        'photo_url': 'https://smilehaus.nz/wp-content/uploads/2015/10/7R31038_0669_SmileHaus_24.jpg',
        'filename': 'dr-wynton-smilehaus',
    },
    {
        'id': 1395,
        'name': 'Dr. Josh',
        'gender': 'M',
        'specialties': 'Associate Dentist',
        'bio': 'Practises client-centred dentistry with an empathetic approach, giving 100% to helping patients achieve complete dental health.',
        'photo_url': 'https://smilehaus.nz/wp-content/uploads/2015/10/7R30928_0669_SmileHaus_24.jpg',
        'filename': 'dr-josh-smilehaus',
    },
    {
        'id': 1396,
        'name': 'Dr. Therese',
        'gender': 'F',
        'specialties': 'Associate Dentist',
        'bio': 'Focused on meeting each patient\'s individual needs with gentle, optimal care.',
        'photo_url': 'https://smilehaus.nz/wp-content/uploads/2015/10/home-of-happy-smiles-3.jpg',
        'filename': 'dr-therese-smilehaus',
    },
    {
        'id': 1397,
        'name': 'Rachel',
        'gender': 'F',
        'specialties': 'Dental Hygienist',
        'bio': 'Passionate about oral health and loves to help patients achieve a disease-free mouth. Offers whitening and periodontal treatment services.',
        'photo_url': 'https://smilehaus.nz/wp-content/uploads/2015/10/7R30978_0669_SmileHaus_24.jpg',
        'filename': 'rachel-smilehaus',
    },
    {
        'id': 1398,
        'name': 'Kim',
        'gender': 'F',
        'specialties': 'Dental Hygienist',
        'bio': 'Excels at making smiles bright with a welcoming demeanour and many satisfied clients.',
        'photo_url': 'https://smilehaus.nz/wp-content/uploads/2015/10/7R30942_0669_SmileHaus_24.jpg',
        'filename': 'kim-smilehaus',
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
            bio = $${p['bio']}$$,
            photo_url = {photo_val},
            source_url = '{SOURCE}'
        WHERE id = {p['id']}
    """
    res = q(sql)
    print(f'  Updated: {res}')

print('\nFinal list:')
rows = q('SELECT name, specialties, photo_url IS NOT NULL as has_photo FROM clinic_practitioners WHERE clinic_id = 1536 ORDER BY id')
for r in rows:
    print(r)
