import requests, sys, io, urllib.parse
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
from dotenv import load_dotenv
import os
load_dotenv(r'c:\Users\Ciaran\Desktop\Dental_Directory\.env')
MGMT = os.environ['SUPABASE_MANAGEMENT_KEY']
SUPABASE_URL = os.environ['SUPABASE_URL']
JWT = os.environ['SUPABASE_JWT']
BUCKET = f'{SUPABASE_URL}/storage/v1/object/public/practitioner-photos/practitioners'
CDN = 'https://irp.cdn-website.com/76d7f6bd/dms3rep/multi/opt'
HEADERS = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36'}

def q(sql):
    r = requests.post('https://api.supabase.com/v1/projects/ankyjpgcocsvvtyyymys/database/query',
        headers={'Authorization': f'Bearer {MGMT}', 'Content-Type': 'application/json'},
        json={'query': sql}, verify=False)
    return r.json()

def upload(img_url, slug):
    r = requests.get(img_url, timeout=20, verify=False, headers=HEADERS)
    if not r.ok: print(f'  Download failed {r.status_code}'); return None
    ext = img_url.split('?')[0].split('.')[-1].split('-')[0].lower()
    if ext not in ('jpg','jpeg','png','webp'): ext = 'jpg'
    ct = {'jpg':'image/jpeg','jpeg':'image/jpeg','png':'image/png','webp':'image/webp'}.get(ext,'image/jpeg')
    fname = f'{slug}.{ext}'
    up = requests.post(f'{SUPABASE_URL}/storage/v1/object/practitioner-photos/practitioners/{fname}',
        headers={'Authorization': f'Bearer {JWT}', 'Content-Type': ct, 'x-upsert': 'true'},
        data=r.content, timeout=30, verify=False)
    if up.ok: print(f'  Uploaded {fname}'); return f'{BUCKET}/{fname}'
    print(f'  Upload failed: {up.text[:80]}'); return None

SOURCE = 'https://www.discoverdental.co.nz/our-team'

# Practitioner id → (name, img_filename, specialties, gender)
team = [
    (804, 'Ben Catherwood',   'Ben+1280-1920w.jpg',                                         None,                            'M'),
    (805, 'Richard Greenwood','4-Meet+the+Team+RG2+1280-1920w.jpg',                         None,                            'M'),
    (806, 'Angela McKeefry',  'Angela-McKeefry-1280-1920w.jpg',                             None,                            'F'),
    (807, 'Chloe Stroud',     'Chloe-1280-1920w.jpg',                                       None,                            'F'),
    (808, 'Alaina Kalyan',    '4-Meet-the-Team-AK-1280-34bb7ef9-1920w.jpg',                'Hygienist, Oral Health Therapist','F'),
    (809, 'Denise Hunter',    'Denise-1280-d0f5fde4-1920w.jpg',                            None,                            'F'),
    (810, 'Mélina Garneau',   'melina-f13628f0-322c052f-1920w.jpg',                        None,                            'F'),
    (811, 'Rachael Gibson',   'FB_IMG_1720512939195-9b762991-11deb612-7635b03f-333f1b7b-1920w.jpg', 'Hygienist, Oral Health Therapist', 'F'),
    (812, 'Sheryne Beeby',    'Sheryne-b50316fc-1920w.jpg',                                None,                            'F'),
    # 813 Priscilla Kumar — photo is a mascot bear, skip
    (814, 'Louise Cautley',   'Louise-Pic-qlk9dy4p98pst4bjnzceo4skyv3qxt21l9nsfbj6cw+%28002%29-1920w.jpg', 'Hygienist, Oral Health Therapist', 'F'),
]

for pid, name, img_file, specialties, gender in team:
    print(f'\n{name}:')
    url = f'{CDN}/{img_file}'
    slug = name.lower().replace(' ', '-').replace('é', 'e').replace('é', 'e') + '-discover-dental'
    photo = upload(url, slug)
    spec_sql = f"specialties = $${specialties}$$," if specialties else ''
    if photo:
        print(q(f"""UPDATE clinic_practitioners
            SET photo_url = '{photo}',
                gender = '{gender}',
                {spec_sql}
                source_url = '{SOURCE}'
            WHERE id = {pid} RETURNING id, name"""))
    else:
        print(q(f"""UPDATE clinic_practitioners
            SET gender = '{gender}',
                {spec_sql}
                source_url = '{SOURCE}'
            WHERE id = {pid} RETURNING id, name"""))

# Priscilla — just set gender and specialties, no photo
print('\nPriscilla Kumar (no headshot):')
print(q(f"UPDATE clinic_practitioners SET gender = 'F', specialties = $$Hygienist, Oral Health Therapist$$, source_url = '{SOURCE}' WHERE id = 813 RETURNING id, name"))

print('\nDone.')
