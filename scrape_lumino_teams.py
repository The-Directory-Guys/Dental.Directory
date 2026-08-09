"""
Scrape practitioner photos from all Lumino clinic meet-our-team pages.
Generates SQL to update photo_url in clinic_practitioners.
"""
import sys
import re
import time
import requests
from bs4 import BeautifulSoup

sys.stdout.reconfigure(encoding='utf-8', errors='replace')

SUPABASE_URL = "https://ankyjpgcocsvvtyyymys.supabase.co"
ANON_KEY = os.environ['SUPABASE_ANON_KEY']
SB_HEADERS = {"apikey": ANON_KEY, "Authorization": f"Bearer {ANON_KEY}"}
WEB_HEADERS = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"}

LUMINO_BASE = "https://lumino.co.nz"

def fetch_lumino_clinics():
    url = f"{SUPABASE_URL}/rest/v1/dental_clinics?select=id,name,city,website&website=ilike.*lumino.co.nz*&business_status=eq.OPERATIONAL&limit=200"
    r = requests.get(url, headers=SB_HEADERS)
    return r.json()

def fetch_practitioners(clinic_id):
    url = f"{SUPABASE_URL}/rest/v1/clinic_practitioners?select=id,name&clinic_id=eq.{clinic_id}"
    r = requests.get(url, headers=SB_HEADERS)
    return r.json()

def scrape_team_page(team_url):
    """Returns list of {name, photo_url} dicts."""
    try:
        r = requests.get(team_url, headers=WEB_HEADERS, timeout=15)
        if r.status_code != 200:
            return []
    except Exception as e:
        print(f"  Error fetching {team_url}: {e}")
        return []

    soup = BeautifulSoup(r.text, "html.parser")

    # Lumino team cards: look for images with /media/ src alongside nearby name text
    members = []

    # Strategy 1: find elements with class containing 'team' or 'staff' or 'member'
    cards = soup.find_all(class_=re.compile(r'team|staff|member|practitioner', re.I))

    for card in cards:
        img = card.find("img", src=re.compile(r"/media/"))
        if not img:
            continue
        # Get the name from a heading or strong tag within the card
        name_el = card.find(["h1","h2","h3","h4","h5","strong","p"])
        if not name_el:
            continue
        name = name_el.get_text(strip=True)
        if len(name) < 3 or len(name) > 80:
            continue
        src = img.get("src", "")
        if not src:
            continue
        # Make absolute and strip query string
        if src.startswith("/"):
            src = LUMINO_BASE + src
        src = src.split("?")[0]
        # Skip generic placeholder images
        if "person.png" in src or "placeholder" in src.lower() or "default" in src.lower():
            continue
        members.append({"name": name, "photo_url": src})

    # Strategy 2: if strategy 1 found nothing, try img[alt] near headings
    if not members:
        for img in soup.find_all("img", src=re.compile(r"/media/")):
            alt = img.get("alt", "").strip()
            src = img.get("src", "").split("?")[0]
            if not alt or len(alt) < 3 or "person.png" in src:
                continue
            if src.startswith("/"):
                src = LUMINO_BASE + src
            members.append({"name": alt, "photo_url": src})

    # Deduplicate by photo_url
    seen = set()
    unique = []
    for m in members:
        if m["photo_url"] not in seen:
            seen.add(m["photo_url"])
            unique.append(m)

    return unique

def normalise(name):
    """Strip Dr/Dr. prefix and lowercase for matching."""
    return re.sub(r"^(Dr\.?|Mr\.?|Ms\.?|Mrs\.?|Prof\.?)\s*", "", name, flags=re.I).strip().lower()

def match_practitioner(scraped_name, practitioners):
    """Return best matching practitioner id or None."""
    norm_scraped = normalise(scraped_name)
    # Exact normalised match
    for p in practitioners:
        if normalise(p["name"]) == norm_scraped:
            return p["id"]
    # Partial: scraped name contained in DB name or vice versa
    for p in practitioners:
        db_norm = normalise(p["name"])
        if norm_scraped in db_norm or db_norm in norm_scraped:
            return p["id"]
    return None

def main():
    clinics = fetch_lumino_clinics()
    print(f"Found {len(clinics)} Lumino clinics\n")

    updates = []   # (practitioner_id, photo_url, practitioner_name, clinic_name)
    no_page = []
    no_match = []

    for clinic in clinics:
        clinic_id = clinic["id"]
        clinic_name = clinic["name"]
        website = clinic.get("website", "")
        if not website:
            continue

        team_url = website.rstrip("/") + "/meet-our-team/"
        practitioners = fetch_practitioners(clinic_id)

        members = scrape_team_page(team_url)

        if not members:
            no_page.append(clinic_name)
            time.sleep(0.3)
            continue

        print(f"[{clinic_name}] {len(members)} members found")

        for m in members:
            pid = match_practitioner(m["name"], practitioners)
            if pid:
                updates.append((pid, m["photo_url"], m["name"], clinic_name))
                print(f"  MATCH  {m['name']} -> id {pid}")
            else:
                no_match.append((m["name"], clinic_name))
                print(f"  NO MATCH: {m['name']}")

        time.sleep(0.5)  # polite delay

    print(f"\n\n=== SUMMARY ===")
    print(f"Updates: {len(updates)}")
    print(f"No team page: {len(no_page)}")
    print(f"No DB match: {len(no_match)}")

    print("\n=== SQL ===")
    for pid, photo_url, name, clinic in updates:
        safe_url = photo_url.replace("'", "''")
        print(f"UPDATE clinic_practitioners SET photo_url = '{safe_url}' WHERE id = {pid}; -- {name} @ {clinic}")

    if no_match:
        print("\n-- Unmatched (not in DB):")
        for name, clinic in no_match:
            print(f"--   {name} @ {clinic}")

if __name__ == "__main__":
    main()
