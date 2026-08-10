import requests, sys, io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
from bs4 import BeautifulSoup
from dotenv import load_dotenv
import os
load_dotenv(r'c:\Users\Ciaran\Desktop\Dental_Directory\.env')

HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36',
    'Accept': 'text/html,application/xhtml+xml,*/*;q=0.8',
    'Accept-Language': 'en-NZ,en;q=0.9',
}

r = requests.get('https://www.discoverdental.co.nz/our-team', verify=False, headers=HEADERS, timeout=15)
soup = BeautifulSoup(r.text, 'html.parser')

# All img tags with any src/data-src
print('=== ALL IMAGES (any src) ===')
for img in soup.find_all('img'):
    src = img.get('src') or img.get('data-src') or img.get('data-lazy-src') or ''
    alt = img.get('alt', '')
    if src and 'logo' not in src.lower() and 'icon' not in src.lower():
        print(f'  alt="{alt}" src="{src}"')

# Background images in style attributes
print('\n=== BACKGROUND IMAGES ===')
for tag in soup.find_all(style=True):
    style = tag.get('style', '')
    if 'url(' in style:
        print(f'  {style[:200]}')

# Look for any JSON data (React/Vue props) containing image URLs
print('\n=== SCRIPT DATA (image refs) ===')
for script in soup.find_all('script'):
    text = script.string or ''
    if 'team' in text.lower() or '.jpg' in text or '.png' in text or '.webp' in text:
        lines = [l.strip() for l in text.split('\n') if ('.jpg' in l or '.png' in l or '.webp' in l) and len(l.strip()) < 300]
        for l in lines[:10]:
            print(f'  {l}')
