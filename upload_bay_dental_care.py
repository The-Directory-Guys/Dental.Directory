import sys, io, re
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
    """Download photo and upload to Supabase storage."""
    try:
        resp = requests.get(img_url, timeout=15, verify=False,
            headers={'User-Agent': 'Mozilla/5.0'})
        if not resp.ok:
            print(f'  Download failed {resp.status_code}: {img_url}')
            return None
        ext = img_url.split('.')[-1].split('?')[0].lower()
        fname = f'{filename}.{ext}'
        content_type = {
            'webp': 'image/webp', 'jpg': 'image/jpeg',
            'jpeg': 'image/jpeg', 'png': 'image/png', 'avif': 'image/avif',
        }.get(ext, 'image/jpeg')
        up = requests.post(
            f'{SUPABASE_URL}/storage/v1/object/practitioner-photos/practitioners/{fname}',
            headers={
                'Authorization': f'Bearer {STORAGE_JWT}',
                'Content-Type': content_type,
                'x-upsert': 'true',
            },
            data=resp.content, timeout=30, verify=False)
        if up.ok or up.status_code == 200:
            url = f'{BUCKET_BASE}/{fname}'
            print(f'  Uploaded: {fname}')
            return url
        else:
            print(f'  Upload failed {up.status_code}: {up.text[:100]}')
            return None
    except Exception as e:
        print(f'  Error: {e}')
        return None

CLINIC_ID = 1499
SOURCE = 'https://baydentalcare.nz/the-people/'

team = [
    {
        'name': 'Dr Nicholas Cutfield',
        'gender': 'M',
        'specialties': 'Principal Dentist & Owner',
        'experience': 'BSc BDS',
        'bio': 'Nick is the lead dentist and owner of Bay Dental Care. In general practice since 2012, he also worked with Hawke\'s Bay Hospital\'s maxillofacial department. He prioritises continuing education and specialises in digital dentistry, practising patient-centred care. Enjoys motorsport, cooking, and fitness.',
        'photo_url': 'https://baydentalcare.nz/wp-content/uploads/2023/02/nicholas-cutfield-bay-dental-Dentist-hastings-640x1024.webp',
        'filename': 'nicholas-cutfield-bay-dental-care',
    },
    {
        'name': 'Kelly Cutfield',
        'gender': 'F',
        'specialties': 'Skin Therapist',
        'experience': None,
        'bio': 'An aesthetician with nearly 20 years of experience who founded Muse Skin in 2018. She provides medical-grade skin treatments using ZO Skin Health products and collaborates with Dr Nick on combined treatments.',
        'photo_url': 'https://baydentalcare.nz/wp-content/uploads/2020/07/KELLY.webp',
        'filename': 'kelly-cutfield-bay-dental-care',
    },
    {
        'name': 'Bridget Rattray',
        'gender': 'F',
        'specialties': 'Dental Hygienist',
        'experience': 'BHSc (Oral Health)',
        'bio': 'Passionate about clean teeth and gums, Bridget is known for her gentle technique and sense of humour. She uses EMS Airflow technology and brings joyous energy to the clinic. A Hastings local with husband and two children.',
        'photo_url': 'https://baydentalcare.nz/wp-content/uploads/2023/02/bridget-rattray-bay-dentist-hastings-640x1024.webp',
        'filename': 'bridget-rattray-bay-dental-care',
    },
    {
        'name': 'Jay Jesani',
        'gender': 'M',
        'specialties': 'Dentist',
        'experience': None,
        'bio': 'Originally from Leeds, Jay has over 10 years of experience in Hawke\'s Bay. Enjoys travelling, quality food, and wine.',
        'photo_url': 'https://baydentalcare.nz/wp-content/uploads/2026/06/Jay4-683x1024.avif',
        'filename': 'jay-jesani-bay-dental-care',
    },
    {
        'name': 'Caroline Cash',
        'gender': 'F',
        'specialties': 'Surgical & Clinical Assistant',
        'experience': None,
        'bio': 'Caroline brings extensive dental experience and can assist with virtually every procedure. A Hastings local who loves her job due to the patient focus, and enjoys outdoor activities and socialising.',
        'photo_url': 'https://baydentalcare.nz/wp-content/uploads/2023/02/caroline-cash-bay-dentist-hastings-640x1024.webp',
        'filename': 'caroline-cash-bay-dental-care',
    },
    {
        'name': 'Maddy Clarke',
        'gender': 'F',
        'specialties': 'Treatment Coordinator & Clinical Assistant',
        'experience': None,
        'bio': 'Top student nationally in her NZDA dental assisting certification. Dependable and trustworthy, Maddy applies her skills daily and is passionate about her role and animals.',
        'photo_url': 'https://baydentalcare.nz/wp-content/uploads/2023/03/Maddy-Clarke-bay-dentist-in-hastings-683x1024.webp',
        'filename': 'maddy-clarke-bay-dental-care',
    },
]

# Check existing
existing = q(f'SELECT id, name FROM clinic_practitioners WHERE clinic_id = {CLINIC_ID}')
existing_map = {r['name'].lower(): r['id'] for r in existing}
print(f'Existing practitioners: {len(existing)}')

for p in team:
    print(f'\n{p["name"]}')
    photo_url = upload_photo(p['photo_url'], p['filename'])
    exp_val = f"$${p['experience']}$$" if p['experience'] else 'NULL'
    photo_val = f"'{photo_url}'" if photo_url else 'NULL'

    if p['name'].lower() in existing_map:
        # Update existing record
        pid = existing_map[p['name'].lower()]
        sql = f"""
            UPDATE clinic_practitioners SET
                gender = '{p['gender']}',
                specialties = $${p['specialties']}$$,
                experience = {exp_val},
                bio = $${p['bio']}$$,
                photo_url = {photo_val},
                source_url = '{SOURCE}'
            WHERE id = {pid}
        """
        res = q(sql)
        print(f'  Updated id {pid}: {res}')
    else:
        sql = f"""
            INSERT INTO clinic_practitioners
                (clinic_id, name, gender, specialties, experience, bio, photo_url, source_url)
            VALUES (
                {CLINIC_ID},
                $${p['name']}$$,
                '{p['gender']}',
                $${p['specialties']}$$,
                {exp_val},
                $${p['bio']}$$,
                {photo_val},
                '{SOURCE}'
            )
        """
        res = q(sql)
        print(f'  Inserted: {res}')

print('\nDone. Final list:')
rows = q(f'SELECT name, specialties, photo_url IS NOT NULL as has_photo FROM clinic_practitioners WHERE clinic_id = {CLINIC_ID} ORDER BY id')
for r in rows:
    print(r)
