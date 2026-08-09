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

CLINIC_ID = 1533
SOURCE = 'https://parksidedental.co.nz/our-team/'

# Existing dentists — update with photo, bio, experience, gender
dentists = [
    {
        'id': 1373,
        'name': 'Kris Sweetapple',
        'gender': 'M',
        'experience': 'BDS Otago, FRACDS (GDP)',
        'bio': 'Clinical Director of Hospital Dentistry at Hawke\'s Bay Hospital. Passionate about oral surgery and improving patient oral health through quality, evidence-based care. Recipient of the 2023 New Zealand Dental Association\'s Outstanding Young Dentist award.',
        'photo_url': 'https://parksidedental.co.nz/wp-content/uploads/kris-sweetapple-dentist-parkside-dental.png',
        'filename': 'kris-sweetapple-parkside-dental',
    },
    {
        'id': 1374,
        'name': 'Taryn Yew',
        'gender': 'F',
        'experience': 'BDS Otago',
        'bio': 'Fluent in Mandarin and English. Her talents particularly shine in cosmetic dentistry, where she expertly combines artistry and technical expertise. Enjoys biking, cooking, and exploring New Zealand.',
        'photo_url': 'https://parksidedental.co.nz/wp-content/uploads/taryn-yew-dentist-parkside-dental.png',
        'filename': 'taryn-yew-parkside-dental',
    },
    {
        'id': 1375,
        'name': 'Zinah Awbi',
        'gender': 'F',
        'experience': 'BDS (Hons) Otago',
        'bio': 'Graduated with First Class Honours. Committed to providing patient-centred care, ensuring every visit is as comfortable and stress-free as possible.',
        'photo_url': 'https://parksidedental.co.nz/wp-content/uploads/ed00f825-1b0c-4a90-a702-41d55e034db2-3-removebg-preview.png',
        'filename': 'zinah-awbi-parkside-dental',
    },
    {
        'id': 1376,
        'name': 'Jason Lee',
        'gender': 'M',
        'experience': 'BDS (Hons) Otago',
        'bio': 'Special interest in minimally invasive adhesive dentistry and biomimetic techniques. Focuses on patient education and informed decision-making.',
        'photo_url': 'https://parksidedental.co.nz/wp-content/uploads/065ee6ba-678b-442d-a430-a24df854b0d3-3-removebg-preview.png',
        'filename': 'jason-lee-parkside-dental',
    },
    {
        'id': 1377,
        'name': 'Riku Koyama',
        'gender': 'M',
        'experience': 'BDS Otago',
        'bio': 'Active in the New Zealand Dental Association\'s Sustainability Working Group. Passionate about preventative dentistry and personalised patient care.',
        'photo_url': 'https://parksidedental.co.nz/wp-content/uploads/Riku-Koyama-1.png',
        'filename': 'riku-koyama-parkside-dental',
    },
]

# New support staff — insert
support = [
    {
        'name': 'Hannah Buckman',
        'gender': 'F',
        'specialties': 'Practice Manager',
        'bio': 'Returned to Napier after six years in Japan. Committed to maintaining quality care standards and positive patient experiences.',
        'photo_url': 'https://parksidedental.co.nz/wp-content/uploads/Hannah-Practice-Manager.jpg',
        'filename': 'hannah-buckman-parkside-dental',
    },
    {
        'name': 'Rose Siron',
        'gender': 'F',
        'specialties': 'Clinical Manager & Dental Assistant',
        'bio': 'Originally from the Northern Philippines. Finds fulfilment in her dual role helping patients improve their oral health.',
        'photo_url': 'https://parksidedental.co.nz/wp-content/uploads/Rose-Dental-Assistant.jpg',
        'filename': 'rose-siron-parkside-dental',
    },
    {
        'name': 'Rosie Cornish',
        'gender': 'F',
        'specialties': 'Dental Assistant',
        'bio': 'Hawke\'s Bay native. Finds fulfilment in helping patients improve their confidence and achieve their best smiles.',
        'photo_url': 'https://parksidedental.co.nz/wp-content/uploads/Rosie-Dental-Assistant.jpg',
        'filename': 'rosie-cornish-parkside-dental',
    },
    {
        'name': 'Pam Versoza',
        'gender': 'F',
        'specialties': 'Dental Assistant',
        'bio': 'Relocated from the Philippines. Avid photographer and explorer, passionate about patient comfort and oral health education.',
        'photo_url': 'https://parksidedental.co.nz/wp-content/uploads/Pam-Dental-Assistant.jpg',
        'filename': 'pam-versoza-parkside-dental',
    },
    {
        'name': 'Jasmine Baxter',
        'gender': 'F',
        'specialties': 'Receptionist & Dental Assistant',
        'bio': 'Local Hawke\'s Bay resident who excels in her dual role as receptionist and dental assistant, supporting positive patient experiences.',
        'photo_url': 'https://parksidedental.co.nz/wp-content/uploads/Jasmine-Receptionist.jpg',
        'filename': 'jasmine-baxter-parkside-dental',
    },
]

# Update existing dentists
print('Updating dentists...')
for p in dentists:
    print(f'\n{p["name"]}')
    photo_url = upload_photo(p['photo_url'], p['filename'])
    photo_val = f"'{photo_url}'" if photo_url else 'NULL'
    sql = f"""
        UPDATE clinic_practitioners SET
            gender = '{p['gender']}',
            experience = $${p['experience']}$$,
            bio = $${p['bio']}$$,
            photo_url = {photo_val},
            source_url = '{SOURCE}'
        WHERE id = {p['id']}
    """
    res = q(sql)
    print(f'  Updated: {res}')

# Insert support staff
print('\nInserting support staff...')
existing = {r['name'].lower() for r in q(f'SELECT name FROM clinic_practitioners WHERE clinic_id = {CLINIC_ID}')}
for p in support:
    if p['name'].lower() in existing:
        print(f'  Skipping (exists): {p["name"]}')
        continue
    print(f'\n{p["name"]}')
    photo_url = upload_photo(p['photo_url'], p['filename'])
    photo_val = f"'{photo_url}'" if photo_url else 'NULL'
    sql = f"""
        INSERT INTO clinic_practitioners (clinic_id, name, gender, specialties, bio, photo_url, source_url)
        VALUES ({CLINIC_ID}, $${p['name']}$$, '{p['gender']}', $${p['specialties']}$$, $${p['bio']}$$, {photo_val}, '{SOURCE}')
    """
    res = q(sql)
    print(f'  Inserted: {res}')

print('\nFinal list:')
rows = q(f'SELECT name, specialties, experience, photo_url IS NOT NULL as has_photo FROM clinic_practitioners WHERE clinic_id = {CLINIC_ID} ORDER BY id')
for r in rows:
    print(r)
