import requests, os
from dotenv import load_dotenv
load_dotenv(r'c:\Users\Ciaran\Desktop\Dental_Directory\.env')

JWT  = os.environ['SUPABASE_JWT']
ANON = os.environ['SUPABASE_ANON_KEY']
URL  = 'https://ankyjpgcocsvvtyyymys.supabase.co'

r = requests.patch(f'{URL}/rest/v1/dental_clinics?id=eq.1655',
    headers={'apikey': ANON, 'Authorization': f'Bearer {JWT}',
             'Content-Type': 'application/json', 'Prefer': 'return=minimal'},
    json={'services': 'Dental Laboratory'},
    verify=False)
print(r.status_code)
