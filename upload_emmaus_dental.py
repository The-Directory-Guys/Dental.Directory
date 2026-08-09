import sys, io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

import requests, os
from dotenv import load_dotenv
load_dotenv(r'c:\Users\Ciaran\Desktop\Dental_Directory\.env')
MGMT_KEY = os.environ['SUPABASE_MANAGEMENT_KEY']

def q(sql):
    r = requests.post('https://api.supabase.com/v1/projects/ankyjpgcocsvvtyyymys/database/query',
        headers={'Authorization': f'Bearer {MGMT_KEY}', 'Content-Type': 'application/json'},
        json={'query': sql}, timeout=30, verify=False)
    return r.json()

SOURCE = 'https://emmaus.dental/'
MOTUEKA = 1658
RICHMOND = 1659

# Richmond: 12 dentists + 3 oral health therapists
richmond_team = [
    ('Graham Leathley',    'M', 'Dentist', 'Mon\u2013Wed'),
    ('Clarence Sutardja',  'M', 'Dentist', 'Mon, Thu\u2013Fri'),
    ('Jacob Linn',         'M', 'Dentist', 'Mon\u2013Wed'),
    ('Annmarie Urunkar',   'F', 'Dentist', 'Mon\u2013Tue, Thu\u2013Fri'),
    ('Matthew Clark',      'M', 'Dentist', 'Mon, Thu\u2013Fri'),
    ('Marius Van Staden',  'M', 'Dentist', 'Mon\u2013Thu'),
    ('Declan White',       'M', 'Dentist', 'Tue\u2013Fri'),
    ('Annemieke Lewis',    'F', 'Dentist', 'Tue\u2013Fri'),
    ('Sophie Gibbons',     'F', 'Dentist', 'Mon\u2013Wed, Fri'),
    ('Chase Stephens',     'M', 'Dentist', 'Mon\u2013Wed'),
    ('Shaun Du Preez',     'M', 'Dentist', 'Mon'),
    ('Jennifer Kong',      'F', 'Dentist', 'Thu'),
    ('Rachael Teece Bate', 'F', 'Oral Health Therapist', 'Tue, Thu'),
    ('Rachael Scowen',     'F', 'Oral Health Therapist', 'Fri'),
    ('Denise Xu',          'F', 'Oral Health Therapist', 'Wed\u2013Fri'),
]

# Motueka: 6 dentists + 1 hygienist
motueka_team = [
    ('Shaun Du Preez',    'M', 'Dentist',    'Mon\u2013Thu'),
    ('Jennifer Kong',     'F', 'Dentist',    'Mon\u2013Wed'),
    ('Clarence Sutardja', 'M', 'Dentist',    'Tue\u2013Wed'),
    ('Chase Stephens',    'M', 'Dentist',    'Mon, Thu\u2013Fri'),
    ('Jacob Linn',        'M', 'Dentist',    'Thu'),
    ('Max Pang',          'M', 'Dentist',    'Mon, Fri'),
    ('Kathryn Tiedeman',  'F', 'Hygienist',  'Mon, Fri'),
]

# Step 1: delete existing practitioners for both clinics
print('Deleting existing practitioners...')
result = q(f'DELETE FROM clinic_practitioners WHERE clinic_id IN ({MOTUEKA}, {RICHMOND})')
print(f'  Deleted: {result}')

# Step 2: insert Richmond team
print(f'\nInserting Richmond (clinic {RICHMOND}) — {len(richmond_team)} people...')
for name, gender, role, days in richmond_team:
    sql = f"""
        INSERT INTO clinic_practitioners (clinic_id, name, gender, specialties, bio, source_url)
        VALUES ({RICHMOND}, $${name}$$, '{gender}', $${role}$$, $${days}$$, '{SOURCE}')
    """
    res = q(sql)
    print(f'  {name} ({days}): {res}')

# Step 3: insert Motueka team
print(f'\nInserting Motueka (clinic {MOTUEKA}) — {len(motueka_team)} people...')
for name, gender, role, days in motueka_team:
    sql = f"""
        INSERT INTO clinic_practitioners (clinic_id, name, gender, specialties, bio, source_url)
        VALUES ({MOTUEKA}, $${name}$$, '{gender}', $${role}$$, $${days}$$, '{SOURCE}')
    """
    res = q(sql)
    print(f'  {name} ({days}): {res}')

# Verify
print('\nVerification:')
for clinic_id, label in [(RICHMOND, 'Richmond'), (MOTUEKA, 'Motueka')]:
    rows = q(f'SELECT name, specialties, bio FROM clinic_practitioners WHERE clinic_id = {clinic_id} ORDER BY id')
    print(f'\n{label} ({len(rows)} people):')
    for r in rows:
        print(f'  {r["name"]} | {r["specialties"]} | {r["bio"]}')
