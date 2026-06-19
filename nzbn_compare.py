import requests
import os
import json
import sys
import urllib3
from difflib import SequenceMatcher
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

# Classification codes to EXCLUDE (non-clinic businesses)
EXCLUDE_CLASSIFICATIONS = {
    'C241215',  # Denture fabrication
    'C241218',  # Dental equipment/supplies
    'C241219',  # Dental laboratory
}

# Classification codes known to be actual clinics
CLINIC_CLASSIFICATIONS = {
    'C241211',  # General dental practice
    'C241212',  # Specialist dental practice
    'C241213',  # Orthodontic practice
    'C241214',  # Other dental practice
}


def fetch_nzbn_dental():
    entities = []
    for term in ['dental', 'dentist', 'orthodont', 'smiles', 'oral health']:
        page = 0
        while True:
            r = requests.get(
                f'{NZBN_BASE}/entities',
                headers=NZBN_HEADERS,
                params={
                    'search-term': term,
                    'entity-status': 'REGISTERED',
                    'page-size': 200,
                    'page': page,
                },
                verify=False,
            )
            data = r.json()
            items = data.get('items', [])
            if not items:
                break
            entities.extend(items)
            total = data.get('totalItems', 0)
            print(f"  '{term}' page {page}: {len(items)} items (total {total})")
            if (page + 1) * 200 >= total:
                break
            page += 1
    # Deduplicate by NZBN
    seen = set()
    unique = []
    for e in entities:
        nzbn = e.get('nzbn')
        if nzbn not in seen:
            seen.add(nzbn)
            unique.append(e)
    return unique


def fetch_supabase_clinics():
    clinics = []
    offset = 0
    while True:
        r = requests.get(
            f'{SUPABASE_URL}/rest/v1/dental_clinics',
            headers=SUPABASE_HEADERS,
            params={'select': 'id,name,city,region,website', 'limit': 1000, 'offset': offset},
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


def similarity(a, b):
    return SequenceMatcher(None, a.lower(), b.lower()).ratio()


def best_match(name, trading_names, supabase_names):
    candidates = [name] + [t.get('name', '') for t in (trading_names or [])]
    best_score = 0
    best_name = None
    for candidate in candidates:
        for db_name in supabase_names:
            score = similarity(candidate, db_name)
            if score > best_score:
                best_score = score
                best_name = db_name
    return best_score, best_name


def get_entity_city(nzbn):
    try:
        r = requests.get(
            f'{NZBN_BASE}/entities/{nzbn}',
            headers=NZBN_HEADERS,
            verify=False,
            timeout=15,
        )
        data = r.json()
        for addr in data.get('addresses', {}).get('addressList', []):
            if addr.get('addressType') in ('OFFICE', 'REGISTERED') and not addr.get('endDate'):
                return addr.get('address3', '') or addr.get('address2', '') or 'unknown'
    except Exception:
        pass
    return 'unknown'


def main():
    print('Fetching NZBN dental entities...')
    nzbn_entities = fetch_nzbn_dental()
    print(f'Total unique NZBN entities: {len(nzbn_entities)}\n')

    print('Fetching Supabase clinics...')
    supabase_clinics = fetch_supabase_clinics()
    print(f'Total Supabase clinics: {len(supabase_clinics)}\n')

    supabase_names = {c['name'].lower(): c for c in supabase_clinics}

    unmatched = []
    matched = 0

    for entity in nzbn_entities:
        name = entity.get('entityName', '')
        trading = entity.get('tradingNames', [])
        classifications = [c.get('classificationCode') for c in entity.get('classifications', [])]

        # Skip non-clinic businesses if we know their classification
        if any(c in EXCLUDE_CLASSIFICATIONS for c in classifications):
            continue

        score, matched_name = best_match(name, trading, supabase_names)

        if score >= 0.75:
            matched += 1
        else:
            unmatched.append({
                'name': name,
                'trading_names': [t.get('name') for t in (trading or [])],
                'nzbn': entity.get('nzbn'),
                'classifications': classifications,
                'best_match': matched_name,
                'best_score': round(score, 2),
            })

    print(f'Matched: {matched}')
    print(f'Unmatched (not in Supabase): {len(unmatched)}\n')
    print('Fetching city info for unmatched entities...\n')

    results = []
    for i, e in enumerate(unmatched):
        city = get_entity_city(e['nzbn'])
        e['city'] = city
        results.append(e)
        if (i + 1) % 20 == 0:
            print(f'  {i + 1}/{len(unmatched)} done...')

    results.sort(key=lambda x: x.get('city', ''))

    print('\n=== NZBN dental entities NOT found in Supabase ===\n')
    for e in results:
        trading = ', '.join(e['trading_names']) if e['trading_names'] else ''
        trading_str = f' (trading as: {trading})' if trading else ''
        print(f"{e['name']}{trading_str}")
        print(f"  City: {e['city']} | NZBN: {e['nzbn']}")
        print(f"  Best Supabase match: '{e['best_match']}' (score: {e['best_score']})")
        print()

    # Save full results to file
    with open('nzbn_unmatched.json', 'w', encoding='utf-8') as f:
        json.dump(results, f, indent=2, ensure_ascii=False)
    print(f'Full results saved to nzbn_unmatched.json')


if __name__ == '__main__':
    main()
