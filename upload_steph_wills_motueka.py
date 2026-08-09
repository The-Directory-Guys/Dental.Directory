import sys, io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

import requests, os
from dotenv import load_dotenv
load_dotenv(r'c:\Users\Ciaran\Desktop\Dental_Directory\.env')
MGMT_KEY = os.environ['SUPABASE_MANAGEMENT_KEY']
SUPABASE_URL = os.environ['SUPABASE_URL']
STORAGE_JWT = os.environ['SUPABASE_JWT']
BUCKET_BASE = f'{SUPABASE_URL}/storage/v1/object/public/practitioner-photos/practitioners'
SOURCE = 'https://www.stephwillsdental.co.nz/our-team'
CLINIC_ID = 1679

def q(sql):
    r = requests.post('https://api.supabase.com/v1/projects/ankyjpgcocsvvtyyymys/database/query',
        headers={'Authorization': f'Bearer {MGMT_KEY}', 'Content-Type': 'application/json'},
        json={'query': sql}, timeout=30, verify=False)
    return r.json()

def upload_photo(img_url, filename):
    try:
        resp = requests.get(img_url, timeout=20, verify=False, headers={'User-Agent': 'Mozilla/5.0'})
        if not resp.ok:
            print(f'  Download failed {resp.status_code}')
            return None
        ext = img_url.split('?')[0].split('.')[-1].lower()
        if ext not in ('jpg','jpeg','png','webp'): ext = 'jpg'
        fname = f'{filename}.{ext}'
        content_type = {'jpg':'image/jpeg','jpeg':'image/jpeg','png':'image/png','webp':'image/webp'}.get(ext,'image/jpeg')
        up = requests.post(
            f'{SUPABASE_URL}/storage/v1/object/practitioner-photos/practitioners/{fname}',
            headers={'Authorization': f'Bearer {STORAGE_JWT}', 'Content-Type': content_type, 'x-upsert': 'true'},
            data=resp.content, timeout=30, verify=False)
        if up.ok:
            print(f'  Uploaded: {fname}')
            return f'{BUCKET_BASE}/{fname}'
        print(f'  Upload failed {up.status_code}: {up.text[:100]}')
        return None
    except Exception as e:
        print(f'  Error: {e}')
        return None

WIX = 'https://static.wixstatic.com/media'

team = [
    {
        'name': 'Heidi Seifried',
        'gender': 'F',
        'experience': 'BDS (Otago) 1998',
        'specialties': 'General dentistry',
        'bio': 'Has worked part time as an associate dentist at the practice since 2005. Graduated from Otago University with a BDS (credit) in 1998 and went on to work in the UK, completing dental vocational training at a mixed private-NHS practice in the Lake District. She then worked for Dental Health Services Victoria at Ballarat Base Hospital, Australia, and at a private Christchurch practice before returning to the Nelson-Tasman region. Also a qualified winemaker.',
        'photo': f'{WIX}/1e8d6f_7ef84612bbea4eb6a3e2a5fef2dbbadd~mv2_d_2592_3888_s_4_2.jpg',
        'slug': 'heidi-seifried-steph-wills',
    },
    {
        'name': 'Turoa Gallagher',
        'gender': 'M',
        'experience': 'BDS (Otago) 2015',
        'specialties': 'General dentistry',
        'bio': 'Graduated with a BDS from the University of Otago in 2015. Performs all aspects of general dentistry and incorporates Tikanga Maori in his approach, helping to create a calming and caring environment for patients.',
        'photo': f'{WIX}/1e8d6f_c1fee27473e44b89a73a5e957d10bca0~mv2_d_3888_2592_s_4_2.jpg',
        'slug': 'turoa-gallagher-steph-wills',
    },
    {
        'name': 'Nick Griffen',
        'gender': 'M',
        'experience': 'BDS (Otago) 2022',
        'specialties': 'General dentistry',
        'bio': 'Graduated from the University of Otago with a Bachelor of Dental Surgery in 2022, completing his final year at the Auckland Dental Facility. Interested in all aspects of general dentistry and passionate about staying up to date with current literature and techniques. Outside dentistry he is a keen musician (guitar, drums, bass and keyboard) and has been involved with various Kapa Haka groups.',
        'photo': f'{WIX}/1e8d6f_e9c0d3ce323f4afe88a08d828c0a0896~mv2.jpg',
        'slug': 'nick-griffen-steph-wills',
    },
    {
        'name': 'Kathryn Tiedemann',
        'gender': 'F',
        'experience': 'Dental hygiene, periodontics and pain control (Otago + Australia)',
        'specialties': 'Dental hygiene, periodontics, pain control',
        'bio': 'After graduating from Otago, continued her studies in dental hygiene, periodontics and pain control in Australia. Has worked in Christchurch, NSW, Napier, and Blenheim before returning to the Nelson-Tasman region. Passionate about achieving optimum oral health outcomes, providing thorough and pain-free gum disease treatment, and motivating patients to maintain good oral health at home.',
        'photo': f'{WIX}/1e8d6f_2e0054c83bf548aea9ab2c78f2750fe5~mv2.jpg',
        'slug': 'kathryn-tiedemann-steph-wills',
    },
]

for p in team:
    print(f'\n{p["name"]}')
    photo_url = upload_photo(p['photo'], p['slug'])
    photo_val = f"'{photo_url}'" if photo_url else 'NULL'
    res = q(f"""
        INSERT INTO clinic_practitioners (clinic_id, name, gender, experience, specialties, bio, photo_url, source_url)
        VALUES ({CLINIC_ID}, $${p['name']}$$, '{p['gender']}', $${p['experience']}$$,
                $${p['specialties']}$$, $${p['bio']}$$, {photo_val}, '{SOURCE}')
        RETURNING id
    """)
    print(f'  Inserted: {res}')

print('\nFinal team for clinic 1679:')
rows = q('SELECT name, experience, photo_url IS NOT NULL as has_photo FROM clinic_practitioners WHERE clinic_id = 1679 ORDER BY id')
for r in rows: print(r)
