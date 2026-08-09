import requests, sys, io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
from bs4 import BeautifulSoup
from dotenv import load_dotenv
import os
load_dotenv(r'c:\Users\Ciaran\Desktop\Dental_Directory\.env')
MGMT_KEY = os.environ['SUPABASE_MANAGEMENT_KEY']

def q(sql):
    r = requests.post('https://api.supabase.com/v1/projects/ankyjpgcocsvvtyyymys/database/query',
        headers={'Authorization': f'Bearer {MGMT_KEY}', 'Content-Type': 'application/json'},
        json={'query': sql}, verify=False)
    return r.json()

rows = q("SELECT id, name FROM dental_clinics WHERE name ILIKE '%waimea dental%'")
for r in rows: print(r)
cid = rows[0]['id'] if rows else None

if cid:
    print('\n=== practitioners ===')
    for r in q(f'SELECT id, name, experience, bio, photo_url FROM clinic_practitioners WHERE clinic_id = {cid}'): print(r)

print('\n=== WEBSITE ===')
r = requests.get('https://www.waimeadental.co.nz/endodontist-nelson-richmond',
    verify=False, headers={'User-Agent': 'Mozilla/5.0'}, timeout=15)
soup = BeautifulSoup(r.text, 'html.parser')
for tag in soup.find_all(['h1','h2','h3','p','li']):
    t = tag.get_text(' ', strip=True)
    if t and len(t) > 15:
        print(f'[{tag.name}] {t}')
imgs = [img.get('src','') for img in soup.find_all('img') if img.get('src') and 'logo' not in img.get('src','').lower()]
print(f'\nImages: {imgs[:10]}')
