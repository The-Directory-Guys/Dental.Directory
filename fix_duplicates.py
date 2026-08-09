import sys, io, requests, os
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
from dotenv import load_dotenv
load_dotenv(r'c:\Users\Ciaran\Desktop\Dental_Directory\.env')
MGMT_KEY = os.environ['SUPABASE_MANAGEMENT_KEY']
SUPABASE_URL = os.environ['SUPABASE_URL']
JWT = os.environ['SUPABASE_JWT']
BUCKET = f'{SUPABASE_URL}/storage/v1/object/public/practitioner-photos/practitioners'

def q(sql):
    r = requests.post('https://api.supabase.com/v1/projects/ankyjpgcocsvvtyyymys/database/query',
        headers={'Authorization': f'Bearer {MGMT_KEY}', 'Content-Type': 'application/json'},
        json={'query': sql}, verify=False)
    return r.json()

def upload(img_url, slug):
    r = requests.get(img_url, timeout=20, verify=False, headers={'User-Agent': 'Mozilla/5.0'})
    ext = img_url.split('?')[0].split('.')[-1].lower()
    if ext not in ('jpg','jpeg','png','webp'): ext = 'jpg'
    fname = f'{slug}.{ext}'
    ct = {'jpg':'image/jpeg','jpeg':'image/jpeg','png':'image/png','webp':'image/webp'}.get(ext,'image/jpeg')
    up = requests.post(f'{SUPABASE_URL}/storage/v1/object/practitioner-photos/practitioners/{fname}',
        headers={'Authorization': f'Bearer {JWT}', 'Content-Type': ct, 'x-upsert': 'true'},
        data=r.content, timeout=30, verify=False)
    if up.ok:
        print(f'  Uploaded {fname}')
        return f'{BUCKET}/{fname}'
    print(f'  Upload failed: {up.text[:80]}')
    return None

# Delete Quin Dental originals (bare entries, superseded by 3817-3826)
print('Deleting Quin Dental originals 717-721...')
print(q('DELETE FROM clinic_practitioners WHERE id IN (717,718,719,720,721)'))

# Delete Bays Dentures duplicate
print('Deleting Bays Dentures duplicate 3816...')
print(q('DELETE FROM clinic_practitioners WHERE id = 3816'))

# Upload correct Daniela photo and update id 779
print('Uploading Daniela Steenpass photo...')
daniela_url = 'https://images.squarespace-cdn.com/content/v1/592fe418c534a5187d6fd365/1506074277918-0SU0BBBZB8DPOZSC9CSW/Daniela.jpg?format=1000w'
photo = upload(daniela_url, 'daniela-steenpass-bays-dentures')
if photo:
    print(q(f"UPDATE clinic_practitioners SET photo_url = '{photo}' WHERE id = 779"))

print('Done.')
