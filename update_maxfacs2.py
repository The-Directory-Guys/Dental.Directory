import requests, os
from dotenv import load_dotenv
load_dotenv(r'c:\Users\Ciaran\Desktop\Dental_Directory\.env')
MGMT = os.environ['SUPABASE_MANAGEMENT_KEY']

def q(sql):
    r = requests.post('https://api.supabase.com/v1/projects/ankyjpgcocsvvtyyymys/database/query',
        headers={'Authorization': f'Bearer {MGMT}', 'Content-Type': 'application/json'},
        json={'query': sql}, verify=False)
    return r.json()

bio = "Mr David Chin-Shong is a specialist oral and maxillofacial surgeon with dual qualifications in medicine and dentistry, registered with the NZ Medical Council, the Dental Council of New Zealand, and the Royal Australasian College of Dental Surgeons. He graduated in medicine in 1996 from the Royal College of Surgeons in Ireland and in dentistry in 2002 from University College Cork, then completed specialist training in oral and maxillofacial surgery in London and Liverpool, qualifying as a consultant surgeon in 2008. He also completed a craniofacial fellowship at Alder Hey Children's Hospital and received two UK Aesthetic Dentistry awards. David has a particular interest in making the surgical experience as comfortable as possible for anxious patients. He offers Target Controlled Infusion (TCI) intravenous sedation, using a computerised pump to tailor sedation to each patient's physiology, with continuous monitoring of brain wave activity (EEG), breathing, heart rate and blood pressure. For dental implant cases, he uses 3D digital planning with CBCT imaging, intraoral scanning and computer-designed surgical guides. He practises across five Wellington locations and works closely with referring dentists to ensure coordinated patient care."

exp = "MB BCh BAO (Royal College of Surgeons Ireland) 1996, BDS (University College Cork) 2002, Specialist Oral & Maxillofacial Surgeon, consultant 2008, craniofacial fellowship Alder Hey Children's Hospital"

spec = "Oral and maxillofacial surgery, wisdom teeth removal, dental implants, dental extractions, biopsy, TCI sedation"

print(q(f"""UPDATE clinic_practitioners
    SET bio = $${bio}$$,
        experience = $${exp}$$,
        specialties = $${spec}$$,
        source_url = 'https://maxfacsoralsurgery.co.nz/about'
    WHERE id = 879 RETURNING id, name"""))

print('Done.')
