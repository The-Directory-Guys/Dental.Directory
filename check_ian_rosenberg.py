import requests, os
from dotenv import load_dotenv
load_dotenv(r'c:\Users\Ciaran\Desktop\Dental_Directory\.env')
MGMT = os.environ['SUPABASE_MANAGEMENT_KEY']

def q(sql):
    r = requests.post('https://api.supabase.com/v1/projects/ankyjpgcocsvvtyyymys/database/query',
        headers={'Authorization': f'Bearer {MGMT}', 'Content-Type': 'application/json'},
        json={'query': sql}, verify=False)
    return r.json()

bio = "Ian Rosenberg is a dental surgeon who founded Dental@105 in 1980. With over four decades of experience, he is known for his genuine interest in his patients and his warm, personal approach to care."

print(q(f"UPDATE clinic_practitioners SET bio = $${bio}$$ WHERE id = 1389 RETURNING id, name, bio"))
