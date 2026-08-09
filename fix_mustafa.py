import requests, os
from dotenv import load_dotenv
load_dotenv(r'c:\Users\Ciaran\Desktop\Dental_Directory\.env')
MGMT = os.environ['SUPABASE_MANAGEMENT_KEY']

def q(sql):
    r = requests.post('https://api.supabase.com/v1/projects/ankyjpgcocsvvtyyymys/database/query',
        headers={'Authorization': f'Bearer {MGMT}', 'Content-Type': 'application/json'},
        json={'query': sql}, verify=False)
    return r.json()

SOURCE = 'https://dentalreflections.co.nz/meet-the-team/'

mustafa_bio = "Mustafa Ali is a Clinical Dental Technician with over 13 years of experience, holding a Bachelor of Dental Technology and a Postgraduate Diploma in Clinical Dental Technology from the University of Otago. As the lead clinician at Dental Reflections, he uses modern digital workflows including 3D scanning and computer-aided design to create natural-looking, well-fitted dentures. His calm and patient-focused approach helps patients feel comfortable and well-informed throughout their treatment."

print(q(f"""UPDATE clinic_practitioners
    SET name = 'Mustafa Ali',
        bio = $${mustafa_bio}$$,
        specialties = $$Full dentures, partial dentures, denture relines, denture repairs, night guards, 3D scanning$$,
        experience = $$BDT, PGDipCDT (University of Otago), 13+ years as Clinical Dental Technician$$,
        gender = 'M',
        source_url = '{SOURCE}'
    WHERE id = 866 RETURNING id, name"""))
