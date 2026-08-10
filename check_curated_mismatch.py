import requests, os
from dotenv import load_dotenv
load_dotenv(r'c:\Users\Ciaran\Desktop\Dental_Directory\.env')
MGMT = os.environ['SUPABASE_MANAGEMENT_KEY']

def q(sql):
    r = requests.post('https://api.supabase.com/v1/projects/ankyjpgcocsvvtyyymys/database/query',
        headers={'Authorization': f'Bearer {MGMT}', 'Content-Type': 'application/json'},
        json={'query': sql}, verify=False)
    return r.json()

# Find all clinics where is_curated count != is_curated_rating count
rows = q("""
    SELECT clinic_id,
           COUNT(*) FILTER (WHERE is_curated) as curated_display,
           COUNT(*) FILTER (WHERE is_curated_rating) as curated_rating
    FROM google_reviews
    GROUP BY clinic_id
    HAVING COUNT(*) FILTER (WHERE is_curated) != COUNT(*) FILTER (WHERE is_curated_rating)
    ORDER BY clinic_id
""")
print(f'{len(rows)} clinics with mismatched counts:')
for r in rows:
    print(r)
