import requests, os
from dotenv import load_dotenv
load_dotenv(r'c:\Users\Ciaran\Desktop\Dental_Directory\.env')
MGMT = os.environ['SUPABASE_MANAGEMENT_KEY']

def q(sql):
    r = requests.post('https://api.supabase.com/v1/projects/ankyjpgcocsvvtyyymys/database/query',
        headers={'Authorization': f'Bearer {MGMT}', 'Content-Type': 'application/json'},
        json={'query': sql}, verify=False)
    return r.json()

agg = q("SELECT COUNT(*) as cnt, ROUND(AVG(rating)::numeric, 1) as avg FROM google_reviews WHERE clinic_id = 2530")[0]
print('Aggregate:', agg)

cnt = agg['cnt']
avg = agg['avg']

res = q(f"UPDATE dental_clinics SET rating = {avg}, total_ratings = {cnt} WHERE id = 2530 RETURNING id, name, rating, total_ratings")
print('Updated:', res)
