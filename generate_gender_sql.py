"""
Generate SQL UPDATE statements for clinic_practitioners gender.
Paste the output into the Supabase SQL editor.
"""
import re
import requests
import gender_guesser.detector as gender_detector

SUPABASE_URL = "https://ankyjpgcocsvvtyyymys.supabase.co"
ANON_KEY = os.environ['SUPABASE_ANON_KEY']
HEADERS = {"apikey": ANON_KEY, "Authorization": f"Bearer {ANON_KEY}"}

# ID-based overrides for names that are ambiguous, parenthetical, or missed by the name lookup
ID_OVERRIDES = {
    31: None,    # Ash Tracy - ambiguous
    94: "F",     # Tabi Cameron
    202: "F",    # Te Maia Johnson-Watson
    205: None,   # Pip Anderson - ambiguous
    230: "F",    # Nicha Nivatvongs
    244: "F",    # Rozeleen Rahiman
    275: None,   # Dr Bayley Anderson - ambiguous
    299: "F",    # Natalyn Tiang
    306: "M",    # Dr. Am Limchalerm (Thai male)
    320: None,   # Bayley Anderson - ambiguous
    362: None,   # Dr Ash Kaimal - ambiguous
    373: None,   # Dr Hua Gao - ambiguous
    1460: "F",   # Dr Pyria
    442: None,   # Dr Bomi Aum - ambiguous
    461: "M",    # Yash Khan
    530: None,   # Yu Ishikawa (Ishi) - ambiguous
    539: "F",    # Jane-Anne Armstrong
    652: "F",    # Airdrie Stuart
    658: "F",    # Dr Maria (Elizma) Schoeman
    692: "M",    # Chase Stephens
    708: "F",    # Dr Binnie Ahamat
    710: None,   # Dr Siemin Theis - ambiguous
    732: "M",    # Chase Stephens
    762: None,   # Dr Sam Schroder - ambiguous
    769: None,   # Dr Siemin Theis - ambiguous
    781: None,   # Dr Sam Schroder - ambiguous
    815: "M",    # Dr Jareth Lau
    821: "M",    # Dr Diogo (DJ) Godoy Zanicotti
    936: None,   # Alex Fang - ambiguous
    941: "F",    # Al-Julanda (AJ)
    942: None,   # Thipa - ambiguous
    950: None,   # Dr Robin Chen - ambiguous
    994: "F",    # Dr Li Ling Cheah
}

OVERRIDES = {
    "ashley": "F", "ash": None, "jo": "F", "sam": None, "alex": None,
    "robin": None, "jayden": "M", "jaden": "M", "morgan": None,
    "lesley": "F", "leslie": None, "tash": "F", "tabi": None,
    "taylah": "F", "tyla": "F", "aleisha": "F", "kerina": "F",
    "fionna": "F", "alianna": "F", "shaylee": "F",
    # South Asian
    "rohit": "M", "asmah": "F", "pandeep": "F", "sherin": "F",
    "chamil": "M", "shorokh": "M", "suhaib": "M", "meena": "F",
    "yasmin": "F", "kasia": "F", "haneen": "F", "arun": "M",
    "amrit": "F", "lawanya": "F", "ajith": "M", "chamara": "M",
    "yasasmi": "F", "pedja": "M", "riccard": "M", "stephano": "M",
    "swati": "F", "pushpreet": "F", "shalini": "F", "divya": "F",
    "bhavya": "F", "harish": "M", "ankit": "M", "purobi": "F",
    "sonali": "F", "aditi": "F", "kamaljit": "F", "rupika": "F",
    "dinesh": "M", "kamal": "M", "rohan": "M", "vishi": "M",
    "jaideep": "M", "sowmiya": "F", "thipa": None, "teshalini": "F",
    "gurpinder": "M", "navin": "M", "imad": "M", "sanya": "F",
    "mustafa": "M", "majd": "M", "nibras": "M", "bash": "M",
    "muskan": "F", "saleema": "F", "taneshia": "F", "loice": "F",
    # East Asian
    "weisong": "M", "yunam": "M", "liying": "F", "hoon": "M",
    "soon": "M", "sheng": "M", "shu-yi": "F", "chuen": "M",
    "sunyoung": "F", "yeehaow": "M", "hyemi": "F", "joo": "F",
    "tina": "F", "thu": "F", "tuyen": "F", "hua": None,
    "wei": "F", "mwaffak": "M", "zaid": "M", "lye": "M",
    "dikesh": "M", "aidan": "M", "ryan": "M", "diogo": "M",
    "jesslyn": "F", "raquel": "F", "ebony-jay": "F", "erina": "F",
    "tamaki": "F", "soo-wee": "F", "lakshmi": "F", "loan": "F",
    "madelina": "F", "bomi": None, "pyria": None,
    # Arabic / Middle Eastern
    "kefilwe": "F", "bara'a": "F", "haneen": "F", "huda": "F",
    "romanah": "F", "omar": "M", "yahya": "M", "salah": "M",
    "hamid": "M", "ahmad": "M", "haidar": "M", "ashish": "M",
    "manish": "M", "naser": "M", "wael": "M", "abu": "M",
    "younes": "M", "emad": "M", "zahra": "F", "amani": "F",
    "mwaffak": "M",
    # Maori / Pacific
    "te": None, "teuila": "F", "ree": "F", "tino": "M", "luka": None,
    "rory": "M",
    # NZ / misc
    "prue": "F", "sherryn": "F", "leeandra": "F", "vinny": "M",
    "belvina": "F", "bernice": "F", "tania": "F", "pip": None,
    "bayley": None, "angus": "M", "liam": "M",
    "ness": "F", "jonty": "M", "senthilkumar": "M", "pedja": "M",
    "warwick": "M", "grahame": "M", "hadrien": "M", "ingo": "M",
    "clarence": "M", "marius": "M", "declan": "M", "shaun": "M",
    "sergio": "M", "gian": "M", "cyrana": "F", "dannika": "F",
    "neisha": "F", "teuila": "F", "ebony": "F", "stacey": "F",
    "nuala": "F", "carike": "F", "larissa": "F", "lysandra": "F",
    "renee": "F", "renée": "F", "madelina": "F", "mélina": "F",
    "melina": "F", "sheyda": "F", "twyla": "F", "twyla": "F",
    "iva": "F", "tia": "F", "reina": "F", "anais": "F",
    "al-julanda": "F", "kamila": "F", "chantelle": "F",
    "catalina": "F", "kali": "F", "alaina": "F", "kira": "F",
    "gabby": "F", "janelle": "F", "jordyn": "F", "chase": "M",
    "hunter": "M", "max": "M", "lester": "M", "gerry": "M",
    "rob": "M", "jed": "M", "tony": "M", "bruce": "M",
    "percival": "M", "roly": "M", "craig": "M", "gareth": "M",
    "pete": "M", "jareth": "M", "diogo": "M", "luka": "M",
    "sinead": "F", "sharna": "F", "sheryne": "F", "lynley": "F",
    "teegan": "F", "immy": "F", "indi": "F", "evonne": "F",
    "binnie": "F", "suh": "F", "li": "F", "dilani": "F",
    "siemin": None, "tabi": "F", "robin": None, "thipa": None,
    "miche": "M", "miché": "M",
}

def extract_first_name(raw):
    s = raw.strip()
    title_gender = None
    if re.match(r"^Mr\.?\s", s, re.IGNORECASE):
        title_gender = "M"
    elif re.match(r"^(Ms|Mrs)\.?\s", s, re.IGNORECASE):
        title_gender = "F"
    name = re.sub(r"^(Dr|Mr|Ms|Mrs|Professor|Prof)\.?\s*", "", s, flags=re.IGNORECASE).strip()
    paren = re.search(r"\(([^)]+)\)", name)
    if paren:
        return paren.group(1).strip().split()[0], title_gender
    return (name.split()[0] if name else ""), title_gender

def infer_gender(first, title_gender, d):
    if title_gender:
        return title_gender
    if not first:
        return None
    low = first.lower()
    if low in OVERRIDES:
        return OVERRIDES[low]
    result = d.get_gender(first)
    if result in ("male", "mostly_male"):
        return "M"
    if result in ("female", "mostly_female"):
        return "F"
    return None

def main():
    d = gender_detector.Detector(case_sensitive=False)
    resp = requests.get(
        f"{SUPABASE_URL}/rest/v1/clinic_practitioners?select=id,name&limit=5000",
        headers=HEADERS,
    )
    resp.raise_for_status()
    rows = resp.json()
    print(f"-- Fetched {len(rows)} practitioners")

    m_ids, f_ids, unknown = [], [], []
    for row in rows:
        rid = row["id"]
        if rid in ID_OVERRIDES:
            g = ID_OVERRIDES[rid]
        else:
            first, title_g = extract_first_name(row["name"] or "")
            g = infer_gender(first, title_g, d)
        if g == "M":
            m_ids.append(rid)
        elif g == "F":
            f_ids.append(rid)
        else:
            unknown.append((rid, row["name"]))

    print(f"-- M: {len(m_ids)}, F: {len(f_ids)}, Unknown: {len(unknown)}\n")

    if m_ids:
        ids = ",".join(str(i) for i in m_ids)
        print(f"UPDATE clinic_practitioners SET gender = 'M' WHERE id IN ({ids});\n")

    if f_ids:
        ids = ",".join(str(i) for i in f_ids)
        print(f"UPDATE clinic_practitioners SET gender = 'F' WHERE id IN ({ids});\n")

    print("-- Unknown (not updated):")
    for id_, name in unknown:
        print(f"--   {id_}: {name}")

if __name__ == "__main__":
    main()
