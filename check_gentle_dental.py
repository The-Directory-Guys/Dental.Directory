import requests, os
from dotenv import load_dotenv
load_dotenv(r'c:\Users\Ciaran\Desktop\Dental_Directory\.env')
MGMT = os.environ['SUPABASE_MANAGEMENT_KEY']

def q(sql):
    r = requests.post('https://api.supabase.com/v1/projects/ankyjpgcocsvvtyyymys/database/query',
        headers={'Authorization': f'Bearer {MGMT}', 'Content-Type': 'application/json'},
        json={'query': sql}, verify=False)
    return r.json()

# Check google_reviews schema sample
print('Sample google_reviews:')
for r in q("SELECT * FROM google_reviews WHERE clinic_id = 2530 LIMIT 3"):
    print(r)

print('\nAll columns in google_reviews:')
print(q("SELECT column_name FROM information_schema.columns WHERE table_name = 'google_reviews' ORDER BY ordinal_position"))

# Check if there's a place_rating or similar field on dental_clinics
print('\nAll columns in dental_clinics:')
print(q("SELECT column_name FROM information_schema.columns WHERE table_name = 'dental_clinics' ORDER BY ordinal_position"))
