import requests, sys, io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
from bs4 import BeautifulSoup

r = requests.get('https://www.tahunanuidental.co.nz/', verify=False, headers={'User-Agent': 'Mozilla/5.0'}, timeout=15)
soup = BeautifulSoup(r.text, 'html.parser')
print('=== PAGE TEXT ===')
for tag in soup.find_all(['h1','h2','h3','p','li']):
    t = tag.get_text(' ', strip=True)
    if t and len(t) > 10:
        print(f'[{tag.name}] {t[:200]}')
