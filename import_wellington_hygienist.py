import sys
import json
import os
import urllib.request
import urllib.error
from dotenv import load_dotenv
load_dotenv()
sys.stdout.reconfigure(encoding='utf-8')

SUPABASE_URL = 'https://ankyjpgcocsvvtyyymys.supabase.co'
SUPABASE_ANON_KEY = os.environ['SUPABASE_ANON_KEY']
SUPABASE_SERVICE_KEY = os.environ['SUPABASE_SERVICE_KEY']
SUPABASE_KEY = SUPABASE_ANON_KEY  # read operations use anon key

# Phone/manually-verified Wellington hygienist prices
# (search_name, price_nzd, price_label, source, notes)
# search_name is used for fuzzy matching against DB clinic names
WELLINGTON_PRICES = [
    ("Art of Dentistry",                    200, "$200/hour",                              "phone",   "Phone verified 26/05/26"),
    ("Ashwin Magan Dental Surgery",         120, "~$120 (scale & polish by dentist)",      "phone",   "Phone verified 26/05/26"),
    ("Beachside Dental Surgery",            179, "$179, 45–60 min",                        "phone",   "Phone verified 27/05/26"),
    ("Discover Dental",                     275, "$275/hour",                              "phone",   "Phone verified 26/05/26"),
    ("Bing Dental",                         195, "$195 (up to 1 hour)",                   "phone",   "Phone verified 26/05/26"),
    ("Central Hutt Dental",                 250, "$250, 60 min",                           "phone",   "Phone verified 27/05/26"),
    ("Centre of Dental Excellence",         185, "$180–$190, ~60 min",                    "phone",   "Phone verified 28/05/26"),
    ("Champion Dental Centre",              180, "$180–$195, ~45 min",                    "phone",   "Phone verified 27/05/26"),
    ("City Dentists",                       240, "$240, 60 min",                           "phone",   "Phone verified 27/05/26"),
    ("Darling Dental",                      200, "$200 new patient, 60 min",              "phone",   "Phone verified 27/05/26"),
    ("Smile Design Dental Group",           225, "$225–$265 (~50–60 min)",                "phone",   "Phone verified 28/05/26"),
    ("Eastbourne Dental Centre",            140, "$140–$190, 45–60 min",                  "phone",   "Phone verified 28/05/26"),
    ("Grace Dental",                        170, "~$170",                                  "phone",   "Phone verified 28/05/26"),
    ("Greytown Dental",                     145, "$145 (30 min maintenance clean)",        "phone",   "Phone verified 29/05/26"),
    ("Hutt Dental Hub",                     180, "$180–$200 regular, ~30–45 min",         "phone",   "Phone verified 28/05/26"),
    ("Kapiti Dental Centre",                 80, "~$80",                                   "phone",   "Phone verified 29/05/26"),
    ("Andrew Middlemiss Dental",            217, "$217 maintenance (45 min)",              "phone",   "Phone verified 29/05/26"),
    ("Naenae Dental Clinic",                180, "$180 maintenance (~30 min)",             "phone",   "Phone verified 29/05/26"),
    ("Newtown Dental",                      190, "~$160–$220",                             "phone",   "Phone verified 03/06/26"),
    ("Wishart Dental Centre",               180, "$180, ~30 min",                          "phone",   "Phone verified 03/06/26"),
    ("Johnsonville Family Dentist",         195, "$195 subsequent (~50–60 min)",           "phone",   "Phone verified 04/06/26"),
    ("The Wellington Dental Practice",      240, "$240, 60 min",                           "phone",   "Phone verified 04/06/26"),
    ("Peninsula Dental Centre",             220, "$220, 60 min",                           "phone",   "Phone verified 04/06/26"),
    ("Capital Dental Newtown",              195, "$195 full mouth clean, ~50 min",         "phone",   "Phone verified 04/06/26"),
    ("Phillip Chin Dental Practice",        165, "$165+, ~30 min",                         "phone",   "Phone verified 04/06/26"),
    ("Whitby Dental Centre",                175, "$170–$180 existing patient",             "phone",   "Phone verified 04/06/26"),
    ("Wellington Dentists Ltd",             221, "$221 first appointment (~45 min)",       "phone",   "Phone verified 04/06/26"),
    ("Simply Dental",                       184, "$184 (30 min)",                          "phone",   "Phone verified 04/06/26"),
    ("Wainui Dental",                       200, "$200 (60 min)",                          "phone",   "Phone verified 04/06/26"),
    ("Switch Dental Lower Hutt",            172, "$172–$229 existing patient",             "phone",   "Phone verified 04/06/26"),
    ("Real Dentistry",                      195, "$195 existing patient (~50 min)",        "phone",   "Phone verified 04/06/26"),
    ("The Dental Studio Laura Ng Lower Hutt", 185, "$185 (full mouth clean; 60 min)",     "phone",   "Phone verified 04/06/26"),
    ("The Dental Studio Laura Ng Johnsonville", 185, "$185 (full mouth clean; 60 min)",   "phone",   "Phone verified 04/06/26"),
    ("Thorndon Dental Surgery",             169, "$169–$255 existing patient",             "phone",   "Phone verified 05/06/26"),
    ("Supreme Dental Concepts Wellington",  200, "$190–$210, 45 min",                     "phone",   "Phone verified 05/06/26 (Wellington branch)"),
    ("Supreme Dental Concepts Lower Hutt",  200, "$190–$210, 45 min",                     "phone",   "Phone verified 05/06/26 (Lower Hutt branch)"),
    ("Rimu Road Dental Surgery",            179, "$179 (45–60 min)",                       "phone",   "Phone verified 05/06/26"),
    ("Capital Dental The Terrace",          195, "$195 (45–60 min)",                       "phone",   "Phone verified 05/06/26"),
    ("Capital Dental Brandon Street",       195, "$195 (45 min)",                          "phone",   "Phone verified 10/06/26"),
    ("Capital Dental Lower Hutt",           195, "$195 (60 min)",                          "phone",   "Phone verified 09/06/26"),
    ("Capital Dental Thorndon",             195, "$195 (45–50 min)",                       "phone",   "Phone verified 19/06/26"),
    ("Sunshine Dental Porirua",             190, "$190 deep-scale treatment per session",  "website", "From website price list"),
    ("Sunshine Dental Johnsonville",        190, "$190 deep-scale treatment per session",  "website", "From website price list"),
    ("Johnsonville Dental Centre",          180, "Scale and polish: $180",                 "website", "From website price list"),
    ("Paremata Dental Surgery",             150, "$150 scaling and polishing, 15 min",     "phone",   "Phone verified 09/06/26"),
]

# Special cases: some names in the DB differ from the text files
# We'll handle these with manual overrides in match logic
SPECIAL_MATCHES = {
    # search_name (lowercase) -> partial string to look for in DB name
    "the dental studio laura ng lower hutt": "dental studio",
    "the dental studio laura ng johnsonville": "dental studio",
    "supreme dental concepts wellington": "supreme dental concepts",
    "supreme dental concepts lower hutt": "supreme dental concepts",
    "capital dental the terrace": "capital dental",
    "capital dental brandon street": "capital dental",
    "capital dental lower hutt": "capital dental",
    "capital dental thorndon": "capital dental",
    "capital dental newtown": "capital dental",
    "wainuiomata dental": "wainui dental",
}

def supabase_request(method, path, body=None):
    url = SUPABASE_URL + '/rest/v1/' + path
    data = json.dumps(body).encode('utf-8') if body else None
    req = urllib.request.Request(url, data=data, method=method)
    req.add_header('apikey', SUPABASE_KEY)
    req.add_header('Authorization', 'Bearer ' + SUPABASE_KEY)
    req.add_header('Content-Type', 'application/json')
    req.add_header('Accept', 'application/json')
    req.add_header('Prefer', 'return=minimal')
    with urllib.request.urlopen(req) as resp:
        body = resp.read()
        return json.loads(body) if body else None

def fetch_paginated(table, select='*', filters=''):
    all_rows = []
    offset = 0
    while True:
        sep = '&' if filters else ''
        path = f'{table}?select={select}{sep}{filters}'
        url = SUPABASE_URL + '/rest/v1/' + path
        req = urllib.request.Request(url)
        req.add_header('apikey', SUPABASE_KEY)
        req.add_header('Authorization', 'Bearer ' + SUPABASE_KEY)
        req.add_header('Accept', 'application/json')
        req.add_header('Range-Unit', 'items')
        req.add_header('Range', f'{offset}-{offset+999}')
        with urllib.request.urlopen(req) as resp:
            batch = json.loads(resp.read().decode('utf-8'))
        all_rows.extend(batch)
        if len(batch) < 1000:
            break
        offset += 1000
    return all_rows

print("Fetching Wellington clinics...")
all_clinics = fetch_paginated('dental_clinics', 'id,name,city,region,address')
welly_clinics = [c for c in all_clinics if c.get('region') in (
    'Wellington', 'Greater Wellington', 'Wairarapa', 'Wider Wellington Region'
) or (c.get('city') or '').lower() == 'wellington']
print(f"  {len(all_clinics)} total clinics, {len(welly_clinics)} in Wellington region")

# Build lookup: lowercase name -> list of clinic rows
clinic_by_name = {}
for c in welly_clinics:
    key = (c['name'] or '').lower().strip()
    clinic_by_name.setdefault(key, []).append(c)

def find_clinic(search_name):
    """Return matching clinic(s) from DB."""
    sl = search_name.lower().strip()

    # Direct lookup
    if sl in clinic_by_name:
        return clinic_by_name[sl]

    # Check special overrides
    fragment = SPECIAL_MATCHES.get(sl)
    if fragment:
        matches = [c for c in welly_clinics if fragment in (c['name'] or '').lower()]
        if matches:
            return matches

    # Starts-with match
    matches = [c for c in welly_clinics if (c['name'] or '').lower().startswith(sl[:20])]
    if matches:
        return matches

    # Contains match (first 15 chars of search in DB name)
    fragment = sl[:15]
    matches = [c for c in welly_clinics if fragment in (c['name'] or '').lower()]
    if matches:
        return matches

    return []

print("\nFetching existing hygienist scraped_prices...")
all_prices = fetch_paginated('scraped_prices', 'id,clinic_id,treatment,source', '')
# Keywords that indicate hygienist/scale treatments
HYGIENIST_KEYWORDS = ['hygienist', 'hygiene', 'scale', 'clean', 'polish', 'periodontal', 'perio']
EXCLUDE_KEYWORDS = ['exam', 'checkup', 'check-up', 'x-ray', 'xray', 'consult', 'extraction', 'filling', 'crown']

def is_hygienist_row(row):
    t = (row.get('treatment') or '').lower()
    if any(kw in t for kw in HYGIENIST_KEYWORDS):
        if not any(ex in t for ex in EXCLUDE_KEYWORDS):
            return True
    return False

existing_hyg_clinic_ids = set(r['clinic_id'] for r in all_prices if is_hygienist_row(r))
print(f"  {len(existing_hyg_clinic_ids)} clinics already have hygienist rows")

# Now match and build insert list
to_insert = []
no_match = []
already_have = []
multi_match = []

for entry in WELLINGTON_PRICES:
    search_name, price_nzd, price_label, source, notes = entry
    matches = find_clinic(search_name)

    if not matches:
        no_match.append(search_name)
        continue

    if len(matches) > 2:
        multi_match.append((search_name, [m['name'] for m in matches]))
        continue

    # For multi-match of exactly 2 (like Dental Studio two branches, Supreme two branches),
    # check if the search name gives a hint for which branch
    if len(matches) == 2:
        sl = search_name.lower()
        if 'johnsonville' in sl:
            branch_matches = [m for m in matches if 'johnsonville' in (m.get('address') or '').lower() or 'johnsonville' in (m['name'] or '').lower()]
            if branch_matches:
                matches = branch_matches
        elif 'lower hutt' in sl or 'hutt' in sl:
            branch_matches = [m for m in matches if 'lower hutt' in (m.get('city') or '').lower() or 'hutt' in (m.get('address') or '').lower()]
            if branch_matches:
                matches = branch_matches
        elif 'wellington' in sl and 'lower' not in sl:
            branch_matches = [m for m in matches if (m.get('city') or '').lower() == 'wellington']
            if branch_matches:
                matches = branch_matches
        elif 'terrace' in sl:
            branch_matches = [m for m in matches if 'terrace' in (m.get('address') or '').lower() or 'terrace' in (m['name'] or '').lower()]
            if branch_matches:
                matches = branch_matches
        elif 'brandon' in sl:
            branch_matches = [m for m in matches if 'brandon' in (m.get('address') or '').lower() or 'brandon' in (m['name'] or '').lower()]
            if branch_matches:
                matches = branch_matches
        elif 'thorndon' in sl:
            branch_matches = [m for m in matches if 'thorndon' in (m.get('address') or '').lower() or 'thorndon' in (m['name'] or '').lower()]
            if branch_matches:
                matches = branch_matches
        elif 'newtown' in sl:
            branch_matches = [m for m in matches if 'newtown' in (m.get('address') or '').lower() or 'newtown' in (m['name'] or '').lower()]
            if branch_matches:
                matches = branch_matches

    for clinic in matches:
        cid = clinic['id']
        if cid in existing_hyg_clinic_ids:
            already_have.append((search_name, clinic['name'], cid))
        else:
            to_insert.append({
                'clinic_id': cid,
                'source': source,
                'treatment': 'Hygienist',
                'price_nzd': price_nzd,
                'price_label': price_label,
                'source_url': '',
                'notes': notes,
                '_match_name': clinic['name'],
                '_search': search_name,
            })

print(f"\n{'='*60}")
print(f"MATCH SUMMARY")
print(f"{'='*60}")
print(f"Ready to insert: {len(to_insert)}")
print(f"Already have hygienist rows: {len(already_have)}")
print(f"No match found: {len(no_match)}")
print(f"Ambiguous (3+ matches): {len(multi_match)}")

if no_match:
    print(f"\nNO MATCH:")
    for n in no_match:
        print(f"  - {n}")

if already_have:
    print(f"\nALREADY HAVE HYGIENIST ROWS (skipping):")
    for search, db_name, cid in already_have:
        print(f"  {search!r} -> {db_name!r} (clinic_id={cid})")

if multi_match:
    print(f"\nAMBIGUOUS MATCHES (skipping):")
    for search, names in multi_match:
        print(f"  {search!r} -> {names}")

    # Deduplicate by clinic_id (keep first match per clinic)
    seen_clinic_ids = set()
    deduped = []
    for row in to_insert:
        if row['clinic_id'] not in seen_clinic_ids:
            seen_clinic_ids.add(row['clinic_id'])
            deduped.append(row)
        else:
            print(f"  [DEDUP] Skipping duplicate clinic_id {row['clinic_id']} for {row['_search']!r}")
    to_insert = deduped

if to_insert:
    print(f"\nINSERTING ({len(to_insert)} rows):")
    for row in to_insert:
        print(f"  {row['_search']!r} -> {row['_match_name']!r} (id={row['clinic_id']}) | ${row['price_nzd']} | {row['price_label']}")

    rows = [{k: v for k, v in r.items() if not k.startswith('_')} for r in to_insert]
    url = SUPABASE_URL + '/rest/v1/scraped_prices'
    data = json.dumps(rows).encode('utf-8')
    req = urllib.request.Request(url, data=data, method='POST')
    req.add_header('apikey', SUPABASE_SERVICE_KEY)
    req.add_header('Authorization', 'Bearer ' + SUPABASE_SERVICE_KEY)
    req.add_header('Content-Type', 'application/json')
    req.add_header('Accept', 'application/json')
    req.add_header('Prefer', 'return=minimal')
    try:
        with urllib.request.urlopen(req) as resp:
            print(f"\nInserted {len(rows)} rows. HTTP {resp.status}")
    except urllib.error.HTTPError as e:
        print(f"Error: {e.code} {e.reason}")
        print(e.read().decode('utf-8'))
