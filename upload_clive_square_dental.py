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
        if ext not in ('jpg', 'jpeg', 'png', 'webp'):
            ext = 'jpg'
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

CLINIC_ID = 1506
SOURCE = 'https://clivesquaredental.co.nz/our-team/'
BASE = 'https://clivesquaredental.co.nz/wp-content/uploads/2026/06'

# Delete the duplicate "Betty" entry (ID 1415) — Brad Betty is one person
print('Removing duplicate "Betty" entry...')
res = q('DELETE FROM clinic_practitioners WHERE id = 1415')
print(f'  {res}')

team = [
    {
        'id': 1414,
        'name': 'Brad Betty',
        'gender': 'M',
        'specialties': 'Dental Surgeon',
        'experience': 'BSc, BDS',
        'bio': "A Hawkes Bay native, Brad attended Hastings Boys' High before graduating from Otago with a degree with credit. After graduating he worked for two years under oral surgeon Mr David Arnott, then alongside Dr David Marshall before spending time in London, Edinburgh, and Plymouth. On returning to New Zealand he took over Clive Square Dental from Drs Murray Holland and Stewart Longly. Brad is passionate about patient-centred care and loves trout fishing on the Tutaekuri River and surfing at Waimarama Beach with his family.",
        'photo_url': f'{BASE}/brad-web.jpg',
        'filename': 'brad-betty-clive-square-dental',
    },
    {
        'id': 1416,
        'name': 'Mike McCaw',
        'gender': 'M',
        'specialties': 'Dental Surgeon',
        'experience': 'BSc, BDS',
        'bio': "Mike was born and schooled in Napier, graduating from the Otago School of Dentistry in 1994. After practising in Auckland for several years he returned to the Bay in 2002, working at Dental on Raffles for 10 years before joining Clive Square Dental in 2012. With over 20 years of experience in general dentistry, Mike is a member of the New Zealand Dental Association and regularly attends courses on the latest advances in modern dentistry. Outside dentistry he enjoys snowboarding, guitar, mountain biking, and travelling with his family.",
        'photo_url': f'{BASE}/mike-web.jpg',
        'filename': 'mike-mccaw-clive-square-dental',
    },
    {
        'id': 1417,
        'name': 'Paola Fenton',
        'gender': 'F',
        'specialties': 'Dental Surgeon',
        'experience': 'BDS, Myofunctional Therapy Provider, IAOMT SMART Member',
        'bio': "Proudly based in Hawke's Bay and caring for the community since 2015, Paola is passionate about creating a dental experience where patients feel genuinely listened to and comfortable. She has a special interest in advanced restorative and cosmetic dentistry, airway-focused and growth-guided care for children, myofunctional therapy, and interceptive preventive dentistry that identifies and addresses concerns early. Paola believes great dentistry is about caring for people, not just teeth.",
        'photo_url': f'{BASE}/paola-web.jpg',
        'filename': 'paola-fenton-clive-square-dental',
    },
    {
        'id': 1418,
        'name': 'Emily Thomsen',
        'gender': 'F',
        'specialties': 'Oral Health Therapist',
        'experience': 'RDT',
        'bio': "A born-and-raised Hawkes Bay local who returned home after travelling in her early 20s, Emily is passionate about health and education. She provides dental treatment for adolescents and oral hygiene care in a relaxed, caring environment, and is proud to offer hygiene treatments using EMS Airflow — a gentle, effective technology suitable for all teeth including implants and orthodontic appliances. Outside work Emily loves waka ama paddling, tramping, e-biking, and anything beach or nature related.",
        'photo_url': f'{BASE}/emily-web.jpg',
        'filename': 'emily-thomsen-clive-square-dental',
    },
    {
        'id': 1419,
        'name': 'Tania Bryan',
        'gender': 'F',
        'specialties': 'Practice Manager',
        'experience': None,
        'bio': "One of the first faces you'll see at Clive Square Dental, Tania began as a school leaver training as a dental assistant before working her way up to Practice Manager, taking over the role from her mother Lyn who retired after over 30 years with the practice. Tania knows how daunting a dental visit can be, so she takes pride in putting patients at ease and building lasting rapport with the practice's long-term and often multi-generational patients. Outside work she loves spending time with her family, travelling, and exploring the outdoors.",
        'photo_url': f'{BASE}/tania-web.jpg',
        'filename': 'tania-bryan-clive-square-dental',
    },
]

for p in team:
    print(f'\n{p["name"]}')
    photo_url = upload_photo(p['photo_url'], p['filename'])
    photo_val = f"'{photo_url}'" if photo_url else 'NULL'
    exp_val = f"$${p['experience']}$$" if p['experience'] else 'NULL'
    sql = f"""
        UPDATE clinic_practitioners SET
            name = $${p['name']}$$,
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
rows = q(f'SELECT id, name, specialties, photo_url IS NOT NULL as has_photo FROM clinic_practitioners WHERE clinic_id = {CLINIC_ID} ORDER BY id')
for row in rows:
    print(row)
