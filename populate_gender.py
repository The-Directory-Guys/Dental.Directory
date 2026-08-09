"""
Infer gender from practitioner first names and update Supabase.
Maps: male/mostly_male → M, female/mostly_female → F, unknown/andy → null (skip)
"""
import re
import requests
import gender_guesser.detector as gender_detector

SUPABASE_URL = "https://ankyjpgcocsvvtyyymys.supabase.co"
ANON_KEY = os.environ['SUPABASE_ANON_KEY']
HEADERS = {
    "apikey": ANON_KEY,
    "Authorization": f"Bearer {ANON_KEY}",
    "Content-Type": "application/json",
    "Prefer": "return=minimal",
}

# Known ambiguous first names that the library misclassifies
OVERRIDES = {
    # Ambiguous English
    "ashley": "F", "ash": None, "jo": "F", "sam": None, "alex": None,
    "robin": None, "jayden": "M", "jaden": "M", "morgan": None,
    "lesley": "F", "leslie": None, "tash": "F", "tabi": None,
    "taylah": "F", "tyla": "F", "aleisha": "F", "kerina": "F",
    "fionna": "F", "alianna": "F", "shaylee": "F",
    # South Asian
    "rohit": "M", "asmah": "F", "pandeep": "F", "sherin": "F",
    "chamil": "M", "shorokh": "M", "suhaib": "M", "meena": "F",
    "yasmin": "F", "kasia": "F", "haneen": "F", "arun": "M",
    # East Asian
    "weisong": "M", "yunam": "M", "liying": "F", "hoon": "M",
    "soon": "M", "sheng": "M", "shu-yi": "F",
    # African / other
    "kefilwe": "F", "bara'a": "F",
    # Maori / Pacific
    "te": None,
    # Sri Lankan / South Asian extras
    "amrit": "F", "lawanya": "F", "ajith": "M", "chamara": "M",
    "yasasmi": "F", "pedja": "M", "riccard": "M", "stephano": "M",
    # Thai / SE Asian
    "nicha": "F", "natalyn": "F", "rozeleen": "F",
    # Other
    "prue": "F", "sherryn": "F", "leeandra": "F", "vinny": "M",
    "belvina": "F", "bernice": "F", "tania": "F", "pip": None,
    "bayley": None, "angus": "M", "liam": "M",
}

def extract_first_name(raw: str) -> tuple:
    """Return (first_name, title_gender) where title_gender is M/F/None from Mr/Ms/Mrs."""
    s = raw.strip()
    title_gender = None
    if re.match(r"^Mr\.?\s", s, re.IGNORECASE):
        title_gender = "M"
    elif re.match(r"^(Ms|Mrs)\.?\s", s, re.IGNORECASE):
        title_gender = "F"
    # Strip all titles (Dr, Mr, Ms, Mrs)
    name = re.sub(r"^(Dr|Mr|Ms|Mrs)\.?\s*", "", s, flags=re.IGNORECASE).strip()
    # Handle parenthetical preferred names: "Shu-yi Lee (Susan)" -> "Susan"
    paren = re.search(r"\(([^)]+)\)", name)
    if paren:
        return paren.group(1).strip().split()[0], title_gender
    return (name.split()[0] if name else ""), title_gender


def infer_gender(first: str, title_gender, d) -> str | None:
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

    # Fetch all practitioners
    resp = requests.get(
        f"{SUPABASE_URL}/rest/v1/clinic_practitioners?select=id,name&limit=5000",
        headers=HEADERS,
    )
    resp.raise_for_status()
    rows = resp.json()
    print(f"Fetched {len(rows)} practitioners")

    updates = {"M": [], "F": [], None: []}
    for row in rows:
        first, title_g = extract_first_name(row["name"] or "")
        g = infer_gender(first, title_g, d)
        updates[g].append(row["id"])

    print(f"  M: {len(updates['M'])}")
    print(f"  F: {len(updates['F'])}")
    print(f"  Unknown (skipped): {len(updates[None])}")

    # Show unknowns so we can review
    unknown_names = [r["name"] for r in rows if r["id"] in updates[None]]
    print(f"\nUnknown names sample: {unknown_names[:30]}")

    confirm = input("\nProceed with updating M and F records? (y/n): ").strip().lower()
    if confirm != "y":
        print("Aborted.")
        return

    # Update in batches by gender value
    for gender_val in ("M", "F"):
        ids = updates[gender_val]
        updated = 0
        for i in range(0, len(ids), 50):
            batch = ids[i:i+50]
            id_filter = "(" + ",".join(f"id.eq.{id_}" for id_ in batch) + ")"
            r = requests.patch(
                f"{SUPABASE_URL}/rest/v1/clinic_practitioners?or={id_filter}",
                headers=HEADERS,
                json={"gender": gender_val},
            )
            if r.ok:
                updated += len(batch)
            else:
                print(f"  Error batch {i}: {r.status_code} {r.text}")
        print(f"Updated {updated} records -> {gender_val}")

    print("\nDone.")


if __name__ == "__main__":
    main()
