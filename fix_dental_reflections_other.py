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
BUCKET = f"{os.environ['SUPABASE_URL']}/storage/v1/object/public/practitioner-photos/practitioners"

mustafa_photo = f'{BUCKET}/mustafa-ali-dental-reflections.png'
jordyn_photo  = f'{BUCKET}/jordyn-te-kani-dental-reflections.jpg'

mustafa_bio = "Mustafa Ali is a Clinical Dental Technician with over 13 years of experience, holding a Bachelor of Dental Technology and a Postgraduate Diploma in Clinical Dental Technology from the University of Otago. As the lead clinician at Dental Reflections, he uses modern digital workflows including 3D scanning and computer-aided design to create natural-looking, well-fitted dentures. His calm and patient-focused approach helps patients feel comfortable and well-informed throughout their treatment."

jordyn_bio = "Jordyn Te Kani is the Team Leader and Operations Manager at Dental Reflections, bringing four years of practice management experience across both clinic and laboratory environments. She leads day-to-day operations and coordinates between clinicians, technicians, and patients to keep appointments on track. Her approachable and solutions-focused approach means patients feel supported and confident throughout their treatment."

stephanie_bio = "Stephanie Smit is the Front Office Coordinator at Dental Reflections, holding a Level 3 Certificate in Business Administration and bringing 12 years of experience in customer service and administration. She is the welcoming first point of contact for patients, managing appointments, enquiries, and front office coordination. Her friendly and attentive manner is particularly valued by patients who may feel nervous about dental visits."

# ids: Mustafa=899,916  Jordyn=897,914  Stephanie=898,915
updates = [
    (899, 'Mustafa Ali', mustafa_bio, 'BDT, PGDipCDT (University of Otago), 13+ years as Clinical Dental Technician',
     'Full dentures, partial dentures, denture relines, denture repairs, night guards, 3D scanning', 'M', mustafa_photo),
    (916, 'Mustafa Ali', mustafa_bio, 'BDT, PGDipCDT (University of Otago), 13+ years as Clinical Dental Technician',
     'Full dentures, partial dentures, denture relines, denture repairs, night guards, 3D scanning', 'M', mustafa_photo),
    (897, 'Jordyn Te Kani', jordyn_bio, None, None, 'F', jordyn_photo),
    (914, 'Jordyn Te Kani', jordyn_bio, None, None, 'F', jordyn_photo),
    (898, 'Stephanie Smit', stephanie_bio, None, None, 'F', None),
    (915, 'Stephanie Smit', stephanie_bio, None, None, 'F', None),
]

for pid, name, bio, exp, spec, gender, photo in updates:
    exp_sql    = f"experience = $${exp}$$," if exp else ''
    spec_sql   = f"specialties = $${spec}$$," if spec else ''
    photo_sql  = f"photo_url = '{photo}'," if photo else "photo_url = NULL,"
    print(q(f"""UPDATE clinic_practitioners
        SET name = '{name}',
            bio = $${bio}$$,
            {exp_sql}
            {spec_sql}
            gender = '{gender}',
            {photo_sql}
            source_url = '{SOURCE}'
        WHERE id = {pid} RETURNING id, name"""))

print('Done.')
