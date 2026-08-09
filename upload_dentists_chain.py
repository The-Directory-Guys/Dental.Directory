import sys, io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

import requests
import os
import re
from dotenv import load_dotenv

load_dotenv(r"c:\Users\Ciaran\Desktop\Dental_Directory\.env")

SUPABASE_URL = os.environ["SUPABASE_URL"]
SUPABASE_JWT = os.environ['SUPABASE_JWT']
MGMT_KEY = os.environ["SUPABASE_MANAGEMENT_KEY"]
BUCKET = "practitioner-photos"

HEADERS_DL = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/124.0.0.0 Safari/537.36",
    "Accept": "image/*,*/*",
}

def db_query(sql):
    r = requests.post(
        "https://api.supabase.com/v1/projects/ankyjpgcocsvvtyyymys/database/query",
        headers={"Authorization": f"Bearer {MGMT_KEY}", "Content-Type": "application/json"},
        json={"query": sql}, timeout=30, verify=False,
    )
    return r.json() if r.status_code in (200, 201) else []

def db_exec(sql):
    r = requests.post(
        "https://api.supabase.com/v1/projects/ankyjpgcocsvvtyyymys/database/query",
        headers={"Authorization": f"Bearer {MGMT_KEY}", "Content-Type": "application/json"},
        json={"query": sql}, timeout=30, verify=False,
    )
    if r.status_code not in (200, 201):
        print(f"    DB ERROR: {r.text[:300]}")
    return r.status_code

def name_slug(name):
    return re.sub(r"[^a-z0-9]+", "-", name.lower()).strip("-")

def ext_from_url(url):
    path = url.split("?")[0]
    return path.rsplit(".", 1)[-1].lower()

def upload_photo(filename, data, ext):
    ctype = "image/png" if ext == "png" else "image/jpeg"
    file_path = f"practitioners/{filename}"
    r = requests.post(
        f"{SUPABASE_URL}/storage/v1/object/{BUCKET}/{file_path}",
        headers={"Authorization": f"Bearer {SUPABASE_JWT}", "Content-Type": ctype, "x-upsert": "true"},
        data=data, timeout=60, verify=False,
    )
    public_url = f"{SUPABASE_URL}/storage/v1/object/public/{BUCKET}/{file_path}"
    return r.status_code, public_url

LOCATIONS = [
    {
        "clinic_id": 1542,
        "source_url": "https://www.dentiststaradale.co.nz/expertise/meet-the-team/",
        "base_url": "https://www.dentiststaradale.co.nz",
        "tag": "taradale",
        "team": [
            {"name": "Dr Sean Phillips", "gender": "M", "specialties": "General Dentist",
             "experience": "BDS, GradDipClinDent Full Face Orthodontics (Bolton)",
             "photo_path": "/media/1681/sean-philips.jpg?width=360&quality=80"},
            {"name": "Dr Mei Ironside", "gender": "F", "specialties": "General Dentist",
             "experience": "BDS (Otago), GradDip Digital Orthodontics",
             "photo_path": "/media/1633/mei-ironside.jpg?width=360&quality=80"},
            {"name": "Li-Ann", "gender": "F", "specialties": "General Dentist",
             "experience": "BDS (Otago)",
             "photo_path": "/media/1861/profile-image-li-ann.jpg?width=360&quality=80"},
            {"name": "Jodie Phillips", "gender": "F", "specialties": "Oral Health Therapist",
             "experience": "Degree in Oral Health (AUT)",
             "photo_path": "/media/1677/jodie.jpg?width=360&quality=80"},
            {"name": "Sue", "gender": "F", "specialties": "Oral Health Therapist",
             "experience": None,
             "photo_path": "/media/1862/profile-image-sue.jpg?width=360&quality=80"},
            {"name": "Abigail", "gender": "F", "specialties": "Dental Assistant",
             "experience": None,
             "photo_path": "/media/1860/profile-image-abigail.jpg?width=360&quality=80"},
            {"name": "Alycia", "gender": "F", "specialties": "Dental Assistant",
             "experience": None,
             "photo_path": "/media/1657/alycia.jpg?width=360&quality=80"},
            {"name": "Eva", "gender": "F", "specialties": "Dental Assistant",
             "experience": None,
             "photo_path": "/media/1858/profile-image-eva.jpg?width=360&quality=80"},
            {"name": "Janaya", "gender": "F", "specialties": "Dental Assistant",
             "experience": None,
             "photo_path": "/media/1859/profile-image-janaya.jpg?width=360&quality=80"},
            {"name": "Kelly", "gender": "F", "specialties": "Dental Assistant",
             "experience": None,
             "photo_path": "/media/1632/kelly.jpg?width=360&quality=80"},
            {"name": "Phoebe", "gender": "F", "specialties": "Dental Assistant",
             "experience": None,
             "photo_path": "/media/1857/profile-image-phoebe.jpg?width=360&quality=80"},
            {"name": "Hannah", "gender": "F", "specialties": "Receptionist",
             "experience": None,
             "photo_path": "/media/1850/hannah.jpeg?width=360&quality=80"},
        ],
    },
    {
        "clinic_id": 1217,
        "source_url": "https://www.dentistsrotorua.co.nz/expertise/meet-the-team/",
        "base_url": "https://www.dentistsrotorua.co.nz",
        "tag": "rotorua",
        "team": [
            {"name": "Dr Gaius Zhang", "gender": "M", "specialties": "General Dentist",
             "experience": "BDS (Otago)",
             "photo_path": "/media/1621/gaius.jpg"},
            {"name": "Dr Danny Lee", "gender": "M", "specialties": "General Dentist",
             "experience": "BDS with Distinction (Otago, 2015)",
             "photo_path": "/media/1627/danny.jpg"},
            {"name": "Dr Sharleen Lu", "gender": "F", "specialties": "General Dentist",
             "experience": "BDS (Otago), Diploma in Orthodontics",
             "photo_path": "/media/1815/processed-380a0369-bace-4664-8834-541f1e3d3a24.jpeg"},
            {"name": "Bonnie Lu", "gender": "F", "specialties": "Oral Health Therapist",
             "experience": "Degree in Oral Health (AUT, 2024)",
             "photo_path": "/media/1799/bonnie.png"},
            {"name": "Sameera", "gender": "F", "specialties": "Oral Health Therapist",
             "experience": None,
             "photo_path": "/media/1800/sameera.png"},
            {"name": "Amber", "gender": "F", "specialties": "Dental Assistant",
             "experience": None,
             "photo_path": "/media/1803/amber.jpg"},
            {"name": "Cheyenne", "gender": "F", "specialties": "Dental Assistant",
             "experience": None,
             "photo_path": "/media/1671/chey.jpg"},
            {"name": "Jayde", "gender": "F", "specialties": "Dental Assistant",
             "experience": None,
             "photo_path": "/media/1804/jayde.png"},
            {"name": "Kiara O'Leary", "gender": "F", "specialties": "Dental Assistant",
             "experience": None,
             "photo_path": "/media/1802/kiara.jpg"},
            {"name": "Tammy", "gender": "F", "specialties": "Dental Assistant",
             "experience": None,
             "photo_path": "/media/1801/tammy.png"},
            {"name": "Dallas", "gender": "F", "specialties": "Receptionist",
             "experience": None,
             "photo_path": "/media/1843/dallas.jpg"},
            {"name": "Tara", "gender": "F", "specialties": "Receptionist",
             "experience": None,
             "photo_path": "/media/1797/tara.jpg"},
        ],
    },
    {
        "clinic_id": 2116,
        "source_url": "https://www.dentiststaupo.co.nz/expertise/meet-the-team/",
        "base_url": "https://www.dentiststaupo.co.nz",
        "tag": "taupo",
        "team": [
            {"name": "Dr Arjuna Rajasingham", "gender": "M", "specialties": "General Dentist",
             "experience": "BDS (Otago, 1999), Diploma in Orthodontics (London City University)",
             "photo_path": "/media/1515/arjuna-rajasingham.jpg"},
            {"name": "Dr Brian Ng", "gender": "M", "specialties": "General Dentist",
             "experience": "BDS (Otago, 2015)",
             "photo_path": "/media/1500/taupo-brian.jpg"},
            {"name": "Dr Colette Khoo", "gender": "F", "specialties": "General Dentist",
             "experience": "BDS (Otago, 2015)",
             "photo_path": "/media/1501/taupo-collete.jpg"},
            {"name": "Dr Zaiyou Chen", "gender": "M", "specialties": "General Dentist",
             "experience": "BDS with First Class Honours (Otago)",
             "photo_path": "/media/1660/zai.jpeg"},
            {"name": "Moyi Dai", "gender": "F", "specialties": "General Dentist",
             "experience": "Dental Clinician (University of Queensland)",
             "photo_path": "/media/1854/img_4686.jpeg"},
            {"name": "Dr Olivia Liong", "gender": "F", "specialties": "General Dentist",
             "experience": None,
             "photo_path": "/media/1856/img_4682.jpeg"},
            {"name": "Alana", "gender": "F", "specialties": "Oral Health Therapist",
             "experience": "Bachelor of Oral Health (AUT)",
             "photo_path": "/media/1836/alana.jpeg"},
            {"name": "Lee-Anne", "gender": "F", "specialties": "Orthodontic Auxiliary",
             "experience": None,
             "photo_path": "/media/1842/lee-anne.jpeg"},
            {"name": "Jade", "gender": "F", "specialties": "Dental Assistant",
             "experience": None,
             "photo_path": "/media/1560/jade.jpg"},
            {"name": "Sambi", "gender": "F", "specialties": "Dental Assistant",
             "experience": "NZDA (2022)",
             "photo_path": "/media/1488/sambi.jpg"},
            {"name": "Danica", "gender": "F", "specialties": "Dental Assistant",
             "experience": None,
             "photo_path": "/media/1841/danica.jpeg"},
            {"name": "Lizzie", "gender": "F", "specialties": "Dental Assistant",
             "experience": None,
             "photo_path": "/media/1837/lizzie.jpeg"},
            {"name": "Regan", "gender": "F", "specialties": "Dental Assistant",
             "experience": None,
             "photo_path": "/media/1838/regan.jpeg"},
            {"name": "Serene", "gender": "F", "specialties": "Dental Assistant",
             "experience": None,
             "photo_path": "/media/1839/serene.jpeg"},
            {"name": "Anya", "gender": "F", "specialties": "Dental Assistant",
             "experience": None,
             "photo_path": "/media/1853/img_4685.jpeg"},
            {"name": "Hannah", "gender": "F", "specialties": "Dental Assistant",
             "experience": None,
             "photo_path": "/media/1834/hannah.jpeg"},
            {"name": "Kylie", "gender": "F", "specialties": "Office Manager",
             "experience": None,
             "photo_path": "/media/1646/img_5871.jpeg"},
            {"name": "Annette", "gender": "F", "specialties": "Receptionist",
             "experience": None,
             "photo_path": "/media/1835/annette.jpeg"},
            {"name": "Murphy", "gender": "F", "specialties": "Receptionist",
             "experience": None,
             "photo_path": "/media/1855/img_4668.jpeg"},
        ],
    },
    {
        "clinic_id": 1218,
        "source_url": "https://www.dentiststauranga.co.nz/expertise/meet-the-team/",
        "base_url": "https://www.dentiststauranga.co.nz",
        "tag": "tauranga",
        "team": [
            {"name": "Dr Alastair Miller", "gender": "M", "specialties": "General Dentist",
             "experience": "BDS (Otago, 1988)",
             "photo_path": "/media/1506/alastair-miller.jpg"},
            {"name": "Dr Graeme Lynam", "gender": "M", "specialties": "General Dentist",
             "experience": "BDS (Otago, 1978)",
             "photo_path": "/media/1123/graeme-lynam.jpg"},
            {"name": "Dr Bodon Li", "gender": "M", "specialties": "General Dentist",
             "experience": "BDS (Otago)",
             "photo_path": "/media/1659/bodon.jpeg"},
            {"name": "Dr Aishah Na", "gender": "F", "specialties": "General Dentist",
             "experience": "BDS (Otago)",
             "photo_path": "/media/1637/aishah.jpg"},
            {"name": "Kailey Hopper", "gender": "F", "specialties": "Oral Health Therapist",
             "experience": "Degree in Oral Health Therapy (Otago)",
             "photo_path": "/media/1603/kailey-hopper.jpg"},
            {"name": "Ann Maree Roebuck", "gender": "F", "specialties": "Office Manager",
             "experience": "NZDA Qualified",
             "photo_path": "/media/1508/ann-maree-roebuck.jpg"},
            {"name": "Alicia Upfold", "gender": "F", "specialties": "Dental Assistant",
             "experience": None,
             "photo_path": "/media/1604/alicia-upfold-da.jpg"},
            {"name": "Annette Lee", "gender": "F", "specialties": "Dental Assistant",
             "experience": "Dental Nurse Training School",
             "photo_path": "/media/1509/annette-lee.jpg"},
            {"name": "Avalon Williams", "gender": "F", "specialties": "Dental Assistant",
             "experience": None,
             "photo_path": "/media/1715/avalon-williams.jpg"},
            {"name": "Bianca", "gender": "F", "specialties": "Dental Assistant",
             "experience": None,
             "photo_path": "/media/1830/bianca.jpg"},
            {"name": "Chris Bertram", "gender": "F", "specialties": "Receptionist",
             "experience": None,
             "photo_path": "/media/1716/chris-bertram.jpg"},
            {"name": "Nicola Naylor", "gender": "F", "specialties": "Dental Assistant",
             "experience": "Dental Nursing (since 1990)",
             "photo_path": "/media/1605/nicola-naylor.jpg"},
        ],
    },
    {
        "clinic_id": 1618,
        "source_url": "https://www.dentistswhanganui.co.nz/expertise/meet-the-team/",
        "base_url": "https://www.dentistswhanganui.co.nz",
        "tag": "whanganui",
        "team": [
            {"name": "Dr Adam Durning", "gender": "M", "specialties": "General Dentist",
             "experience": "BDS (Otago, 1990), Diplomat World Congress of Micro Dentistry",
             "photo_path": "/media/1517/img_2364.jpg"},
            {"name": "Dr Jamie Searle", "gender": "M", "specialties": "General Dentist",
             "experience": "BDS, Member NZDA & NZIMID",
             "photo_path": "/media/1519/img_2325.jpg"},
            {"name": "Dr Mark Huang", "gender": "M", "specialties": "General Dentist",
             "experience": "BDS (Otago, 2004)",
             "photo_path": "/media/1518/img_2221.jpg"},
            {"name": "Dr Sue Cheah", "gender": "F", "specialties": "General Dentist",
             "experience": "BDS (Otago, 2015)",
             "photo_path": "/media/1521/img_2353.jpg"},
            {"name": "Dr Tony Lin", "gender": "M", "specialties": "General Dentist",
             "experience": "BDS (Otago, 2015)",
             "photo_path": "/media/1520/img_2343.jpg"},
            {"name": "Dr Jino Kunnetthedam", "gender": "M", "specialties": "General Dentist",
             "experience": "BDS with Distinction (Otago)",
             "photo_path": "/media/1651/jino.jpg"},
            {"name": "Dr Michael Zhang", "gender": "M", "specialties": "General Dentist",
             "experience": "BDS (Otago)",
             "photo_path": "/media/1649/michael.jpg"},
            {"name": "Louise", "gender": "F", "specialties": "Dental Hygienist",
             "experience": None,
             "photo_path": "/media/1529/img_2296.jpg"},
            {"name": "Richelle", "gender": "F", "specialties": "Dental Hygienist",
             "experience": None,
             "photo_path": "/media/1528/img_2292.jpg"},
            {"name": "Jeimy", "gender": "F", "specialties": "Laboratory Manager",
             "experience": "Degree in Dentistry (University of Colombia)",
             "photo_path": "/media/1530/img_2380.jpg"},
            {"name": "Kelly", "gender": "F", "specialties": "Office Manager",
             "experience": None,
             "photo_path": "/media/1525/img_2340.jpg"},
            {"name": "Acacia", "gender": "F", "specialties": "Dental Assistant",
             "experience": None,
             "photo_path": "/media/1531/img_2265.jpg"},
            {"name": "Ani", "gender": "F", "specialties": "Dental Assistant",
             "experience": None,
             "photo_path": "/media/1685/ani.jpg"},
            {"name": "Danielle", "gender": "F", "specialties": "Receptionist",
             "experience": None,
             "photo_path": "/media/1496/dani.jpg"},
            {"name": "Grace", "gender": "F", "specialties": "Dental Assistant",
             "experience": None,
             "photo_path": "/media/1871/grace.jpeg"},
            {"name": "Jessi", "gender": "F", "specialties": "Dental Assistant",
             "experience": None,
             "photo_path": "/media/1443/img_2335.jpg"},
            {"name": "Kendall", "gender": "F", "specialties": "Laboratory Assistant",
             "experience": None,
             "photo_path": "/media/1532/img_2275.jpg"},
            {"name": "Mahalia", "gender": "F", "specialties": "Dental Assistant",
             "experience": None,
             "photo_path": "/media/1831/mahalia.jpg"},
            {"name": "Melissa", "gender": "F", "specialties": "Dental Assistant",
             "experience": None,
             "photo_path": "/media/1872/melissa.jpeg"},
            {"name": "Milly-Rose", "gender": "F", "specialties": "Dental Assistant",
             "experience": None,
             "photo_path": "/media/1873/milly-rose.jpeg"},
            {"name": "Mya", "gender": "F", "specialties": "Receptionist",
             "experience": None,
             "photo_path": "/media/1832/mya.jpg"},
            {"name": "Theo", "gender": "M", "specialties": "Sterilisation Technician",
             "experience": None,
             "photo_path": "/media/1654/theo.jpg"},
        ],
    },
]

for loc in LOCATIONS:
    clinic_id = loc["clinic_id"]
    print(f"\n{'='*60}")
    print(f"Clinic {clinic_id} — {loc['tag'].upper()}")
    print(f"{'='*60}")

    # Check existing practitioners
    existing_rows = db_query(f"SELECT name FROM clinic_practitioners WHERE clinic_id = {clinic_id}")
    existing_names = {r["name"].lower() for r in existing_rows}
    print(f"  Existing: {len(existing_names)} practitioners")

    for p in loc["team"]:
        name = p["name"]
        if name.lower() in existing_names:
            print(f"  SKIP (exists): {name}")
            continue

        print(f"\n  --- {name} ---")
        photo_url = loc["base_url"] + p["photo_path"]
        ext = ext_from_url(photo_url)
        filename = f"{name_slug(name)}-{loc['tag']}.{ext}"

        # Download photo
        try:
            r = requests.get(photo_url, headers=HEADERS_DL, timeout=30, verify=False)
            print(f"    Download: {r.status_code}, {len(r.content)} bytes")
            if r.status_code != 200 or len(r.content) < 3000:
                print("    SKIP (bad download)")
                continue
            img_data = r.content
        except Exception as e:
            print(f"    SKIP (error: {e})")
            continue

        # Upload to Supabase storage
        up_status, public_url = upload_photo(filename, img_data, ext)
        print(f"    Upload: {up_status} → {filename}")

        # Insert DB row
        exp_val = f"$${p['experience']}$$" if p["experience"] else "NULL"
        sql = f"""
            INSERT INTO clinic_practitioners
              (clinic_id, name, gender, specialties, experience, photo_url, source_url)
            VALUES
              ({clinic_id}, $${name}$$, '{p["gender"]}', $${p["specialties"]}$$,
               {exp_val}, '{public_url}', '{loc["source_url"]}');
        """
        status = db_exec(sql)
        print(f"    DB insert: {status}")

print("\n\nDone.")
