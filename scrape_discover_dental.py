import requests, sys, io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
from bs4 import BeautifulSoup
from dotenv import load_dotenv
import os
load_dotenv(r'c:\Users\Ciaran\Desktop\Dental_Directory\.env')
MGMT = os.environ['SUPABASE_MANAGEMENT_KEY']

def q(sql):
    r = requests.post('https://api.supabase.com/v1/projects/ankyjpgcocsvvtyyymys/database/query',
        headers={'Authorization': f'Bearer {MGMT}', 'Content-Type': 'application/json'},
        json={'query': sql}, verify=False)
    return r.json()

HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36',
    'Accept': 'text/html,application/xhtml+xml,*/*;q=0.8',
    'Accept-Language': 'en-NZ,en;q=0.9',
}

print('=== DB ===')
clinics = q("SELECT id, name, website, category FROM dental_clinics WHERE name ILIKE '%discover dental%'")
for c in clinics:
    print(c)
    practs = q(f"SELECT id, name, bio FROM clinic_practitioners WHERE clinic_id = {c['id']}")
    for p in practs:
        print(f"  -> {p['id']} | {p['name']} | bio={'yes' if p['bio'] else 'NO'}")

print('\n=== WEBSITE ===')
r = requests.get('https://www.discoverdental.co.nz/our-team', verify=False, headers=HEADERS, timeout=15)
print(f'Status: {r.status_code}')
soup = BeautifulSoup(r.text, 'html.parser')

for tag in soup.find_all(['h1','h2','h3','h4','p','li']):
    t = tag.get_text(' ', strip=True)
    if t and len(t) > 10:
        print(f'[{tag.name}] {t}')

imgs = [img.get('src','') for img in soup.find_all('img')
        if img.get('src','') and 'logo' not in img.get('src','').lower()
        and img.get('src','').startswith('http')]
print(f'\nImages: {imgs[:20]}')
