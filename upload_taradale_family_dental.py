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

BASE_IMG = 'https://www.taradalefamilydental.co.nz/image_transformations'

def upload_photo(path_with_hash, filename):
    url = f'{BASE_IMG}/{path_with_hash}&format=auto&quality=90&width=800'
    try:
        resp = requests.get(url, timeout=15, verify=False, headers={'User-Agent': 'Mozilla/5.0'})
        if not resp.ok:
            print(f'  Download failed {resp.status_code}')
            return None
        ct = resp.headers.get('content-type', '')
        ext = 'avif' if 'avif' in ct else ('webp' if 'webp' in ct else 'jpg')
        fname = f'{filename}.{ext}'
        content_type = {'avif': 'image/avif', 'webp': 'image/webp'}.get(ext, 'image/jpeg')
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

CLINIC_ID = 1539
SOURCE = 'https://www.taradalefamilydental.co.nz/dental-team-taradale'

team = [
    {
        'name': 'Sharon Son',
        'gender': 'F',
        'specialties': 'Dentist',
        'experience': 'BDS Otago',
        'bio': "Originally from South Korea, Sharon migrated to New Zealand in 2000 and grew up in Auckland. She graduated from the University of Otago in 2011 and gained experience in Australia and Auckland before joining Taradale Family Dental in 2018. Sharon prides herself on making patients comfortable and regularly attends courses and conferences to stay current. She is a member of the NZDA.",
        'photo': '6a2b608de7dd6d0ad7e31ad6/sharon?h=73f81085',
        'filename': 'sharon-son-taradale-family-dental',
    },
    {
        'name': 'Dave Tyman',
        'gender': 'M',
        'specialties': 'Principal Dentist',
        'experience': 'BDS Otago',
        'bio': "Dave grew up in Hawke's Bay and attended Napier Boys' High School before graduating from Otago University in 2013. He practised in Auckland before returning home to Hawke's Bay, where he co-owns Taradale Family Dental with Sharon. He values the variety of general dentistry and focuses on presenting all options to patients with a gentle touch. An avid fisherman and sports enthusiast, Dave plays for the local Taradale football club.",
        'photo': '6a2b6087596266921ee31ae0/dave?h=0ade9ab0',
        'filename': 'dave-tyman-taradale-family-dental',
    },
    {
        'name': 'Mark Purkiss',
        'gender': 'M',
        'specialties': 'Dentist',
        'experience': 'BSc BDS Manchester',
        'bio': "Originally from the UK, Mark graduated from Manchester University in 1991 and has over 30 years of experience in the UK and New Zealand. During his degree he completed a separate Pathology BSc and was the first dental student at his school to participate in an Erasmus exchange to Denmark. He has completed a two-year American Orthodontics course and is a member of the ICCDE and NZDA, completing over 60 hours of additional study each year. Mark moved to Taradale in 2004.",
        'photo': '6a2b60888153efaef626a126/mark?h=3c67f8e1',
        'filename': 'mark-purkiss-taradale-family-dental',
    },
    {
        'name': 'Sheree Lack',
        'gender': 'F',
        'specialties': 'Practice Manager',
        'experience': None,
        'bio': "Sheree has been a member of the Taradale Family Dental team since it was established in 2007. She welcomes patients at reception and takes pride in making every visit a positive and comfortable experience.",
        'photo': '6a2b6089e7dd6d0ad7e31ad2/sheree?h=3d9f53e9',
        'filename': 'sheree-lack-taradale-family-dental',
    },
    {
        'name': "Irene O'Malley",
        'gender': 'F',
        'specialties': 'Dental Assistant & Receptionist',
        'experience': None,
        'bio': "A local Hawke's Bay girl, Irene has been with the team since Taradale Family Dental first opened its doors. She job-shares between reception and dental assisting.",
        'photo': '6a2b608a729f3d505ee31ae5/irene?h=a309b8f0',
        'filename': 'irene-omalley-taradale-family-dental',
    },
    {
        'name': 'Jo Dighton',
        'gender': 'F',
        'specialties': 'Dental Assistant & Receptionist',
        'experience': None,
        'bio': "Jo moved to New Zealand from Hythe in southern England in 2005 with her husband and two children, and has worked at Taradale Family Dental for 10 years. She enjoys meeting and assisting patients and loves everything Hawke's Bay has to offer.",
        'photo': '6a2b608bd481ae05c8e5bf68/jo?h=f5e4cfc0',
        'filename': 'jo-dighton-taradale-family-dental',
    },
    {
        'name': 'Zoe Symonds',
        'gender': 'F',
        'specialties': 'Dental Assistant',
        'experience': None,
        'bio': "Zoe is a local Hawke's Bay resident who previously worked alongside Dave at another practice before joining the Taradale Family Dental team. She lives with her husband and two sons who play rugby for Taradale.",
        'photo': '6a2b608cdc9073341326a16b/zoe?h=4a23e746',
        'filename': 'zoe-symonds-taradale-family-dental',
    },
]

current = {r['name'].lower() for r in q(f'SELECT name FROM clinic_practitioners WHERE clinic_id = {CLINIC_ID}')}

for p in team:
    if p['name'].lower() in current:
        print(f'Skipping (exists): {p["name"]}')
        continue
    print(f'\n{p["name"]}')
    photo_url = upload_photo(p['photo'], p['filename'])
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
