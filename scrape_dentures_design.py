import requests, sys, io, re
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
rows = q("SELECT id, name, description, founded_year, website, photo_url FROM dental_clinics WHERE name ILIKE '%dentures by design%'")
for r in rows: print(r)
cid = rows[0]['id'] if rows else None

if cid:
    print('\n=== practitioners ===')
    for r in q(f'SELECT id, name, experience, bio, photo_url FROM clinic_practitioners WHERE clinic_id = {cid}'): print(r)
    print('\n=== scraped_prices ===')
    for r in q(f'SELECT treatment, price_label FROM scraped_prices WHERE clinic_id = {cid}'): print(r)
    print('\n=== amenities ===')
    for r in q(f'SELECT payment_partners, membership_plans FROM clinic_amenities WHERE clinic_id = {cid}'): print(r)

# Scrape main page and about page
for url in ['https://www.denturesbydesignnz.com/', 'https://www.denturesbydesignnz.com/about']:
    print(f'\n=== {url} ===')
    try:
        r = requests.get(url, verify=False, headers={'User-Agent': 'Mozilla/5.0'}, timeout=15)
        soup = BeautifulSoup(r.text, 'html.parser')
        for tag in soup.find_all(['h1','h2','h3','p','li']):
            t = tag.get_text(' ', strip=True)
            if t and len(t) > 15:
                print(f'[{tag.name}] {t}')
        # Find images
        imgs = [img.get('src','') for img in soup.find_all('img') if img.get('src')]
        print(f'Images: {imgs[:10]}')
    except Exception as e:
        print(f'Error: {e}')
