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
rows = q("SELECT id, name, category, description, photo_url FROM dental_clinics WHERE id = 2923")
for r in rows: print(r)
print()
for r in q("SELECT treatment, price_label, notes FROM scraped_prices WHERE clinic_id = 2923"): print(r)
for r in q("SELECT * FROM clinic_amenities WHERE clinic_id = 2923"): print(r)

for url in ['https://sparklewhite.co.nz/', 'https://sparklewhite.co.nz/services', 'https://sparklewhite.co.nz/pricing']:
    print(f'\n=== {url} ===')
    try:
        r = requests.get(url, verify=False, headers={'User-Agent': 'Mozilla/5.0'}, timeout=15)
        soup = BeautifulSoup(r.text, 'html.parser')
        for tag in soup.find_all(['h1','h2','h3','h4','p','li']):
            t = tag.get_text(' ', strip=True)
            if t and len(t) > 10:
                print(f'[{tag.name}] {t}')
        imgs = [img.get('src','') for img in soup.find_all('img') if img.get('src') and len(img.get('src','')) > 5]
        print(f'Images: {imgs[:8]}')
    except Exception as e:
        print(f'Error: {e}')
