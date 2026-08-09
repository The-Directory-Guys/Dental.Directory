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

print('=== DB ===')
rows = q("SELECT id, name, description, website, photo_url FROM dental_clinics WHERE name ILIKE '%max facs%' OR name ILIKE '%maxfacs%'")
for r in rows: print(r)
cid = rows[0]['id'] if rows else None
if cid:
    print('\n=== practitioners ===')
    for r in q(f'SELECT id, name, experience, bio, photo_url FROM clinic_practitioners WHERE clinic_id = {cid} ORDER BY id'): print(r)

print('\n=== WEBSITE ===')
HEADERS = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36',
           'Accept': 'text/html,application/xhtml+xml,*/*;q=0.8'}
r = requests.get('https://maxfacsoralsurgery.co.nz/about', verify=False, headers=HEADERS, timeout=15)
print(f'Status: {r.status_code}')
soup = BeautifulSoup(r.text, 'html.parser')
for tag in soup.find_all(['h1','h2','h3','h4','p','li']):
    t = tag.get_text(' ', strip=True)
    if t and len(t) > 10:
        print(f'[{tag.name}] {t}')
imgs = [img.get('src','') for img in soup.find_all('img') if img.get('src','').startswith('http') and 'logo' not in img.get('src','').lower()]
print(f'\nImages: {imgs[:12]}')
