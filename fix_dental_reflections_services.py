import requests, os, sys, io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
from dotenv import load_dotenv
load_dotenv(r'c:\Users\Ciaran\Desktop\Dental_Directory\.env')
MGMT = os.environ['SUPABASE_MANAGEMENT_KEY']
SUPABASE_URL = os.environ['SUPABASE_URL']
JWT = os.environ['SUPABASE_JWT']
BUCKET = f'{SUPABASE_URL}/storage/v1/object/public/practitioner-photos/practitioners'
HEADERS = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'}

def q(sql):
    r = requests.post('https://api.supabase.com/v1/projects/ankyjpgcocsvvtyyymys/database/query',
        headers={'Authorization': f'Bearer {MGMT}', 'Content-Type': 'application/json'},
        json={'query': sql}, verify=False)
    return r.json()

# 1. Set services = 'Dentures' for all three clinics
for cid in [2837, 2852, 2843]:
    print(q(f"UPDATE dental_clinics SET services = 'Dentures' WHERE id = {cid} RETURNING id, name, services"))

# 2. Upload Stephanie's photo and update all three of her entries
print('\nUploading Stephanie photo...')
r = requests.get('https://dentalreflections.co.nz/wp-content/uploads/2025/11/Diwali-2025-7.jpg',
    timeout=20, verify=False, headers=HEADERS)
print(f'Download: {r.status_code}, {len(r.content)} bytes')

up = requests.post(f'{SUPABASE_URL}/storage/v1/object/practitioner-photos/practitioners/stephanie-smit-dental-reflections.jpg',
    headers={'Authorization': f'Bearer {JWT}', 'Content-Type': 'image/jpeg', 'x-upsert': 'true'},
    data=r.content, timeout=30, verify=False)
print(f'Upload: {up.status_code}')

if up.ok:
    photo = f'{BUCKET}/stephanie-smit-dental-reflections.jpg'
    for pid in [865, 898, 915]:
        print(q(f"UPDATE clinic_practitioners SET photo_url = '{photo}' WHERE id = {pid} RETURNING id, name"))

print('Done.')
