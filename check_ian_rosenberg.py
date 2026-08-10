import requests, os
from dotenv import load_dotenv
load_dotenv(r'c:\Users\Ciaran\Desktop\Dental_Directory\.env')
MGMT = os.environ['SUPABASE_MANAGEMENT_KEY']

def q(sql):
    r = requests.post('https://api.supabase.com/v1/projects/ankyjpgcocsvvtyyymys/database/query',
        headers={'Authorization': f'Bearer {MGMT}', 'Content-Type': 'application/json'},
        json={'query': sql}, verify=False)
    return r.json()

print('Clinic:', q("SELECT id, name, founded_year FROM dental_clinics WHERE id = 1510"))

# Clear duplicate experience/bio from Ian Rosenberg
print(q("UPDATE clinic_practitioners SET experience = NULL, bio = NULL WHERE id = 1389 RETURNING id, name, experience, bio"))
