import requests, sys, io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
from bs4 import BeautifulSoup

HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36',
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
    'Accept-Language': 'en-NZ,en;q=0.9',
    'Accept-Encoding': 'gzip, deflate, br',
    'Connection': 'keep-alive',
}

for url in ['https://www.dentalaesthetics.co.nz/our-team/', 'https://www.dentalaesthetics.co.nz/']:
    print(f'\n=== {url} ===')
    r = requests.get(url, verify=False, headers=HEADERS, timeout=15)
    print(f'Status: {r.status_code}')
    soup = BeautifulSoup(r.text, 'html.parser')
    for tag in soup.find_all(['h1','h2','h3','h4','p','li']):
        t = tag.get_text(' ', strip=True)
        if t and len(t) > 10:
            print(f'[{tag.name}] {t}')
    imgs = [img.get('src','') for img in soup.find_all('img') if img.get('src','') and 'logo' not in img.get('src','').lower() and img.get('src','').startswith('http')]
    print(f'Images: {imgs[:15]}')
