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
        resp = requests.get(img_url, timeout=20, verify=False, headers={'User-Agent': 'Mozilla/5.0'})
        if not resp.ok:
            print(f'  Download failed {resp.status_code}: {img_url}')
            return None
        ext = img_url.split('?')[0].split('.')[-1].lower()
        if ext not in ('jpg', 'jpeg', 'png', 'webp'):
            ext = 'jpg'
        fname = f'{filename}.{ext}'
        content_type = {'jpg': 'image/jpeg', 'jpeg': 'image/jpeg', 'png': 'image/png', 'webp': 'image/webp'}.get(ext, 'image/jpeg')
        up = requests.post(
            f'{SUPABASE_URL}/storage/v1/object/practitioner-photos/practitioners/{fname}',
            headers={'Authorization': f'Bearer {STORAGE_JWT}', 'Content-Type': content_type, 'x-upsert': 'true'},
            data=resp.content, timeout=30, verify=False)
        if up.ok:
            url = f'{BUCKET_BASE}/{fname}'
            print(f'  Uploaded: {fname}')
            return url
        print(f'  Upload failed {up.status_code}: {up.text[:120]}')
        return None
    except Exception as e:
        print(f'  Error: {e}')
        return None

# ── Munro Dental (clinic_id=1667) ────────────────────────────────────────────
SQ = 'https://images.squarespace-cdn.com/content/v1/5efa885720ccac1eaafe7b40'
munro_team = [
    {'id': 736, 'photo': f'{SQ}/1602198972472-2LSSOBF2X20PMPPM9DGH/Alex+Munro+Munro+Dental.jpeg', 'slug': 'alex-munro-munro-dental'},
    {'id': 737, 'photo': f'{SQ}/a50f1187-ba8b-44ab-93aa-0fd0096523e2/Amy.jpg', 'slug': 'amy-langfield-munro-dental'},
    {'id': 738, 'photo': f'{SQ}/b91aea61-e487-43ae-9f7e-c816de7425e4/Riley+copy.jpg', 'slug': 'riley-thoroughgood-munro-dental'},
    {'id': 739, 'photo': f'{SQ}/7f09210a-d4d1-45a9-8a2a-8d7bee110701/Olive+Kennedy.jpg', 'slug': 'olive-kennedy-munro-dental'},
    {'id': 740, 'photo': f'{SQ}/7ae230b9-3ac6-4441-94f3-9660a865d53a/Shedya+Pirkaman.jpg', 'slug': 'sheyda-pirkaman-munro-dental'},
    {'id': 742, 'photo': f'{SQ}/098d5911-b4da-4eb3-8e1c-e983022e7b66/Rachel.jpg', 'slug': 'rachel-tiplady-munro-dental'},
    {'id': 743, 'photo': f'{SQ}/bd8cb32a-d6c3-4a38-ac88-0b4ee0102c0d/Karen.jpg', 'slug': 'karen-mclean-munro-dental'},
    {'id': 744, 'photo': f'{SQ}/5189b14b-01e0-4092-b639-9c1732f6db48/Jade+Kenning.jpg', 'slug': 'jade-kenning-munro-dental'},
    {'id': 745, 'photo': f'{SQ}/270c77e9-98f1-456b-8aba-c38ded708555/Phoenix.jpg', 'slug': 'phoenix-flutey-tapata-munro-dental'},
    {'id': 746, 'photo': f'{SQ}/ad086107-049a-467d-9c4a-ae0c6c10d3af/Jacqueline+Clark.jpg', 'slug': 'jacqueline-clarke-munro-dental'},
]
print('=== Munro Dental photos ===')
SOURCE_MUNRO = 'https://www.munrodental.co.nz/our-team-munro-dental-patient-care'
for p in munro_team:
    url = upload_photo(p['photo'], p['slug'])
    if url:
        res = q(f"UPDATE clinic_practitioners SET photo_url = '{url}', source_url = '{SOURCE_MUNRO}' WHERE id = {p['id']}")
        print(f"  DB updated id={p['id']}: {res}")

# ── Steph Wills (practitioner ids 757 and 771) ────────────────────────────────
print('\n=== Steph Wills photo ===')
SOURCE_SW = 'https://www.stephwillsdental.co.nz/our-team'
STEPH_IMG = 'https://static.wixstatic.com/media/1e8d6f_f44a9edf8e82401cad31ef963a2c25ab~mv2.jpg'
steph_url = upload_photo(STEPH_IMG, 'steph-wills-dental')
if steph_url:
    for pid in (757, 771):
        res = q(f"UPDATE clinic_practitioners SET photo_url = '{steph_url}', source_url = '{SOURCE_SW}' WHERE id = {pid}")
        print(f"  DB updated id={pid}: {res}")

# Also update Steph's experience/bio in both records
bio = "Has 40 years experience in dentistry, having worked in hospital and private practice in Invercargill, NHS and private practice in Wales, and in Motueka since 1998. Bought the practice in 2000. Especially interested in the restoration of worn dentition."
for pid in (757, 771):
    res = q(f"""UPDATE clinic_practitioners SET
        experience = $$BDS (Otago) 1998, DipClinDent (Otago) (Paeds) 1994$$,
        specialties = $$General dentistry, restoration of worn dentition, paediatric dentistry$$,
        bio = $${bio}$$
    WHERE id = {pid}""")
    print(f"  Bio/exp updated id={pid}: {res}")

# ── Pearl of Ahuriri — clinic space photos ────────────────────────────────────
print('\n=== Pearl of Ahuriri clinic photos ===')
SQ_POA = 'https://images.squarespace-cdn.com/content/v1/619d626a4012a442c7c164c6'
clinic_photos = [
    (f'{SQ_POA}/e1cfd8f1-d02d-451e-a091-084b8ec9086d/POA+%282%29.jpg', 'pearl-of-ahuriri-clinic-1'),
    (f'{SQ_POA}/cd9723e5-4bd6-4222-ae90-4cb16e592986/POA+%284%29.jpg', 'pearl-of-ahuriri-clinic-2'),
    (f'{SQ_POA}/93cc5a27-81c9-482b-9eca-e83c865bd966/Image+3.jpg',       'pearl-of-ahuriri-clinic-3'),
    (f'{SQ_POA}/1683839018477-0T1T2HG6T28W3IVS9R1F/image-asset.jpeg',   'pearl-of-ahuriri-clinic-4'),
    (f'{SQ_POA}/62a75983-8eca-4599-9d98-5b1b5e934b08/20221110_120256.jpg','pearl-of-ahuriri-clinic-5'),
    (f'{SQ_POA}/ffa9bf70-02eb-44a8-9417-6fefba5b011d/20221110_120247.jpg','pearl-of-ahuriri-clinic-6'),
]
uploaded_clinic_photos = []
for img_url, slug in clinic_photos:
    url = upload_photo(img_url, slug)
    if url:
        uploaded_clinic_photos.append(url)

# Set first uploaded photo as the clinic's photo_url
if uploaded_clinic_photos:
    res = q(f"UPDATE dental_clinics SET photo_url = '{uploaded_clinic_photos[0]}' WHERE id = 1535")
    print(f"  Clinic photo_url set: {res}")
    print(f"  All uploaded ({len(uploaded_clinic_photos)}): {uploaded_clinic_photos}")

print('\nDone.')
