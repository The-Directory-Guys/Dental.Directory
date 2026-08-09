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

SOURCE = 'https://maxfacsoralsurgery.co.nz/about'

# Check which clinics David is linked to
print('David clinic links:')
print(q("SELECT clinic_id FROM clinic_practitioners WHERE id = 801"))

# Both clinic IDs
ALLEN_ST  = 2828
LOWER_HUTT = 2849

desc = "Specialist oral and maxillofacial surgery practice run by Mr David Chin-Shong across five Wellington locations. Services include dental extractions, wisdom teeth removal, dental implants, biopsies, and sedation options for anxious patients. Offers Target Controlled Infusion (TCI) intravenous sedation and 3D digital implant planning with CBCT imaging and computer-designed surgical guides."

# 1. Both clinics — description
for cid in [ALLEN_ST, LOWER_HUTT]:
    print(q(f"UPDATE dental_clinics SET description = $${desc}$$ WHERE id = {cid} RETURNING id, name"))

# 2. Fix Lower Hutt website HTTP → HTTPS
print(q("UPDATE dental_clinics SET website = 'https://maxfacsoralsurgery.co.nz/' WHERE id = 2849 RETURNING id, website"))

# 3. Link David to Lower Hutt clinic as well (if not already)
existing = q("SELECT id FROM clinic_practitioners WHERE clinic_id = 2849 AND name ILIKE '%david%'")
print(f'David in Lower Hutt: {existing}')
if not existing:
    print(q("""INSERT INTO clinic_practitioners (clinic_id, name, gender, experience, specialties, bio, source_url)
        SELECT 2849, name, gender, experience, specialties, bio, source_url
        FROM clinic_practitioners WHERE id = 801
        RETURNING id, name"""))

# 4. Update David's bio and experience with full website content
bio = "Mr David Chin-Shong is a specialist oral and maxillofacial surgeon with dual qualifications in medicine and dentistry, registered with the NZ Medical Council, the Dental Council of New Zealand, and the Royal Australasian College of Dental Surgeons. He graduated in medicine in 1996 from the Royal College of Surgeons in Ireland and in dentistry in 2002 from University College Cork, then completed specialist training in oral and maxillofacial surgery in London and Liverpool, qualifying as a consultant surgeon in 2008. He also completed a craniofacial fellowship at Alder Hey Children's Hospital and received two UK Aesthetic Dentistry awards. David has a particular interest in making the surgical experience as comfortable as possible for anxious patients. He offers Target Controlled Infusion (TCI) intravenous sedation, using a computerised pump to tailor sedation to each patient's physiology, with continuous monitoring of brain wave activity (EEG), breathing, heart rate and blood pressure. For dental implant cases, he uses 3D digital planning with CBCT imaging, intraoral scanning and computer-designed surgical guides. He practises across five Wellington locations and works closely with referring dentists to ensure coordinated patient care."

experience = "MB BCh BAO (Royal College of Surgeons Ireland) 1996, BDS (University College Cork) 2002, Specialist Oral & Maxillofacial Surgeon, consultant 2008, craniofacial fellowship Alder Hey Children's Hospital"

print(q(f"""UPDATE clinic_practitioners
    SET bio = $${bio}$$,
        experience = $${experience}$$,
        specialties = $$Oral and maxillofacial surgery, wisdom teeth removal, dental implants, dental extractions, biopsy, TCI sedation$$,
        source_url = '{SOURCE}'
    WHERE id = 801 RETURNING id, name"""))

# Also update the Lower Hutt copy if just inserted
new = q("SELECT id FROM clinic_practitioners WHERE clinic_id = 2849 AND name ILIKE '%david%' AND id != 801")
if new:
    nid = new[0]['id']
    print(q(f"""UPDATE clinic_practitioners
        SET bio = $${bio}$$,
            experience = $${experience}$$,
            specialties = $$Oral and maxillofacial surgery, wisdom teeth removal, dental implants, dental extractions, biopsy, TCI sedation$$,
            source_url = '{SOURCE}'
        WHERE id = {nid} RETURNING id, name"""))

print('\nDone.')
