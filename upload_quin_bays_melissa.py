import sys, io, requests, re
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
from dotenv import load_dotenv
import os
load_dotenv(r'c:\Users\Ciaran\Desktop\Dental_Directory\.env')
MGMT_KEY = os.environ['SUPABASE_MANAGEMENT_KEY']
SUPABASE_URL = os.environ['SUPABASE_URL']
JWT = os.environ['SUPABASE_JWT']
BUCKET = f'{SUPABASE_URL}/storage/v1/object/public/practitioner-photos/practitioners'
HEADERS = {"apikey": JWT, "Authorization": f"Bearer {JWT}", "Content-Type": "application/json"}

def q(sql):
    r = requests.post('https://api.supabase.com/v1/projects/ankyjpgcocsvvtyyymys/database/query',
        headers={'Authorization': f'Bearer {MGMT_KEY}', 'Content-Type': 'application/json'},
        json={'query': sql}, timeout=30, verify=False)
    return r.json()

def upload(img_url, slug):
    try:
        r = requests.get(img_url, timeout=20, verify=False, headers={'User-Agent': 'Mozilla/5.0'})
        if not r.ok: print(f'  Download failed {r.status_code}'); return None
        ext = img_url.split('?')[0].split('.')[-1].lower()
        if ext not in ('jpg','jpeg','png','webp'): ext = 'jpg'
        fname = f'{slug}.{ext}'
        ct = {'jpg':'image/jpeg','jpeg':'image/jpeg','png':'image/png','webp':'image/webp'}.get(ext,'image/jpeg')
        up = requests.post(f'{SUPABASE_URL}/storage/v1/object/practitioner-photos/practitioners/{fname}',
            headers={'Authorization': f'Bearer {JWT}', 'Content-Type': ct, 'x-upsert': 'true'},
            data=r.content, timeout=30, verify=False)
        if up.ok: print(f'  Uploaded {fname}'); return f'{BUCKET}/{fname}'
        print(f'  Upload failed {up.status_code}: {up.text[:80]}'); return None
    except Exception as e: print(f'  Error: {e}'); return None

def insert_practitioner(clinic_id, name, gender, experience, specialties, bio, photo_url, source):
    pv = f"'{photo_url}'" if photo_url else 'NULL'
    res = q(f"""INSERT INTO clinic_practitioners (clinic_id,name,gender,experience,specialties,bio,photo_url,source_url)
        VALUES ({clinic_id},$${name}$$,'{gender}',$${experience}$$,$${specialties}$$,$${bio}$$,{pv},'{source}')
        RETURNING id""")
    print(f'  Inserted {name}: {res}')

SQ_QUIN = 'https://images.squarespace-cdn.com/content/v1/597ffac67131a5eb04fcb974'
SOURCE_QUIN = 'https://www.quindental.nz/our-team'

# ── Bays Dentures (id 1652) ────────────────────────────────────────────────────
print('=== Bays Dentures ===')
q("UPDATE dental_clinics SET website = 'https://www.baysdentures.co.nz/' WHERE id = 1652")
print('  Website updated to HTTPS')

# Check for Daniela photo on their site
bays_html = requests.get('https://www.baysdentures.co.nz/', verify=False, headers={'User-Agent':'Mozilla/5.0'}).text
bays_imgs = re.findall(r'https://images\.squarespace-cdn\.com/[^\s"\'<>]+\.(?:jpg|jpeg|png|webp)', bays_html, re.I)
bays_imgs = list(dict.fromkeys(bays_imgs))
print(f'  Images found: {bays_imgs[:5]}')
daniela_photo = None
for img in bays_imgs:
    if 'logo' not in img.lower() and 'banner' not in img.lower():
        daniela_photo = upload(img, 'daniela-steenpass-bays-dentures')
        if daniela_photo: break

pv = f"'{daniela_photo}'" if daniela_photo else 'NULL'
res = q(f"""INSERT INTO clinic_practitioners (clinic_id,name,gender,experience,specialties,bio,photo_url,source_url)
    VALUES (1652,$$Daniela Steenpass$$,'F',$$DentTech, PGDipClinDentTech$$,$$Dentures, complete dentures, partial dentures, denture repair, denture relines$$,
    $$Has over 30 years of expertise in denture design. Renowned for crafting high-quality, well-fitting, and natural-looking dentures. Offers a free initial consultation.$$,
    {pv},'https://www.baysdentures.co.nz/')
    RETURNING id""")
print(f'  Daniela inserted: {res}')

# ── Quin Dental (id 1677) ──────────────────────────────────────────────────────
print('\n=== Quin Dental ===')
clinical = [
    {
        'name': 'Gerry Quin', 'gender': 'M',
        'experience': 'BDS (Otago) 1987, MS (Tufts, Boston) 2014',
        'specialties': 'General dentistry, non-extraction orthodontics, dentofacial orthopaedics, crown and bridge, amalgam removal',
        'bio': 'Graduated from Otago Dental School in 1987 and worked as a Dental House Surgeon at Waikato Hospital before moving to Nelson in 1989. Practised at Nile Street for over 29 years before founding Quin Dental in 2017. Completed a Master of Science at Tufts University, Boston in 2014. Founding member of the NZ Institute of Minimal Intervention Dentistry and an IAO member and instructor. Enjoys combining prevention with treatments that improve long-term health.',
        'photo': f'{SQ_QUIN}/0af426c9-cceb-45e3-942c-073406f4bfb4/Gerry.JPG',
        'slug': 'gerry-quin-quin-dental',
    },
    {
        'name': 'Anna Measures', 'gender': 'F',
        'experience': 'BDS (Otago) 1999',
        'specialties': 'General dentistry, treating children, dental anxiety',
        'bio': 'Graduated from the Otago School of Dentistry in 1999 with credit and began her career as a maxillofacial house surgeon at Christchurch Hospital. Spent time in the UK working in private and public practices and as an Area Clinical Manager for a dental corporate. Joined Quin Dental in 2020 after returning to New Zealand. Enjoys working with children and providing a friendly, relaxed atmosphere.',
        'photo': f'{SQ_QUIN}/20418937-ae97-44b1-a2bf-0ff2bca2c334/Anna+Nana.JPG',
        'slug': 'anna-measures-quin-dental',
    },
    {
        'name': 'Rachel Sladden', 'gender': 'F',
        'experience': 'BDS (Sheffield) 2021, MRCS (England)',
        'specialties': 'General dentistry, paediatric dentistry, treating anxious patients, oral and maxillofacial surgery, restorative dentistry',
        'bio': 'Graduated with honours from the University of Sheffield in 2021, then pursued postgraduate Dental Core Training in Oral & Maxillofacial Surgery, Restorative, and Paediatric Dentistry at University Hospital Bristol. Has a special interest in treating children and supporting anxious patients. Committed to outreach work with underserved communities, including a voluntary project in the Maasai Mara region of Kenya.',
        'photo': f'{SQ_QUIN}/d264cfd2-4284-4b7e-a2c0-7c431149809b/Rachel.jpg',
        'slug': 'rachel-sladden-quin-dental',
    },
    {
        'name': 'Kelsey Spiers', 'gender': 'F',
        'experience': 'BHSc Oral Health (AUT) 2013',
        'specialties': 'Oral health therapy, dental hygiene, periodontics, Guided Biofilm Therapy (GBT), forensic dentistry',
        'bio': 'Graduated from Auckland University of Technology with a Bachelor of Health Science in Oral Health in 2013. Uses a range of techniques including hand scaling, Cavitron ultrasonic scaling, and Guided Biofilm Therapy (GBT) with EMS Airflow. Also involved in forensic dentistry and community oral health initiatives, including a project focused on improving oral health for the elderly.',
        'photo': f'{SQ_QUIN}/faaac450-7ac7-42f2-a7d1-8f383bdcb256/Kelsey+..JPG',
        'slug': 'kelsey-spiers-quin-dental',
    },
]

admin = [
    {'name': 'Gabrielle Quin',  'gender': 'F', 'specialties': 'Practice Manager', 'photo': f'{SQ_QUIN}/0b2fdc04-9aa6-42f9-913e-6c629c5df1f5/Gabrielle+Quin+-+Quin+Dental+Staff.jpg', 'slug': 'gabrielle-quin-quin-dental'},
    {'name': 'Chris Kemp',      'gender': 'F', 'specialties': 'Reception',         'photo': f'{SQ_QUIN}/c74dd205-ad90-46ee-9dab-22bef9dc7b11/Chris+Kemp+-+QuinDentalStaff003.jpg',  'slug': 'chris-kemp-quin-dental'},
    {'name': 'Janelle',         'gender': 'F', 'specialties': 'Dental Assistant',  'photo': f'{SQ_QUIN}/4990bf90-e575-4366-a12a-7deb6bbb0075/Janelleeeeeee.JPG',                    'slug': 'janelle-quin-dental'},
    {'name': 'Faye',            'gender': 'F', 'specialties': 'Dental Assistant',  'photo': f'{SQ_QUIN}/f6b1e905-a1f9-499a-a35b-3a9cc0b0473d/faye.JPG',                             'slug': 'faye-quin-dental'},
    {'name': 'Verity',          'gender': 'F', 'specialties': 'Dental Assistant',  'photo': f'{SQ_QUIN}/3f69e7ba-8c11-4f26-9d12-ec67e0faad80/Verity.JPG',                           'slug': 'verity-quin-dental'},
    {'name': 'Brenna',          'gender': 'F', 'specialties': 'Dental Assistant',  'photo': f'{SQ_QUIN}/cb3e3ceb-1c4a-4b18-8e33-ea19b7497b36/brenna+.jpg',                          'slug': 'brenna-quin-dental'},
]

for p in clinical:
    print(f'\n{p["name"]}')
    photo_url = upload(p['photo'], p['slug'])
    insert_practitioner(1677, p['name'], p['gender'], p['experience'], p['specialties'], p['bio'], photo_url, SOURCE_QUIN)

for p in admin:
    print(f'\n{p["name"]}')
    photo_url = upload(p['photo'], p['slug'])
    pv = f"'{photo_url}'" if photo_url else 'NULL'
    res = q(f"""INSERT INTO clinic_practitioners (clinic_id,name,gender,specialties,photo_url,source_url)
        VALUES (1677,$${p['name']}$$,'{p['gender']}',$${p['specialties']}$$,{pv},'{SOURCE_QUIN}')
        RETURNING id""")
    print(f'  Inserted: {res}')

# ── Melissa Munro photo (id 741) ───────────────────────────────────────────────
print('\n=== Melissa Munro photo ===')
melissa_img = 'https://images.squarespace-cdn.com/content/v1/5efa885720ccac1eaafe7b40/1602198630466-HIG37MFPUBEFXWU6744Q/Melissa+Munro+Munro+Dental+Nelson?format=750w'
url = upload(melissa_img, 'melissa-munro-munro-dental')
if url:
    res = q(f"UPDATE clinic_practitioners SET photo_url='{url}', source_url='https://www.munrodental.co.nz/our-team-munro-dental-patient-care' WHERE id=741")
    print(f'  Updated: {res}')

print('\nDone.')
