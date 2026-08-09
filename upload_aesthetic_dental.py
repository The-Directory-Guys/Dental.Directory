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
        if ext not in ('jpg', 'jpeg', 'png', 'webp'): ext = 'jpg'
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

CLINIC_ID = 1497
SOURCE = 'https://www.aestheticdental.co.nz/dental-clinic-hastings'

existing = [
    {
        'id': 1388,
        'name': 'Dr Tracey Eales',
        'gender': 'F',
        'specialties': 'Director & Dentist',
        'experience': 'BDS Otago, FRACDS',
        'bio': "Tracey has been Director of Aesthetic Dental for over 20 years. She graduated near the top of her class from Otago Dental School in 1992, then worked at Invercargill Hospital before spending 11 years in the UK, completing a fellowship with the Royal College of Surgeons. A forensic odontologist who assists police with identification cases, she serves on the NZSFO executive committee as regional coordinator for Hawke's Bay, Manawatū, and Taranaki. Committed to lifelong learning, she regularly attends international courses and conferences.",
        'photo_url': 'https://irp.cdn-website.com/5f820488/dms3rep/multi/team-img-tracey-new.jpg',
        'filename': 'tracey-eales-aesthetic-dental',
    },
]

new_staff = [
    {
        'name': 'Morgan Jenkins',
        'gender': 'F',
        'specialties': 'Oral Health Therapist',
        'experience': 'BHSc Oral Health Therapy (AUT), BSc Human Nutrition (Massey)',
        'bio': 'Morgan graduated in Oral Health Therapy at AUT in 2016, having also completed a Science degree in Human Nutrition from Massey University. She gained experience across public dental therapy services, a private orthodontic practice, and a private hygiene clinic in Auckland before returning to Hawke\'s Bay in 2019. In 2024 she completed postgraduate study in myofunctional therapy. Morgan is passionate about periodontal treatment and educating patients on the link between oral and systemic health.',
        'photo_url': 'https://irp.cdn-website.com/5f820488/dms3rep/multi/morgan+profile.jpeg',
        'filename': 'morgan-jenkins-aesthetic-dental',
    },
    {
        'name': 'Billie-Michelle Adams',
        'gender': 'F',
        'specialties': 'Practice Manager',
        'experience': None,
        'bio': 'Billie began her dental career in Wellington and has spent 20 years in the industry. She lived in Sydney for six years, working alongside cosmetic dentists, oral surgeons, and prosthodontists. Now Practice Manager at Aesthetic Dental, she brings broad expertise and a genuine dedication to creating a welcoming experience for both patients and the team.',
        'photo_url': 'https://irp.cdn-website.com/5f820488/dms3rep/multi/Billie+profile.jpg',
        'filename': 'billie-adams-aesthetic-dental',
    },
    {
        'name': 'Irene Jardine',
        'gender': 'F',
        'specialties': 'Dental Assistant',
        'experience': 'Dental Assisting Certificate (Melbourne)',
        'bio': 'Irene has 17 years of experience in dentistry, having earned her Dental Assisting Certificate in Melbourne before moving to New Zealand. She has been a valued member of the Aesthetic Dental team for 10 years.',
        'photo_url': 'https://irp.cdn-website.com/5f820488/dms3rep/multi/Irene.png',
        'filename': 'irene-jardine-aesthetic-dental',
    },
    {
        'name': 'Sophie Burbury',
        'gender': 'F',
        'specialties': 'Dental Assistant',
        'experience': None,
        'bio': 'The newest member of the team, Sophie brings a warm, friendly nature and genuine enthusiasm for learning. She is eager to expand her knowledge and develop her skills as she begins her journey in dentistry.',
        'photo_url': 'https://irp.cdn-website.com/5f820488/dms3rep/multi/Sophie+Burbury.png',
        'filename': 'sophie-burbury-aesthetic-dental',
    },
]

print('Updating existing...')
for p in existing:
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

print('\nInserting new staff...')
current = {r['name'].lower() for r in q(f'SELECT name FROM clinic_practitioners WHERE clinic_id = {CLINIC_ID}')}
for p in new_staff:
    if p['name'].lower() in current:
        print(f'  Skipping (exists): {p["name"]}')
        continue
    print(f'\n{p["name"]}')
    photo_url = upload_photo(p['photo_url'], p['filename'])
    exp_val = f"$${p['experience']}$$" if p['experience'] else 'NULL'
    photo_val = f"'{photo_url}'" if photo_url else 'NULL'
    sql = f"""
        INSERT INTO clinic_practitioners (clinic_id, name, gender, specialties, experience, bio, photo_url, source_url)
        VALUES ({CLINIC_ID}, $${p['name']}$$, '{p['gender']}', $${p['specialties']}$$, {exp_val}, $${p['bio']}$$, {photo_val}, '{SOURCE}')
    """
    res = q(sql)
    print(f'  Inserted: {res}')

print('\nFinal list:')
rows = q(f'SELECT name, specialties, photo_url IS NOT NULL as has_photo FROM clinic_practitioners WHERE clinic_id = {CLINIC_ID} ORDER BY id')
for r in rows: print(r)
