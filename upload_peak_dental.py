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
            print(f'  Download failed {resp.status_code}'); return None
        ext = img_url.split('.')[-1].split('?')[0].lower()
        if ext not in ('jpg', 'jpeg', 'png', 'webp'): ext = 'jpg'
        fname = f'{filename}.{ext}'
        ct = {'jpg': 'image/jpeg', 'jpeg': 'image/jpeg', 'png': 'image/png', 'webp': 'image/webp'}.get(ext, 'image/jpeg')
        up = requests.post(
            f'{SUPABASE_URL}/storage/v1/object/practitioner-photos/practitioners/{fname}',
            headers={'Authorization': f'Bearer {STORAGE_JWT}', 'Content-Type': ct, 'x-upsert': 'true'},
            data=resp.content, timeout=30, verify=False)
        if up.ok:
            print(f'  Uploaded: {fname}'); return f'{BUCKET_BASE}/{fname}'
        print(f'  Upload failed: {up.text[:80]}'); return None
    except Exception as e:
        print(f'  Error: {e}'); return None

CLINIC_ID = 1534
SOURCE = 'https://www.peakdental.co.nz/about-us/'
BASE = 'https://www.peakdental.co.nz/wp-content/uploads'

existing = [
    {
        'id': 1345,
        'name': 'Donna Holder',
        'gender': 'F',
        'specialties': 'Lead Dentist',
        'experience': 'BDS (Otago)',
        'bio': "Donna is the owner of Peak Dental, which she purchased in 2021. Originally from Oamaru, she graduated from Otago University in 1998 and worked as a Dental House Surgeon at Christchurch Hospital before moving into private practice. She relocated to Havelock North with her family in 2011 following the Christchurch earthquakes and worked locally before taking over Peak Dental. Donna enjoys all aspects of dentistry — from restorations and crowns to implants — and believes strongly in regular maintenance and prevention for long-term oral health.",
        'photo_url': f'{BASE}/2022/09/Peak-Dental-Donna-Holder.jpg',
        'filename': 'donna-holder-peak-dental',
    },
    {
        'id': 1346,
        'name': 'Jo Jackson',
        'gender': 'F',
        'specialties': 'Dentist',
        'experience': 'BDS (Otago)',
        'bio': "Jo has been a dentist at Peak Dental since 2021. She graduated from Otago University in 1998, then spent 15 years working in a general dental practice in South West London before settling in Hawke's Bay in 2018. Jo values the long-term relationships she builds with her patients and is passionate about helping them achieve healthy teeth and smiles.",
        'photo_url': f'{BASE}/2022/09/peak-dental-jo-jackson.jpg',
        'filename': 'jo-jackson-peak-dental',
    },
    {
        'id': 1347,
        'name': 'Pip Brickell',
        'gender': 'F',
        'specialties': 'Dentist',
        'experience': 'BDS (Otago)',
        'bio': "Pip graduated with a Bachelor of Dental Surgery from Otago University and joined Peak Dental in Havelock North. She enjoys the variety of general practice — restorations, crowns, root canals, periodontal treatment — and appreciates the constantly evolving technology and materials in modern dentistry. Having been frightened of the dentist herself growing up, Pip is particularly attuned to patient anxieties and takes pride in creating a calm, empathetic experience.",
        'photo_url': f'{BASE}/2022/09/peak-dental-Pip-Brickell.jpg',
        'filename': 'pip-brickell-peak-dental',
    },
    {
        'id': 1348,
        'name': 'Gary Mitchelmore',
        'gender': 'M',
        'specialties': 'Dentist',
        'experience': 'BDS (Otago), PGDipDentSurg (Oral Surgery, Otago)',
        'bio': "Gary qualified at the University of Otago in 1984 and, after a brief locum post in Oamaru, joined the New Zealand Army as a Dental Officer, serving in New Zealand and overseas for ten years. During this time he completed a Postgraduate Diploma in Oral Surgery at Otago. After leaving the military, Gary ran his own practice in Dannevirke for 23 years before moving to Hawke's Bay. He has a special interest in oral surgery and intravenous sedation.",
        'photo_url': f'{BASE}/2024/05/Peak-Dental_-Gary.png',
        'filename': 'gary-mitchelmore-peak-dental',
    },
]

new_staff = [
    {
        'name': 'Monz',
        'gender': 'F',
        'specialties': 'Lead Receptionist',
        'experience': None,
        'bio': None,
        'photo_url': f'{BASE}/2022/09/peak-dental-monz.jpg',
        'filename': 'monz-peak-dental',
    },
    {
        'name': 'Caroline',
        'gender': 'F',
        'specialties': 'Dental Assistant',
        'experience': None,
        'bio': None,
        'photo_url': f'{BASE}/2022/09/peak-dental-caroline.jpg',
        'filename': 'caroline-peak-dental',
    },
    {
        'name': 'Kayla',
        'gender': 'F',
        'specialties': 'Dental Assistant',
        'experience': None,
        'bio': None,
        'photo_url': f'{BASE}/2024/05/Peak-Dental_-Kayla.png',
        'filename': 'kayla-peak-dental',
    },
    {
        'name': 'Dani',
        'gender': 'F',
        'specialties': 'Dental Assistant',
        'experience': None,
        'bio': None,
        'photo_url': f'{BASE}/2024/05/Peak-Dental_-Dani.png',
        'filename': 'dani-peak-dental',
    },
]

print('Updating existing dentists...')
for p in existing:
    print(f'\n{p["name"]}')
    photo_url = upload_photo(p['photo_url'], p['filename'])
    photo_val = f"'{photo_url}'" if photo_url else 'NULL'
    bio_val = f"$${p['bio']}$$" if p['bio'] else 'NULL'
    sql = f"""
        UPDATE clinic_practitioners SET
            gender = '{p['gender']}',
            specialties = $${p['specialties']}$$,
            experience = $${p['experience']}$$,
            bio = {bio_val},
            photo_url = {photo_val},
            source_url = '{SOURCE}'
        WHERE id = {p['id']}
    """
    print(' ', q(sql))

print('\nInserting support staff...')
current = {r['name'].lower() for r in q(f'SELECT name FROM clinic_practitioners WHERE clinic_id = {CLINIC_ID}')}
for p in new_staff:
    if p['name'].lower() in current:
        print(f'  Skipping (exists): {p["name"]}'); continue
    print(f'\n{p["name"]}')
    photo_url = upload_photo(p['photo_url'], p['filename'])
    photo_val = f"'{photo_url}'" if photo_url else 'NULL'
    sql = f"""
        INSERT INTO clinic_practitioners (clinic_id, name, gender, specialties, source_url, photo_url)
        VALUES ({CLINIC_ID}, $${p['name']}$$, '{p['gender']}', $${p['specialties']}$$, '{SOURCE}', {photo_val})
    """
    print(' ', q(sql))

print('\nUpdating clinic description...')
print(q("""
    UPDATE dental_clinics SET
        description = $$A locally owned dental practice situated in a beautiful Art Deco building on Te Mata Road in Havelock North. Open for over 20 years, Peak Dental is led by Dr Donna Holder and offers comprehensive general dentistry for the whole family. The team's philosophy is to build long-lasting patient relationships through regular check-ups and preventive care.$$
    WHERE id = 1534
"""))

print('\nFinal list:')
for row in q(f'SELECT id, name, specialties, photo_url IS NOT NULL as has_photo FROM clinic_practitioners WHERE clinic_id = {CLINIC_ID} ORDER BY id'):
    print(row)
