import requests, sys, io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
from dotenv import load_dotenv
import os
load_dotenv(r'c:\Users\Ciaran\Desktop\Dental_Directory\.env')
MGMT = os.environ['SUPABASE_MANAGEMENT_KEY']
SUPABASE_URL = os.environ['SUPABASE_URL']
JWT = os.environ['SUPABASE_JWT']
BUCKET = f'{SUPABASE_URL}/storage/v1/object/public/practitioner-photos/practitioners'
HEADERS = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36'}

def q(sql):
    r = requests.post('https://api.supabase.com/v1/projects/ankyjpgcocsvvtyyymys/database/query',
        headers={'Authorization': f'Bearer {MGMT}', 'Content-Type': 'application/json'},
        json={'query': sql}, verify=False)
    return r.json()

def upload(img_url, slug):
    r = requests.get(img_url, timeout=20, verify=False, headers=HEADERS)
    if not r.ok: print(f'  Download failed {r.status_code}'); return None
    ext = img_url.split('?')[0].split('.')[-1].lower()
    if ext not in ('jpg','jpeg','png','webp'): ext = 'jpg'
    ct = {'jpg':'image/jpeg','jpeg':'image/jpeg','png':'image/png','webp':'image/webp'}.get(ext,'image/jpeg')
    fname = f'{slug}.{ext}'
    up = requests.post(f'{SUPABASE_URL}/storage/v1/object/practitioner-photos/practitioners/{fname}',
        headers={'Authorization': f'Bearer {JWT}', 'Content-Type': ct, 'x-upsert': 'true'},
        data=r.content, timeout=30, verify=False)
    if up.ok: print(f'  Uploaded {fname}'); return f'{BUCKET}/{fname}'
    print(f'  Upload failed: {up.text[:80]}'); return None

SOURCE = 'https://dentalreflections.co.nz/meet-the-team/'

desc = "A denturist practice serving Lower Hutt, Upper Hutt, and Wainuiomata, offering full dentures, partial dentures, denture relines and repairs, and night guards. Led by Clinical Dental Technician Mustafa Ali, who uses digital workflows including 3D scanning and computer-aided design to create natural-looking, well-fitted dentures."

# 1. Update all three clinics — category and description
for cid in [2837, 2852, 2843]:
    print(q(f"UPDATE dental_clinics SET category = 'denturist', description = $${desc}$$ WHERE id = {cid} RETURNING id, name, category"))

# 2. Clean up Lower Hutt website UTM param
print(q("UPDATE dental_clinics SET website = 'https://dentalreflections.co.nz/' WHERE id = 2837 RETURNING id, website"))

# 3. Update practitioner names, bios, specialties

mustafa_bio = "Mustafa Ali is a Clinical Dental Technician with over 13 years of experience, holding a Bachelor of Dental Technology and a Postgraduate Diploma in Clinical Dental Technology from the University of Otago. As the lead clinician at Dental Reflections, he uses modern digital workflows including 3D scanning and computer-aided design to create natural-looking, well-fitted dentures. His calm and patient-focused approach helps patients feel comfortable and well-informed throughout their treatment."

jordyn_bio = "Jordyn Te Kani is the Team Leader and Operations Manager at Dental Reflections, bringing four years of practice management experience across both clinic and laboratory environments. She leads day-to-day operations and coordinates between clinicians, technicians, and patients to keep appointments on track. Her approachable and solutions-focused approach means patients feel supported and confident throughout their treatment."

stephanie_bio = "Stephanie Smit is the Front Office Coordinator at Dental Reflections, holding a Level 3 Certificate in Business Administration and bringing 12 years of experience in customer service and administration. She is the welcoming first point of contact for patients, managing appointments, enquiries, and front office coordination. Her friendly and attentive manner is particularly valued by patients who may feel nervous about dental visits."

print(q(f"""UPDATE clinic_practitioners
    SET name = 'Mustafa Ali',
        bio = $${mustafa_bio}$$,
        specialties = $$Full dentures, partial dentures, denture relines, denture repairs, night guards, 3D scanning$$,
        experience = $$BDT, PGDipCDT (University of Otago), 13+ years$$,
        gender = 'male',
        source_url = '{SOURCE}'
    WHERE id = 866 RETURNING id, name"""))

print(q(f"""UPDATE clinic_practitioners
    SET name = 'Jordyn Te Kani',
        bio = $${jordyn_bio}$$,
        source_url = '{SOURCE}'
    WHERE id = 864 RETURNING id, name"""))

print(q(f"""UPDATE clinic_practitioners
    SET name = 'Stephanie Smit',
        bio = $${stephanie_bio}$$,
        source_url = '{SOURCE}'
    WHERE id = 865 RETURNING id, name"""))

# 4. Upload photos
print('\nUploading photos:')

print('Mustafa:')
mustafa_photo = upload('https://dentalreflections.co.nz/wp-content/uploads/2026/04/Mustafa-1.png', 'mustafa-ali-dental-reflections')
if mustafa_photo:
    print(q(f"UPDATE clinic_practitioners SET photo_url = '{mustafa_photo}' WHERE id = 866 RETURNING id, name"))

print('Jordyn:')
jordyn_photo = upload('https://dentalreflections.co.nz/wp-content/uploads/2025/05/DSC00331-scaled.jpg', 'jordyn-te-kani-dental-reflections')
if jordyn_photo:
    print(q(f"UPDATE clinic_practitioners SET photo_url = '{jordyn_photo}' WHERE id = 864 RETURNING id, name"))

print('\nDone.')
