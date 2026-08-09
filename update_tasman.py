import requests, sys, io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
from dotenv import load_dotenv
import os
load_dotenv(r'c:\Users\Ciaran\Desktop\Dental_Directory\.env')
MGMT_KEY = os.environ['SUPABASE_MANAGEMENT_KEY']

def q(sql):
    r = requests.post('https://api.supabase.com/v1/projects/ankyjpgcocsvvtyyymys/database/query',
        headers={'Authorization': f'Bearer {MGMT_KEY}', 'Content-Type': 'application/json'},
        json={'query': sql}, verify=False)
    return r.json()

# 1. Clinic — description + fix website to HTTPS
desc = "Located in the Lower Queen Street Health complex in Richmond — a comprehensive health centre also home to a general medical practice and medical specialists. Offering a relaxed, honest and thorough style of dentistry centred on high quality care, with a focus on helping patients overcome the common obstacles of cost, anxiety and dental complacency."
print(q(f"""UPDATE dental_clinics
    SET description = $${desc}$$,
        website = 'https://www.tasmandental.co.nz/'
    WHERE id = 1682 RETURNING id"""))

# 2. Jonathan Clark (id 758)
jonathan_bio = "After growing up in Richmond, Jonathan graduated dentistry in Otago in 1999. He then practised in the UK for two years before returning to Wellington where he bought into a practice on The Terrace. After getting married, Jonathan and his family moved to Nelson in 2007 and he went on to found Tasman Dental Centre at the Lower Queen Street Health Complex."
print(q(f"""UPDATE clinic_practitioners
    SET experience = 'BDS (Otago) 1999',
        bio = $${jonathan_bio}$$,
        source_url = 'https://www.tasmandental.co.nz/about-tasman-dental/'
    WHERE id = 758 RETURNING id, name"""))

# 3. Ben Simmons (id 759)
ben_bio = "Originally from Levin, Ben joins the team following 15 years of experience across New Zealand, Australia and the UK. He and Jonathan were classmates at Otago Dental School. Known for delivering high quality service in a gentle and caring manner and for his ability to put people at ease, Ben has developed a wide range of skills in general and cosmetic dental care. His passion is cosmetics — he has an extensive portfolio of smile improvements and believes in clear and honest communication so that unexpected surprises can be avoided."
print(q(f"""UPDATE clinic_practitioners
    SET bio = $${ben_bio}$$,
        specialties = 'General dentistry, cosmetic dentistry',
        source_url = 'https://www.tasmandental.co.nz/about-tasman-dental/'
    WHERE id = 759 RETURNING id, name"""))

print('Done.')
