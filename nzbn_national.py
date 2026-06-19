import requests
import json
import sys
import os
import urllib3
from dotenv import load_dotenv

urllib3.disable_warnings()
sys.stdout.reconfigure(encoding='utf-8')
load_dotenv()

NZBN_KEY = os.getenv('NZBN_API_KEY')
SUPABASE_URL = os.getenv('SUPABASE_URL')
SUPABASE_KEY = os.getenv('SUPABASE_SERVICE_KEY')

NZBN_BASE = 'https://api.business.govt.nz/gateway/nzbn/v5'
NZBN_HEADERS = {'Ocp-Apim-Subscription-Key': NZBN_KEY}
SUPABASE_HEADERS = {'apikey': SUPABASE_KEY, 'Authorization': f'Bearer {SUPABASE_KEY}'}

EXCLUDE_KEYWORDS = [
    'orthodont', 'laboratory', ' lab ', ' labs ', 'lab limited', 'lab ltd',
    'engineering', 'equipment', 'instrument', 'marketing', 'association',
    'incorporated', 'holdings', 'properties', 'property', ' trust',
    'supplies', 'supply', 'pet dentistry', 'ebos', 'denttech', 'dentalmate',
    'social housing', 'ceramics', 'fabricat', 'technolog', 'manufactur',
    'investment', 'ventures', 'capital ', 'group properties', 'dental works',
    'dental creations', 'dental engineering', 'dental equipment',
    'nz dental association', 'dental association', 'insurance',
    'whitening', 'bleach', 'consulting', 'management', 'services limited'
]

# Keywords that suggest a real clinic despite being in the exclude list
INCLUDE_OVERRIDE = ['dental services limited']  # keep these (e.g. sole trader clinics)


def is_likely_clinic(name):
    name_lower = name.lower()
    for kw in EXCLUDE_KEYWORDS:
        if kw in name_lower:
            # Check overrides
            if any(ov in name_lower for ov in INCLUDE_OVERRIDE):
                return True
            return False
    return True


def fetch_supabase_clinics():
    clinics = []
    offset = 0
    while True:
        r = requests.get(
            f'{SUPABASE_URL}/rest/v1/dental_clinics',
            headers=SUPABASE_HEADERS,
            params={'select': 'id,name,city,address,legal_business_name', 'limit': 1000, 'offset': offset},
            verify=False,
        )
        batch = r.json()
        if not batch:
            break
        clinics.extend(batch)
        if len(batch) < 1000:
            break
        offset += 1000
    return clinics


def get_entity_detail(nzbn):
    try:
        r = requests.get(
            f'{NZBN_BASE}/entities/{nzbn}',
            headers=NZBN_HEADERS,
            verify=False,
            timeout=15,
        )
        d = r.json()
        address = ''
        street = ''
        city = ''
        for addr in d.get('addresses', {}).get('addressList', []):
            if addr.get('addressType') in ('OFFICE', 'REGISTERED') and not addr.get('endDate'):
                street = addr.get('address1', '') or ''
                city = addr.get('address3', '') or addr.get('address2', '') or ''
                address = ', '.join(x for x in [street, addr.get('address2'), city, addr.get('postCode')] if x)
                break
        websites = d.get('websites', [])
        website = websites[0].get('url', '') if websites else ''
        phones = d.get('phoneNumbers', [])
        phone = ''
        for p in phones:
            if p.get('phonePurpose') == 'main':
                phone = f"{p.get('phoneAreaCode', '')} {p.get('phoneNumber', '')}"
                break
        trading_list = d.get('tradingNames', {})
        if isinstance(trading_list, dict):
            trading = [t.get('name') for t in trading_list.get('tradingNameList', [])
                       if t.get('name') and not t.get('endDate') and t.get('name') != 'No trading name']
        else:
            trading = []
        return {'address': address, 'street': street, 'city': city, 'website': website, 'phone': phone, 'trading': trading}
    except Exception:
        return {'address': '', 'street': '', 'city': '', 'website': '', 'phone': '', 'trading': []}


def address_in_db(street, city, db_clinics):
    if not street:
        return []
    street_lower = street.lower().strip()
    # Extract street number and name
    parts = street_lower.split()
    # Try matching on key words from street (skip number)
    street_words = [p for p in parts if not p.isdigit() and len(p) > 2]
    matches = []
    for c in db_clinics:
        addr = (c.get('address') or '').lower()
        if street_words and all(w in addr for w in street_words[:2]):
            matches.append(c)
    return matches


def main():
    print('Loading nzbn_unmatched.json...')
    with open('nzbn_unmatched.json', encoding='utf-8') as f:
        unmatched = json.load(f)
    print(f'Total unmatched: {len(unmatched)}')

    print('Fetching Supabase clinics...')
    db_clinics = fetch_supabase_clinics()
    print(f'Total DB clinics: {len(db_clinics)}\n')

    # Filter to likely clinics
    candidates = [e for e in unmatched if is_likely_clinic(e['name'])]
    print(f'After filtering non-clinics: {len(candidates)} candidates\n')

    results = {
        'already_in_db': [],
        'possibly_missing': [],
    }

    for i, entity in enumerate(candidates):
        if (i + 1) % 25 == 0:
            print(f'  {i + 1}/{len(candidates)} processed...')

        detail = get_entity_detail(entity['nzbn'])
        street = detail['street']
        city = detail['city']

        db_matches = address_in_db(street, city, db_clinics)

        entry = {
            'name': entity['name'],
            'trading': detail['trading'],
            'nzbn': entity['nzbn'],
            'city': city,
            'address': detail['address'],
            'website': detail['website'],
            'phone': detail['phone'],
        }

        if db_matches:
            entry['db_matches'] = [{'id': m['id'], 'name': m['name']} for m in db_matches]
            results['already_in_db'].append(entry)
        else:
            results['possibly_missing'].append(entry)

    # Save results
    with open('nzbn_national_results.json', 'w', encoding='utf-8') as f:
        json.dump(results, f, indent=2, ensure_ascii=False)

    print(f'\n=== RESULTS ===')
    print(f'Already in DB (different legal name): {len(results["already_in_db"])}')
    print(f'Possibly missing from DB: {len(results["possibly_missing"])}')
    print()

    # Print missing grouped by city
    by_city = {}
    for e in results['possibly_missing']:
        city = e['city'] or 'Unknown'
        by_city.setdefault(city, []).append(e)

    print('=== POSSIBLY MISSING — by city ===\n')
    for city in sorted(by_city.keys()):
        print(f'--- {city} ({len(by_city[city])}) ---')
        for e in by_city[city]:
            trading = f' (trading as: {", ".join(e["trading"])})' if e['trading'] else ''
            print(f'  {e["name"]}{trading}')
            print(f'    {e["address"]}')
            if e['website']:
                print(f'    {e["website"]}')
        print()

    print('\n=== ALREADY IN DB (different legal name) ===\n')
    for e in results['already_in_db']:
        matches = ', '.join(m['name'] for m in e['db_matches'])
        print(f'  {e["name"]} → {matches} ({e["city"]})')

    print('\nFull results saved to nzbn_national_results.json')


if __name__ == '__main__':
    main()
