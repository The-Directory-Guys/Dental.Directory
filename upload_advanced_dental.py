import requests
import os
from dotenv import load_dotenv

load_dotenv(r"c:\Users\Ciaran\Desktop\Dental_Directory\.env")

SUPABASE_URL = os.environ["SUPABASE_URL"]
SUPABASE_JWT = os.environ['SUPABASE_JWT']
MGMT_KEY = os.environ["SUPABASE_MANAGEMENT_KEY"]
BUCKET = "practitioner-photos"
CLINIC_ID = 1651

HEADERS_DL = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/120.0.0.0 Safari/537.36",
    "Referer": "https://www.advanceddental.co.nz/",
}

def db(sql):
    r = requests.post(
        "https://api.supabase.com/v1/projects/ankyjpgcocsvvtyyymys/database/query",
        headers={"Authorization": f"Bearer {MGMT_KEY}", "Content-Type": "application/json"},
        json={"query": sql}, timeout=30, verify=False,
    )
    return r.status_code

practitioners = [
    {
        "filename": "hunter-robb.jpg",
        "name": "Hunter Robb",
        "gender": "M",
        "specialties": "Principal Dentist",
        "experience": "BDS (Otago, 1997)",
        "bio": "Graduated Otago Dental School in 1997, with experience in Wellington Hospital, Britain, and Australia. Joined Advanced Dental in 2004 and became principal in 2008.",
        "photo_url": "https://images.squarespace-cdn.com/content/v1/597925aacd39c3750038d54c/aa353eb7-b8b5-40ad-9c79-4e2d9568e1e9/unnamed+%281%29.jpg",
    },
    {
        "filename": "james-marshall.jpg",
        "name": "James Marshall",
        "gender": "M",
        "specialties": "Principal Dentist, Implantology",
        "experience": "BDS (Otago, 1995)",
        "bio": "Graduated Otago Dental School in 1995 and has been principal since 2002. Special interest in implantology, with multiple mini residency courses completed.",
        "photo_url": "https://images.squarespace-cdn.com/content/v1/597925aacd39c3750038d54c/5b8578e9-9542-4c42-8b43-5ff95e7f6db9/IMG_2976.jpg",
    },
    {
        "filename": "gareth-gregg.jpg",
        "name": "Gareth Gregg",
        "gender": "M",
        "specialties": "Associate Dentist",
        "experience": "Charles Clifford Dental School, Sheffield (1995)",
        "bio": "Graduated from Charles Clifford Dental School, Sheffield in 1995. Previously owned Welcome Bay Dental Care in Tauranga for nearly 20 years before relocating to Nelson in 2022.",
        "photo_url": "https://images.squarespace-cdn.com/content/v1/597925aacd39c3750038d54c/d8ad8bf2-9871-4e0d-b3bc-223983678c1f/IMG_7427.jpg",
    },
    {
        "filename": "samantha-grant.jpg",
        "name": "Samantha Grant",
        "gender": "F",
        "specialties": "Associate Dentist, Cosmetic dentistry, Facial aesthetics, Implantology",
        "experience": "BDS (Otago, 2010) with credit",
        "bio": "NZ Dental Association advisory council member. Trained in injectable facial aesthetics, cosmetic dentistry, and implantology. Special interest in Botulinum Toxin for migraine and jaw pain.",
        "photo_url": "https://images.squarespace-cdn.com/content/v1/597925aacd39c3750038d54c/cce14cc4-3009-45f2-bf6a-2aed145d8ab8/IMG_0415+%281%29.jpg",
    },
    {
        "filename": "rob-beaglehole.jpg",
        "name": "Rob Beaglehole",
        "gender": "M",
        "specialties": "Associate Dentist, Dental public health",
        "experience": "BDS (Otago, 1997), MDPH",
        "bio": "Dental Public Health Specialist with extensive public health experience, including 12 years at Nelson Hospital. NZ Dental Association spokesperson.",
        "photo_url": "https://images.squarespace-cdn.com/content/v1/597925aacd39c3750038d54c/b8e2939c-da8c-43b5-84a1-461936b59842/IMG_1162.jpeg",
    },
    {
        "filename": "tanya-aggarwal.jpg",
        "name": "Tanya Aggarwal",
        "gender": "F",
        "specialties": "Oral Health Therapist",
        "experience": "University of Otago",
        "bio": "University of Otago graduate who moved to Nelson in 2022. Dual scope in dental therapy and hygiene. Works with children and adolescents providing restorative care through Nelson District Health Board.",
        "photo_url": "https://images.squarespace-cdn.com/content/v1/597925aacd39c3750038d54c/d4a84534-94f0-478b-a21f-b57cc99c6f07/IMG_0766.jpg",
    },
    {
        "filename": "liss-kelly.jpg",
        "name": "Liss Kelly",
        "gender": "F",
        "specialties": "Oral Health Therapist",
        "experience": "University of Otago (2016), Postgraduate Diploma in Public Health (2018)",
        "bio": "University of Otago 2016 graduate with a Postgraduate Diploma in Public Health (2018). Extensive experience in preventative and restorative dental care for children and adolescents.",
        "photo_url": "https://images.squarespace-cdn.com/content/v1/597925aacd39c3750038d54c/9f7f683e-6eae-4327-968d-bea89d78acbd/IMG_4610+%283%29.jpeg",
    },
]

for p in practitioners:
    print(f"\n--- {p['name']} ---")
    r = requests.get(p["photo_url"], headers=HEADERS_DL, timeout=30, verify=False)
    print(f"  Download: {r.status_code}, {len(r.content)} bytes")
    if r.status_code != 200 or len(r.content) < 1000:
        print("  SKIP (bad download)")
        continue

    file_path = f"practitioners/{p['filename']}"
    up = requests.post(
        f"{SUPABASE_URL}/storage/v1/object/{BUCKET}/{file_path}",
        headers={"Authorization": f"Bearer {SUPABASE_JWT}", "Content-Type": "image/jpeg", "x-upsert": "true"},
        data=r.content, timeout=30, verify=False,
    )
    print(f"  Upload: {up.status_code}")

    public_url = f"{SUPABASE_URL}/storage/v1/object/public/{BUCKET}/{file_path}"
    sql = f"""
        INSERT INTO clinic_practitioners (clinic_id, name, gender, specialties, experience, bio, photo_url, source_url)
        VALUES (
            {CLINIC_ID},
            $${p['name']}$$,
            '{p['gender']}',
            $${p['specialties']}$$,
            $${p['experience']}$$,
            $${p['bio']}$$,
            '{public_url}',
            'https://www.advanceddental.co.nz/our-dentists'
        );
    """
    print(f"  DB: {db(sql)}")

print("\nDone.")
