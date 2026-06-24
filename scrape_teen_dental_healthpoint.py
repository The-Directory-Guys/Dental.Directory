"""
Scrape Healthpoint for teen dental providers (funded=9to18) and cross-reference
with our Supabase dental_clinics database to identify matching clinic IDs.

Output: healthpoint_teen_dental.json  — raw Healthpoint list
        teen_dental_matches.json       — matched clinic IDs
        teen_dental_unmatched.json     — Healthpoint entries with no DB match
"""

import os, sys, json, time, re
import requests
from bs4 import BeautifulSoup
from difflib import SequenceMatcher
from dotenv import load_dotenv

load_dotenv()
SUPABASE_URL = os.environ['SUPABASE_URL']
SUPABASE_KEY = os.environ['SUPABASE_SERVICE_KEY']
SB_HEADERS = {'apikey': SUPABASE_KEY, 'Authorization': f'Bearer {SUPABASE_KEY}'}

HP_BASE = 'https://www.healthpoint.co.nz/dentistry/'
RESULTS_PER_PAGE = 40
TOTAL_RESULTS = 689


def normalize_phone(phone_str):
    """Strip all non-digits from phone, then normalise to a comparable string."""
    if not phone_str:
        return ''
    digits = re.sub(r'\D', '', phone_str)
    # NZ numbers: strip leading 0 and country code if present
    if digits.startswith('640'):
        digits = digits[2:]   # 640x... → 0x...
    elif digits.startswith('64'):
        digits = '0' + digits[2:]  # 64x... → 0x...
    return digits


def scrape_healthpoint():
    """Scrape all teen dental providers from Healthpoint."""
    providers = []
    session = requests.Session()
    session.headers.update({
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
        'Accept': 'text/html,application/xhtml+xml',
    })

    offsets = list(range(0, TOTAL_RESULTS + RESULTS_PER_PAGE, RESULTS_PER_PAGE))
    for offset in offsets:
        if offset == 0:
            url = HP_BASE + '?funded=9to18'
        else:
            url = HP_BASE + f'?funded=9to18&services={offset}'

        print(f'Fetching offset {offset}...')
        try:
            r = session.get(url, timeout=15)
            if r.status_code != 200:
                print(f'  HTTP {r.status_code}, skipping')
                continue

            soup = BeautifulSoup(r.text, 'html.parser')
            lis = [li for li in soup.find_all('li') if li.find('h4')]

            for li in lis:
                h4 = li.find('h4')
                name = h4.get_text(strip=True)

                # Extract phone from tel: link
                tel_link = li.find('a', href=re.compile(r'^tel:'))
                phone_raw = ''
                if tel_link:
                    phone_raw = tel_link['href'].replace('tel:', '').strip()

                # Extract Healthpoint URL slug
                name_link = h4.find('a')
                hp_url = name_link['href'] if name_link and name_link.get('href') else ''

                providers.append({
                    'name': name,
                    'phone_raw': phone_raw,
                    'phone_norm': normalize_phone(phone_raw),
                    'hp_url': hp_url,
                })

            print(f'  Got {len(lis)} results, total: {len(providers)}')
            time.sleep(0.6)

        except Exception as e:
            print(f'  Error at offset {offset}: {e}')

    # Deduplicate by normalised phone, then by name
    seen_phones = set()
    seen_names = set()
    unique = []
    for p in providers:
        key_p = p['phone_norm']
        key_n = p['name'].lower().strip()
        if key_p and key_p in seen_phones:
            continue
        if key_n in seen_names:
            continue
        if key_p:
            seen_phones.add(key_p)
        seen_names.add(key_n)
        unique.append(p)

    print(f'\nTotal unique HP providers: {len(unique)}')
    return unique


def fetch_our_clinics():
    """Fetch all clinics from Supabase."""
    all_clinics = []
    offset = 0
    while True:
        r = requests.get(
            f'{SUPABASE_URL}/rest/v1/dental_clinics?select=id,name,suburb_town,city,region,services,phone_national,phone_international&business_status=eq.OPERATIONAL&limit=1000&offset={offset}',
            headers=SB_HEADERS
        )
        batch = r.json()
        if not batch:
            break
        all_clinics.extend(batch)
        offset += 1000
        if len(batch) < 1000:
            break

    # Build phone lookup: normalised phone → clinic
    phone_lookup = {}
    for c in all_clinics:
        for field in ('phone_national', 'phone_international'):
            norm = normalize_phone(c.get(field, '') or '')
            if norm and len(norm) >= 7:
                phone_lookup.setdefault(norm, []).append(c)

    print(f'Fetched {len(all_clinics)} clinics, {len(phone_lookup)} unique phone entries')
    return all_clinics, phone_lookup


def normalize_name(s):
    """Lowercase + strip punctuation for name fuzzy matching."""
    s = s.lower().strip()
    s = re.sub(r'[^a-z0-9\s]', ' ', s)
    s = re.sub(r'\s+', ' ', s).strip()
    for suffix in ['ltd', 'limited', 'dental surgery', 'dental clinic', 'dental centre',
                   'dental center', 'dental practice', 'dentistry', 'dental']:
        s = re.sub(rf'\b{suffix}\b', '', s)
    return s.strip()


def name_sim(a, b):
    return SequenceMatcher(None, normalize_name(a), normalize_name(b)).ratio()


def match_providers(hp_providers, our_clinics, phone_lookup):
    """Match Healthpoint providers to our clinic IDs."""
    matches = []
    unmatched = []
    NAME_THRESHOLD = 0.72

    for hp in hp_providers:
        matched = None
        method = ''

        # 1. Phone match (most reliable)
        if hp['phone_norm'] and len(hp['phone_norm']) >= 7:
            candidates = phone_lookup.get(hp['phone_norm'], [])
            if len(candidates) == 1:
                matched = candidates[0]
                method = 'phone_exact'
            elif len(candidates) > 1:
                # Pick by best name match
                best = max(candidates, key=lambda c: name_sim(hp['name'], c['name']))
                matched = best
                method = 'phone+name'

        # 2. Name fuzzy match fallback
        if not matched:
            best_score = 0
            best_clinic = None
            for clinic in our_clinics:
                score = name_sim(hp['name'], clinic['name'])
                if score > best_score:
                    best_score = score
                    best_clinic = clinic
            if best_score >= NAME_THRESHOLD:
                matched = best_clinic
                method = f'name_fuzzy({best_score:.2f})'

        if matched:
            matches.append({
                'clinic_id': matched['id'],
                'clinic_name': matched['name'],
                'clinic_suburb': matched.get('suburb_town', ''),
                'clinic_region': matched.get('region', ''),
                'hp_name': hp['name'],
                'hp_phone': hp['phone_raw'],
                'method': method,
            })
        else:
            unmatched.append({
                'hp_name': hp['name'],
                'hp_phone': hp['phone_raw'],
                'hp_url': hp['hp_url'],
            })

    # Deduplicate matched clinic_ids (keep first occurrence)
    seen_ids = set()
    deduped = []
    for m in matches:
        if m['clinic_id'] not in seen_ids:
            seen_ids.add(m['clinic_id'])
            deduped.append(m)

    print(f'Matched: {len(deduped)} unique clinics, Unmatched: {len(unmatched)}')
    return deduped, unmatched


def update_supabase(clinic_ids, dry_run=False):
    """Add 'Teen Dental' to the services field for matched clinic IDs."""
    if not clinic_ids:
        print('No clinic IDs to update')
        return 0

    ids_str = ','.join(str(i) for i in clinic_ids)
    r = requests.get(
        f'{SUPABASE_URL}/rest/v1/dental_clinics?id=in.({ids_str})&select=id,name,services',
        headers=SB_HEADERS
    )
    clinics = r.json()

    updated = 0
    already = 0
    for clinic in clinics:
        current = clinic.get('services') or ''
        parts = [s.strip() for s in current.split(',') if s.strip()]
        if 'Teen Dental' not in parts:
            parts.append('Teen Dental')
            new_services = ', '.join(parts)
            if dry_run:
                print(f'  [DRY RUN] Would update: {clinic["name"]} → {new_services}')
                updated += 1
            else:
                patch = requests.patch(
                    f'{SUPABASE_URL}/rest/v1/dental_clinics?id=eq.{clinic["id"]}',
                    headers={**SB_HEADERS, 'Content-Type': 'application/json', 'Prefer': 'return=minimal'},
                    json={'services': new_services}
                )
                if patch.status_code in (200, 204):
                    updated += 1
                else:
                    print(f'  FAILED {clinic["id"]}: {patch.status_code} {patch.text[:100]}')
        else:
            already += 1

    print(f'Updated: {updated}, Already had Teen Dental: {already}')
    return updated


if __name__ == '__main__':
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument('--skip-scrape', action='store_true', help='Use existing healthpoint_teen_dental.json')
    parser.add_argument('--dry-run', action='store_true', help='Show updates without writing to Supabase')
    parser.add_argument('--update', action='store_true', help='Actually write to Supabase')
    args = parser.parse_args()

    if args.skip_scrape and os.path.exists('healthpoint_teen_dental.json'):
        with open('healthpoint_teen_dental.json') as f:
            hp_providers = json.load(f)
        print(f'Loaded {len(hp_providers)} providers from healthpoint_teen_dental.json')
    else:
        print('=== Step 1: Scrape Healthpoint ===')
        hp_providers = scrape_healthpoint()
        with open('healthpoint_teen_dental.json', 'w') as f:
            json.dump(hp_providers, f, indent=2)
        print(f'Saved to healthpoint_teen_dental.json')

    print('\n=== Step 2: Fetch our clinics ===')
    our_clinics, phone_lookup = fetch_our_clinics()

    print('\n=== Step 3: Match providers ===')
    matches, unmatched = match_providers(hp_providers, our_clinics, phone_lookup)

    with open('teen_dental_matches.json', 'w') as f:
        json.dump(matches, f, indent=2)
    with open('teen_dental_unmatched.json', 'w') as f:
        json.dump(unmatched, f, indent=2)

    print(f'\nSample matches:')
    for m in matches[:15]:
        print(f'  [{m["method"]}] {m["hp_name"]} → {m["clinic_name"]} ({m["clinic_suburb"]})')

    if args.update:
        print('\n=== Step 4: Update Supabase ===')
        clinic_ids = [m['clinic_id'] for m in matches]
        update_supabase(clinic_ids, dry_run=args.dry_run)
    else:
        print(f'\nReview teen_dental_matches.json, then rerun with --update to write to Supabase.')
        print(f'Use --dry-run --update to preview changes without writing.')
