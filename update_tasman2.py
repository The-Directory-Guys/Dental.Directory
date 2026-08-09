import requests, sys, io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
from dotenv import load_dotenv
import os
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

def upload(img_url, slug, ext='jpg'):
    r = requests.get(img_url, timeout=20, verify=False, headers={'User-Agent': 'Mozilla/5.0'})
    if not r.ok: print(f'  Download failed {r.status_code}'); return None
    fname = f'{slug}.{ext}'
    up = requests.post(f'{SUPABASE_URL}/storage/v1/object/practitioner-photos/practitioners/{fname}',
        headers={'Authorization': f'Bearer {JWT}', 'Content-Type': 'image/jpeg', 'x-upsert': 'true'},
        data=r.content, timeout=30, verify=False)
    if up.ok: print(f'  Uploaded {fname}'); return f'{BUCKET}/{fname}'
    print(f'  Upload failed: {up.text[:80]}'); return None

SOURCE = 'https://www.tasmandental.co.nz/about-tasman-dental/'

# 1. Fix description — remove em dash
desc = "Located in the Lower Queen Street Health complex in Richmond, a comprehensive health centre also home to a general medical practice and medical specialists. Offering a relaxed, honest and thorough style of dentistry centred on high quality care, with a focus on helping patients overcome the common obstacles of cost, anxiety and dental complacency."
print(q(f"UPDATE dental_clinics SET description = $${desc}$$ WHERE id = 1682 RETURNING id"))

# 2. Standardise scraped_prices labels
# "Student discount" → "Free teen dental care"
print(q("""UPDATE scraped_prices
    SET treatment = 'Free teen dental care',
        price_label = 'Free dental care for eligible students aged 13-17 under the NZ Dental Benefits Scheme'
    WHERE clinic_id = 1682 AND treatment = 'Student discount' RETURNING treatment"""))

# "WINZ" label stays; update price_label to standard form
print(q("""UPDATE scraped_prices
    SET price_label = 'Work and Income (WINZ) dental treatment grants accepted'
    WHERE clinic_id = 1682 AND treatment = 'WINZ' RETURNING treatment"""))

# 3. Clear payment_partners — all entries duplicate scraped_prices pills
print(q("UPDATE clinic_amenities SET payment_partners = NULL WHERE clinic_id = 1682 RETURNING clinic_id"))

# 4. Upload clinic photo
print('\nClinic photo:')
clinic_photo = upload('https://www.tasmandental.co.nz/resources/uploads/LowerQueenStreetHealth.jpg', 'tasman-dental-centre-clinic')
if clinic_photo:
    print(q(f"UPDATE dental_clinics SET photo_url = '{clinic_photo}' WHERE id = 1682 RETURNING id"))

# 5. Upload Jonathan Clark photo (id 758)
print('\nJonathan Clark:')
j_photo = upload('https://www.tasmandental.co.nz/resources/uploads/Jonathan.jpg', 'jonathan-clark-tasman-dental')
if j_photo:
    print(q(f"UPDATE clinic_practitioners SET photo_url = '{j_photo}' WHERE id = 758 RETURNING id, name"))

# 6. Upload Ben Simmons photo (id 759)
print('\nBen Simmons:')
b_photo = upload('https://www.tasmandental.co.nz/resources/uploads/Ben.jpg', 'ben-simmons-tasman-dental')
if b_photo:
    print(q(f"UPDATE clinic_practitioners SET photo_url = '{b_photo}' WHERE id = 759 RETURNING id, name"))

print('\nDone.')
