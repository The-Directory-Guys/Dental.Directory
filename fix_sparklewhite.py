import requests, os
from dotenv import load_dotenv
load_dotenv(r'c:\Users\Ciaran\Desktop\Dental_Directory\.env')
MGMT_KEY = os.environ['SUPABASE_MANAGEMENT_KEY']
r = requests.post('https://api.supabase.com/v1/projects/ankyjpgcocsvvtyyymys/database/query',
    headers={'Authorization': f'Bearer {MGMT_KEY}', 'Content-Type': 'application/json'},
    json={'query': "UPDATE dental_clinics SET website = 'https://sparklewhite.co.nz/' WHERE id = 2923 RETURNING id, name, website"},
    verify=False)
print(r.json())
